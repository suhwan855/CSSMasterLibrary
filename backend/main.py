# main.py
from typing import List, Optional
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from openai import OpenAI
import psycopg2
import os, json, requests

from db import init_pool, close_pool, count_by_category, list_by_category

# ======== ⚙️ ENV 로드 ========
load_dotenv()

# ✅ 환경변수에서 값 읽기
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PG_DSN = os.getenv("PG_DSN")  # or 개별 DB_* 로 조합해도 됨
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173")

# ✅ 필수 값 검증 (서버 켜질 때 바로 실패시켜서 실수 방지)
assert OPENAI_API_KEY, "OPENAI_API_KEY 환경변수를 설정하세요."
assert PG_DSN, "PG_DSN 환경변수를 설정하세요."

# ======== 🧠 모델/세션 ========
model = SentenceTransformer("jhgan/ko-sroberta-multitask")
chat_sessions = {}

# ✅ OpenAI 클라이언트 (하드코딩 제거)
client = OpenAI(api_key=OPENAI_API_KEY)

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
    total = await count_by_category(category)
    offset = (page - 1) * page_size
    rows = await list_by_category(category, offset, page_size)
    items = [ComponentOut(**row) for row in rows]
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


# ======== 💬 Chat Request ========
class ChatRequest(BaseModel):
    query: str
    session_id: str = "default"


# ======== 🔍 DB 검색 (RAG) ========
def retrieve_similar(query, top_k=3):
    emb = model.encode(query).tolist()
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
