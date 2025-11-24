# mini_crawl_uiverse_buttons_to_db.py
# Author DOM 추출 + tqdm 진행률 + logging 요약 출력 + DB insert (근본 해결 적용)
# pip install tqdm selenium webdriver-manager psycopg[binary]

import re
import time
import html as htmlmod
import logging
from typing import List, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from tqdm import tqdm
import psycopg
from psycopg.rows import dict_row

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# ===================== 로깅 설정 =====================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("uiverse")

# ===================== 설정 =====================
BASE = "https://uiverse.io"
CATEGORY = "Buttons"  # 다른 카테고리 크롤링 시 바꿔주세요
LIST_URL = BASE + "/buttons?page={page}"

HEADLESS_LIST   = False   # 목록(윈도우 뜸)
HEADLESS_DETAIL = True    # 상세(윈도우 안 뜸)

MAX_WORKERS   = 6
SCROLL_STEPS  = 18
SCROLL_DY     = 1800
SCROLL_PAUSE  = 0.35

# /Author/slug-123 (대부분 Uiverse 상세 URL 패턴)
PAT = re.compile(r"^/[A-Za-z0-9-]+/[A-Za-z0-9-]+-\d+$")

# ---- DB 연결 설정 (환경에 맞게 수정) ----
PG_DSN = {
    "host": "220.74.18.216",
    "port": 5432,
    "user": "admin",
    "password": "qwe123",
    "dbname": "daelim",
}
TABLE = "components_tbl_test"

# ===================== 유틸 =====================
def make_driver(headless: bool = True):
    opt = webdriver.ChromeOptions()
    if headless:
        opt.add_argument("--headless=new")
    opt.add_argument("--window-size=1366,3000")
    opt.add_argument("--lang=ko-KR")
    opt.add_argument("--disable-gpu")
    opt.add_argument("--no-sandbox")
    opt.add_argument("--disable-dev-shm-usage")
    opt.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
    opt.add_experimental_option("excludeSwitches", ["enable-automation"])
    opt.add_experimental_option("useAutomationExtension", False)
    opt.add_argument("--disable-blink-features=AutomationControlled")

    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=opt)
    driver.set_page_load_timeout(60)
    driver.implicitly_wait(2)
    try:
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
        })
    except Exception:
        pass
    return driver

def slug(url: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "-", url.strip("/").split("/")[-1]).strip("-").lower() or "component"

def humanize_slug(s: str) -> str:
    s = re.sub(r"-\d+$", "", s)  # 뒤쪽 숫자 제거
    parts = [p for p in s.replace("_", "-").split("-") if p]
    return " ".join(w.capitalize() for w in parts) or "Component"

def parse_author_from_url(detail_url: str) -> Optional[str]:
    # https://uiverse.io/<author>/<slug-123>
    try:
        path = detail_url.split("://", 1)[-1].split("/", 1)[-1]
        bits = [b for b in path.split("/") if b]
        return bits[0] if len(bits) >= 2 else None
    except Exception:
        return None

# ========= (A) 근본 해결용 정리 유틸: CSS-only 판별 & 엔티티/이스케이프 정리 =========
CSS_ONLY_RE = re.compile(r"^[^{]*\{[\s\S]*\}[\s\S]*$", re.M)

def _looks_css_only(s: str) -> bool:
    if not s:
        return False
    t = s.strip()
    # 태그 기호가 있으면 HTML일 가능성이 큼
    if "<" in t and ">" in t:
        return False
    # 중괄호 블록이 보이면 CSS 가능성
    return bool(CSS_ONLY_RE.search(t))

def _clean_piece(s: str) -> str:
    """엔티티 복원 + 흔한 이스케이프 제거 + 앞뒤 공백 제거"""
    if not s:
        return ""
    s = htmlmod.unescape(s)
    s = s.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
    return s.strip()

# ===================== 목록: 링크 수집 =====================
def collect_links(page_num: int) -> List[str]:
    d = make_driver(headless=HEADLESS_LIST)
    try:
        d.get(LIST_URL.format(page=page_num))

        # 메인 도착 대기
        try:
            WebDriverWait(d, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, "main")))
        except TimeoutException:
            pass

        # "Get code" 또는 data-discover 대기
        try:
            WebDriverWait(d, 10).until(
                EC.presence_of_element_located((
                    By.XPATH,
                    "//*[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'get code')]"
                ))
            )
        except TimeoutException:
            try:
                WebDriverWait(d, 6).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "a[data-discover='true'][href^='/']"))
                )
            except TimeoutException:
                pass

        # 스크롤로 지연 로딩 요소 로드
        for _ in range(SCROLL_STEPS):
            d.execute_script(f"window.scrollBy(0, {SCROLL_DY});")
            time.sleep(SCROLL_PAUSE)
        d.execute_script("window.scrollTo(0, 0);")

        links = set()

        # 1) "Get code" 앵커
        for a in d.find_elements(
            By.XPATH,
            "//a[contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'get code') and starts-with(@href,'/')]"
        ):
            href = a.get_attribute("href") or ""
            rel = "/" + href.split("/", 3)[-1] if href.startswith("http") else href
            if PAT.match(rel):
                links.add(BASE + rel)

        # 2) backup: data-discover
        for a in d.find_elements(By.CSS_SELECTOR, "a[data-discover='true'][href^='/']"):
            href = a.get_attribute("href") or ""
            rel = "/" + href.split("/", 3)[-1] if href.startswith("http") else href
            if PAT.match(rel):
                links.add(BASE + rel)

        # 3) 최후: 모든 a[href^='/']에서 정규식 필터
        if not links:
            for a in d.find_elements(By.XPATH, "//a[starts-with(@href,'/')]"):
                href = a.get_attribute("href") or ""
                rel = "/" + href.split("/", 3)[-1] if href.startswith("http") else href
                if PAT.match(rel):
                    links.add(BASE + rel)

        return sorted(links)
    finally:
        d.quit()

# ===================== 상세: 탭 활성화 → 패널 범위에서 코드 읽기 =====================
def _click_tab_and_get_panel(d, tab_key: str, wait: WebDriverWait):
    """tab_key: 'html'|'css' → role=tab 버튼 클릭 후 aria-controls 패널 반환"""
    btn = None
    try:
        btn = d.find_element(By.CSS_SELECTOR, f"button[role='tab'][id*='trigger-{tab_key}']")
    except Exception:
        label = tab_key.upper()
        for xp in (
            f"//button[@role='tab' and normalize-space()='{label}']",
            f"//button[@role='tab' and contains(.,'{label}')]",
            f"//*[self::a or self::button][@role='tab' and contains(.,'{label}')]",
        ):
            try:
                btn = d.find_element(By.XPATH, xp); break
            except Exception:
                pass
    if not btn:
        return None

    # 활성화 시도
    try:
        d.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
        btn.click(); time.sleep(0.15)
        for _ in range(3):
            if (btn.get_attribute("data-state") or "").lower() == "active":
                break
            btn.click(); time.sleep(0.15)
    except Exception:
        pass

    panel = None
    try:
        panel_id = btn.get_attribute("aria-controls") or ""
        if panel_id:
            wait.until(EC.presence_of_element_located((By.ID, panel_id)))
            panel = d.find_element(By.ID, panel_id)
            d.execute_script("arguments[0].scrollIntoView({block:'center'});", panel)
            time.sleep(0.1)
    except Exception:
        panel = None
    return panel

def _read_code_from_panel(d, panel, prefer_id: str) -> str:
    """panel 내부에서 textarea.value 우선으로 코드 읽기"""
    root = panel if panel is not None else d

    # 1) id로 직접
    try:
        el = root.find_element(By.ID, prefer_id)
        d.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        time.sleep(0.05)
        val = (d.execute_script("return arguments[0].value;", el) or "").strip()
        if val:
            return val
    except Exception:
        pass

    # 2) 같은 클래스의 textarea
    try:
        areas = root.find_elements(By.CSS_SELECTOR, "textarea.npm__react-simple-code-editor__textarea")
        for t in areas:
            v = (t.get_attribute("value") or "").strip()
            if v:
                return v
    except Exception:
        pass

    # 3) pre > code
    try:
        codes = root.find_elements(By.CSS_SELECTOR, "pre code")
        for c in codes:
            v = (c.text or "").strip()
            if v:
                return v
    except Exception:
        pass

    # 4) contenteditable
    try:
        edits = root.find_elements(By.CSS_SELECTOR, "[contenteditable='true']")
        for e in edits:
            v = (e.get_attribute("textContent") or "").strip()
            if v:
                return v
    except Exception:
        pass

    return ""

def _extract_author_dom_first(d) -> Optional[str]:
    # 작성자 DOM 우선 추출, 실패 시 None
    try:
        el = d.find_element(By.CSS_SELECTOR, "div.card__nickname")
        tx = (el.text or "").strip().lstrip("@")
        if tx:
            return tx
    except Exception:
        pass
    for sel in [
        "[class*='card__nickname']",
        ".card__nickname.text-color",
        "div.card__nickname.text-color.flex.items-center",
        "[class*='card__nickname'] a",
    ]:
        try:
            el = d.find_element(By.CSS_SELECTOR, sel)
            tx = (el.text or "").strip().lstrip("@")
            if tx:
                return tx
        except Exception:
            pass
    return None

def read_codes(detail_url: str) -> Tuple[str, str, str, str]:
    """
    returns: (slug, html, css, author)
    """
    d = make_driver(headless=HEADLESS_DETAIL)
    try:
        d.get(detail_url)
        wait = WebDriverWait(d, 15)
        time.sleep(0.6)

        # (있으면) 쿠키/모달 닫기 — 실패해도 무시
        for xp in (
            "//button[contains(.,'Accept') or contains(.,'I agree') or contains(.,'Got it') or contains(.,'확인')]",
            "//div[contains(@class,'cookie') or contains(@class,'modal')]//button",
        ):
            try:
                d.find_element(By.XPATH, xp).click(); time.sleep(0.2)
            except Exception:
                pass

        author = _extract_author_dom_first(d) or None
        if not author:
            author = parse_author_from_url(detail_url) or None

        # HTML / CSS 탭 → 각 패널
        html_panel = _click_tab_and_get_panel(d, "html", wait)
        css_panel  = _click_tab_and_get_panel(d, "css",  wait)

        # 각 탭 패널 내부에서 읽기
        html_raw = _read_code_from_panel(d, html_panel, "codeArea2")
        css      = _read_code_from_panel(d, css_panel,  "codeArea1")

        # 백업 경로: 전체 문서 스캔
        if not (html_raw and css):
            for t in d.find_elements(By.CSS_SELECTOR, "textarea.npm__react-simple-code-editor__textarea"):
                v = (t.get_attribute("value") or "").strip()
                if not v:
                    continue
                vu = htmlmod.unescape(v)
                if (not html_raw) and ("<" in vu and ">" in vu and "{" not in vu[:200]):
                    html_raw = v
                if (not css) and ("{" in v and "}" in v and "</" not in v):
                    css = v
                if html_raw and css:
                    break
            if not (html_raw and css):
                for c in d.find_elements(By.CSS_SELECTOR, "pre code"):
                    v = (c.text or "").strip()
                    if not v:
                        continue
                    vu = htmlmod.unescape(v)
                    if (not html_raw) and ("<" in vu and ">" in vu and "{" not in vu[:200]):
                        html_raw = v
                    if (not css) and ("{" in v and "}" in v and "</" not in v):
                        css = v
                    if html_raw and css:
                        break

        # ========= (A) 1차 정리: 엔티티/이스케이프 정리 + CSS-only 판별 보정 =========
        html = _clean_piece(html_raw or "")
        css  = _clean_piece(css or "")

        # HTML 탭이 사실상 CSS 텍스트였던 경우 → CSS로 합치고 HTML 비우기
        if _looks_css_only(html):
            css = f"{html}\n{css}".strip()
            html = ""

        return slug(detail_url), html, css, (author or "")
    finally:
        d.quit()

# ===================== 합본 빌더(강화판) =====================
DOCT_RE = re.compile(r"<!doctype", re.I)

def _extract_body_inner(html_or_snippet: str) -> str:
    """
    html_or_snippet 이 완전 문서면 body.innerHTML만, snippet이면 그대로.
    단, snippet/문자열이 CSS-only로 보이면 빈 문자열 반환(데모 마크업 생성 트리거).
    """
    s = (html_or_snippet or "").strip()
    if not s:
        return ""
    # CSS-only처럼 보이면 body에 넣지 않음
    if _looks_css_only(s):
        return ""
    # 완전 문서면 body만 추출
    if DOCT_RE.search(s) or ("<html" in s.lower()) or ("<body" in s.lower()):
        m = re.search(r"<body[^>]*>([\s\S]*?)</body>", s, re.I)
        return (m.group(1) if m else "").strip()
    # snippet은 그대로
    return s

def _normalize_whitespace(s: str) -> str:
    return re.sub(r"[ \t]+\n", "\n", (s or "")).strip()

def build_combined_document(inner_html: str, css: str) -> str:
    """
    HTML 스니펫 + CSS를 안전한 '완전 HTML 문서'로 합본 생성
    - HTML이 완전 문서여도 body만 추출하여 중복 head 방지
    - CSS만 들어온 특수케이스 방지(데모 마크업 자동 추가)
    """
    html_part = _extract_body_inner(htmlmod.unescape(inner_html or ""))
    css_part  = _normalize_whitespace(htmlmod.unescape(css or ""))

    html_part = _normalize_whitespace(html_part)

    # HTML이 비고 CSS만 있는 경우 → 대표 클래스명으로 데모 생성
    if (not html_part) and css_part:
        m = re.search(r"\.([A-Za-z_][\w-]*)\s*{", css_part)
        cls = m.group(1) if m else None
        if cls and re.search(r"btn|button", cls, re.I):
            html_part = f'<button class="{cls}">Button</button>'
        elif cls:
            html_part = f'<div class="{cls}">Preview</div>'
        else:
            html_part = "<button>Button</button>"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Uiverse Preview</title>
<style>
/* --- Uiverse component CSS --- */
{css_part}
html, body {{ margin:0; padding:16px; }}
</style>
</head>
<body>
{html_part}
</body>
</html>"""

# ===================== DB 저장 =====================
def insert_component(cur, *, name: str, description: Optional[str], preview_html: Optional[str],
                     combined_code: str, library: str, source_url: str,
                     author: Optional[str], category: str):
    sql = f"""
    INSERT INTO {TABLE}
      (components_name, components_description, components_preview_html,
       components_code, components_library, components_source_url,
       components_author, components_category)
    VALUES (%(name)s, %(desc)s, %(preview)s, %(code)s, %(lib)s, %(src)s, %(author)s, %(cat)s)
    """
    cur.execute(sql, {
        "name": name,
        "desc": description,
        "preview": preview_html,     # 정책상 NULL 저장
        "code": combined_code,       # 완전 HTML 합본
        "lib": library,
        "src": source_url,
        "author": author,
        "cat": category,
    })

# ===================== 실행 루프 (수집 → 파싱 → DB) =====================
def crawl_to_db(p_from=1, stop_after_two_empty=True, max_workers=MAX_WORKERS):
    page = p_from
    empty_streak = 0
    total_saved = 0

    with psycopg.connect(**PG_DSN, row_factory=dict_row) as conn:
        conn.autocommit = False

        while True:
            log.info("🌍 page %s", page)
            links = collect_links(page)
            log.info("  links: %d", len(links))

            if not links:
                empty_streak += 1
                if stop_after_two_empty and empty_streak >= 2:
                    break
                page += 1
                continue

            empty_streak = 0
            page_ok = page_skip = page_err = 0

            # 상세 파싱은 병렬, DB는 메인 스레드에서 순차 커밋
            with ThreadPoolExecutor(max_workers=max_workers) as ex:
                futures = [ex.submit(read_codes, u) for u in links]
                with tqdm(total=len(links), desc=f"page {page} details", unit="item") as pbar:
                    for fut in as_completed(futures):
                        try:
                            slug_, html, css, author = fut.result()
                        except Exception as e:
                            log.error("  ⚠️ detail error: %s", e)
                            page_err += 1
                            pbar.update(1)
                            continue

                        if not (html or css):
                            log.warning("  ⚠️ skip(no code): %s", slug_)
                            page_skip += 1
                            pbar.update(1)
                            continue

                        # slug만으로는 원 URL을 정확히 역매핑하기 어려움 → best-effort
                        source_url = ""
                        for u in links:
                            if slug(u) == slug_:
                                source_url = u
                                break

                        name = humanize_slug(slug_)
                        library = "universe"   # 기존 데이터와 호환 위해 유지
                        category = CATEGORY
                        description = None

                        # ★ HTML+CSS 합본(완전 문서) — 강화판 빌더 사용
                        combined_doc = build_combined_document(html or "", css or "")

                        try:
                            with conn.cursor() as cur:
                                insert_component(
                                    cur,
                                    name=name,
                                    description=description,
                                    preview_html=None,          # ← NULL
                                    combined_code=combined_doc, # ← 합본을 code에
                                    library=library,
                                    source_url=source_url,
                                    author=(author or None),
                                    category=category,
                                )
                            conn.commit()
                            total_saved += 1
                            page_ok += 1
                            log.info("  ✅ inserted: %s (author: %s)", name, author or "unknown")
                        except Exception as e:
                            conn.rollback()
                            page_err += 1
                            log.error("  ❌ insert failed: %s -> %s", name, e)

                        pbar.update(1)

            log.info("page %s summary -> ok:%d skip:%d err:%d", page, page_ok, page_skip, page_err)
            page += 1

    log.info("🎉 done. total inserted: %d", total_saved)

# ===================== 엔트리포인트 =====================
if __name__ == "__main__":
    crawl_to_db(p_from=1, max_workers=MAX_WORKERS)
