import React from "react";

export default function CTA({ copyCSS, toggleTheme }) {
  return (
    <section id="cta">
      <div className="container card ring" style={{ display: "grid", gap: "16px", gridTemplateColumns: "1.2fr 1fr", alignItems: "center" }}>
        <div>
          <h3 style={{ margin: "0 0 6px" }}>그냥 복사해서 쓰면 됩니다</h3>
          <p className="muted" style={{ margin: 0 }}>아래 버튼을 눌러 CSS만 클립보드에 복사합니다.</p>
        </div>
        <div style={{ textAlign: "right" }}>
          <button className="btn" onClick={copyCSS}>CSS 라이브러리 복사</button>
          <button className="btn secondary" onClick={toggleTheme}>테마 전환</button>
        </div>
      </div>
    </section>
  );
}
