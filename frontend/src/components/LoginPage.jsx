import { useState } from "react";

export default function LoginPage({ onLogin }) {
  const [username, setUsername] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!username.trim()) return;
    setLoading(true);
    setError("");
    try {
      await onLogin(username.trim());
    } catch (err) {
      setError(err.message || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-screen">
      <form className="login-card" onSubmit={handleSubmit}>
        <h1>Legal / Policy Q&amp;A Agent</h1>
        <p>Sign in to start a research session.</p>
        <input
          type="text"
          placeholder="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          autoFocus
        />
        <input type="password" placeholder="Password (any value works in this demo)" />
        <button type="submit" disabled={loading}>
          {loading ? "Signing in..." : "Sign in"}
        </button>
        {error && <p style={{ color: "#c0392b", fontSize: 12, marginTop: 8 }}>{error}</p>}
        <p className="login-hint">
          Demo auth accepts any username/password and issues a JWT for the session.
        </p>
      </form>
    </div>
  );
}
