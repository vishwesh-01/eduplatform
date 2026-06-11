/**
 * dateFormatters.js
 * Utility helpers for formatting dates and durations in the UI.
 */

/**
 * Format an ISO date string or Date object as a localised date string.
 * Example: "15 January 2025"
 * @param {string|Date} date
 * @returns {string}
 */
export const formatDate = (date) => {
  if (!date) return '';
  const d = typeof date === 'string' ? new Date(date) : date;
  return d.toLocaleDateString('en-GB', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  });
};

/**
 * Format a duration in decimal hours to a human-readable string.
 * Example: 12.5 → "12h 30m"
 * @param {number} hours - Decimal hours (e.g. 12.5)
 * @returns {string}
 */
export const formatDuration = (hours) => {
  if (hours == null) return '';
  const h = Math.floor(hours);
  const m = Math.round((hours - h) * 60);
  if (m === 0) return `${h}h`;
  if (h === 0) return `${m}m`;
  return `${h}h ${m}m`;
};
