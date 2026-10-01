import React from "react";

export default function CTA() {
  return (
    <section id="cta">
      <div className="container card cta-panel" style={{ display: "grid", gap: "16px", gridTemplateColumns: "1.2fr 1fr", alignItems: "center" }}>
        <div>
          <span className="eyebrow"><span /> START EXPLORING</span>
          <h3 style={{ margin: "10px 0 6px" }}>다음 인터페이스를 더 빠르게 완성하세요.</h3>
          <p className="muted" style={{ margin: 0 }}>필요한 컴포넌트를 찾고, 미리 보고, 코드까지 확인할 수 있습니다.</p>
        </div>
        <div style={{ textAlign: "right" }}>
          <a className="btn" href="/search">라이브러리 검색 <span aria-hidden="true">→</span></a>
        </div>
      </div>
    </section>
  );
}
