CSSMasterLibrary

오픈소스 UI 코드를 자동으로 수집·정제하고, 검색과 브라우저 미리보기를 통해 원하는 컴포넌트를 탐색할 수 있는 개발자 도구입니다.

주요 기능
오픈소스 UI 코드 자동 수집
HTML·CSS·Tailwind 코드 정제
키워드 및 벡터 기반 컴포넌트 검색
카테고리별 UI 탐색
브라우저 기반 실시간 미리보기
컴포넌트 코드 확인
기술 스택
Frontend: React, Vite, Tailwind CSS
Backend: FastAPI, Python
Crawling: Selenium
Database: PostgreSQL, pgvector
AI: SentenceTransformers
핵심 구현
동적으로 로딩되는 페이지에서 UI 코드를 수집하는 크롤링 파이프라인을 구현했습니다.
키워드 검색과 임베딩 벡터 검색을 결합한 하이브리드 검색을 적용했습니다.
iframe srcDoc을 활용해 수집한 컴포넌트를 기존 페이지와 분리된 환경에서 미리보기로 제공했습니다.
CSS만 존재하는 코드에는 기본 DOM 구조를 추가해 렌더링될 수 있도록 처리했습니다.
