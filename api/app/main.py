# FilePath: api/app/main.py
import uvicorn
from fastapi import FastAPI, APIRouter
from contextlib import asynccontextmanager
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from http import HTTPStatus

from .core.db import connect_to_mongo, close_mongo_connection
from .core.settings import ALLOWED_ORIGINS, MONGO_DB, SESSION_SECRET_KEY

from .users.router import UserRouter
from .courses.router import CourseRouter
from .questions.router import QuestionRouter
from .qca.router import QcaRouter
from .surveys.router import SurveyRouter 
from .survey_attempts.router import SurveyAttemptRouter



@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Application startup: Connecting to MongoDB...")
    try:
        await connect_to_mongo()
        app.state.mongo_client = MONGO_DB.client
    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")
        raise
    yield
    print("Application shutdown: Closing MongoDB connection...")
    if hasattr(app.state, "mongo_client") and app.state.mongo_client:
        await close_mongo_connection()
        app.state.mongo_client = None
    print("MongoDB connection closed.")

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET_KEY,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

api_root = APIRouter(prefix="/api/v1")

api_root.include_router(UserRouter, prefix="/users", tags=["User"])
api_root.include_router(CourseRouter, prefix="/courses", tags=["Courses"])
api_root.include_router(QuestionRouter, prefix="/questions", tags=["Questions"])
api_root.include_router(QcaRouter, prefix="/question-course-associations", tags=["Question-Course Associations"])
api_root.include_router(SurveyRouter, prefix="/surveys", tags=["Surveys"]) 
api_root.include_router(SurveyAttemptRouter, prefix="/survey-attempts", tags=["Survey Attempts"])

app.include_router(api_root)

@app.get("/")
async def redirect_to_docs():
    return RedirectResponse(url="/docs", status_code=HTTPStatus.PERMANENT_REDIRECT)

def run():
    uvicorn.run(app, host="127.0.0.1", port=8000)

if __name__ == "__main__":
    run()
