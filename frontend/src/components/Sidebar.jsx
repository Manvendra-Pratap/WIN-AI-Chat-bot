export default function Sidebar({
  sessionId,
  messageCount,
  connection,
  systemPrompt,
  onSystemPromptChange,
  onNewChat,
}) {
  const connectionLabel =
    connection === "online" ? "Connected" : connection === "offline" ? "Offline" : "Checking...";

  return (
    <aside className="sidebar">
      <div className="brand">
        <span className="brand-mark" aria-hidden="true">W</span>
        <span className="brand-name">WIN-AI</span>
      </div>

      <button className="new-chat-button" onClick={onNewChat} type="button">
        + New chat
      </button>

      <div className="sidebar-section">
        <h2 className="sidebar-label">Session</h2>
        <p className="session-id" title={sessionId}>{sessionId}</p>
        <p className="sidebar-meta">
          {messageCount} message{messageCount === 1 ? "" : "s"}
        </p>
      </div>

      <div className="sidebar-section">
        <h2 className="sidebar-label">Connection</h2>
        <p className={`status status-${connection}`}>
          <span className="status-dot" aria-hidden="true" />
          {connectionLabel}
        </p>
      </div>

      <div className="sidebar-section sidebar-settings">
        <h2 className="sidebar-label">Settings</h2>
        <label className="system-prompt-label" htmlFor="system-prompt">
          System prompt (optional)
        </label>
        <textarea
          id="system-prompt"
          data-testid="system-prompt-input"
          className="system-prompt-input"
          placeholder="e.g. Answer concisely, in French."
          value={systemPrompt}
          onChange={(e) => onSystemPromptChange(e.target.value)}
          rows={3}
        />
      </div>
    </aside>
  );
}
