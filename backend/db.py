# backend/db.py
import os
import asyncpg
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set")

_pool: asyncpg.Pool | None = None

# 기준 카테고리 집합 (Others 제외 기준)
# 필요 시 자유롭게 수정/추가. 오타 방지용으로 Logins/Loings 둘 다 포함.
PRIMARY_CATEGORIES = [
    "Buttons", "Inputs", "Cards", "Badges", "Alerts", "Alpinejs",
    "Logins", "Loings"  # 둘 중 하나만 쓰면 된다면 한쪽 삭제 가능
]

async def init_pool():
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            dsn=DATABASE_URL,
            min_size=1,
            max_size=10,
            command_timeout=30,
        )

async def close_pool():
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None

# --- SQL ---

# 1) 특정 카테고리 카운트
SQL_COUNT_BY_CATEGORY = """
SELECT COUNT(*) AS total
FROM public.components_tbl_test
WHERE LOWER(components_category) = LOWER($1);
"""

# 2) OTHERS 카운트: 기준 카테고리에 속하지 않는 모든 항목
SQL_COUNT_OTHERS = """
SELECT COUNT(*) AS total
FROM public.components_tbl_test
WHERE
  COALESCE(TRIM(components_category),'') <> ''
  AND LOWER(components_category) NOT IN (
    SELECT LOWER(x) FROM UNNEST($1::text[]) AS x
  );
"""

# 3) 특정 카테고리 리스트
# --- 변경 포인트만 발췌 ---

SQL_LIST_BY_CATEGORY = """
SELECT
  components_id                 AS id,
  components_name               AS name,
  components_author             AS author,
  COALESCE(components_code, '') AS code,   -- 합본 HTML
  NULL                          AS css,
  NULL                          AS preview,
  components_library            AS library,
  components_source_url         AS source_url,
  COALESCE(components_category,'') AS category          -- ✅ 추가!
FROM public.components_tbl_test
WHERE LOWER(components_category) = LOWER($1)
ORDER BY components_id DESC
OFFSET $2
LIMIT $3;
"""

SQL_LIST_OTHERS = """
SELECT
  components_id                 AS id,
  components_name               AS name,
  components_author             AS author,
  COALESCE(components_code, '') AS code,
  NULL                          AS css,
  NULL                          AS preview,
  components_library            AS library,
  components_source_url         AS source_url,
  COALESCE(components_category,'') AS category          -- ✅ 추가!
FROM public.components_tbl_test
WHERE
  COALESCE(TRIM(components_category),'') <> ''
  AND LOWER(components_category) NOT IN (
    SELECT LOWER(x) FROM UNNEST($1::text[]) AS x
  )
ORDER BY components_id DESC
OFFSET $2
LIMIT $3;
"""


# --- 공개 함수 ---

async def count_by_category_or_others(category_or_bucket: str) -> int:
    """
    프론트에서 'others'가 오면 Others 로직으로 카운트,
    아니면 해당 카테고리 정확 매칭으로 카운트.
    """
    assert _pool is not None, "Pool not initialized"
    is_others = category_or_bucket.lower() == "others"
    async with _pool.acquire() as conn:
        if is_others:
            total = await conn.fetchval(SQL_COUNT_OTHERS, PRIMARY_CATEGORIES)
        else:
            total = await conn.fetchval(SQL_COUNT_BY_CATEGORY, category_or_bucket)
        return int(total or 0)

async def list_by_category_or_others(category_or_bucket: str, offset: int, limit: int) -> List[Dict]:
    """
    프론트에서 'others'가 오면 Others 로직으로 리스트,
    아니면 해당 카테고리 정확 매칭으로 리스트.
    """
    assert _pool is not None, "Pool not initialized"
    is_others = category_or_bucket.lower() == "others"
    async with _pool.acquire() as conn:
        if is_others:
            rows = await conn.fetch(SQL_LIST_OTHERS, PRIMARY_CATEGORIES, offset, limit)
        else:
            rows = await conn.fetch(SQL_LIST_BY_CATEGORY, category_or_bucket, offset, limit)
        return [dict(r) for r in rows]

# --- (하위 호환) 기존 함수 명 유지가 필요하면 아래처럼 래핑 가능 ---
async def count_by_category(category: str) -> int:
    return await count_by_category_or_others(category)

async def list_by_category(category: str, offset: int, limit: int) -> List[Dict]:
    return await list_by_category_or_others(category, offset, limit)
