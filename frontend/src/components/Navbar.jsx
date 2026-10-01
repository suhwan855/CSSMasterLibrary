import React from "react";
import { useNavigate } from "react-router-dom";

export default function Navbar({ toggleTheme }) {
  const navigate = useNavigate();

  return (
    <header className="nav">
      <div className="container nav-inner">
        <a className="logo" href="/" aria-label="CSS Master Library 홈">
          <span className="brand-mark">C</span>
          <span>CSS Master</span>
          <span className="brand-label">Library</span>
        </a>
        <nav className="menu">
          <a href="#features">소개</a>
          <a href="#components">카테고리</a>
          <button className="nav-link-button" onClick={() => navigate("/search")}>UI 검색</button>
          <button
            onClick={() => navigate("/chatbot")}
            style={{
              background: "none",
              border: "none",
              color: "inherit",
              cursor: "pointer",
            }}
          >
            AI 도우미
          </button>
          <div
            className="switch"
            onClick={toggleTheme}
            aria-label="테마 전환"
          >
            <i></i>
          </div>
        </nav>
      </div>
    </header>
  );
}
