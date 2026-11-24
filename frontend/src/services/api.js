const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export class ChatError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

async function readErrorDetail(response) {
  try {
    const body = await response.json();
    if (body && typeof body.detail === "string") return body.detail;
  } catch {
    // body wasn't JSON -- fall through to the generic message
  }
  return `Request failed with status ${response.status}`;
}

export async function postChat({ sessionId, message, systemPrompt }) {
  const response = await fetch(`${BASE_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: sessionId,
      message,
      ...(systemPrompt ? { system_prompt: systemPrompt } : {}),
    }),
  });

  if (!response.ok) {
    throw new ChatError(await readErrorDetail(response), response.status);
  }

  const data = await response.json();
  if (!data || typeof data.reply !== "string" || !data.metadata) {
    throw new ChatError("Unexpected response from server", response.status);
  }
  return data;
}

export async function getHealth() {
  const response = await fetch(`${BASE_URL}/health`);
  if (!response.ok) throw new Error("backend unhealthy");
  return response.json();
}
