import React, { useRef } from "react";
import { useNavigate } from "react-router-dom";

export default function ComponentsSection() {
  const navigate = useNavigate();
  const trackRef = useRef(null);

  const categories = ["Buttons","Inputs","Cards","Badges","Alerts","Alpinejs", "Logins", "Calendar", "Others"];

  return (
    <section id="components">
      <div className="container">
        <div className="section-heading">
          <div>
            <span className="eyebrow"><span /> BROWSE BY CATEGORY</span>
            <h2 className="title">카테고리별로 둘러보기</h2>
          </div>
          <p className="subtitle">원하는 유형을 선택해<br />수집된 UI를 비교해 보세요.</p>
        </div>
        <hr className="divider" />

        {/* 가로 스크롤 트랙 */}
        <div
          ref={trackRef}
          className="horizontal-scroll no-scrollbar"
          style={{
            display: "flex",
            gap: "16px",
            overflowX: "auto",
            scrollSnapType: "x mandatory",
            paddingBottom: "8px",
          }}
        >
          {categories.map((cat) => (
            <div
              key={cat}
              style={{
                flex: "0 0 auto",
                width: "280px",              // 카드 너비
                scrollSnapAlign: "start",
              }}
            >
              <div className="card category-card" style={{ height: "100%" }}>
                <span className="category-number">{String(categories.indexOf(cat) + 1).padStart(2, "0")}</span>
                <h3>{cat}</h3>
                <button
                  className="btn secondary"
                  onClick={() => navigate(`/preview/${cat.toLowerCase()}`)}
                >
                  컬렉션 보기 <span aria-hidden="true">→</span>
                </button>
              </div>
            </div>
          ))}
        </div>

      </div>
    </section>
  );
}
