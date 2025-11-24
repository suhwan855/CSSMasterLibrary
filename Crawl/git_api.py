import os, time, requests, psycopg2
from datetime import datetime
from dotenv import load_dotenv

# ========= 환경설정 =========
load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
PG_DSN = os.getenv("PG_DSN")

assert GITHUB_TOKEN, "GITHUB_TOKEN 환경변수를 설정하세요."
assert PG_DSN, "PG_DSN 환경변수를 설정하세요."

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28"
}


# ========= 설정 =========
ALLOWED_LICENSES = {
    "MIT", "CC0-1.0", "CC-BY-4.0", "BSD-3-Clause", "BSD-2-Clause", "Apache-2.0",
    "Unknown", "NOASSERTION"
}
FILE_EXTS = (".css", ".scss", ".sass")

ART_KEYWORDS = [
    "@keyframes", "clip-path", "gradient", "filter", "shadow",
    "transform", "translate", "rotate", "scale", "mask",
    "skew", "animation", "perspective"
]

BRANCH_CANDIDATES = ["main", "master", "gh-pages", "source"]

# ========= 공통: 안전한 GET (retry/backoff + rate-limit 대기) =========
def github_get(url, params=None, max_retries=5, timeout=20):
    retries = 0
    while True:
        try:
            r = requests.get(url, headers=HEADERS, params=params, timeout=timeout)
        except requests.exceptions.ConnectionError as e:
            retries += 1
            if retries > max_retries:
                print(f"🚫 ConnectionError: {e} — 재시도 초과, 스킵: {url}")
                return None
            wait = 3 * retries
            print(f"⚠️ 연결 끊김... {wait}s 대기 후 재시도 ({retries}/{max_retries})")
            time.sleep(wait)
            continue

        # rate limit
        if r.status_code == 403 and r.headers.get("X-RateLimit-Remaining") == "0":
            reset = int(r.headers.get("X-RateLimit-Reset", "0") or 0)
            wait = max(0, reset - int(time.time()) + 3)
            reset_time = datetime.fromtimestamp(reset).strftime("%H:%M:%S")
            print(f"⏳ Rate limit hit, waiting {wait}s (reset @{reset_time})")
            time.sleep(wait)
            continue

        # 서버 일시 오류
        if r.status_code in (502, 503, 504):
            retries += 1
            if retries > max_retries:
                print(f"🚫 GitHub {r.status_code} — 재시도 초과, 스킵: {url}")
                return None
            wait = 2 * retries
            print(f"⚠️ GitHub {r.status_code} — {wait}s 후 재시도")
            time.sleep(wait)
            continue

        return r

# ========= DB =========
def db():
    return psycopg2.connect(PG_DSN)

def load_processed_authors(cur):
    # 이미 한 번이라도 저장된 author(=owner)는 skip → 이어받기
    cur.execute("SELECT DISTINCT art_author FROM css_art_tbl;")
    return {row[0] for row in cur.fetchall()}

def save_css(cur, path, css, owner, url, lic):
    cur.execute("""
        INSERT INTO css_art_tbl (art_name, art_css, art_author, art_source_url, license_type)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT DO NOTHING;
    """, (path, css, owner, url, lic))

# ========= 탐색/다운로드 =========
def get_default_or_fallback_branch(owner, repo):
    # 1) repo info default_branch 우선
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
    # git tree 재귀로 .css/.scss/.sass 경로 전부 추출
    r = github_get(f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1")
    if not r or r.status_code != 200:
        return []
    tree = r.json().get("tree", [])
    return [item["path"] for item in tree if item.get("path","").endswith(FILE_EXTS)]

def download_raw(owner, repo, branch, path):
    raw = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"
    r = github_get(raw)
    if not r or r.status_code != 200:
        return None
    try:
        return r.text
    except Exception:
        return None

def is_artistic(css_text):
    if not css_text:
        return False
    lower = css_text.lower()
    # 완화: 키워드 1개만 있어도 통과 (수집량 극대화)
    return any(k in lower for k in ART_KEYWORDS)

# ========= 레포 검색 (그대로 사용하거나, 이미 모아둔 리스트 사용) =========
def search_repositories(queries, pages=10):
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
            print(f"🔎 {q} p{page}: 누적 레포 {len(repos)}")
            time.sleep(0.8)
    return list(repos.values())

# ========= 메인 =========
def run():
    queries = [
        "css art language:css stars:>5", "pure css art language:css stars:>5",
        "css animation language:css stars:>5", "css experiment language:css",
        "css illustration language:css", "single div art language:css",
        "css 3d art language:css", "neon css language:css",
        "css optical illusion language:css", "css gradient art language:css",
        "css morph animation language:css", "css glassmorphism language:css",
        "css particle animation language:css", "css creative design language:css",
        "css challenge language:css", "css typography art language:css",
        "css shader effect language:css", "css line art language:css",
        "css landscape language:css", "css motion experiment language:css"
    ]

    # 1) 레포 목록
    repos = search_repositories(queries, pages=10)
    print(f"✅ Unique repos: {len(repos)}")

    # 2) DB 연결 & 이어받기 준비
    conn = db()
    cur = conn.cursor()
    processed_authors = load_processed_authors(cur)
    print(f"↪️ 이어받기: 이미 처리된 author {len(processed_authors)}명 skip")

    saved_total = 0
    processed = 0

    for repo in repos:
        owner, name, url, lic = repo["owner"], repo["name"], repo["url"], repo["license"]

        # 이어받기: 이미 수집한 author면 통과
        if owner in processed_authors:
            continue

        # 라이선스 필터
        if lic not in ALLOWED_LICENSES:
            print(f"⛔ 라이선스 제외: {owner}/{name} ({lic})")
            continue

        # 브랜치 결정
        branch = get_default_or_fallback_branch(owner, name)
        if not branch:
            print(f"⚪ 브랜치 확인 실패: {owner}/{name}")
            continue

        # 파일 경로 추출
        paths = list_code_paths(owner, name, branch)
        if not paths:
            print(f"⚪ CSS 없음: {owner}/{name}")
            continue

        kept = 0
        for path in paths:
            code = download_raw(owner, name, branch, path)
            if not code:
                continue
            if not is_artistic(code):
                continue
            try:
                save_css(cur, path, code, owner, url, lic)
                kept += 1
                saved_total += 1
            except Exception as e:
                # 스키마/인코딩 이슈는 건너뛴다
                print(f"DB insert error ({owner}/{name}:{path}): {e}")

        conn.commit()
        processed += 1
        if kept > 0:
            # 이 author는 처리된 것으로 마킹 (다음 실행부터 skip)
            processed_authors.add(owner)

        print(f"💾 {owner}/{name}@{branch} → kept {kept} css (total saved: {saved_total})")
        time.sleep(0.4)

    cur.close()
    conn.close()
    print(f"🎉 완료! 처리 레포 {processed}, 저장 파일 {saved_total}")

if __name__ == "__main__":
    run()