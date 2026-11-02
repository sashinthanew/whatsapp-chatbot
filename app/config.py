import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DB_NAME = os.getenv("DB_NAME", "course_advisor")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "course_chunks")
VECTOR_INDEX_NAME = os.getenv("VECTOR_INDEX_NAME", "vector_index")

# RAG parameters (matching your spec)
TOP_K = 4              # your spec: "the best 4 chunks"
THRESHOLD = 0.72       # your spec: minimum similarity score
EMBEDDING_DIM = 768    # Gemini embedding dimension