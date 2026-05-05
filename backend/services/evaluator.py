import os
import random
from sqlalchemy.orm import Session
from ..models import Document, DocumentChunk
from .chat_service import retrieve_context, get_chat_response
from openai import OpenAI

def generate_test_cases(db: Session, num_cases: int = 5):
    """
    进阶版测试集生成：基于 Evol-Instruct 思想进行语义混淆与重写
    """
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    client = OpenAI(api_key=api_key, base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"))
    
    docs = db.query(Document).all()
    if not docs:
        return []
    
    valid_docs = [d for d in docs if d.chunks]
    if not valid_docs:
        return []

    test_cases = []
    
    for i in range(num_cases):
        doc = random.choice(valid_docs)
        chunk = random.choice(doc.chunks)
        sample_text = chunk.text_content[:1000]
        
        # 步骤 1: 生成基础问题
        try:
            base_prompt = f"根据以下文本生成一个事实性问题。文本：{sample_text}"
            res1 = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": base_prompt}],
                temperature=0.7
            )
            base_question = res1.choices[0].message.content.strip()
            
            # 步骤 2: 语义进化 (Evol-Instruct)
            # 让问题变得更自然、模糊，避开原文中的直接关键词
            evolve_prompt = (
                f"请改写以下问题，使其更像真实用户的模糊提问。要求：\n"
                f"1. 使用同义词替换原文中的核心关键词。\n"
                f"2. 语气更自然，可以稍微简略或口语化。\n"
                f"3. 严禁使用‘根据这段话’等提示语。\n"
                f"原问题：{base_question}"
            )
            res2 = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": evolve_prompt}],
                temperature=0.8
            )
            evolved_question = res2.choices[0].message.content.strip().replace("\"", "")
            
            test_cases.append({
                "id": i + 1,
                "question": evolved_question,
                "base_question": base_question,
                "expected_doc_id": doc.id,
                "expected_filename": doc.filename,
                "context_sample": sample_text[:100] + "..."
            })
        except Exception as e:
            print(f"Error evolving test case: {e}")
            
    return test_cases

def judge_faithfulness(question: str, answer: str, contexts: list[str]) -> float:
    """
    LLM-as-a-Judge: 评测回答的忠实度 (Faithfulness)
    """
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    client = OpenAI(api_key=api_key, base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"))
    
    context_str = "\n\n".join(contexts)
    prompt = (
        "你是一个严谨的 RAG 评测专家。请判断【回答】是否完全基于【参考上下文】得出，是否存在幻觉或编造。\n"
        f"问题：{question}\n"
        f"参考上下文：{context_str}\n"
        f"系统回答：{answer}\n\n"
        "评分标准：\n"
        "1. 完全基于上下文，无幻觉：1.0\n"
        "2. 部分基于上下文，但包含少量编造信息：0.5\n"
        "3. 严重脱离上下文或完全编造：0.0\n"
        "请直接返回一个数字评分（0.0, 0.5, 1.0），不要有其他解释。"
    )
    
    try:
        res = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        score = float(res.choices[0].message.content.strip())
        return score
    except:
        return 0.5

def run_recall_evaluation(db: Session, num_cases: int = 5):
    """
    进阶评测：Recall@K + LLM-as-a-Judge 忠实度检查
    """
    test_cases = generate_test_cases(db, num_cases)
    if not test_cases:
        return {"error": "测试集生成失败，请检查文档和 API。"}
        
    hits = 0
    total_faithfulness = 0.0
    results = []
    
    for case in test_cases:
        # 1. 评测检索 (Retrieval)
        retrieved_chunks = retrieve_context(db, case["question"])
        retrieved_doc_ids = [c.document_id for c in retrieved_chunks]
        is_hit = case["expected_doc_id"] in retrieved_doc_ids
        if is_hit: hits += 1
        
        # 2. 评测回答质量 (Generation)
        chat_res = get_chat_response(db, case["question"])
        answer = chat_res["answer"]
        contexts = [c.text_content for c in retrieved_chunks]
        
        faith_score = judge_faithfulness(case["question"], answer, contexts)
        total_faithfulness += faith_score
            
        results.append({
            "case_id": case["id"],
            "question": case["question"],
            "expected_doc": case["expected_filename"],
            "is_hit": is_hit,
            "faithfulness_score": faith_score,
            "ai_answer": answer[:100] + "..."
        })
        
    return {
        "status": "success",
        "metrics": {
            "recall_score": f"{(hits / len(test_cases)) * 100:.2f}%",
            "avg_faithfulness": f"{(total_faithfulness / len(test_cases)) * 100:.2f}%",
            "total_cases": len(test_cases)
        },
        "details": results
    }
