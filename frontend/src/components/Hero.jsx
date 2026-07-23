import React from "react";
import { useNavigate } from "react-router-dom";

export default function Hero() {
  const navigate = useNavigate();
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
            여러 오픈소스에 흩어진 CSS·Tailwind 컴포넌트를 자연어로 검색하고, 격리된 미리보기에서 바로 비교하세요.
          </p>
          <button className="btn" onClick={() => navigate("/search")}>컴포넌트 검색</button>
          <a className="btn secondary" href="#components">카테고리 둘러보기</a>
        </div>
        <div className="card ring hover-rise">
          <div className="shimmer" style={{ height: "220px", borderRadius: "12px", marginBottom: "14px" }}></div>
          <h3 style={{ margin: 0, marginBottom: "6px" }}>검색부터 미리보기까지</h3>
          <p className="muted" style={{ marginBottom: "14px" }}>
            키워드와 벡터 유사도를 결합하고, 서로 다른 코드 형식을 iframe 문서로 정규화합니다.
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
