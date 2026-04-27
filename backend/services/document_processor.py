import os
from sqlalchemy.orm import Session
from ..models import Document, DocumentChunk
import pdfplumber
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OllamaEmbeddings

# Initialize Ollama embeddings
embeddings = OllamaEmbeddings(model="bge-m3")

def extract_pdf_with_tables(file_path: str) -> str:
    """使用 pdfplumber 提取文字并尝试还原表格为 Markdown 格式"""
    full_text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                # 1. 提取普通文本
                page_text = page.extract_text() or ""
                
                # 2. 尝试提取表格
                tables = page.extract_tables()
                table_markdowns = []
                
                for table in tables:
                    if not table: continue
                    # 将嵌套列表转换为 Markdown 表格字符串
                    rows = []
                    for i, row in enumerate(table):
                        # 清理单元格中的换行符，并替换 None 为空字符串
                        clean_row = [str(cell).replace("\n", " ") if cell is not None else "" for cell in row]
                        rows.append("| " + " | ".join(clean_row) + " |")
                        # 如果是第一行（表头），增加分割线
                        if i == 0:
                            rows.append("| " + " | ".join(["---"] * len(clean_row)) + " |")
                    
                    if rows:
                        table_markdowns.append("\n" + "\n".join(rows) + "\n")
                
                # 合并当前页面的文本和表格
                full_text += page_text + "\n"
                for tm in table_markdowns:
                    full_text += tm
                full_text += "\n" # 页面间分隔
                
        return full_text
    except Exception as e:
        print(f"PDF 解析失败: {e}")
        return ""

def process_and_store_document(db: Session, file_path: str, filename: str, content_type: str) -> Document:
    # 1. Extract text
    text_content = ""
    if content_type == "application/pdf":
        text_content = extract_pdf_with_tables(file_path)
    else:
        # Assume text format
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            text_content = f.read()
            
    # Postgres cannot store null bytes (\x00). Sanitize the text.
    text_content = text_content.replace("\x00", "")
            
    # 2. Save Document to DB
    db_doc = Document(filename=filename, content_type=content_type)
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)

    # 3. Chunk text
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        is_separator_regex=False,
    )
    chunks = text_splitter.split_text(text_content)

    # 4. Generate Embeddings and store chunks
    if chunks:
        # Generate embeddings using Ollama
        embedded_chunks = embeddings.embed_documents(chunks)
        
        for i, chunk_text in enumerate(chunks):
            db_chunk = DocumentChunk(
                document_id=db_doc.id,
                text_content=chunk_text,
                embedding=embedded_chunks[i]
            )
            db.add(db_chunk)
        
        db.commit()

    return db_doc
