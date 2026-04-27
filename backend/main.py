import os
from dotenv import load_dotenv
# Load variables from .env file in project root
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from .database import engine, Base
from .routers import documents, chat

# Initialize database tables and vector extension
with engine.connect() as conn:
    conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    conn.commit()

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Enterprise Knowledge Base API",
    description="API for RAG and Document Management",
    version="0.1.0"
)

# Allow CORS for the Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health_check():
    return {"status": "ok", "message": "Enterprise KB Backend is running!"}

app.include_router(documents.router, tags=["Documents"])
app.include_router(chat.router, tags=["Chat"])
