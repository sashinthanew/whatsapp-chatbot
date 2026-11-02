import google.generativeai as genai
import math
from app.db import get_collection
from app.config import GEMINI_API_KEY, VECTOR_INDEX_NAME, EMBEDDING_DIM

genai.configure(api_key=GEMINI_API_KEY)

def normalize(vec):
    norm = math.sqrt(sum(x * x for x in vec))
    return [x / norm for x in vec] if norm else vec

def embed(text):
    r = genai.embed_content(
        model="models/gemini-embedding-001",
        content=text,
        task_type="retrieval_query",
        output_dimensionality=EMBEDDING_DIM
    )
    return normalize(r["embedding"])

col = get_collection()
qv = embed("What modules does BSc Data Science have?")

results = list(col.aggregate([
    {"$vectorSearch": {"index": VECTOR_INDEX_NAME, "path": "embedding",
                       "queryVector": qv, "numCandidates": 50, "limit": 4}},
    {"$project": {"_id": 0, "text": 1, "chunk_type": 1, "course_name": 1,
                  "score": {"$meta": "vectorSearchScore"}}}
]))

print(f"Found {len(results)} chunks:")
for r in results:
    print(f"  [{r['score']:.3f}] {r['course_name']} — {r['chunk_type']}")
    print(f"         {r['text'][:80]}")