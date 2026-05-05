from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from pgvector.sqlalchemy import Vector
from .database import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    file_path = Column(String)  # 新增：记录原始文件的物理路径
    content_type = Column(String)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    chunks = relationship("DocumentChunk", back_populates="document")

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    text_content = Column(Text)
    # 1024 is the dimension for bge-m3
    embedding = Column(Vector(1024))
    
    # Full-text search support
    # We'll use a gin index for fast keyword searching
    # search_vector = Column(TSVECTOR) # Requires additional imports, but we can also use plain Text and a gin index on the text_content

    document = relationship("Document", back_populates="chunks")
