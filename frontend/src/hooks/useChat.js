import { useState, useCallback, useRef } from "react";
import { streamChat } from "../api/client.js";

let sessionCounter = 0;
function newSessionId() {
  sessionCounter += 1;
  return `sess_${Date.now()}_${sessionCounter}`;
}

export function useChat(token) {
  const [sessions, setSessions] = useState(() => {
    const id = newSessionId();
    return { [id]: { id, title: "New conversation", messages: [] } };
  });
  const [activeSessionId, setActiveSessionId] = useState(() => Object.keys(sessions)[0]);
  const [streaming, setStreaming] = useState(false);
  const [status, setStatus] = useState("");
  const streamingMsgIndex = useRef(null);

  const activeSession = sessions[activeSessionId];

  const newSession = useCallback(() => {
    const id = newSessionId();
    setSessions((prev) => ({ ...prev, [id]: { id, title: "New conversation", messages: [] } }));
    setActiveSessionId(id);
  }, []);

  const switchSession = useCallback((id) => {
    setActiveSessionId(id);
  }, []);

  const sendMessage = useCallback(
    (query) => {
      if (!query.trim() || streaming) return;
      const sessionId = activeSessionId;

      setSessions((prev) => {
        const session = prev[sessionId];
        const isFirstMessage = session.messages.length === 0;
        const newMessages = [
          ...session.messages,
          { role: "user", content: query },
          { role: "assistant", content: "", citations: [], pending: true },
        ];
        streamingMsgIndex.current = newMessages.length - 1;
        return {
          ...prev,
          [sessionId]: {
            ...session,
            title: isFirstMessage ? query.slice(0, 40) : session.title,
            messages: newMessages,
          },
        };
      });

      setStreaming(true);
      setStatus("Connecting...");

      const appendToAssistant = (updater) => {
        setSessions((prev) => {
          const session = prev[sessionId];
          const messages = [...session.messages];
          const idx = streamingMsgIndex.current;
          messages[idx] = updater(messages[idx]);
          return { ...prev, [sessionId]: { ...session, messages } };
        });
      };

      streamChat({
        token,
        query,
        sessionId,
        onEvent: (eventName, data) => {
          if (eventName === "status") {
            setStatus(data.msg);
          } else if (eventName === "token") {
            appendToAssistant((msg) => ({
              ...msg,
              content: msg.content + data.text,
              pending: false,
            }));
          } else if (eventName === "done") {
            appendToAssistant((msg) => ({
              ...msg,
              citations: data.citations || [],
              intent: data.intent,
              toolResults: data.tool_results || [],
              pending: false,
            }));
            setStatus("");
            setStreaming(false);
          } else if (eventName === "error") {
            appendToAssistant((msg) => ({
              ...msg,
              content: msg.content || `Error: ${data.error || "something went wrong"}`,
              pending: false,
            }));
            setStatus("");
            setStreaming(false);
          }
        },
        onDone: () => {
          setStreaming(false);
          setStatus("");
        },
        onError: (err) => {
          appendToAssistant((msg) => ({
            ...msg,
            content: msg.content || `Connection error: ${err.message}`,
            pending: false,
          }));
          setStreaming(false);
          setStatus("");
        },
      });
    },
    [activeSessionId, streaming, token]
  );

  return {
    sessions: Object.values(sessions).reverse(),
    activeSession,
    activeSessionId,
    streaming,
    status,
    sendMessage,
    newSession,
    switchSession,
  };
}
