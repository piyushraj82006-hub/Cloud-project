/**
 * Format seconds into human-readable time string.
 * Examples: 152 → "2m 32s", 45 → "45s", 0 → "0s"
 */
export function formatTime(seconds: number | null | undefined): string {
  if (seconds === null || seconds === undefined || seconds < 0) return 'N/A'
  const minutes = Math.floor(seconds / 60)
  const secs = seconds % 60
  if (minutes > 0) return `${minutes}m ${secs}s`
  return `${secs}s`
}

/**
 * Format timestamp to readable date.
 * "2026-08-22T08:00:00Z" → "Aug 22, 2026 · 08:00 UTC"
 */
export function formatTimestamp(ts: string | null | undefined): string {
  if (!ts) return 'N/A'
  try {
    const date = new Date(ts)
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    }) + ' · ' + date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      timeZone: 'UTC',
      timeZoneName: 'short',
    })
  } catch {
    return ts
  }
}

/**
 * Format score with color class.
 */
export function getScoreColor(score: number): string {
  if (score >= 70) return 'var(--status-pass)'
  if (score >= 50) return 'var(--status-warn)'
  return 'var(--status-fail)'
}

/**
 * Format delta with sign and color.
 */
export function formatDelta(delta: number, inverse = false): { text: string; improved: boolean } {
  const sign = delta > 0 ? '+' : ''
  const improved = inverse ? delta < 0 : delta > 0
  return {
    text: `${sign}${delta}`,
    improved,
  }
}
