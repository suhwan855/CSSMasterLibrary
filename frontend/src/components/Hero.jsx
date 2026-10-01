import React from "react";
import { useNavigate } from "react-router-dom";

export default function Hero() {
  const navigate = useNavigate();
  return (
    <section className="hero">
      <div className="bg-orb"></div>
      <div className="container hero-grid">
        <div>
          <div className="eyebrow" style={{marginBottom: 20}}><span /> CURATED INTERFACE ARCHIVE</div>
          <h1 className="title">
            좋은 인터페이스를<br />
            <span className="text-gradient">더 빠르게 발견하세요.</span>
          </h1>
          <p className="subtitle">
            여러 오픈소스에 흩어진 CSS와 Tailwind 컴포넌트를 한곳에서 검색하고, 실제 렌더링 결과와 코드를 바로 비교할 수 있습니다.
          </p>
          <div className="hero-actions">
            <button className="btn" onClick={() => navigate("/search")}>컴포넌트 검색 <span aria-hidden="true">→</span></button>
            <a className="btn secondary" href="#components">카테고리 둘러보기</a>
          </div>
        </div>
        <div className="card hero-preview">
          <div className="preview-toolbar"><span /><span /><span /><small>component.preview</small></div>
          <div className="preview-stage">
            <span className="preview-kicker">NEW COLLECTION</span>
            <strong>Build with clarity.</strong>
            <button>Explore components</button>
          </div>
          <h3 style={{ margin: 0, marginBottom: "6px" }}>검색부터 미리보기까지, 한 흐름으로</h3>
          <p className="muted" style={{ marginBottom: "14px" }}>
            키워드와 벡터 유사도를 결합하고, 서로 다른 코드 형식을 iframe 문서로 정규화합니다.
          </p>
        </div>
      </div>
    </section>
  );
}
