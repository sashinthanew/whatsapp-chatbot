from pathlib import Path
from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from app.models import ChatRequest
from app.rag import embed_query, retrieve, generate_answer
import httpx
import os
from dotenv import load_dotenv

# Load the environment variables from the .env file
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="Course Advisor RAG")

# ==========================================
# READ CREDENTIALS FROM .env FILE (Safe & Secure)
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
# ==========================================

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
def index():
    return FileResponse(str(STATIC_DIR / "index.html"))

# --- 1. YOUR WEB CHAT ---
@app.post("/api/chat")
def chat(req: ChatRequest):
    try:
        if not req.query.strip():
            return {"answer": "Please ask a question about our courses.", "sources": [], "retrieved_chunks": []}

        embed_text = req.query
        for h in reversed(req.history):
            if h.role == "user":
                embed_text = h.content + " " + req.query
                break

        qv = embed_query(embed_text)
        chunks = retrieve(qv)
        result = generate_answer(req.query, chunks, req.history)
        
        return result
    except Exception as e:
        print("\n=== FATAL BACKEND ERROR ===")
        import traceback
        traceback.print_exc()
        print("===========================\n")
        return JSONResponse(
            status_code=500,
            content={"answer": f"Backend error: {str(e)}", "sources": [], "retrieved_chunks": []}
        )

# --- 2. WHATSAPP WEBHOOK VERIFICATION ---
@app.get("/webhook")
async def verify_webhook(request: Request):
    params = request.query_params
    if params.get("hub.mode") == "subscribe" and params.get("hub.verify_token") == VERIFY_TOKEN:
        return Response(content=params.get("hub.challenge"), media_type="text/plain")
    return Response(content="Verification failed", status_code=403)

# --- 3. WHATSAPP INCOMING MESSAGES ---
@app.post("/webhook")
async def receive_whatsapp_message(request: Request):
    body = await request.json()
    
    try:
        entry = body["entry"][0]["changes"][0]["value"]
        
        if "messages" not in entry:
            return {"status": "ok"}
            
        message = entry["messages"][0]
        
        if "text" not in message:
            return {"status": "ok"}
            
        user_text = message["text"]["body"]
        sender_phone = message["from"]
        
        print(f"\n📱 WhatsApp Message from {sender_phone}: {user_text}")
        
        qv = embed_query(user_text)
        chunks = retrieve(qv)
        result = generate_answer(user_text, chunks, [])
        reply_text = result["answer"]
        
        print(f"🤖 Bot Replying: {reply_text}")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages",
                headers={"Authorization": f"Bearer {WHATSAPP_TOKEN}"},
                json={
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": sender_phone,
                    "type": "text",
                    "text": {"body": reply_text}
                }
            )
            if response.status_code != 200:
                print(f"❌ WhatsApp API Error: {response.text}")

    except Exception as e:
        print(f"Webhook Error: {e}")

    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)