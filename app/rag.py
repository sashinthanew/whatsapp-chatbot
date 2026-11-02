from openai import OpenAI
import os
import math
import google.generativeai as genai
from app.db import get_collection
from app.config import GEMINI_API_KEY, VECTOR_INDEX_NAME, TOP_K, THRESHOLD, EMBEDDING_DIM

# Initialize Groq client using OpenAI SDK
groq_client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.getenv("GROQ_API_KEY")  # Add this to your .env file
)

genai.configure(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = """You are a friendly, helpful course advisor for an educational institution.

STRICT RULES:
1. FACTUAL ACCURACY: For any specific course details (fees, modules, duration, entry requirements, careers), you MUST answer ONLY using the provided context. Do not invent numbers or facts.
2. MISSING FACTS: If a user asks a specific factual question (e.g., "What is the fee for Medicine?") and it is NOT in the context, say: "I don't have those specific details right now, but our registration team can help you with that."
3. GENERAL CHAT: If a user asks a general question (e.g., "Can I pay in installments?", "Do you offer online classes?", "How do I register?"), DO NOT say "I don't have that information." Instead, reply naturally: "That's a great question! For specific details about payments/online classes, please connect with our registration team. They will guide you through the process."
4. REGISTRATION HANDOFF: You do NOT process registrations. If the student wants to register, say: "I'd love to help you get started! Please share your name, phone number, and the course you're interested in, and I'll connect you with our registration team."
5. TONE: Keep answers clear, warm, and professional. Use bullet points for lists.
"""

def normalize(vec):
    norm = math.sqrt(sum(x * x for x in vec))
    if norm == 0:
        return vec
    return [x / norm for x in vec]

def embed_query(text):
    result = genai.embed_content(
        model="models/gemini-embedding-001",
        content=text,
        task_type="retrieval_query",
        output_dimensionality=EMBEDDING_DIM
    )
    return normalize(result["embedding"])

def retrieve(query_vector):
    col = get_collection()
    pipeline = [
        {
            "$vectorSearch": {
                "index": VECTOR_INDEX_NAME,
                "path": "embedding",
                "queryVector": query_vector,
                "numCandidates": 50,
                "limit": TOP_K
            }
        },
        {
            "$project": {
                "_id": 0,
                "text": 1,
                "chunk_type": 1,
                "course_name": 1,
                "source": 1,
                "score": {"$meta": "vectorSearchScore"}
            }
        }
    ]
    return list(col.aggregate(pipeline))

def generate_answer(query, chunks, history):
    filtered = [c for c in chunks if c["score"] >= THRESHOLD]

    if not filtered:
        return {
            "answer": "I don't have that information — please contact our registration team for details.",
            "sources": [],
            "retrieved_chunks": []
        }

    context = "\n\n".join([f"[{c['chunk_type']}] {c['text']}" for c in filtered])

    # Build messages for OpenAI-compatible API
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT + f"\n\nContext:\n{context}"}
    ]
    
    # Add history (convert your frontend history format to OpenAI format)
    for h in history:
        # Pydantic objects use dot notation (h.role), not dictionary brackets (h["role"])
        role = "assistant" if h.role == "model" else h.role
        messages.append({"role": role, "content": h.content})
        
    messages.append({"role": "user", "content": query})

    # Call Groq (using a capable free model)
    response = groq_client.chat.completions.create(
       model="openai/gpt-oss-120b",  # Or "llama-3.1-8b-instant" for faster/cheaper
        messages=messages,
        temperature=0.2
    )

    answer_text = response.choices[0].message.content

    return {
        "answer": answer_text,
        "sources": list(set([c["source"] for c in filtered])),
        "retrieved_chunks": [{"course": c["course_name"], "type": c["chunk_type"], "score": round(c["score"], 3)} for c in filtered]
    }