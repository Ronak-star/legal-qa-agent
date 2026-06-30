const GATEWAY_URL = import.meta.env.VITE_GATEWAY_URL || "http://localhost:4000";

export async function login(username) {
  const res = await fetch(`${GATEWAY_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username }),
  });
  if (!res.ok) throw new Error("Login failed");
  return res.json();
}

/**
 * Opens an SSE connection to the gateway's chat stream endpoint.
 * Calls onEvent(eventName, data) for each event, onDone() when finished.
 */
export function streamChat({ token, query, sessionId, onEvent, onDone, onError }) {
  const params = new URLSearchParams({ query, sessionId });
  const url = `${GATEWAY_URL}/api/v1/chat/stream?${params.toString()}`;

  // EventSource doesn't support custom headers, so we pass the token via a
  // short-lived query param in this demo. In production, prefer a signed
  // short-lived ticket issued by a separate endpoint, or use fetch() with
  // ReadableStream instead of EventSource to keep the Authorization header.
  fetchSSE(url, token, onEvent, onDone, onError);
}

async function fetchSSE(url, token, onEvent, onDone, onError) {
  try {
    const res = await fetch(url, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok || !res.body) {
      onError?.(new Error(`Stream failed: ${res.status}`));
      return;
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      const events = buffer.split("\n\n");
      buffer = events.pop(); // last (possibly incomplete) chunk stays in buffer

      for (const raw of events) {
        if (!raw.trim()) continue;
        const lines = raw.split("\n");
        let eventName = "message";
        let data = "";
        for (const line of lines) {
          if (line.startsWith("event:")) eventName = line.slice(6).trim();
          if (line.startsWith("data:")) data += line.slice(5).trim();
        }
        try {
          onEvent(eventName, JSON.parse(data));
        } catch {
          onEvent(eventName, data);
        }
      }
    }
    onDone?.();
  } catch (err) {
    onError?.(err);
  }
}

export async function uploadDocument({ token, sourceName, text }) {
  const res = await fetch(`${GATEWAY_URL}/api/v1/documents/upload`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ sourceName, text }),
  });
  if (!res.ok) throw new Error("Upload failed");
  return res.json();
}
