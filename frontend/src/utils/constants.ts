// CloudGuard DR — Constants

/** API base URL — reads from env or defaults to relative path */
export const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

/** localStorage keys */
export const STORAGE_KEYS = {
  TOKEN: 'cloudguard_token',
  THEME: 'cloudguard_theme',
} as const

/** Default threshold values */
export const DEFAULT_THRESHOLDS = {
  RTO_TARGET: 300,
  RPO_TARGET: 60,
  SCORE_THRESHOLD: 70,
} as const

/** Score color thresholds */
export const SCORE_THRESHOLDS = {
  PASS: 70,
  WARN: 50,
} as const

/** Pagination */
export const ITEMS_PER_PAGE = 10
