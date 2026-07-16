from pymongo import MongoClient

from app.config import MONGODB_URI

client = MongoClient(
    MONGODB_URI,
    serverSelectionTimeoutMS=3000,
    tz_aware=True,
)

db = client["main"]
