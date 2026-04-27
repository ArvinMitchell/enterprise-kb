import os
from sqlalchemy.orm import Session
from ..models import DocumentChunk, Document
from langchain_community.embeddings import OllamaEmbeddings
from openai import OpenAI

# Initialize Ollama embeddings
embeddings = OllamaEmbeddings(model="bge-m3")

def get_chat_response(db: Session, query: str) -> dict:
    # 1. Embed the user's query
    query_embedding = embeddings.embed_query(query)

    # 2. Retrieve top 3 most relevant chunks from Postgres using pgvector
    # Order by L2 distance (lowest is most similar)
    top_chunks = db.query(DocumentChunk).order_by(
        DocumentChunk.embedding.l2_distance(query_embedding)
    ).limit(3).all()

    if not top_chunks:
        return {
            "answer": "知识库中目前没有任何文档，请先上传文档。",
            "sources": []
        }

    # 3. Format the context from retrieved chunks
    context_text = "\n\n---\n\n".join(
        [f"片段 {i+1} (来源: {chunk.document.filename}):\n{chunk.text_content}" for i, chunk in enumerate(top_chunks)]
    )

    sources = [chunk.document.filename for chunk in top_chunks]
    # Deduplicate sources
    sources = list(set(sources))

    # 4. Generate answer using DeepSeek via OpenAI client
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    base_url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    
    if not api_key:
        return {
            "answer": "错误：未配置 DEEPSEEK_API_KEY，请在 .env 中设置。",
            "sources": []
        }
        
    client = OpenAI(api_key=api_key, base_url=base_url)

    system_prompt = (
        "你是一个企业级的智能知识库助手。请严格根据以下提供的参考片段回答用户的问题。\n"
        "如果提供的片段中没有包含答案，请直接回答“根据当前知识库，我无法找到相关信息”，不要编造。\n\n"
        "参考片段如下：\n"
        f"{context_text}"
    )

    response = client.chat.completions.create(
        model="deepseek-v4-flash",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ],
        temperature=0.3
    )

    answer = response.choices[0].message.content

    return {
        "answer": answer,
        "sources": sources
    }
