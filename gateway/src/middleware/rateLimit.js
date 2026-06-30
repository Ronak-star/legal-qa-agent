/**
 * In-memory token-bucket rate limiter, keyed by user id.
 *
 * PRODUCTION SWAP: replace the Map below with Redis. Each bucket becomes a
 * Redis hash with TTL instead of an in-process object, e.g.:
 *   const tokens = await redis.get(`ratelimit:${userId}`)
 *   await redis.set(`ratelimit:${userId}`, tokens - 1, { EX: 60 })
 * The middleware signature and behavior stay identical.
 */

const BUCKET_CAPACITY = 30; // requests
const REFILL_WINDOW_MS = 60 * 1000; // per minute

const buckets = new Map();

export function rateLimitMiddleware(req, res, next) {
  const userId = req.user?.sub || req.ip;
  const now = Date.now();

  let bucket = buckets.get(userId);
  if (!bucket) {
    bucket = { tokens: BUCKET_CAPACITY, lastRefill: now };
    buckets.set(userId, bucket);
  }

  const elapsed = now - bucket.lastRefill;
  if (elapsed > REFILL_WINDOW_MS) {
    bucket.tokens = BUCKET_CAPACITY;
    bucket.lastRefill = now;
  }

  if (bucket.tokens <= 0) {
    const retryAfter = Math.ceil((REFILL_WINDOW_MS - elapsed) / 1000);
    res.set("Retry-After", String(retryAfter));
    return res.status(429).json({ error: "Rate limit exceeded", retryAfter });
  }

  bucket.tokens -= 1;
  next();
}
