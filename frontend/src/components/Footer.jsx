import React from "react";

export default function Footer() {
  return (
    <footer>
      <div className="container" style={{ display: "flex", justifyContent: "space-between", gap: "12px", flexWrap: "wrap" }}>
        <div>© 2026 CSS Master Library.</div>
        <div className="muted">
          Curated interface patterns for better products.
        </div>
      </div>
    </footer>
  );
}
