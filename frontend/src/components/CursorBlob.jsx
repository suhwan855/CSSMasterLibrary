import React, { useEffect, useRef } from "react";

export default function CursorBlob() {
  const blobRef = useRef(null);

  useEffect(() => {
    const blob = blobRef.current;
    let targetX = window.innerWidth / 2;
    let targetY = window.innerHeight / 2;

    const handleMouse = (e) => {
      targetX = e.clientX;
      targetY = e.clientY;
    };
    window.addEventListener("mousemove", handleMouse);

    let rafId;
    const animate = () => {
      if (!blob) return;
      const rect = blob.getBoundingClientRect();
      const x = rect.left + rect.width / 2;
      const y = rect.top + rect.height / 2;
      const dx = (targetX - x) * 0.06;
      const dy = (targetY - y) * 0.06;
      blob.style.transform = `translate(${x + dx - rect.width / 2}px, ${y + dy - rect.height / 2}px)`;
      rafId = requestAnimationFrame(animate);
    };
    animate();

    return () => {
      window.removeEventListener("mousemove", handleMouse);
      cancelAnimationFrame(rafId);
    };
  }, []);

  return <div className="blob" ref={blobRef}></div>;
}
