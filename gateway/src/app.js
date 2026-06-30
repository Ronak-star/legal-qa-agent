import "dotenv/config";
import express from "express";
import cors from "cors";
import morgan from "morgan";

import { authMiddleware } from "./middleware/auth.js";
import { rateLimitMiddleware } from "./middleware/rateLimit.js";
import { auditMiddleware } from "./middleware/audit.js";

import authRoutes from "./routes/auth.js";
import chatRoutes from "./routes/chat.js";
import documentsRoutes from "./routes/documents.js";

const app = express();
const PORT = process.env.PORT || 4000;

app.use(cors({ origin: process.env.CORS_ORIGIN || "*" }));
app.use(express.json({ limit: "5mb" }));
app.use(morgan("dev"));
app.use(auditMiddleware);

app.get("/health", (req, res) => res.json({ status: "ok" }));

// Public routes
app.use("/auth", authRoutes);

// Protected routes — auth + rate limit applied
app.use("/api/v1/chat", authMiddleware, rateLimitMiddleware, chatRoutes);
app.use("/api/v1/documents", authMiddleware, rateLimitMiddleware, documentsRoutes);

app.listen(PORT, () => {
  console.log(`Gateway listening on http://localhost:${PORT}`);
});
