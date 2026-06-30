import { useState, useEffect } from "react";
import LoginPage from "./components/LoginPage.jsx";
import Sidebar from "./components/Sidebar.jsx";
import ChatInterface from "./components/ChatInterface.jsx";
import { useChat } from "./hooks/useChat.js";
import { login } from "./api/client.js";

const STORAGE_KEY = "legalqa_auth";

export default function App() {
  const [auth, setAuth] = useState(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  });

  useEffect(() => {
    if (auth) localStorage.setItem(STORAGE_KEY, JSON.stringify(auth));
    else localStorage.removeItem(STORAGE_KEY);
  }, [auth]);

  const handleLogin = async (username) => {
    const data = await login(username);
    setAuth(data);
  };

  const handleLogout = () => setAuth(null);

  if (!auth) {
    return <LoginPage onLogin={handleLogin} />;
  }

  return <AuthenticatedApp auth={auth} onLogout={handleLogout} />;
}

function AuthenticatedApp({ auth, onLogout }) {
  const chat = useChat(auth.token);

  return (
    <div className="app-shell">
      <Sidebar
        sessions={chat.sessions}
        activeSessionId={chat.activeSessionId}
        onNewSession={chat.newSession}
        onSwitchSession={chat.switchSession}
        user={auth.user}
        onLogout={onLogout}
      />
      <ChatInterface chat={chat} />
    </div>
  );
}
