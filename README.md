# CSSMasterLibrary

여러 오픈소스 사이트에 흩어진 CSS·Tailwind UI 스니펫을 수집하고, 검색부터 격리된 미리보기와 코드 확인까지 연결한 개발자 도구입니다.

## 핵심 기능

- Selenium 기반 지연 로딩 페이지 수집과 코드 에디터 추출 폴백
- 코드·메타데이터 정제 및 PostgreSQL/pgvector 임베딩 저장
- 이름·설명 키워드 점수와 벡터 유사도를 결합한 하이브리드 검색
- 카테고리와 라이브러리 필터
- 전체 HTML, 부분 HTML, CSS-only, Tailwind 스니펫을 `iframe srcDoc`로 정규화
- 카테고리별 DOM 크기와 스타일 신호를 이용한 렌더링 품질 검사
- DB 없이도 핵심 화면을 확인할 수 있는 내장 데모 모드

```text
Open-source UI sites
  → Selenium crawlers
  → parsing / cleanup / deduplication
  → PostgreSQL + pgvector
  → FastAPI hybrid search API
  → React search and category UI
  → isolated iframe preview
```

## 빠른 실행: 데모 모드

데이터베이스나 API 키 없이 컴포넌트 목록과 검색 화면을 실행할 수 있습니다.

### 백엔드

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 프론트엔드

```bash
cd frontend
npm install
npm run dev
```

브라우저에서 `http://localhost:5173`을 열고 **컴포넌트 검색**을 선택합니다. 데모 검색어로 `네온`, `검색`, `카드`, `button`을 사용할 수 있습니다.

## PostgreSQL 하이브리드 검색 모드

1. PostgreSQL에 `vector`, `pg_trgm` 확장을 활성화합니다.
2. `backend/.env.example`을 `.env`로 복사합니다.
3. `DATABASE_URL`을 설정하면 서버가 자동으로 실제 DB 모드로 전환됩니다.

검색 점수는 벡터 코사인 유사도 65%, 이름·설명 키워드 유사도 35%로 계산됩니다. `DATABASE_URL`이 없으면 동일 API 계약을 유지하면서 내장 데이터의 키워드 검색을 사용합니다.

## 주요 API

| Method | Path | 설명 |
| --- | --- | --- |
| GET | `/health` | 서버 상태 |
| GET | `/components` | 카테고리별 페이지 조회 |
| GET | `/components/search?q=...` | 키워드·벡터 하이브리드 검색 |
| POST | `/chat/stream` | 검색 문맥 기반 HTML/CSS 생성 |

## 디렉터리

```text
backend/   FastAPI, PostgreSQL 조회, 하이브리드 검색, RAG
frontend/  React/Vite 검색 UI, 코드 보기, iframe 미리보기
Crawl/     출처별 Selenium/GitHub 수집 스크립트
RAG/       임베딩 생성 및 초기 실험 코드
```

## 환경변수

- `DATABASE_URL`: asyncpg가 사용하는 PostgreSQL DSN
- `PG_DSN`: RAG의 동기 pgvector 조회 DSN (`DATABASE_URL`을 대체해 목록 API에도 사용 가능)
- `OPENAI_API_KEY`: AI 코드 생성 기능을 사용할 때만 필요
- `EMBEDDING_MODEL`: 기본값 `jhgan/ko-sroberta-multitask`
- `ALLOWED_ORIGINS`: 쉼표로 구분한 프론트엔드 origin
- `VITE_API_BASE`: 프론트엔드 API 주소, 기본값 `http://localhost:8000`

> 외부에서 수집한 코드는 신뢰할 수 없는 입력입니다. 운영 배포 시 iframe sandbox와 CSP의 허용 범위를 서비스 요구사항에 맞게 추가로 제한해야 합니다.
