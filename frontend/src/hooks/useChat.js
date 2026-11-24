import { useCallback, useEffect, useState } from "react";
import { ChatError, getHealth, postChat } from "../services/api";
import { generateSessionId } from "../utils/session";

let idCounter = 0;
function nextId() {
  idCounter += 1;
  return idCounter;
}

export function useChat() {
  const [sessionId, setSessionId] = useState(generateSessionId);
  const [messages, setMessages] = useState([]);
  const [systemPrompt, setSystemPrompt] = useState("");
  const [sending, setSending] = useState(false);
  const [connection, setConnection] = useState("checking");

  useEffect(() => {
    let cancelled = false;
    const check = () => {
      getHealth()
        .then(() => !cancelled && setConnection("online"))
        .catch(() => !cancelled && setConnection("offline"));
    };
    check();
    const interval = setInterval(check, 15000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  const newChat = useCallback(() => {
    setSessionId(generateSessionId());
    setMessages([]);
  }, []);

  const sendMessage = useCallback(
    async (text) => {
      const trimmed = text.trim();
      if (!trimmed || sending) return;

      setMessages((prev) => [...prev, { id: nextId(), role: "user", content: trimmed }]);
      setSending(true);

      try {
        const data = await postChat({
          sessionId,
          message: trimmed,
          systemPrompt: systemPrompt.trim() || undefined,
        });
        setConnection("online");
        setMessages((prev) => [
          ...prev,
          { id: nextId(), role: "assistant", content: data.reply, metadata: data.metadata },
        ]);
      } catch (err) {
        const message =
          err instanceof ChatError
            ? err.message
            : "Can't reach the server. Check your connection and try again.";
        if (!(err instanceof ChatError)) setConnection("offline");
        setMessages((prev) => [...prev, { id: nextId(), role: "error", content: message }]);
      } finally {
        setSending(false);
      }
    },
    [sessionId, systemPrompt, sending]
  );

  return {
    sessionId,
    messages,
    sending,
    connection,
    systemPrompt,
    setSystemPrompt,
    sendMessage,
    newChat,
  };
}
