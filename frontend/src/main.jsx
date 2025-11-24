// src/main.jsx
import React from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom"; // SPA 라우팅 위해
import App from "./App.jsx";
import "./NeonWave.css";  // CSS 불러오기
createRoot(document.getElementById("root")).render(
  <BrowserRouter>
    <App />
  </BrowserRouter>
);
