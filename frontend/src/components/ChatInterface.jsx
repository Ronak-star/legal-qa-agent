import { useState, useRef, useEffect } from "react";

const SUGGESTIONS = [
  "Is a non-compete clause enforceable in California?",
  "Summarize the GDPR lawful bases for processing data",
  "What does CCPA require of businesses?",
  "Classify this clause: the parties agree to binding arbitration...",
];

function Avatar({ role }) {
  return (
    <div className={`msg-avatar ${role}`}>
      {role === "user" ? "U" : "AI"}
    </div>
  );
}

function CitationsList({ citations }) {
  if (!citations || citations.length === 0) return null;
  return (
    <div className="citations-block">
      <div className="citations-label">Sources</div>
      {citations.map((c) => (
        <div className="citation-item" key={c.n}>
          <span className="citation-num">[{c.n}]</span>
          <span>
            <strong>{c.source}</strong> ({c.page}) — {c.excerpt}
          </span>
        </div>
      ))}
    </div>
  );
}

export default function ChatInterface({ chat }) {
  const { activeSession, streaming, status, sendMessage } = chat;
  const [input, setInput] = useState("");
  const scrollRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [activeSession?.messages]);

  const handleSend = () => {
    if (!input.trim() || streaming) return;
    sendMessage(input.trim());
    setInput("");
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const messages = activeSession?.messages || [];

  return (
    <main className="chat-main">
      <div className="chat-topbar">
        <span>{activeSession?.title || "New conversation"}</span>
        {streaming && status && <span className="status-pill">{status}</span>}
      </div>

      <div className="chat-scroll" ref={scrollRef}>
        {messages.length === 0 && (
          <div className="empty-state">
            <h2>Ask a legal or policy question</h2>
            <p>
              This agent retrieves relevant statutes and policy references, runs clause
              analysis tools, and cites its sources.
            </p>
            <div className="suggestion-row">
              {SUGGESTIONS.map((s) => (
                <button key={s} className="suggestion-chip" onClick={() => sendMessage(s)}>
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m, i) => (
          <div className={`msg-row ${m.role}`} key={i}>
            <Avatar role={m.role} />
            <div>
              <div className="msg-bubble">
                {m.content || (m.pending ? "..." : "")}
              </div>
              {m.role === "assistant" && <CitationsList citations={m.citations} />}
            </div>
          </div>
        ))}
      </div>

      <div className="chat-input-area">
        <div className="chat-input-row">
          <textarea
            placeholder="Ask about a statute, clause, or policy question..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={streaming}
          />
          <button onClick={handleSend} disabled={streaming || !input.trim()}>
            Send
          </button>
        </div>
        <div className="chat-disclaimer">
          General information only — not a substitute for advice from a licensed attorney.
        </div>
      </div>
    </main>
  );
}
