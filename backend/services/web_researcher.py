import os
import re
import base64
import httpx
import trafilatura
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs

# 下载目录（存放搜索结果，等待用户筛选）
DOWNLOADS_DIR = os.getenv("DOWNLOADS_DIR", "downloads")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")


def sanitize_filename(name: str) -> str:
    """将标题转换为合法的文件名"""
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    name = name.strip().replace(" ", "_")
    return name[:80]  # 截断过长的文件名


def _search_tavily(query: str, max_results: int = 5) -> list[dict]:
    """
    使用 Tavily AI 搜索接口获取高质量内容。
    比直接抓取搜索引擎更稳定，且内容更干净。
    """
    if not TAVILY_API_KEY:
        print("--- 错误: 未配置 TAVILY_API_KEY ---")
        return []

    print(f"--- 正在通过 Tavily 搜索: '{query}' ---")
    url = "https://api.tavily.com/search"
    payload = {
        "api_key": TAVILY_API_KEY,
        "query": query,
        "search_depth": "advanced",
        "max_results": max_results,
        "include_raw_content": False, # 我们后续用 trafilatura 处理，或者直接用 tavily 的 content
    }

    results = []
    try:
        resp = httpx.post(url, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        
        for item in data.get("results", []):
            results.append({
                "href": item.get("url"),
                "title": item.get("title"),
                "content_snippet": item.get("content")
            })
    except Exception as e:
        print(f"--- Tavily 搜索失败: {e} ---")
    
    return results


def search_and_download(query: str, max_results: int = 5) -> dict:
    """
    搜索关键词，抓取网页正文，保存为 Markdown 文件到 downloads/ 目录。
    返回成功保存的文件信息列表。
    """
    os.makedirs(DOWNLOADS_DIR, exist_ok=True)
    saved_files = []
    errors = []

    print(f"--- 开始搜索调研: '{query}', 目标数量: {max_results} ---")

    # 优先使用 Tavily
    if TAVILY_API_KEY:
        results = _search_tavily(query, max_results)
    else:
        print("--- TAVILY_API_KEY 未设置，调研功能受限 ---")
        return {"saved": [], "errors": ["TAVILY_API_KEY not configured"], "query": query}

    print(f"--- 搜索结果: {len(results)} 条 ---")

    for result in results:
        if len(saved_files) >= max_results:
            break

        url = result.get("href", "")
        title = result.get("title", "untitled")
        if not url:
            continue

        print(f"--- 正在抓取正文: {url} ---")
        try:
            # 使用 trafilatura 抓取网页正文
            downloaded = trafilatura.fetch_url(url)
            if not downloaded:
                # 如果 trafilatura 失败，尝试用 Tavily 提供的 snippet（虽然较短）
                text = result.get("content_snippet", "")
                if not text:
                    errors.append({"url": url, "error": "无法获取网页内容"})
                    continue
            else:
                text = trafilatura.extract(
                    downloaded,
                    include_links=False,
                    include_images=False,
                    output_format="markdown",
                )

            if not text or len(text.strip()) < 100:
                errors.append({"url": url, "error": "内容过少或提取失败"})
                continue

            # 构建 Markdown 文件内容
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            md_content = f"""---
title: {title}
source: {url}
query: {query}
downloaded_at: {timestamp}
---

# {title}

> 来源：{url}

{text}
"""
            filename = f"{sanitize_filename(title)}.md"
            filepath = os.path.join(DOWNLOADS_DIR, filename)

            # 避免文件名冲突
            counter = 1
            while os.path.exists(filepath):
                filename = f"{sanitize_filename(title)}_{counter}.md"
                filepath = os.path.join(DOWNLOADS_DIR, filename)
                counter += 1

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(md_content)

            saved_files.append({
                "filename": filename,
                "title": title,
                "source_url": url,
                "size_kb": round(len(md_content.encode("utf-8")) / 1024, 1),
            })
            print(f"--- 已保存: {filename} ---")

        except Exception as e:
            errors.append({"url": url, "error": str(e)})
            print(f"--- 抓取失败 {url}: {e} ---")

    return {"saved": saved_files, "errors": errors, "query": query}


def fetch_url_to_downloads(url: str, custom_title: str = "") -> dict:
    """
    直接从 URL 抓取内容到暂存区
    """
    os.makedirs(DOWNLOADS_DIR, exist_ok=True)
    downloaded = trafilatura.fetch_url(url)
    if not downloaded:
        raise ValueError(f"无法访问 URL: {url}")

    text = trafilatura.extract(downloaded, output_format="markdown")
    if not text:
        raise ValueError("提取正文失败")

    title = custom_title
    if not title:
        soup = BeautifulSoup(downloaded, "html.parser")
        title = soup.title.string if soup.title else url

    filename = f"{sanitize_filename(title)}.md"
    filepath = os.path.join(DOWNLOADS_DIR, filename)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n> Source: {url}\n\n{text}")

    return {
        "filename": filename,
        "title": title,
        "source_url": url,
        "size_kb": round(os.path.getsize(filepath) / 1024, 1)
    }


def list_downloads() -> list[dict]:
    """列出暂存区文件"""
    if not os.path.exists(DOWNLOADS_DIR):
        return []
    
    files = []
    for f in os.listdir(DOWNLOADS_DIR):
        if f.endswith(".md"):
            path = os.path.join(DOWNLOADS_DIR, f)
            files.append({
                "filename": f,
                "size_kb": round(os.path.getsize(path) / 1024, 1),
                "modified_at": datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y-%m-%d %H:%M")
            })
    return sorted(files, key=lambda x: x["modified_at"], reverse=True)


import shutil

def move_to_uploads(filename: str, uploads_dir: str = "uploads") -> dict:
    """移动到正式上传目录"""
    src = os.path.join(DOWNLOADS_DIR, filename)
    dst = os.path.join(uploads_dir, filename)
    
    if not os.path.exists(src):
        raise FileNotFoundError("文件不存在")
    
    os.makedirs(uploads_dir, exist_ok=True)
    shutil.move(src, dst)
    return {"status": "success", "filename": filename}
