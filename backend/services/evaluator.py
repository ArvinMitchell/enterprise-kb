import os
import random
from sqlalchemy.orm import Session
from ..models import Document, DocumentChunk
from .chat_service import retrieve_context
from openai import OpenAI

def generate_test_cases(db: Session, num_cases: int = 10):
    """
    利用 LLM 根据现有文档自动生成测试集（问题, 预期文档）
    """
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    client = OpenAI(api_key=api_key, base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"))
    
    docs = db.query(Document).all()
    if not docs:
        return []
    
    test_cases = []
    
    # 过滤掉没有 chunk 的文档
    valid_docs = [d for d in docs if d.chunks]
    if not valid_docs:
        return []

    print(f"--- Generating {num_cases} test cases from {len(valid_docs)} documents ---")
    
    for i in range(num_cases):
        doc = random.choice(valid_docs)
        chunk = random.choice(doc.chunks)
        
        # 限制文本长度，避免 context 过长
        sample_text = chunk.text_content[:800]
        
        prompt = (
            "你是一个测试专家。请根据以下文本片段，构造一个具体的、自然的用户问题。\n"
            "要求：\n"
            "1. 该问题必须能从这段话中找到明确答案。\n"
            "2. 问题表述要像真实用户提问，不要包含‘根据这段话’之类的描述。\n"
            "3. 直接返回问题，不要有任何前缀。 \n\n"
            f"文本：{sample_text}"
        )
        
        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            question = response.choices[0].message.content.strip().replace("\"", "").replace("？", "?")
            test_cases.append({
                "id": i + 1,
                "question": question,
                "expected_doc_id": doc.id,
                "expected_filename": doc.filename,
                "context_snippet": sample_text[:100] + "..."
            })
        except Exception as e:
            print(f"Failed to generate case {i}: {e}")
            
    return test_cases

def run_recall_evaluation(db: Session, num_cases: int = 5):
    """
    执行 RAG 召回率评分测试
    """
    test_cases = generate_test_cases(db, num_cases)
    if not test_cases:
        return {"error": "数据库中没有足够文档进行测试，请先上传文件。"}
        
    hits = 0
    results = []
    
    for case in test_cases:
        # 模拟真实检索过程
        retrieved_chunks = retrieve_context(db, case["question"])
        retrieved_doc_ids = [c.document_id for c in retrieved_chunks]
        
        is_hit = case["expected_doc_id"] in retrieved_doc_ids
        if is_hit:
            hits += 1
            
        results.append({
            "case_id": case["id"],
            "question": case["question"],
            "expected_source": case["expected_filename"],
            "retrieved_sources": list(set([c.document.filename for c in retrieved_chunks])),
            "is_hit": is_hit
        })
        
    recall_score = (hits / len(test_cases)) * 100
    
    return {
        "status": "success",
        "recall_score": f"{recall_score:.2f}%",
        "total_cases": len(test_cases),
        "hits": hits,
        "details": results
    }
