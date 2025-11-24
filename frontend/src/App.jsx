import React, { useState } from "react";
import { Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";
import Hero from "./components/Hero";
import Features from "./components/Features";
import ComponentsSection from "./components/ComponentsSection";
import ComponentPreview from "./components/ComponentPreview";
import CTA from "./components/CTA";
import Chatbot from "./components/Chatbot";
import Footer from "./components/Footer";
import CursorBlob from "./components/CursorBlob";

export default function App() {
  const [theme, setTheme] = useState("dark");

  const toggleTheme = () => {
    const newTheme = theme === "dark" ? "light" : "dark";
    setTheme(newTheme);
    document.documentElement.setAttribute("data-theme", newTheme);
    localStorage.setItem("theme", newTheme);
  };

  return (
    <>
      <CursorBlob />
      <Navbar theme={theme} toggleTheme={toggleTheme} />
      <Routes>
        <Route
          path="/"
          element={
            <>
              <Hero />
              <Features />
              <ComponentsSection />
              <CTA />
              <Footer />
            </>
          }
        />
        <Route path="/preview/:category" element={<ComponentPreview />} />
        <Route path="/chatbot" element={<Chatbot />} />
      </Routes>
    </>
  );
}
