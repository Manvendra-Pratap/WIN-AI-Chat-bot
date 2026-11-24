function formatLatency(ms) {
  return `${ms} ms`;
}

export default function MessageBubble({ message }) {
  if (message.role === "error") {
    return (
      <div className="message-row error-row">
        <div className="bubble error-bubble" role="alert">
          {message.content}
        </div>
      </div>
    );
  }

  if (message.role === "user") {
    return (
      <div className="message-row user-row">
        <div className="bubble user-bubble">{message.content}</div>
      </div>
    );
  }

  const meta = message.metadata;
  const isCache = meta?.resolution_source === "LLM_CACHE";

  return (
    <div className="message-row assistant-row">
      <div className="bubble assistant-bubble" data-testid="assistant-message">
        <p className="bubble-text">{message.content}</p>
        {meta && (
          <div className={`meta-row ${isCache ? "meta-cache" : "meta-live"}`}>
            <span className="meta-pill" data-testid="meta-source">
              {meta.resolution_source}
            </span>
            <span className="meta-item" data-testid="meta-model">
              {meta.model}
            </span>
            <span className="meta-item" data-testid="meta-latency">
              {formatLatency(meta.latency_ms)}
            </span>
            <span className="meta-item" data-testid="meta-input-tokens">
              Input: {meta.input_tokens} tokens
            </span>
            <span className="meta-item" data-testid="meta-output-tokens">
              Output: {meta.output_tokens} tokens
            </span>
            {meta.fallback_attempts > 0 && (
              <span className="meta-item meta-fallback">
                Failover: {meta.fallback_attempts} key{meta.fallback_attempts === 1 ? "" : "s"} retried
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
