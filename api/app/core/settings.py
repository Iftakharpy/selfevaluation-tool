# api/app/core/settings.py
import os
from pymongo import AsyncMongoClient # type: ignore
from pymongo.asynchronous.database import AsyncDatabase # type: ignore

class DataBase:
    client: AsyncMongoClient | None = None
    db: AsyncDatabase | None = None

MONGO_DB = DataBase()

# --- Database Configuration ---
# These are typically set by environment variables in Docker Compose files
DATABASE_NAME = os.getenv("DATABASE_NAME", "survey_db_default") # Default if not set by env
MONGO_DATABASE_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017") 

# --- Session Management ---
SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY", "a_very_default_and_insecure_secret_key_CHANGE_ME")

# --- Security ---
PWD_ALGORITHM = "bcrypt"

# --- Port Information (Primarily for CORS and informational purposes) ---
# These are the ports *inside* the containers if not overridden by Uvicorn/Vite args
# The actual host ports are defined in docker-compose files.
UI_INTERNAL_VITE_PORT = os.getenv("UI_INTERNAL_VITE_PORT", "5173")
API_INTERNAL_UVICORN_PORT = os.getenv("API_INTERNAL_UVICORN_PORT", "8000")

# --- CORS Configuration ---
# Define origins based on how the UI is accessed on the HOST machine
# For Production:
PROD_UI_DOMAIN = os.getenv("PROD_UI_DOMAIN", None) # e.g., "your-app.com"

# For Development (when accessing services via mapped host ports):
DEV_UI_HOST_PORT_VITE = os.getenv("DEV_UI_HOST_PORT_VITE", "5174") # e.g., http://localhost:5174
DEV_NGINX_PROXY_HOST_PORT = os.getenv("DEV_NGINX_PROXY_HOST_PORT", "8080") # e.g., http://localhost:8080

allowed_origins_list = []

# Development origins
allowed_origins_list.extend([
    f"http://localhost:{DEV_UI_HOST_PORT_VITE}",
    f"http://127.0.0.1:{DEV_UI_HOST_PORT_VITE}",
    f"http://localhost:{DEV_NGINX_PROXY_HOST_PORT}",
    f"http://127.0.0.1:{DEV_NGINX_PROXY_HOST_PORT}",
    "http://localhost", # Common for Nginx if it's on host port 80 or appears as such
    "http://127.0.0.1",
])

# Production origins
if PROD_UI_DOMAIN:
    allowed_origins_list.append(f"http://{PROD_UI_DOMAIN}")
    allowed_origins_list.append(f"https://{PROD_UI_DOMAIN}")

# Remove duplicates and assign
ALLOWED_ORIGINS = list(set(allowed_origins_list))

if not ALLOWED_ORIGINS: # Fallback if nothing configured, for extreme local dev only
    print("WARNING: ALLOWED_ORIGINS is empty. Falling back to allowing '*' for local development ease. Configure PROD_UI_DOMAIN for production.")
    ALLOWED_ORIGINS = ["*"]

print(f"INFO: Backend CORS Allowed Origins: {ALLOWED_ORIGINS}")



STANDARD_QUESTION_MAX_SCORE: float = 10.0

