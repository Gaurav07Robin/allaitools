/**
 * In-Memory Rate Limiter & Cooldown Manager for API Endpoints
 * Protects Cloudflare, AI Horde, and Pollinations free APIs from abuse and quota burnout.
 */

const clientStore = new Map();

// Periodic cleanup of stale clients (older than 1 hour)
if (!globalThis.__rateLimitCleanupRegistered) {
  globalThis.__rateLimitCleanupRegistered = true;
  setInterval(() => {
    const now = Date.now();
    for (const [key, record] of clientStore.entries()) {
      if (now - record.windowStart > 60 * 60 * 1000) {
        clientStore.delete(key);
      }
    }
  }, 10 * 60 * 1000);
}

/**
 * Check and enforce rate limiting for a client.
 * @param {string} ip - Client IP or unique identifier
 * @param {string} action - 'generate' | 'upscale'
 * @param {object} config - Configuration options
 * @returns {object} Result with allowed flag, remaining count, and wait seconds
 */
export function checkRateLimit(ip, action, config = {}) {
  const {
    maxRequests = 5,
    windowMs = 15 * 60 * 1000, // 15-minute rolling window
    cooldownMs = 12 * 1000      // minimum cooldown between requests
  } = config;

  const key = `${action}:${ip || '127.0.0.1'}`;
  const now = Date.now();

  let record = clientStore.get(key);
  if (!record) {
    record = {
      count: 0,
      lastRequestTime: 0,
      windowStart: now
    };
    clientStore.set(key, record);
  }

  // Reset window if rolling window has passed
  if (now - record.windowStart > windowMs) {
    record.count = 0;
    record.windowStart = now;
  }

  // 1. Check cooldown between consecutive requests
  const timeSinceLast = now - record.lastRequestTime;
  if (record.lastRequestTime > 0 && timeSinceLast < cooldownMs) {
    const retryAfterSeconds = Math.ceil((cooldownMs - timeSinceLast) / 1000);
    return {
      allowed: false,
      reason: 'COOLDOWN',
      error: `Please wait ${retryAfterSeconds}s before making another request.`,
      retryAfterSeconds,
      remaining: Math.max(0, maxRequests - record.count),
      limit: maxRequests,
      resetInSeconds: Math.ceil((record.windowStart + windowMs - now) / 1000)
    };
  }

  // 2. Check window quota
  if (record.count >= maxRequests) {
    const resetInSeconds = Math.ceil((record.windowStart + windowMs - now) / 1000);
    return {
      allowed: false,
      reason: 'QUOTA_EXCEEDED',
      error: `Usage limit reached (${maxRequests} requests per ${Math.round(windowMs / 60000)} min). Please wait ${resetInSeconds}s.`,
      retryAfterSeconds: resetInSeconds,
      remaining: 0,
      limit: maxRequests,
      resetInSeconds
    };
  }

  // Record allowed request
  record.count += 1;
  record.lastRequestTime = now;

  return {
    allowed: true,
    remaining: Math.max(0, maxRequests - record.count),
    limit: maxRequests,
    cooldownSeconds: Math.round(cooldownMs / 1000),
    resetInSeconds: Math.ceil((record.windowStart + windowMs - now) / 1000)
  };
}

/**
 * Extract client IP from request headers or socket
 */
export function getClientIp(req) {
  const forwarded = req.headers?.['x-forwarded-for'];
  if (forwarded) {
    const first = typeof forwarded === 'string' ? forwarded.split(',')[0] : forwarded[0];
    if (first) return first.trim();
  }
  return req.headers?.['x-real-ip'] || req.socket?.remoteAddress || req.connection?.remoteAddress || '127.0.0.1';
}
