import { useEffect, useRef } from "react";
import MessageBubble from "./MessageBubble";

const SUGGESTED_PROMPTS = [
  "Summarize this changelog in three bullet points.",
  "Explain how LLM response caching works.",
  "Draft a status update for a delayed migration.",
];

export default function ChatArea({ messages, sending, onSuggestedPrompt }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, sending]);

  if (messages.length === 0) {
    return (
      <div className="chat-area chat-area-empty">
        <div className="welcome">
          <h1>One chat, routed to whatever answers best.</h1>
          <p>WIN-AI serves cached replies instantly and fails over across models when a key is rate-limited — no setup, just ask.</p>
          <div className="suggested-prompts">
            {SUGGESTED_PROMPTS.map((prompt) => (
              <button
                key={prompt}
                type="button"
                className="suggested-prompt"
                onClick={() => onSuggestedPrompt(prompt)}
              >
                {prompt}
              </button>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="chat-area">
      <div className="message-list">
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
        {sending && (
          <div className="message-row assistant-row">
            <div className="bubble assistant-bubble loading-bubble" aria-live="polite" aria-label="WIN-AI is thinking">
              <span className="loading-dot" />
              <span className="loading-dot" />
              <span className="loading-dot" />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
