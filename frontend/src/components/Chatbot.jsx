import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import hljs from "highlight.js";
import "highlight.js/styles/atom-one-dark.css";

export default function Chatbot() {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState([]);
  const [previewHtml, setPreviewHtml] = useState("");

  const sendQuery = async () => {
    if (!query.trim()) return alert("질문을 입력하세요!");

    const userMsg = { role: "user", content: query };
    setMessages((prev) => [...prev, userMsg]);
    const aiMsg = { role: "ai", content: "💬 응답 생성 중..." };
    setMessages((prev) => [...prev, aiMsg]);

    const res = await fetch("http://127.0.0.1:8000/chat/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, session_id: "designer-session" }),
    });

    const reader = res.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let fullText = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      fullText += decoder.decode(value, { stream: true });
    }

    const codeMatch = fullText.match(/```(?:html|css)?([\s\S]*?)```/i);
    const explanation = codeMatch
      ? fullText.slice(0, codeMatch.index).trim()
      : "좋아요! 아래는 요청하신 디자인 코드입니다. 😊";
    const codeText = codeMatch ? codeMatch[1].trim() : fullText.trim();

    const htmlMatch = codeText.match(/<html[\s\S]*?<\/html>/im);
    if (htmlMatch) {
      const htmlCode = htmlMatch[0].replace(/<title>.*?<\/title>/i, "");
      setPreviewHtml(htmlCode);
    }

    setMessages((prev) =>
      prev.map((msg, i) =>
        i === prev.length - 1 ? { ...msg, content: { explanation, codeText } } : msg
      )
    );

    setQuery("");
  };

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "row",
        height: "100vh",
        background: "radial-gradient(circle at 20% 20%, #1a1c2c, #0c0c12 80%)",
        color: "#fff",
        fontFamily: "'Pretendard', 'Noto Sans KR', sans-serif",
        paddingTop: "80px", // ✅ Navbar 높이만큼 띄움
        boxSizing: "border-box",
      }}
    >
      {/* 🪄 왼쪽 미리보기 영역 */}
      <div
        style={{
          flex: 1,
          background: "#fff",
          borderRadius: "16px",
          margin: "20px",
          boxShadow: "0 0 30px rgba(97, 218, 251, 0.25)",
          overflow: "hidden",
        }}
      >
        <iframe
          title="preview"
          srcDoc={previewHtml}
          style={{
            width: "100%",
            height: "100%",
            border: "none",
            borderRadius: "16px",
          }}
        />
      </div>

      {/* 💬 오른쪽 채팅창 */}
      <div
        style={{
          flex: 0.55,
          margin: "20px 20px 20px 0",
          background: "rgba(255,255,255,0.08)",
          backdropFilter: "blur(14px)",
          borderRadius: "16px",
          boxShadow: "0 0 20px rgba(97, 218, 251, 0.15)",
          display: "flex",
          flexDirection: "column",
          border: "1px solid rgba(97, 218, 251, 0.1)",
          position: "relative",

          /* ✅ 추가 부분 */
          width: "100%", // flex 대신 고정 너비로 설정하거나 부모 크기에 맞춤
          maxWidth: "600px", // 최대 너비 제한
          overflow: "hidden", // 넘치는 내용 숨김
          wordWrap: "break-word", // 긴 단어 줄바꿈
          overflowWrap: "break-word", // 최신 브라우저 호환
        }}
      >
        {/* 상단 헤더 */}
        <div
          style={{
            padding: "20px 15px 10px",
            textAlign: "center",
            borderBottom: "1px solid rgba(255,255,255,0.1)",
            position: "relative",
          }}
        >
          {/* ✅ Navbar 아래 자연스럽게 배치된 돌아가기 버튼 */}
          <button
            onClick={() => navigate("/")}
            style={{
              position: "absolute",
              left: "20px",
              top: "15px",
              background: "linear-gradient(135deg, #61dafb, #00b3ff)",
              border: "none",
              padding: "8px 16px",
              borderRadius: "8px",
              color: "#000",
              fontWeight: "bold",
              cursor: "pointer",
              boxShadow: "0 0 10px rgba(97, 218, 251, 0.3)",
              fontSize: "14px",
            }}
          >
            ← 돌아가기
          </button>
          <h2
            style={{
              color: "#61dafb",
              textShadow: "0 0 10px #61dafb, 0 0 25px #007bff",
              margin: 0,
            }}
          >
            🎨 AI CSS Generator
          </h2>
        </div>

        {/* 대화창 */}
        <div
          style={{
            flex: 1,
            overflowY: "auto",
            padding: "15px 20px",
            fontFamily: '"Fira Code", monospace',
          }}
        >
          {messages.map((msg, idx) => (
            <div key={idx} style={{ marginBottom: "15px" }}>
              {msg.role === "user" ? (
                <p style={{ color: "#61dafb" }}>👤 {msg.content}</p>
              ) : typeof msg.content === "string" ? (
                <p style={{ color: "#bde0fe" }}>{msg.content}</p>
              ) : (
                <>
                  <p style={{ color: "#bde0fe" }}>{msg.content.explanation}</p>
                  <pre
                    style={{
                      background: "rgba(255,255,255,0.08)",
                      padding: "12px",
                      borderRadius: "8px",
                      overflowX: "auto",
                    }}
                  >
                    <code
                      className="language-html"
                      dangerouslySetInnerHTML={{
                        __html: hljs.highlightAuto(
                          msg.content.codeText || ""
                        ).value,
                      }}
                    />
                  </pre>
                </>
              )}
            </div>
          ))}
        </div>

        {/* 입력창 */}
        <div
          style={{
            display: "flex",
            gap: "10px",
            padding: "15px 20px 20px",
            borderTop: "1px solid rgba(255, 255, 255, 0.1)",
          }}
        >
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="예: 네온 느낌의 예술적인 버튼 만들어줘"
            style={{
              flex: 1,
              padding: "12px 16px",
              borderRadius: "10px",
              border: "none",
              fontSize: "15px",
              background: "rgba(255,255,255,0.1)",
              color: "#fff",
              outline: "none",
            }}
          />
          <button
            onClick={sendQuery}
            style={{
              padding: "12px 20px",
              borderRadius: "10px",
              border: "none",
              background: "linear-gradient(135deg, #61dafb, #00b3ff)",
              color: "#000",
              fontWeight: "bold",
              cursor: "pointer",
            }}
          >
            전송
          </button>
        </div>
      </div>
    </div>
  );
}
