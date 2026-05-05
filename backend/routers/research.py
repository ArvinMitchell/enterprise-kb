from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from ..database import get_db
from ..services.web_researcher import (
    search_and_download,
    list_downloads,
    move_to_uploads,
    fetch_url_to_downloads,
)
from ..services.document_processor import sync_directory

router = APIRouter()

UPLOADS_DIR = "uploads"
DOWNLOADS_DIR = "downloads"


# ─── Request / Response 模型 ────────────────────────────────────────────────

class WebSearchRequest(BaseModel):
    query: str
    max_results: int = 5

class MoveFileRequest(BaseModel):
    filename: str

class UrlImportRequest(BaseModel):
    url: str
    title: str = ""  # 可选，留空则从页面自动提取


# ─── 网络调研 ────────────────────────────────────────────────────────────────

@router.post("/api/research/web-search")
async def web_search(request: WebSearchRequest):
    """
    搜索关键词，抓取网页正文保存为 Markdown 文件到 downloads/ 目录。
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="搜索关键词不能为空")
    if not (1 <= request.max_results <= 20):
        raise HTTPException(status_code=400, detail="搜索数量需在 1~20 之间")

    result = search_and_download(request.query, request.max_results)
    if not result["saved"]:
        result["warning"] = "未找到可抓取的内容，建议改用'URL 导入'功能直接粘贴文章链接"
    return result


@router.post("/api/research/import-url")
async def import_url(request: UrlImportRequest):
    """直接从指定 URL 抓取内容，保存为 Markdown 文件到 downloads/ 目录"""
    if not request.url.strip().startswith("http"):
        raise HTTPException(status_code=400, detail="请输入合法的 http/https URL")
    try:
        result = fetch_url_to_downloads(request.url, request.title)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/research/downloads")
async def get_downloads():
    """列出 downloads/ 目录中所有可筛选的文件"""
    return {"files": list_downloads()}


@router.post("/api/research/move-to-uploads")
async def move_file_to_uploads(request: MoveFileRequest):
    """将选定的 downloads/ 文件移动到 uploads/ 目录"""
    try:
        result = move_to_uploads(request.filename, UPLOADS_DIR)
        return result
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ─── 批量同步 uploads/ 目录 ──────────────────────────────────────────────────

@router.post("/api/documents/sync-uploads")
async def sync_uploads_directory(db: Session = Depends(get_db)):
    """
    扫描 uploads/ 目录，将新增的文件自动向量化并录入知识库。
    已经入库的文件会被跳过（增量同步）。
    """
    count = sync_directory(db, UPLOADS_DIR)
    return {
        "status": "success",
        "message": f"同步完成，共录入 {count} 个新文件",
        "new_files": count,
    }
