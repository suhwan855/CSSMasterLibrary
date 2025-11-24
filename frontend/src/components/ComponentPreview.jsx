// src/pages/ComponentPreview.jsx
import React, { useEffect, useRef, useState, useMemo } from "react";
import { useParams, useNavigate } from "react-router-dom";
import IframePreview from "../components/IframePreview.jsx";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus as vsTheme } from "react-syntax-highlighter/dist/esm/styles/prism";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";
const PAGE_SIZE = 24;

/* ========== 유틸 ========== */
function decodeEntities(s = "") {
  return (s || "")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&amp;/g, "&")
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'");
}
const guessLanguage = (code = "") => {
  const src = (code || "").trim().toLowerCase();
  if (src.includes("<!doctype") || src.includes("<html") || src.includes("<head") || src.includes("<body") || src.includes("</")) return "html";
  if (src.includes("class ") || src.includes("const ") || src.includes("import ") || src.includes("export ")) return "jsx";
  if (src.includes("{") && src.includes("}")) return "jsx";
  return "html";
};
const keyOf = (item, idx) => String(item?.id ?? item?._id ?? item?.slug ?? `row-${idx}`);
const normalizeCategoryLabel = (s = "") => (s ? s.charAt(0).toUpperCase() + s.slice(1).toLowerCase() : s);

/* 빠른 정적 필터 */
const hasButtonSignatureFast = (html = "") =>
  /<(button)\b|role=["']button["']|class=["'][^"']*\b(btn|button)\b/i.test(html || "");
const includesButtonText = (html = "") => />[^<]*Button[^<]*</i.test(html || "");

export default function ComponentPreview() {
  const { category } = useParams();
  const navigate = useNavigate();

  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);

  const sentinelRef = useRef(null);
  const [openCodeIds, setOpenCodeIds] = useState(() => new Set());
  const [expandedItem, setExpandedItem] = useState(null);
  const isOthers = (category || "").toLowerCase() === "others";

  // ✅ Iframe 프리플라이트 실패로 숨길 아이템 집합
  const [hiddenIds, setHiddenIds] = useState(() => new Set());

  useEffect(() => {
    setItems([]); setTotal(0); setPage(1); setErr(null);
    setOpenCodeIds(new Set()); setExpandedItem(null);
    setHiddenIds(new Set());
  }, [category]);

  // 데이터 로드 (페이지네이션 유지)
  useEffect(() => {
    if (!category) return;
    let ignore = false;
    setLoading(true); setErr(null);

    const normalizedCategory = normalizeCategoryLabel(category);
    const url = new URL(`${API_BASE}/components`);
    url.searchParams.set("category", normalizedCategory);
    url.searchParams.set("page", String(page));
    url.searchParams.set("page_size", String(PAGE_SIZE));

    fetch(url.toString())
      .then(async (res) => {
        if (!res.ok) {
          const text = await res.text().catch(() => "");
          throw new Error(`HTTP ${res.status} — ${text || "Fetch failed"}`);
        }
        return res.json();
      })
      .then((data) => {
        if (ignore) return;
        const nextItems = Array.isArray(data.items) ? data.items : [];
        setTotal(Number(data.total || 0));
        setItems((prev) => {
          if (page === 1) return nextItems;
          const seen = new Set(prev.map((x) => x.id ?? x._id ?? x.slug));
          const merged = [...prev];
          nextItems.forEach((x) => {
            const k = x.id ?? x._id ?? x.slug;
            if (!seen.has(k)) merged.push(x);
          });
          return merged;
        });
      })
      .catch((e) => !ignore && setErr(e.message))
      .finally(() => !ignore && setLoading(false));

    return () => { ignore = true; };
  }, [category, page]);

  const hasMore = items.length < total;

  const subcatCounts = useMemo(() => {
    if (!isOthers) return [];
    const map = new Map();
    for (const it of items) {
      const raw = (it.category || "").trim();
      if (!raw) continue;
      const label = normalizeCategoryLabel(raw);
      map.set(label, (map.get(label) || 0) + 1);
    }
    return Array.from(map.entries()).sort((a, b) => a[0].localeCompare(b[0]));
  }, [isOthers, items]);

  // 무한 스크롤(페이지네이션 유지)
  useEffect(() => {
    if (!hasMore || loading) return;
    const node = sentinelRef.current;
    if (!node) return;

    const io = new IntersectionObserver(
      (entries) => {
        const entry = entries[0];
        if (entry.isIntersecting && !loading) setPage((p) => p + 1);
      },
      { root: null, rootMargin: "400px", threshold: 0 }
    );

    io.observe(node);
    return () => io.disconnect();
  }, [hasMore, loading]);

  useEffect(() => {
    const onKey = (e) => { if (e.key === "Escape") setExpandedItem(null); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const openFull = (item) => {
    const safe = decodeEntities(item.code || "");
    setExpandedItem({ ...item, _safeCode: safe });
  };
  const closeFull = () => setExpandedItem(null);

  return (
    <section className="container" style={{ padding: "40px 0" }}>
      <style>{`
        .cmp-grid {
          display: grid;
          grid-template-columns: repeat(2, minmax(0, 1fr));
          gap: 24px;
          justify-items: stretch;
          align-items: start;
        }
        @media (max-width: 900px) { .cmp-grid { grid-template-columns: 1fr; } }
        .cmp-card { padding: 16px; max-width: 100%; margin: 0 auto; }
        .cmp-preview {
          margin-top: 12px; border: 1px solid rgba(255,255,255,.1);
          border-radius: 12px; padding: 12px; overflow-x: auto; overflow-y: visible;
          display: block; background: #2b2f36;
        }
        .code-shell {
          margin-top: 12px; border: 1px solid rgba(255,255,255,.1);
          border-radius: 12px; overflow: hidden; background: #1e1e1e;
        }
        .code-header {
          display: flex; align-items: center; justify-content: space-between;
          padding: 8px 12px; background: #252526; border-bottom: 1px solid rgba(255,255,255,0.08);
          font-size: 12px; color: #cfd8dc;
        }
        .code-header-left { display: flex; gap: 8px; align-items: center; }
        .traffic { display: inline-flex; gap: 6px; align-items: center; }
        .dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
        .dot.red { background: #ff5f56; } .dot.yellow { background: #ffbd2e; } .dot.green { background: #27c93f; }
        .code-actions { display: flex; gap: 8px; align-items: center; }
        .code-btn {
          background: transparent; border: 1px solid rgba(255,255,255,.15); color: #e0e0e0;
          padding: 4px 8px; border-radius: 8px; font-size: 12px; cursor: pointer;
        }
        .code-btn:hover { background: rgba(255,255,255,.06); }
        .cmp-sentinel { height: 1px; width: 100%; }

        .full-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.6);
          display: flex; align-items: center; justify-content: center; z-index: 1000; }
        .full-sheet {
          width: min(1200px, 96vw); height: min(90vh, 1000px);
          background: #111318; border: 1px solid rgba(255,255,255,.1);
          border-radius: 16px; box-shadow: 0 20px 80px rgba(0,0,0,.35);
          display: flex; flex-direction: column; overflow: hidden;
        }
        .full-header {
          display: flex; align-items: center; justify-content: space-between; gap: 12px;
          padding: 12px 16px; background: #181b22; border-bottom: 1px solid rgba(255,255,255,.08);
        }
        .full-title { display:flex; align-items:center; gap:10px; font-weight:700; }
        .full-body { flex: 1; overflow: auto; padding: 16px; background: #141820; }
        .full-actions { display:flex; gap:8px; }
      `}</style>

      <button className="btn secondary" style={{ marginBottom: "24px" }} onClick={() => navigate(-1)}>
        뒤로가기
      </button>

      <h2 className="title" style={{ marginBottom: "12px" }}>
        {normalizeCategoryLabel(category)} 전체보기
      </h2>

      <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 16, flexWrap: "wrap" }}>
        <span className="chip">총 {total}개</span>
        <span className="chip">{items.length}개 로드됨</span>
        {isOthers && subcatCounts.length > 0 && (
          <>
            <span style={{ opacity: 0.7 }}>|</span>
            <span className="chip">포함 카테고리</span>
            {subcatCounts.map(([sc, count]) => (
              <span key={sc} className="badge">{sc} ({count})</span>
            ))}
          </>
        )}
      </div>

      {err && <div className="card" style={{ borderLeft: "4px solid var(--danger)" }}>에러: {err}</div>}
      {!loading && items.length === 0 && !err && (
        <div className="card">표시할 컴포넌트가 없습니다. (카테고리/필터를 확인하세요)</div>
      )}

      <div className="cmp-grid">
        {items.map((item, idx) => {
          const key = keyOf(item, idx);
          if (hiddenIds.has(key)) return null; // 프리플라이트 실패 → 카드 자체 미표시

          const safeCode = decodeEntities(item.code || "");
          // 1차 빠른 정적 컷: 버튼 흔적 + "Button" 텍스트
          if (!hasButtonSignatureFast(safeCode) || !includesButtonText(safeCode)) return null;

          const lang = guessLanguage(safeCode);
          const codeOpen = openCodeIds.has(key);

          return (
            <div key={key} className="card hover-rise cmp-card" style={{ width: "100%", maxWidth: "100%" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: 8 }}>
                <div style={{ fontWeight: 700, display: "flex", alignItems: "center", gap: 8 }}>
                  {item.name || "(무제)"}
                  {isOthers && item.category && (
                    <span className="badge ghost">#{normalizeCategoryLabel(item.category)}</span>
                  )}
                </div>
                <div style={{ display: "flex", gap: 8 }}>
                  {/* author 완전 제거 */}
                  <button className="btn ghost" onClick={() => openFull(item)} title="전체 확장 보기">
                    전체 확장
                  </button>
                  <button
                    className="btn ghost"
                    onClick={() =>
                      setOpenCodeIds((prev) => {
                        const next = new Set(prev);
                        next.has(key) ? next.delete(key) : next.add(key);
                        return next;
                      })
                    }
                    title="코드 보기/숨기기"
                  >
                    {codeOpen ? "코드 숨기기" : "코드 보기"}
                  </button>
                </div>
              </div>

              {/* 미리보기 (여기서 최종 프리플라이트 실패 시 카드 숨김) */}
              <div className="cmp-preview">
                <IframePreview
                  code={safeCode}
                  maxHeight={10000}
                  onDecide={(ok) => {
                    if (!ok) {
                      setHiddenIds((prev) => {
                        const next = new Set(prev);
                        next.add(key);
                        return next;
                      });
                    }
                  }}
                />
              </div>

              {codeOpen && (
                <div className="code-shell">
                  <div className="code-header">
                    <div className="code-header-left">
                      <span className="traffic">
                        <span className="dot red" />
                        <span className="dot yellow" />
                        <span className="dot green" />
                      </span>
                      <span>{item.filename || (lang === "html" ? "index.html" : "snippet.jsx")}</span>
                    </div>
                    <div className="code-actions">
                      <button
                        className="code-btn"
                        onClick={() => navigator.clipboard.writeText(safeCode || "")}
                        title="코드 복사"
                      >
                        복사
                      </button>
                    </div>
                  </div>
                  <SyntaxHighlighter
                    language={lang}
                    style={vsTheme}
                    customStyle={{ margin: 0, padding: "14px 16px", background: "#1e1e1e", fontSize: 13, lineHeight: 1.6 }}
                    wrapLongLines
                    showLineNumbers
                  >
                    {safeCode || ""}
                  </SyntaxHighlighter>
                </div>
              )}
            </div>
          );
        })}
      </div>

      <div style={{ marginTop: 16 }}>
        {loading && <div className="card">불러오는 중...</div>}
        {!loading && !hasMore && items.length > 0 && <div className="card">마지막까지 다 봤어요 👀</div>}
        {hasMore && <div ref={sentinelRef} className="cmp-sentinel" />}
      </div>

      {/* 풀뷰 모달 (author 제거) */}
      {expandedItem && (
        <div className="full-overlay" onClick={closeFull}>
          <div className="full-sheet" onClick={(e) => e.stopPropagation()}>
            <div className="full-header">
              <div className="full-title">
                <span style={{ fontWeight: 800 }}>{expandedItem.name || "(무제)"}</span>
                {isOthers && expandedItem.category && (
                  <span className="badge ghost">#{normalizeCategoryLabel(expandedItem.category)}</span>
                )}
              </div>
              <div className="full-actions">
                <button className="btn secondary" onClick={closeFull} title="닫기">
                  닫기
                </button>
              </div>
            </div>
            <div className="full-body">
              <div style={{ borderRadius: 12, overflow: "hidden", border: "1px solid rgba(255,255,255,.1)" }}>
                <IframePreview code={expandedItem._safeCode} maxHeight={20000} />
              </div>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
