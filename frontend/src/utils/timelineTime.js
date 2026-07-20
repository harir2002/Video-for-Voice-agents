/**
 * Timeline time helpers for demo JSON.
 *
 * Demo files encode times as mm.ss (not decimal seconds):
 *   0.09 → 0 min 9 sec  → 9s
 *   1.02 → 1 min 2 sec  → 62s
 *   1.13 → 1 min 13 sec → 73s
 *   2.46 → 2 min 46 sec → 166s
 *
 * Convert once at ingest so audio, transcript, chips, and orb all share real seconds.
 */

const TIMED_FIELDS = ['start', 'end', 'uiStart', 'uiTriggerAt', 'time'];

/**
 * Parse a single timeline value into real seconds.
 * Supports mm.ss numbers/strings and colon forms (M:SS / H:MM:SS).
 *
 * @param {number|string|null|undefined} value
 * @returns {number} seconds
 */
export function parseTimelineTime(value) {
  if (value == null || value === '') return 0;

  if (typeof value === 'string' && value.includes(':')) {
    const parts = value.trim().split(':').map((part) => Number(part));
    if (parts.some((n) => Number.isNaN(n))) return 0;
    if (parts.length === 3) return parts[0] * 3600 + parts[1] * 60 + parts[2];
    if (parts.length === 2) return parts[0] * 60 + parts[1];
  }

  const raw = String(value).trim();
  const match = /^(-?\d+)(?:\.(\d+))?$/.exec(raw);
  if (!match) {
    const fallback = Number(value);
    return Number.isFinite(fallback) ? fallback : 0;
  }

  const minutes = parseInt(match[1], 10);
  let secondDigits = match[2] || '0';

  // mm.ss uses two digit-seconds. "1.1" → "1.10" → 70s; "0.09" → 9s.
  if (secondDigits.length === 1) {
    secondDigits = `${secondDigits}0`;
  } else if (secondDigits.length > 2) {
    secondDigits = secondDigits.slice(0, 2);
  }

  const seconds = parseInt(secondDigits, 10);
  return minutes * 60 + seconds;
}

/**
 * Convert timed fields on one object to real seconds.
 * Also normalizes nested timestamps[].time when present.
 */
export function normalizeTimedItem(item) {
  if (!item || typeof item !== 'object' || Array.isArray(item)) return item;

  const next = { ...item };
  for (const key of TIMED_FIELDS) {
    if (next[key] !== undefined && next[key] !== null) {
      next[key] = parseTimelineTime(next[key]);
    }
  }

  if (Array.isArray(next.timestamps)) {
    next.timestamps = next.timestamps.map((entry) => {
      if (!entry || typeof entry !== 'object') return entry;
      if (entry.time === undefined || entry.time === null) return entry;
      return { ...entry, time: parseTimelineTime(entry.time) };
    });
  }

  return next;
}

/**
 * Normalize transcript + annotation arrays from demo JSON.
 */
export function normalizeTimelinePayload({ transcript = [], annotations = [] } = {}) {
  return {
    transcript: (transcript || []).map(normalizeTimedItem),
    annotations: (annotations || []).map(normalizeTimedItem),
  };
}
