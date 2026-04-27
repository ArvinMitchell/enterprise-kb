from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.chat_service import get_chat_response

router = APIRouter()

class ChatRequest(BaseModel):
    query: str

@router.post("/api/chat")
def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
        
    try:
        response = get_chat_response(db, request.query)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
