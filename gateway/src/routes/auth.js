import { Router } from "express";
import { signToken } from "../middleware/auth.js";

const router = Router();

/**
 * Demo auth: accepts any username/password and issues a JWT.
 * Swap this for real credential verification (e.g. against Postgres + bcrypt)
 * in production — everything downstream only depends on the JWT shape
 * { sub, name }, so the rest of the app needs no changes.
 */
router.post("/login", (req, res) => {
  const { username } = req.body || {};
  if (!username) {
    return res.status(400).json({ error: "username is required" });
  }
  const userId = `user_${Buffer.from(username).toString("hex").slice(0, 12)}`;
  const token = signToken({ sub: userId, name: username });
  res.json({ token, user: { id: userId, name: username } });
});

export default router;
