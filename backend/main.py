# main.py
from typing import List, Optional
from functools import lru_cache
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import psycopg2
import os, json, requests

from db import (
    init_pool, close_pool, count_by_category, list_by_category,
    search_components, database_configured,
)

# ======== ⚙️ ENV 로드 ========
load_dotenv()

# ✅ 환경변수에서 값 읽기
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PG_DSN = os.getenv("PG_DSN")  # or 개별 DB_* 로 조합해도 됨
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173")

# ✅ 필수 값 검증 (서버 켜질 때 바로 실패시켜서 실수 방지)
# ======== 🧠 모델/세션 ========
chat_sessions = {}

@lru_cache(maxsize=1)
def get_embedding_model():
    """검색을 처음 사용할 때만 모델을 로드해 일반 목록 API 시작을 가볍게 유지한다."""
    return SentenceTransformer(os.getenv("EMBEDDING_MODEL", "jhgan/ko-sroberta-multitask"))


DEMO_COMPONENTS = [
    {
        "id": 1, "name": "Aurora Gradient Button", "author": "CSSMasterLibrary",
        "description": "빛이 흐르는 그라데이션 CTA 버튼", "category": "Buttons",
        "library": "Vanilla CSS", "source_url": "",
        "code": """<!doctype html><html><head><style>body{display:grid;place-items:center;min-height:240px;background:#0b1020}.aurora{padding:16px 28px;border:0;border-radius:999px;color:#08111f;font-weight:800;background:linear-gradient(120deg,#7df9ff,#a78bfa,#34d399);box-shadow:0 12px 40px #7df9ff55;transition:.25s}.aurora:hover{transform:translateY(-3px) scale(1.03)}</style></head><body><button class=\"aurora\">Explore components</button></body></html>""",
    },
    {
        "id": 2, "name": "Glass Search Field", "author": "CSSMasterLibrary",
        "description": "다크 화면을 위한 글래스모피즘 검색 입력", "category": "Inputs",
        "library": "Vanilla CSS", "source_url": "",
        "code": """<!doctype html><html><head><style>body{display:grid;place-items:center;min-height:240px;background:linear-gradient(135deg,#111827,#312e81)}.search{width:300px;padding:16px 20px;border-radius:16px;border:1px solid #ffffff33;background:#ffffff12;color:white;box-shadow:0 18px 50px #0005;outline:none}.search:focus{border-color:#7df9ff;box-shadow:0 0 0 4px #7df9ff22}</style></head><body><input class=\"search\" placeholder=\"Search UI components...\"></body></html>""",
    },
    {
        "id": 3, "name": "Neon Profile Card", "author": "CSSMasterLibrary",
        "description": "네온 테두리와 상태 배지를 적용한 프로필 카드", "category": "Cards",
        "library": "Vanilla CSS", "source_url": "",
        "code": """<!doctype html><html><head><style>body{display:grid;place-items:center;min-height:280px;background:#090d16;color:#eef}.card{width:260px;padding:24px;border:1px solid #7df9ff55;border-radius:22px;background:#ffffff0d;box-shadow:0 20px 70px #7df9ff20}.tag{color:#34d399;font:600 12px sans-serif}h2,p{font-family:sans-serif}p{color:#9ca3af}</style></head><body><article class=\"card\"><span class=\"tag\">● AVAILABLE</span><h2>UI Engineer</h2><p>Reusable interfaces with careful interaction details.</p></article></body></html>""",
    },
]

# ✅ app 생성
app = FastAPI(title="CSS Components API (async)")

# ======== 🌐 CORS ========
origins = [o.strip() for o in ALLOWED_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ======== 📦 Response Models ========
class ComponentOut(BaseModel):
    id: int
    name: str
    author: Optional[str] = None
    code: str
    category: Optional[str] = None  # Others에서 사용
    description: Optional[str] = None
    library: Optional[str] = None
    source_url: Optional[str] = None
    score: Optional[float] = None


class PaginatedResponse(BaseModel):
    items: List[ComponentOut]
    total: int
    page: int
    page_size: int


# ======== ✅ Lifespan ========
@app.on_event("startup")
async def _startup():
    await init_pool()


@app.on_event("shutdown")
async def _shutdown():
    await close_pool()


@app.get("/health")
async def health():
    return {"ok": True}


# ======== 📚 Components API ========
@app.get("/components", response_model=PaginatedResponse)
async def get_components(
    category: str = Query(..., description="예: buttons/cards/inputs"),
    page: int = Query(1, ge=1),
    page_size: int = Query(24, ge=1, le=100),
):
    if not database_configured():
        matched = [x for x in DEMO_COMPONENTS if category.lower() == "others" or x["category"].lower() == category.lower()]
        start = (page - 1) * page_size
        return PaginatedResponse(items=matched[start:start + page_size], total=len(matched), page=page, page_size=page_size)
    total = await count_by_category(category)
    offset = (page - 1) * page_size
    rows = await list_by_category(category, offset, page_size)
    items = [ComponentOut(**row) for row in rows]
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


class SearchResponse(BaseModel):
    items: List[ComponentOut]
    query: str
    mode: str
    page: int
    page_size: int


@app.get("/components/search", response_model=SearchResponse)
async def component_search(
    q: str = Query(..., min_length=1, max_length=200),
    category: Optional[str] = None,
    library: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(24, ge=1, le=100),
):
    """DB 환경에서는 키워드+벡터 검색, 미설정 환경에서는 내장 데모 검색을 제공한다."""
    offset = (page - 1) * page_size
    if not database_configured():
        needle = q.casefold()
        rows = [
            {**item, "score": 1.0}
            for item in DEMO_COMPONENTS
            if needle in " ".join(str(item.get(k, "")) for k in ("name", "description", "category", "library")).casefold()
            and (not category or item["category"].casefold() == category.casefold())
            and (not library or item["library"].casefold() == library.casefold())
        ]
        return SearchResponse(items=rows[offset:offset + page_size], query=q, mode="demo-keyword", page=page, page_size=page_size)

    embedding = get_embedding_model().encode(q).tolist()
    rows = await search_components(q, embedding, category, library, offset, page_size)
    return SearchResponse(items=[ComponentOut(**row) for row in rows], query=q, mode="hybrid", page=page, page_size=page_size)


# ======== 💬 Chat Request ========
class ChatRequest(BaseModel):
    query: str
    session_id: str = "default"


# ======== 🔍 DB 검색 (RAG) ========
def retrieve_similar(query, top_k=3):
    emb = get_embedding_model().encode(query).tolist()
    with psycopg2.connect(PG_DSN) as conn:   # ✅ PG_DSN 사용
        with conn.cursor() as cur:
            cur.execute("""
                SELECT name, html, css, full_code, author, source_type,
                       1 - (embedding <=> %s::vector) AS similarity
                FROM unified_components_v3
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> %s::vector
                LIMIT %s;
            """, (emb, emb, top_k))
            rows = cur.fetchall()
    return rows


# ======== 🧠 Prompt ========
def build_prompt_with_history(history, query):
    examples = retrieve_similar(query, top_k=3)
    examples_text = "\n\n".join([
        f"[{ex[5]}] 예시 (by {ex[4]}):\nHTML:\n{ex[1]}\n\nCSS:\n{ex[2]}"
        for ex in examples if ex[1] and ex[2]
    ])

    prompt = f"""
당신은 세계적인 웹 아티스트이자 CSS 디자이너입니다.
이전 대화 기록(별도 메시지 리스트로 전달됨)을 참고하여 사용자의 의도를 정확히 파악하고,
아래 주제와 참고 예시에 맞는 감성적이고 예술적인 HTML/CSS 페이지를 작성하세요.

주제: "{query}"

참고 예시 (데이터베이스에서 검색됨):
{examples_text}

규칙:
1. 완전한 HTML5 문서 구조로 작성하세요 (<!DOCTYPE html>부터 </html>까지 포함).
2. 오직 HTML과 내부 <style>만 사용하세요. (JS, 프레임워크, 외부 리소스 사용 금지)
3. 색감은 조화롭고, 디자인은 부드럽고 세련되게 표현하세요.
4. 여백, 비율, 타이포그래피의 균형을 유지하며 미적 완성도를 높이세요.
5. 지나치게 단순하거나 일반적인 스타일을 피하고, 아름다운 창의성을 보여주세요.
6. 애니메이션과 움직이는 모션을 추가해 화려함을 추구하세해요.
7. 코드 생성 후 사용자에게 친구처럼 대하며 간략한 코드 설명을 해주세요.
8. 사용자가 입력한 텍스트로 제목을 만들지 마세요.
"""
    return prompt.strip()


# ======== 🚀 GPT-4o mini Streaming ========
@app.post("/chat/stream")
def chat_stream(req: ChatRequest):
    if not OPENAI_API_KEY or not PG_DSN:
        return StreamingResponse(iter(["채팅 기능에는 OPENAI_API_KEY와 PG_DSN 설정이 필요합니다."]), media_type="text/plain")
    session_id = req.session_id
    query = req.query

    if session_id not in chat_sessions:
        chat_sessions[session_id] = []

    history = chat_sessions[session_id]
    prompt = build_prompt_with_history(history, query)

    def stream_generator():
        with requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",  # ✅ 하드코딩 제거
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "You are a creative web designer."},
                    {"role": "user", "content": prompt}
                ],
                "stream": True
            },
            stream=True
        ) as r:
            full_response = ""
            for line in r.iter_lines():
                if not line or not line.decode().startswith("data: "):
                    continue
                data = line.decode()[6:]
                if data.strip() == "[DONE]":
                    break
                try:
                    json_data = json.loads(data)
                    delta = json_data["choices"][0]["delta"]
                    if "content" in delta:
                        chunk = delta["content"]
                        full_response += chunk
                        yield chunk
                except Exception:
                    continue

            history.append({"role": "user", "content": query})
            history.append({"role": "assistant", "content": full_response})

    return StreamingResponse(stream_generator(), media_type="text/event-stream")
