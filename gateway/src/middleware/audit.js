/**
 * Lightweight audit logger. Swap console.log for Winston + a file/Datadog
 * sink in production — the call site stays the same.
 */

export function auditMiddleware(req, res, next) {
  const start = Date.now();
  res.on("finish", () => {
    const ms = Date.now() - start;
    const user = req.user?.sub || "anonymous";
    console.log(
      `[audit] ${new Date().toISOString()} user=${user} ${req.method} ${req.originalUrl} ` +
      `status=${res.statusCode} ${ms}ms`
    );
  });
  next();
}
