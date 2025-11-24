import React, { useRef } from "react";
import { useNavigate } from "react-router-dom";

export default function ComponentsSection() {
  const navigate = useNavigate();
  const trackRef = useRef(null);

  const categories = ["Buttons","Inputs","Cards","Badges","Alerts","Alpinejs", "Loings", "Calendar", "Others"];

  return (
    <section id="components">
      <div className="container">
        <h2 className="title">컴포넌트 쇼케이스</h2>
        <p className="subtitle">필요한 것만 복사해서 쓰세요.</p>
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
              <div className="card ring" style={{ height: "100%" }}>
                <h3>{cat}</h3>
                <button
                  className="btn secondary"
                  onClick={() => navigate(`/preview/${cat.toLowerCase()}`)}
                >
                  전체 보기
                </button>
              </div>
            </div>
          ))}
        </div>

      </div>
    </section>
  );
}
