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
        if os.path.exists(file_path):
            os.remove(file_path)

@router.post("/api/documents/sync")
async def sync_local_directory(path: str, db: Session = Depends(get_db)):
    """
    同步本地目录下的文件到知识库
    """
    if not os.path.exists(path):
        raise HTTPException(status_code=400, detail="指定的本地路径不存在")
    
    from ..services.document_processor import sync_directory
    try:
        count = sync_directory(db, path)
        return {"status": "success", "processed_files": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/documents/evaluate")
async def evaluate_recall(n: int = 5, db: Session = Depends(get_db)):
    """
    自动生成测试用例并计算 RAG 召回率
    """
    from ..services.evaluator import run_recall_evaluation
    try:
        result = run_recall_evaluation(db, n)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
