/**
 * Shared formatting utilities for the Tata Motors Negotiation Copilot.
 */

/**
 * Format a numeric value to 2 decimal places.
 * Returns '—' for null, undefined, empty string, or non-numeric values.
 * Treats 0 as a valid number and formats as "0.00".
 */
export function fmt(v) {
  if (v === null || v === undefined || v === '' || v === '—') return '—';
  const n = Number(v);
  return isNaN(n) ? String(v) : n.toFixed(2);
}
