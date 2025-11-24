import psycopg2, time, re, concurrent.futures, threading, os, math
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- DB 연결 ---
conn = psycopg2.connect(
    host="220.74.18.216",
    dbname="daelim",
    user="admin",
    password="qwe123",
    port="5432"
)
cur = conn.cursor()
lock = threading.Lock()

# --- 크롬 옵션 ---
def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

BASE_URL = "https://www.creative-tim.com/twcomponents/components"
PROGRESS_FILE = "progress.txt"
ERROR_LOG = "error_log.txt"
OUTPUT_LOG = "output_log.txt"

# --- 유틸 ---
def log_error(msg):
    with open(ERROR_LOG, "a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {msg}\n")

def log_output(msg):
    with open(OUTPUT_LOG, "a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {msg}\n")

def is_duplicate(link):
    with lock:
        cur.execute("SELECT 1 FROM components_tbl_test WHERE components_source_url = %s LIMIT 1;", (link,))
        return cur.fetchone() is not None

# --- 카테고리 수집 ---
def get_categories():
    driver = get_driver()
    driver.get(BASE_URL)

    # 카테고리 로드될 때까지 대기
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((
                By.CSS_SELECTOR,
                "a.px-3.py-1\\.5.text-gray-500.dark\\:text-gray-400.rounded-lg.capitalize.hover\\:bg-gray-100.dark\\:hover\\:bg-gray-800"
            ))
        )
    except Exception as e:
        print("⚠️ 카테고리 로드 실패:", e)
        driver.quit()
        return []

    # 카테고리 추출
    cat_elems = driver.find_elements(
        By.CSS_SELECTOR,
        "a.px-3.py-1\\.5.text-gray-500.dark\\:text-gray-400.rounded-lg.capitalize.hover\\:bg-gray-100.dark\\:hover\\:bg-gray-800"
    )

    categories = []
    for elem in cat_elems:
        name = elem.text.strip()
        href = elem.get_attribute("href")

        # All만 제외
        if name.lower() == "all":
            continue

        if href and name:
            categories.append((name, href))

    print(f"📚 총 {len(categories)}개 카테고리 발견!")
    for i, (n, h) in enumerate(categories, 1):
        print(f"   {i}. {n} → {h}")

    driver.quit()
    return categories


# --- 페이지 단위 링크 수집 ---
def crawl_page(url):
    try:
        driver = get_driver()
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[href*='/component/']"))
        )
        cards = driver.find_elements(By.CSS_SELECTOR, "a[href*='/component/']")
        links = list({c.get_attribute("href") for c in cards if c.get_attribute("href")})
        driver.quit()
        return links
    except Exception as e:
        log_error(f"페이지 로드 실패: {url} - {e}")
        return []

# --- 상세 페이지 크롤링 ---
def crawl_detail(link, category):
    start = time.time()
    try:
        if is_duplicate(link):
            msg = f"⏩ 중복 스킵: {link}"
            log_output(msg)
            return msg

        driver = get_driver()
        driver.get(link)

        # 이름
        try:
            name_elem = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "h1.text-2xl.font-semibold.text-gray-800.dark\\:text-gray-200")
                )
            )
            name = name_elem.text.strip()
        except:
            name = link.split("/")[-1]

        # 설명
        try:
            desc_elem = driver.find_element(
                By.CSS_SELECTOR,
                "p.mt-2.text-gray-500.dark\\:text-gray-400.lg\\:max-w-xl.description-link"
            )
            description = desc_elem.text.strip()
        except:
            description = None

        # 작성자
        try:
            author_elem = driver.find_element(
                By.CSS_SELECTOR,
                "a.text-gray-400.hover\\:underline"
            )
            author_text = author_elem.text.strip()
            author = re.sub(r"^\s*by[:\s]+", "", author_text, flags=re.IGNORECASE).strip()
        except:
            author = "Creative Tim"

        # 코드 추출
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Show Code')]"))
        ).click()
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".view-lines.monaco-mouse-cursor-text"))
        )
        full_code = driver.execute_script("return monaco.editor.getModels()[0].getValue();")
        driver.quit()

        if not full_code or len(full_code.strip()) == 0:
            msg = f"⚠️ 코드 없음: {link}"
            log_output(msg)
            return msg

        # DB 저장
        with lock:
            cur.execute("""
                INSERT INTO components_tbl_test (
                    components_name,
                    components_description,
                    components_preview_html,
                    components_code,
                    components_library,
                    components_source_url,
                    components_author,
                    components_category
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (name, description, None, full_code, "Tailwind", link, author, category))
            conn.commit()

        elapsed = round(time.time() - start, 1)
        msg = f"✅ [{category}] 저장 완료: {name} (작성자: {author}) ⏱ {elapsed}s"
        log_output(msg)
        return msg

    except Exception as e:
        log_error(f"{link} - {e}")
        try: driver.quit()
        except: pass
        return f"❌ 오류: {link} ({e})"

# --- 카테고리 단위 크롤링 ---
def crawl_category(category_name, category_url, category_index, total_categories, total_saved_global):
    start_time = time.time()
    page = 1
    total_saved_local = 0

    print(f"\n🌈 [{category_index}/{total_categories}] {category_name} 카테고리 시작!")

    while True:
        url = f"{category_url}?page={page}"
        print(f"\n📄 [{category_name}] 페이지 {page} 크롤링 중...")

        links = crawl_page(url)
        if not links:
            print(f"⚠️ [{category_name}] 페이지 {page} 항목 없음 → 다음 카테고리로 이동")
            break

        page_start = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            futures = [executor.submit(crawl_detail, link, category_name) for link in links]
            for future in concurrent.futures.as_completed(futures):
                msg = future.result()
                print(f"   {msg}")
                if msg.startswith("✅"):
                    total_saved_local += 1
                    total_saved_global[0] += 1  # 리스트 참조로 전역 카운트 증가

        # ETA 계산
        elapsed = time.time() - start_time
        progress = category_index / total_categories * 100
        avg_time = elapsed / max(category_index, 1)
        remaining = avg_time * (total_categories - category_index)
        eta_min = math.floor(remaining / 60)
        eta_sec = math.floor(remaining % 60)

        print(f"\n📊 카테고리 진행률: {progress:.2f}% | ⏱ ETA: {eta_min:02d}:{eta_sec:02d} 남음")
        print(f"📦 [{category_name}] 누적 {total_saved_local}개 / 전체 {total_saved_global[0]}개 저장 완료")

        page += 1
        time.sleep(1)

    print(f"✅ [{category_name}] 완료 - 총 {total_saved_local}개 저장됨\n")


# --- 메인 실행 ---
if __name__ == "__main__":
    categories = get_categories()
    total_saved_global = [0]  # 리스트로 감싸면 참조 가능 (thread-safe)

    print(f"\n📚 총 {len(categories)}개 카테고리 발견!\n")

    for i, (category_name, category_url) in enumerate(categories, start=1):
        crawl_category(category_name, category_url, i, len(categories), total_saved_global)

    cur.close()
    conn.close()
    print(f"\n🎉 전체 크롤링 완료! 총 {total_saved_global[0]}개 저장됨 🚀")
