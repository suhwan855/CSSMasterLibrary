"""
🌐 UI Component Collector v3 (GitHub → PostgreSQL)
Author: Hyunbin + ChatGPT
Goal: Collect clean, non-duplicate pure HTML/CSS UI components for RAG/embedding
"""

import os, time, requests, psycopg2
from datetime import datetime
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# ========= 환경설정 =========
load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
PG_DSN = os.getenv("PG_DSN") or "dbname=daelim user=admin password=qwe123 host=localhost port=5432"

assert GITHUB_TOKEN, "❌ GITHUB_TOKEN 환경변수를 설정하세요."
assert PG_DSN, "❌ PG_DSN 환경변수를 설정하세요."

HEADERS = {
    "Authorization": f" {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28"
}

# ========= 기본 설정 =========
ALLOWED_LICENSES = {
    "MIT", "CC0-1.0", "CC-BY-4.0", "BSD-3-Clause", "BSD-2-Clause",
    "Apache-2.0", "Unknown", "NOASSERTION"
}
FILE_EXTS = (".html", ".css")
FORBIDDEN_TERMS = ["tailwind", "bootstrap", "react", "vue", "svelte", "<script", "@apply"]

UI_KEYWORDS = [
    "button", "card", "navbar", "input", "form", "grid", "layout", "gallery",
    "profile", "banner", "modal", "footer", "table", "timeline", "login",
    "dashboard", "dropdown", "accordion", "list", "popup", "badge", "sidebar"
]

BRANCH_CANDIDATES = ["main", "master", "gh-pages", "source"]

# ========= 모델 =========
model = SentenceTransformer("jhgan/ko-sroberta-multitask")

# ========= GitHub GET with retry & rate limit =========
def github_get(url, params=None, max_retries=5, timeout=20):
    retries = 0
    while True:
        try:
            r = requests.get(url, headers=HEADERS, params=params, timeout=timeout)
        except requests.exceptions.ConnectionError:
            retries += 1
            if retries > max_retries:
                print(f"🚫 ConnectionError — 스킵: {url}")
                return None
            wait = 3 * retries
            print(f"⚠️ 연결 끊김... {wait}s 대기 후 재시도")
            time.sleep(wait)
            continue

        if r.status_code == 403 and r.headers.get("X-RateLimit-Remaining") == "0":
            reset = int(r.headers.get("X-RateLimit-Reset", "0") or 0)
            wait = max(0, reset - int(time.time()) + 5)
            reset_time = datetime.fromtimestamp(reset).strftime("%H:%M:%S")
            print(f"⏳ Rate limit hit, waiting {wait}s (reset @{reset_time})")
            time.sleep(wait)
            continue

        if r.status_code in (502, 503, 504):
            retries += 1
            if retries > max_retries:
                print(f"🚫 GitHub {r.status_code} — 재시도 초과, 스킵")
                return None
            wait = 2 * retries
            print(f"⚠️ GitHub {r.status_code} — {wait}s 후 재시도")
            time.sleep(wait)
            continue

        return r

# ========= DB =========
def db():
    return psycopg2.connect(PG_DSN)

def save_ui(cur, name, code, author, url, lib, emb):
    cur.execute("""
        INSERT INTO ui_tbl (
            ui_name, ui_full_code, ui_author,
            ui_source_url, ui_library, embedding
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT DO NOTHING;
    """, (name, code, author, url, lib, emb))

# ========= 도우미 =========
def get_default_or_fallback_branch(owner, repo):
    info = github_get(f"https://api.github.com/repos/{owner}/{repo}")
    if info and info.status_code == 200:
        default_branch = info.json().get("default_branch")
        candidates = [default_branch] + BRANCH_CANDIDATES
    else:
        candidates = BRANCH_CANDIDATES

    seen = set()
    for b in candidates:
        if not b or b in seen:
            continue
        seen.add(b)
        resp = github_get(f"https://api.github.com/repos/{owner}/{repo}/branches/{b}")
        if resp and resp.status_code == 200:
            return b
    return None

def list_code_paths(owner, repo, branch):
    r = github_get(f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1")
    if not r or r.status_code != 200:
        return []
    tree = r.json().get("tree", [])
    return [item["path"] for item in tree if item.get("path", "").endswith(FILE_EXTS)]

def download_raw(owner, repo, branch, path):
    raw = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"
    r = github_get(raw)
    if not r or r.status_code != 200:
        return None
    try:
        return r.text
    except Exception:
        return None

def is_pure_ui(code):
    if not code:
        return False
    lower = code.lower()
    return not any(term in lower for term in FORBIDDEN_TERMS)

# ========= 레포 검색 =========
def search_repositories(queries, pages=20):
    repos = {}
    for q in queries:
        for page in range(1, pages + 1):
            params = {"q": q, "sort": "stars", "order": "desc", "per_page": 100, "page": page}
            r = github_get("https://api.github.com/search/repositories", params=params)
            if not r or r.status_code != 200:
                break
            items = r.json().get("items", [])
            if not items:
                break
            for repo in items:
                key = f"{repo['owner']['login']}/{repo['name']}"
                lic = (repo.get("license") or {}).get("spdx_id") or "Unknown"
                repos[key] = {
                    "owner": repo["owner"]["login"],
                    "name": repo["name"],
                    "url": repo["html_url"],
                    "license": lic
                }
            print(f"🔎 {q} (p{page}) — 누적 {len(repos)}개 레포")
            time.sleep(1.0)
    return list(repos.values())

# ========= 메인 =========
def run():
    queries = [
        "pure html ui component language:html stars:>10",
        "simple ui layout language:html stars:>10",
        "css ui design language:css stars:>10",
        "frontend template ui language:html",
        "ui elements html css language:html",
        "minimalist html css ui language:html",
        "html5 dashboard ui language:html",
        "responsive html ui template language:html",
        "html css web component design language:html"
    ]

    repos = search_repositories(queries, pages=20)
    print(f"✅ Unique repos: {len(repos)}")

    conn = db()
    cur = conn.cursor()
    saved_total = 0
    seen_codes = set()  # ✅ 중복 방지용 set

    for repo in repos:
        owner, name, url, lic = repo["owner"], repo["name"], repo["url"], repo["license"]

        if lic not in ALLOWED_LICENSES:
            print(f"⛔ 라이선스 제외: {owner}/{name} ({lic})")
            continue

        branch = get_default_or_fallback_branch(owner, name)
        if not branch:
            print(f"⚪ 브랜치 확인 실패: {owner}/{name}")
            continue

        paths = list_code_paths(owner, name, branch)
        if not paths:
            print(f"⚪ 코드 없음: {owner}/{name}")
            continue

        kept = 0
        for path in paths:
            code = download_raw(owner, name, branch, path)
            if not code or not is_pure_ui(code):
                continue

            # ⚙️ 필터링 로직
            if len(code) < 100:
                continue
            if path.lower().startswith(("index", "demo", "example")):
                continue
            normalized = code.strip()
            if normalized in seen_codes:
                continue
            seen_codes.add(normalized)

            emb = model.encode(code).tolist()

            try:
                save_ui(cur, path, code, owner, url, "pure_html_css", emb)
                kept += 1
                saved_total += 1
            except Exception as e:
                print(f"❌ DB 저장 실패 ({owner}/{name}:{path}) → {e}")
                continue

        conn.commit()
        if kept > 0:
            print(f"💾 {owner}/{name}@{branch} → {kept}개 저장 (총 {saved_total})")
        else:
            print(f"⚪ {owner}/{name} → 저장된 코드 없음")
        time.sleep(0.8)

    cur.close()
    conn.close()
    print(f"🎉 완료! 총 {saved_total}개의 고유 UI 컴포넌트가 수집되었습니다.")

if __name__ == "__main__":
    run()
