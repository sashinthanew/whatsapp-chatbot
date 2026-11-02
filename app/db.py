from pymongo import MongoClient
from urllib.parse import quote_plus
from app.config import MONGODB_URI, DB_NAME, COLLECTION_NAME

_client = None

def _build_uri(raw_uri: str) -> str:
    if not raw_uri.startswith("mongodb"):
        return raw_uri
    scheme, rest = raw_uri.split("://", 1)
    if "@" not in rest:
        return raw_uri
    userinfo, hostpart = rest.rsplit("@", 1)
    if ":" not in userinfo:
        return raw_uri
    user, password = userinfo.split(":", 1)
    safe_user = quote_plus(user)
    safe_pass = quote_plus(password)
    return f"{scheme}://{safe_user}:{safe_pass}@{hostpart}"

def get_collection():
    global _client
    if _client is None:
        _client = MongoClient(_build_uri(MONGODB_URI))
    return _client[DB_NAME][COLLECTION_NAME]