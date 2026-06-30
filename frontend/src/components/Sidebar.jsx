export default function Sidebar({ sessions, activeSessionId, onNewSession, onSwitchSession, user, onLogout }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">Legal / Policy Q&amp;A</div>
      <button className="sidebar-new" onClick={onNewSession}>
        + New conversation
      </button>

      <div className="sidebar-section-label">Recent sessions</div>
      <div style={{ overflowY: "auto", flex: 1 }}>
        {sessions.map((s) => (
          <div
            key={s.id}
            className={`sidebar-session ${s.id === activeSessionId ? "active" : ""}`}
            onClick={() => onSwitchSession(s.id)}
            title={s.title}
          >
            {s.title || "New conversation"}
          </div>
        ))}
      </div>

      <div className="sidebar-footer">
        Signed in as <strong>{user?.name}</strong>
        <br />
        <button onClick={onLogout}>Sign out</button>
      </div>
    </aside>
  );
}
