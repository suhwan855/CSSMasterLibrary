import React from "react";

export default function Hero() {
  return (
    <section className="hero">
      <div className="bg-orb"></div>
      <div className="container hero-grid">
        <div>
          <div className="chip ring" style={{marginBottom: 20}}>⚡ 한 파일로 끝 — 네온/글래스/모션</div>
          <h1 className="title">
            <span className="text-gradient">NeonWave CSS</span><br />
            바로 배포 가능한 
            <br />랜딩 템플릿
          </h1>
          <p className="subtitle">
            유틸리티 + 컴포넌트 + 다크/라이트 테마. 외부 빌드 없이 <span className="kbd">index.html</span> 하나로 쇼케이스 완성.
          </p>
        </div>
        <div className="card ring hover-rise">
          <div className="shimmer" style={{ height: "220px", borderRadius: "12px", marginBottom: "14px" }}></div>
          <h3 style={{ margin: 0, marginBottom: "6px" }}>바닐라 HTML 기반</h3>
          <p className="muted" style={{ marginBottom: "14px" }}>
            React, 빌드툴 없이 순수 HTML/CSS/JS. 필요 시 컴포넌트를 복붙해서 사용.
          </p>
          <pre>
            <code>
              &lt;link rel="stylesheet" href="neonwave.css" /&gt;{`\n`}
              &lt;button class="btn"&gt;Start now&lt;/button&gt;
            </code>
          </pre>
        </div>
      </div>
    </section>
  );
}
