import React from "react";

export default function Features() {
  return (
    <section id="features">
      <div className="container row cols-3">
        <div className="card ring hover-rise">
          <h3>네온 + 글래스</h3>
          <p className="muted">
            네온 글로우, 글래스 모피즘을 기본 제공. 배경 오브와 블러를 조합해 감성 무드 완성.
          </p>
        </div>
        <div className="card ring hover-rise">
          <h3>다크/라이트 테마</h3>
          <p className="muted">
            HTML <span className="kbd">data-theme</span> 속성 한 줄로 전환. 사용자 취향에 맞춰 즉시 반응.
          </p>
        </div>
        <div className="card ring hover-rise">
          <h3>유틸리티 + 컴포넌트</h3>
          <p className="muted">
            버튼/배지/카드/그리드/탭/인풋/스위치 등 바로 쓰는 기본기 세트.
          </p>
        </div>
      </div>
    </section>
  );
}
