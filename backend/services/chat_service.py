import os
from sqlalchemy.orm import Session
from ..models import DocumentChunk, Document
from langchain_community.embeddings import OllamaEmbeddings
from openai import OpenAI

# Initialize Ollama embeddings
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
embeddings = OllamaEmbeddings(
    model="bge-m3",
    base_url=OLLAMA_BASE_URL
)

from sqlalchemy import func, or_

def retrieve_context(db: Session, query: str, top_k: int = 5) -> list[DocumentChunk]:
    """
    混合检索核心逻辑：意图扩展 + (向量检索 & 关键词检索) + RRF 融合
    """
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    client = OpenAI(api_key=api_key, base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"))
    
    # 1. 意图扩展 (Multi-Query)
    expansion_prompt = f"你是一个搜索专家。请将用户问题 '{query}' 改写为 3 个不同的搜索关键词。直接返回列表，每行一个。"
    try:
        expansion_response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": expansion_prompt}],
            temperature=0.3,
            timeout=10
        )
        search_queries = [query] + expansion_response.choices[0].message.content.strip().split("\n")
    except:
        search_queries = [query]

    search_queries = [q.strip() for q in search_queries if q.strip()][:4]

    # 2. 执行混合检索 (Hybrid Search)
    # RRF 权重参数: score = 1 / (rank + k)
    K = 60
    rrf_scores = {} # {chunk_id: score}
    chunk_map = {}  # {chunk_id: chunk_object}

    for q in search_queries:
        # A. 向量检索 (Vector Search)
        q_embedding = embeddings.embed_query(q)
        vector_chunks = db.query(DocumentChunk).order_by(
            DocumentChunk.embedding.l2_distance(q_embedding)
        ).limit(top_k).all()
        
        for rank, chunk in enumerate(vector_chunks):
            chunk_map[chunk.id] = chunk
            rrf_scores[chunk.id] = rrf_scores.get(chunk.id, 0) + 1.0 / (rank + 1 + K)

        # B. 关键词检索 (Full-Text Search)
        # 将查询词转换为 Postgres 搜索格式
        search_terms = " | ".join(q.split())
        keyword_chunks = db.query(DocumentChunk).filter(
            func.to_tsvector('simple', DocumentChunk.text_content).op('@@')(func.to_tsquery('simple', search_terms))
        ).limit(top_k).all()
        
        for rank, chunk in enumerate(keyword_chunks):
            chunk_map[chunk.id] = chunk
            rrf_scores[chunk.id] = rrf_scores.get(chunk.id, 0) + 1.0 / (rank + 1 + K)

    # 3. 按 RRF 分数重排序并取 Top-K
    sorted_ids = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
    final_chunks = [chunk_map[cid] for cid, _ in sorted_ids]
    
    return final_chunks


def get_chat_response(db: Session, query: str) -> dict:
    all_chunks = retrieve_context(db, query)

    if not all_chunks:
        return {
            "answer": "知识库中目前没有任何文档，请先上传文档。",
            "sources": []
        }

    # 3. Format the context
    context_text = "\n\n---\n\n".join(
        [f"片段 {i+1} (来源: {chunk.document.filename}):\n{chunk.text_content}" for i, chunk in enumerate(all_chunks)]
    )
    
    sources = list(set([chunk.document.filename for chunk in all_chunks]))

    # 4. Generate answer
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    base_url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    
    if not api_key:
        return {"answer": "错误：未配置 API Key", "sources": []}
        
    client = OpenAI(api_key=api_key, base_url=base_url)

    system_prompt = (
        "你是一个企业级的智能知识库助手。请严格根据以下提供的参考片段回答用户的问题。\n"
        "### 必须遵循的原则：\n"
        "1. 你的回答必须在句末标注来源，格式为 [片段编号]，例如：'公司的班车时间是早上8点 [1]。'\n"
        "2. 严禁编造任何参考片段中没有的信息。如果片段中没有答案，请直接回答“根据当前知识库，我无法找到相关信息”。\n"
        "3. 保持回答的专业性和结构化。\n\n"
        "参考片段如下：\n"
        f"{context_text}"
    )

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ],
        temperature=0.2
    )

    answer = response.choices[0].message.content

    source_details = [
        {
            "id": i + 1,
            "filename": chunk.document.filename,
            "path": chunk.document.file_path,
            "content": chunk.text_content
        } for i, chunk in enumerate(all_chunks)
    ]

    return {
        "answer": answer,
        "sources": sources,
        "source_details": source_details
    }
