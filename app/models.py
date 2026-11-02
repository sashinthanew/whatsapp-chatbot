from pydantic import BaseModel
from typing import List, Optional

class Message(BaseModel):
    role: str  # "user" or "model"
    content: str

class ChatRequest(BaseModel):
    query: str
    history: Optional[List[Message]] = []

class SourceChunk(BaseModel):
    course: str
    type: str
    score: float

class ChatResponse(BaseModel):
    answer: str
    sources: List[str]
    retrieved_chunks: List[SourceChunk]