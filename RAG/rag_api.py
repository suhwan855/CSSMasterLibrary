from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, HTMLResponse
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from openai import OpenAI
import psycopg2
import os, json, requests

# ======== ⚙️ 기본 설정 ========
app = FastAPI()

# 임베딩 모델 (질의 → 벡터 변환용)
model = SentenceTransformer("jhgan/ko-sroberta-multitask")
chat_sessions = {}

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT", "5432")),
}


# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ======== 💬 요청 스키마 ========
class ChatRequest(BaseModel):
    query: str
    session_id: str = "default"

# ======== 🔍 DB 검색 (RAG) ========
def retrieve_similar(query, top_k=3):
    emb = model.encode(query).tolist()
    with psycopg2.connect(**DB_CONFIG) as conn:
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


# ======== 🧠 프롬프트 생성 (한국어 버전) ========
def build_prompt_with_history(history, query):
    examples = retrieve_similar(query, top_k=3)
    examples_text = "\n\n".join([
        f"[{ex[5]}] 예시 (by {ex[4]}):\nHTML:\n{ex[1]}\n\nCSS:\n{ex[2]}"
        for ex in examples if ex[1] and ex[2]
    ])

    # 💡 [수정] 이전 대화 텍스트 관련 문구를 제거하고 현재 턴의 지시사항만 남깁니다.
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


# ======== 🚀 GPT-4o mini 스트리밍 응답 ========
@app.post("/chat/stream")
def chat_stream(req: ChatRequest):
    session_id = req.session_id
    query = req.query

    # 세션 불러오기 또는 초기화
    if session_id not in chat_sessions:
        chat_sessions[session_id] = []

    history = chat_sessions[session_id]
    prompt = build_prompt_with_history(history, query)

    def stream_generator():
        with requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": "OPENAI_API_KEY",
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

            # 세션에 저장
            history.append({"role": "user", "content": query})
            history.append({"role": "assistant", "content": full_response})

    return StreamingResponse(stream_generator(), media_type="text/event-stream")