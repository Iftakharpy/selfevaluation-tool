import asyncio
from pymongo import AsyncMongoClient
from .settings import MONGO_DATABASE_URL, DATABASE_NAME, MONGO_DB


async def connect_to_mongo():
    # MODIFIED: Check if client is already connected and on the current loop
    current_loop = asyncio.get_running_loop()
    if MONGO_DB.client is not None and hasattr(MONGO_DB.client, '_loop') and MONGO_DB.client._loop == current_loop:
        # print("MongoDB client already connected on the current loop.")
        if MONGO_DB.db is None: # Ensure DB object is also set
             MONGO_DB.db = MONGO_DB.client[DATABASE_NAME]
        return

    # print("Connecting to MongoDB...")
    # If closing an old client from a different loop, do it carefully or let it be.
    # For tests, this path (creating a new client) will likely be taken by TestClient's lifespan.
    if MONGO_DB.client is not None:
        # print("Closing existing MongoDB client before creating a new one...")
        # This is tricky if the old client is on a different, now-closed loop.
        # Better to ensure connect_to_mongo is called only once with the right loop if possible.
        # For now, let's assume we overwrite.
        pass # await close_mongo_connection() # Be careful with this

    client = AsyncMongoClient(MONGO_DATABASE_URL) # This will bind to current_loop
    MONGO_DB.client = client
    # MONGO_DB.client.get_io_loop = asyncio.get_running_loop # Deprecated way to set loop
    
    # The client is bound to the loop it's created on.
    # Ensure a command is run to actually connect and check.
    try:
        await MONGO_DB.client.admin.command('ping') # Or client.server_info()
        MONGO_DB.db = MONGO_DB.client[DATABASE_NAME]
        # print(f"Successfully connected to MongoDB! Client loop: {id(MONGO_DB.client._loop)}, DB: {MONGO_DB.db.name}")
    except Exception as e:
        # print(f"Failed to connect/ping MongoDB: {e}")
        MONGO_DB.client = None # Ensure client is None on failure
        MONGO_DB.db = None
        raise Exception(f"Failed to connect to MongoDB or ping server: {e}")


async def close_mongo_connection():
    # print("Closing MongoDB connection...")
    if MONGO_DB.client is not None:
        await MONGO_DB.client.close()
        MONGO_DB.client = None
        MONGO_DB.db = None
        # print("MongoDB connection closed.")
    # else:
        # print("No MongoDB connection to close.")

def get_user_collection():
    if MONGO_DB.db is None:
        raise Exception("Database not initialized. Call connect_to_mongo first.")
    return MONGO_DB.db["users"]

# You can add other collection getters here if needed
def get_course_collection():
    if MONGO_DB.db is None:
        raise Exception("Database not initialized. Call connect_to_mongo first.")
    return MONGO_DB.db["courses"]

def get_question_collection():
    if MONGO_DB.db is None:
        raise Exception("Database not initialized. Call connect_to_mongo first.")
    return MONGO_DB.db["questions"]

def get_qca_collection():
    if MONGO_DB.db is None:
        raise Exception("Database not initialized. Call connect_to_mongo first.")
    return MONGO_DB.db["question_course_associations"]
