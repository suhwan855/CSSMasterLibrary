import React from "react";

export default function Footer() {
  return (
    <footer>
      <div className="container" style={{ display: "flex", justifyContent: "space-between", gap: "12px", flexWrap: "wrap" }}>
        <div>© 2025 NeonWave CSS. Made for 현빈.</div>
        <div className="muted">
          Press <span className="kbd">T</span> to toggle theme • <span className="kbd">/</span> to focus search (준비중)
        </div>
      </div>
    </footer>
  );
}
