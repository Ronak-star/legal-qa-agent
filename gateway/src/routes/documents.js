import { Router } from "express";
import fetch from "node-fetch";

const router = Router();
const AGENT_URL = process.env.AGENT_URL || "http://localhost:8000";

/**
 * Accepts plain text (extracted client-side or pasted) and forwards it to
 * the agent's ingestion pipeline. A production version would accept
 * multipart PDF uploads here and run PDF text extraction before forwarding.
 */
router.post("/upload", async (req, res) => {
  const { sourceName, text } = req.body || {};
  const userId = req.user?.sub || "anonymous";

  if (!sourceName || !text) {
    return res.status(400).json({ error: "sourceName and text are required" });
  }

  try {
    const agentRes = await fetch(`${AGENT_URL}/ingest`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ source_name: sourceName, text, user_id: userId }),
    });
    const data = await agentRes.json();
    res.json(data);
  } catch (err) {
    res.status(502).json({ error: "Agent service unavailable", detail: err.message });
  }
});

export default router;
