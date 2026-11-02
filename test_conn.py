# test_conn.py
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()
uri = os.getenv("MONGODB_URI")
print("URI prefix:", uri[:30] + "...")  # Don't print the full password

try:
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    print("✅ Connection successful!")
except Exception as e:
    print("❌ Connection failed:", e)