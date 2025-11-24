import React from "react";
import { useNavigate } from "react-router-dom";

export default function Navbar({ theme, toggleTheme }) {
  const navigate = useNavigate();

  const scrollToId = (id) =>
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });

  return (
    <header className="nav">
      <div className="container nav-inner">
        <a className="logo" href="/">
          <span className="dot"></span> NeonWave <span className="badge">CSS</span>
        </a>
        <nav className="menu">
          <a href="#features">특징</a>
          <a href="#components">컴포넌트</a>
          <a className="btn" onClick={() => scrollToId("cta")}>
            바로 쓰기
          </a>
          <button
            onClick={() => navigate("/chatbot")}
            style={{
              background: "none",
              border: "none",
              color: "inherit",
              cursor: "pointer",
            }}
          >
            챗봇
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
