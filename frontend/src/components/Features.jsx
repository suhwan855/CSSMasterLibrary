import React from "react";

export default function Features() {
  return (
    <section id="features">
      <div className="container row cols-3">
        <div className="card feature-card">
          <span className="feature-index">01</span>
          <h3>한곳에서 탐색</h3>
          <p className="muted">
            여러 저장소의 UI 컴포넌트를 일관된 카테고리와 화면에서 살펴보세요.
          </p>
        </div>
        <div className="card feature-card">
          <span className="feature-index">02</span>
          <h3>결과를 바로 확인</h3>
          <p className="muted">
            격리된 미리보기로 코드를 적용하기 전에 실제 렌더링 결과를 확인하세요.
          </p>
        </div>
        <div className="card feature-card">
          <span className="feature-index">03</span>
          <h3>필요한 코드만 복사</h3>
          <p className="muted">
            마음에 드는 패턴을 찾았다면 원본 코드를 열고 곧바로 프로젝트에 활용하세요.
          </p>
        </div>
      </div>
    </section>
  );
}
