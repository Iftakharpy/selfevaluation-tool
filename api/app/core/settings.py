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
# MONGO_DATABASE_URL = os.getenv("MONGO_URL", "mongodb://mongodb_container:27017")


SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY", "your-super-secret-key-for-sessions-CHANGE-ME") # IMPORTANT: Change this in prod!
# For production, ensure this is a strong, randomly generated key and stored securely.

# Password Hashing Algorithm
PWD_ALGORITHM = "bcrypt"


FRONTEND_PORT = os.getenv("FRONTEND_PORT", "5173")  # Default Vite dev server port
FASTAPI_PORT = os.getenv("FASTAPI_PORT", "8000")  # Default FastAPI port
ALLOWED_ORIGINS = [
    f"http://localhost:{FRONTEND_PORT}",  # React app
    f"http://localhost:{FASTAPI_PORT}",  # FastAPI app
    "https://your-production-domain.com",  # Production domain, change as needed
] # Everything for now


ALLOWED_ORIGINS = [
    f"http://localhost:{FRONTEND_PORT}",      # Vite dev server default
    f"http://127.0.0.1:{FRONTEND_PORT}",    # Vite dev server via 127.0.0.1
    f"http://localhost:{FASTAPI_PORT}",      # FastAPI dev server default
    f"http://127.0.0.1:{FASTAPI_PORT}",      # FastAPI dev server via 127.0.0.1
    # Add http://localhost for the Nginx dev proxy if it's different from API host
    # "http://localhost", # If Nginx is on port 80 from the browser's perspective
    # Potentially others if you access via specific IPs during dev,
    # but this can become unwieldy.
    # Example: "http://192.168.1.132:5173"
    # It's often better to keep this list minimal and rely on VITE_API_DIRECT_URL
    # for varied manual setups, or ensure dev Nginx correctly forwards Origin.
]

# When using the dev Nginx proxy (docker-compose.dev.yml), Nginx will forward
# the original Origin header (e.g., http://localhost if you access nginx on port 80).
# So, if your Nginx is on http://localhost, then ALLOWED_ORIGINS should include "http://localhost".
# However, the current CORSMiddleware default behavior for `allow_origin_regex`
# might handle proxied requests if the Origin header matches one of the listed origins,
# or if the proxy forwards the correct origin.
# For the most robust Nginx-proxied setup, ensure Nginx forwards the client's true origin,
# or allow the proxy's origin if that's how it appears to FastAPI.

# Let's refine ALLOWED_ORIGINS for both scenarios:
# 1. Vite dev server direct access (localhost:5173, 127.0.0.1:5173, specific_ip:5173)
# 2. Nginx dev proxy access (localhost, or your nginx dev domain)

# A practical approach for development:
# ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS_DEV", "http://localhost:5173,http://127.0.0.1:5173,http://localhost").split(',')
# For simplicity with your current setup:
ALLOWED_ORIGINS = [
    f"http://localhost:{FRONTEND_PORT}",  # For Vite direct dev access
    f"http://127.0.0.1:{FRONTEND_PORT}", # For Vite direct dev access
    f"http://localhost:{FASTAPI_PORT}",       # For accessing through Nginx dev proxy on port 80
    f"http://127.0.0.1:{FASTAPI_PORT}",
    # Add any specific IPs you use for development, e.g.:
    "http://192.168.x.x",
    "http://<your-ip-address>",
]
# If you access your Nginx dev proxy via an IP like http://192.168.x.x, add that too.
