# core/config.py
import os
from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase



class DataBase:
    client: AsyncMongoClient|None = None
    db: AsyncDatabase|None = None

MONGO_DB = DataBase()

DATABASE_NAME = "survey_db"
MONGO_DATABASE_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")


SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY", "your-super-secret-key-for-sessions-CHANGE-ME") # IMPORTANT: Change this in prod!
# For production, ensure this is a strong, randomly generated key and stored securely.

# Password Hashing Algorithm
PWD_ALGORITHM = "bcrypt"

ALLOWED_ORIGINS = ['*'] # Everything for now
