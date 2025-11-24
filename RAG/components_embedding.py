import psycopg2
import time
from sentence_transformers import SentenceTransformer

# ====== 🧠 모델 로드 ======
print("🧩 임베딩 모델 로딩 중... (1회만 다운로드됨)")
model = SentenceTransformer('multi-qa-mpnet-base-dot-v1')
print("✅ 모델 로드 완료!")

# ====== 🔧 DB 연결 설정 ======
DB_DSN = "dbname=daelim user=admin password=qwe123 host=localhost port=5432"

conn = psycopg2.connect(DB_DSN)
cur = conn.cursor()

# ====== 🧠 임베딩 생성 함수 ======
def generate_embedding_local(text: str):
    """SentenceTransformer 로컬 임베딩 생성"""
    try:
        return model.encode(text).tolist()
    except Exception as e:
        print(f"❌ 임베딩 오류: {e}")
        return None

# ====== 💾 테이블 처리 함수 ======
def process_table(table_name, id_col, text_builder):
    cur.execute(f"SELECT {id_col} FROM {table_name} WHERE embedding IS NULL;")
    rows = cur.fetchall()
    total = len(rows)
    print(f"\n🧱 {table_name}: {total}개 처리 예정")

    for idx, (row_id,) in enumerate(rows, start=1):
        cur.execute(f"SELECT * FROM {table_name} WHERE {id_col} = %s;", (row_id,))
        data = cur.fetchone()
        colnames = [desc[0] for desc in cur.description]
        record = dict(zip(colnames, data))

        text = text_builder(record)
        if not text.strip():
            print(f"⚪ {idx}/{total} {row_id} — 내용 없음, 스킵")
            continue

        emb = generate_embedding_local(text)
        if emb:
            cur.execute(f"UPDATE {table_name} SET embedding = %s WHERE {id_col} = %s;", (emb, row_id))
            conn.commit()
            print(f"✅ {idx}/{total} {row_id} 저장 완료")
        else:
            print(f"❌ {idx}/{total} {row_id} 실패")
        time.sleep(0.05)  # 약간의 대기

# ====== 🧩 UI 기반 텍스트 빌더 ======
def build_ui_text(r):
    return f"""
    Name: {r.get('components_name', '')}
    Category: {r.get('components_category', '')}
    Library: {r.get('components_library', '')}
    Description: {r.get('components_description', '')}
    Code:
    {r.get('components_code', '')}
    """

# ====== 🎨 CSS 아트 기반 텍스트 빌더 ======
def build_art_text(r):
    return f"""
    Title: {r.get('art_name', '')}
    CSS:
    {r.get('art_css', '')}
    """

# ====== 🚀 실행 ======
if __name__ == "__main__":
    try:
        process_table("components_tbl_test", "components_id", build_ui_text)
        process_table("css_art_tbl", "art_id", build_art_text)
    finally:
        cur.close()
        conn.close()
        print("\n🎉 모든 임베딩 생성 완료!")
