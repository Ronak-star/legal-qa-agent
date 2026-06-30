import { Router } from "express";
import fetch from "node-fetch";

const router = Router();
const AGENT_URL = process.env.AGENT_URL || "http://localhost:8000";

/**
 * GET /api/v1/chat/stream?query=...&sessionId=...
 *
 * Proxies the query to the FastAPI agent's SSE endpoint and pipes the stream
 * straight through to the browser. Using GET (not POST) here because
 * EventSource only supports GET requests natively.
 */
router.get("/stream", async (req, res) => {
  const { query, sessionId } = req.query;
  const userId = req.user?.sub || "anonymous";

  if (!query || !sessionId) {
    return res.status(400).json({ error: "query and sessionId are required" });
  }

  res.setHeader("Content-Type", "text/event-stream");
  res.setHeader("Cache-Control", "no-cache");
  res.setHeader("Connection", "keep-alive");
  res.flushHeaders?.();

  try {
    const agentRes = await fetch(`${AGENT_URL}/agent/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, session_id: sessionId, user_id: userId }),
    });

    if (!agentRes.ok || !agentRes.body) {
      res.write(`event: error\ndata: ${JSON.stringify({ error: "Agent service unavailable" })}\n\n`);
      return res.end();
    }

    agentRes.body.on("data", (chunk) => res.write(chunk));
    agentRes.body.on("end", () => res.end());
    req.on("close", () => agentRes.body.destroy());
  } catch (err) {
    res.write(`event: error\ndata: ${JSON.stringify({ error: err.message })}\n\n`);
    res.end();
  }
});

export default router;
