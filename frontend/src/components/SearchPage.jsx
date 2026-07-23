import React, { useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import IframePreview from "./IframePreview";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";
const CATEGORIES = ["", "Buttons", "Inputs", "Cards", "Badges", "Alerts", "Calendar"];

export default function SearchPage() {
  const navigate = useNavigate();
  const [params, setParams] = useSearchParams();
  const [query, setQuery] = useState(params.get("q") || "");
  const [category, setCategory] = useState(params.get("category") || "");
  const [items, setItems] = useState([]);
  const [mode, setMode] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const search = async (event) => {
    event?.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setError("");
    const next = { q: query.trim() };
    if (category) next.category = category;
    setParams(next);
    try {
      const url = new URL(`${API_BASE}/components/search`);
      Object.entries(next).forEach(([key, value]) => url.searchParams.set(key, value));
      const response = await fetch(url);
      if (!response.ok) throw new Error(`검색 요청 실패 (${response.status})`);
      const data = await response.json();
      setItems(Array.isArray(data.items) ? data.items : []);
      setMode(data.mode || "hybrid");
    } catch (reason) {
      setError(reason.message || "검색 중 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="container search-page">
      <button className="btn ghost" onClick={() => navigate("/")}>← 홈으로</button>
      <div className="search-hero">
        <span className="chip">KEYWORD + VECTOR SEARCH</span>
        <h1 className="title">원하는 UI를 자연어로 찾아보세요</h1>
        <p className="subtitle">이름과 설명의 키워드 점수에 코드 임베딩 유사도를 결합해 결과를 정렬합니다.</p>
        <form className="search-form" onSubmit={search}>
          <input className="input" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="예: 네온 효과가 있는 둥근 CTA 버튼" />
          <select className="input search-select" value={category} onChange={(e) => setCategory(e.target.value)}>
            {CATEGORIES.map((value) => <option key={value} value={value}>{value || "모든 카테고리"}</option>)}
          </select>
          <button className="btn" disabled={loading}>{loading ? "검색 중..." : "검색"}</button>
        </form>
      </div>

      <div className="search-summary">
        <strong>{items.length}개 결과</strong>
        {mode && <span className="badge">{mode === "hybrid" ? "Hybrid ranking" : "Demo ranking"}</span>}
      </div>
      {error && <div className="card search-error">{error}</div>}
      {!loading && !error && params.get("q") && items.length === 0 && <div className="card">조건에 맞는 컴포넌트가 없습니다.</div>}

      <section className="search-results">
        {items.map((item) => (
          <article className="card search-result" key={item.id}>
            <div className="search-result-head">
              <div><span className="badge">{item.category}</span><h2>{item.name}</h2></div>
              {typeof item.score === "number" && <span className="search-score">{Math.round(item.score * 100)}%</span>}
            </div>
            <p className="muted">{item.description || "수집된 오픈소스 UI 컴포넌트"}</p>
            <IframePreview code={item.code} category={item.category} height={300} />
            <details><summary>코드 보기</summary><pre><code>{item.code}</code></pre></details>
          </article>
        ))}
      </section>
    </main>
  );
}
