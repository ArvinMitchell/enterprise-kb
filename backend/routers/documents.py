import os
import shutil
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.document_processor import process_and_store_document

router = APIRouter()

# Temporary directory for uploaded files
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/api/documents/upload")
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")
    
    # Save the file temporarily
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        # Process and store the document
        db_doc = process_and_store_document(
            db=db, 
            file_path=file_path, 
            filename=file.filename, 
            content_type=file.content_type
        )
        return {"status": "success", "document_id": db_doc.id, "filename": db_doc.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up temporary file
        if os.path.exists(file_path):
            os.remove(file_path)
