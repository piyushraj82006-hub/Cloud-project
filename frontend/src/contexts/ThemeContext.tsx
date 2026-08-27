import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react'

type Theme = 'dark' | 'light'

export interface AccentColor {
  name: string
  value: string
  hover: string
}

export const ACCENT_PRESETS: AccentColor[] = [
  { name: 'Blue', value: '#3e77e8', hover: '#5a8ef0' },
  { name: 'Teal', value: '#10b981', hover: '#34d399' },
  { name: 'Purple', value: '#8b5cf6', hover: '#a78bfa' },
  { name: 'Rose', value: '#f43f5e', hover: '#fb7185' },
  { name: 'Amber', value: '#f59e0b', hover: '#fbbf24' },
  { name: 'Cyan', value: '#06b6d4', hover: '#22d3ee' },
  { name: 'Orange', value: '#f97316', hover: '#fb923c' },
  { name: 'Lime', value: '#84cc16', hover: '#a3e635' },
]

interface ThemeContextValue {
  theme: Theme
  toggleTheme: () => void
  setTheme: (theme: Theme) => void
  accent: AccentColor
  setAccent: (color: AccentColor) => void
  customAccent: string | null
  setCustomAccent: (hex: string | null) => void
}

const ThemeContext = createContext<ThemeContextValue | null>(null)

const THEME_KEY = 'cloudguard_theme'
const ACCENT_KEY = 'cloudguard_accent'
const CUSTOM_ACCENT_KEY = 'cloudguard_custom_accent'

function getInitialTheme(): Theme {
  return 'dark'
}

function getInitialAccent(): AccentColor {
  try {
    const stored = localStorage.getItem(ACCENT_KEY)
    if (stored) {
      const parsed = JSON.parse(stored) as AccentColor
      if (parsed.value && parsed.hover) return parsed
    }
  } catch {}
  return ACCENT_PRESETS[0] // Blue default
}

function getInitialCustomAccent(): string | null {
  try {
    return localStorage.getItem(CUSTOM_ACCENT_KEY)
  } catch {
    return null
  }
}

function hexToRgb(hex: string): { r: number; g: number; b: number } | null {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex)
  return result ? {
    r: parseInt(result[1], 16),
    g: parseInt(result[2], 16),
    b: parseInt(result[3], 16),
  } : null
}

function applyAccent(color: AccentColor) {
  const root = document.documentElement
  root.style.setProperty('--accent-primary', color.value)
  root.style.setProperty('--accent-hover', color.hover)

  const rgb = hexToRgb(color.value)
  if (rgb) {
    root.style.setProperty('--accent-muted', `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, 0.1)`)
    root.style.setProperty('--accent-subtle', `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, 0.05)`)
  }

  // Update status-info to match accent
  root.style.setProperty('--status-info', color.value)
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<Theme>(getInitialTheme)
  const [accent, setAccentState] = useState<AccentColor>(getInitialAccent)
  const [customAccent, setCustomAccentState] = useState<string | null>(getInitialCustomAccent)

  // Sync theme
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    try {
      localStorage.setItem(THEME_KEY, theme)
    } catch {}
  }, [theme])

  // Sync accent color
  useEffect(() => {
    applyAccent(accent)
    try {
      localStorage.setItem(ACCENT_KEY, JSON.stringify(accent))
    } catch {}
  }, [accent])

  // Apply custom accent if set
  useEffect(() => {
    if (customAccent) {
      const rgb = hexToRgb(customAccent)
      if (rgb) {
        const hoverBright = `#${Math.min(255, rgb.r + 30).toString(16).padStart(2, '0')}${Math.min(255, rgb.g + 30).toString(16).padStart(2, '0')}${Math.min(255, rgb.b + 30).toString(16).padStart(2, '0')}`
        applyAccent({ name: 'Custom', value: customAccent, hover: hoverBright })
      }
    }
  }, [customAccent])

  // Listen for system preference changes
  useEffect(() => {
    const mq = window.matchMedia('(prefers-color-scheme: light)')
    const handler = (e: MediaQueryListEvent) => {
      const stored = localStorage.getItem(THEME_KEY)
      if (!stored) {
        setThemeState(e.matches ? 'light' : 'dark')
      }
    }
    mq.addEventListener('change', handler)
    return () => mq.removeEventListener('change', handler)
  }, [])

  const setTheme = useCallback((t: Theme) => setThemeState(t), [])
  const toggleTheme = useCallback(() => setThemeState(prev => (prev === 'dark' ? 'light' : 'dark')), [])

  const setAccent = useCallback((color: AccentColor) => {
    setAccentState(color)
    setCustomAccentState(null)
    try { localStorage.removeItem(CUSTOM_ACCENT_KEY) } catch {}
  }, [])

  const setCustomAccent = useCallback((hex: string | null) => {
    setCustomAccentState(hex)
    if (hex) {
      try { localStorage.setItem(CUSTOM_ACCENT_KEY, hex) } catch {}
    } else {
      try { localStorage.removeItem(CUSTOM_ACCENT_KEY) } catch {}
      // Revert to current preset
      applyAccent(accent)
    }
  }, [accent])

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme, setTheme, accent, setAccent, customAccent, setCustomAccent }}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme() {
  const ctx = useContext(ThemeContext)
  if (!ctx) throw new Error('useTheme must be used within a ThemeProvider')
  return ctx
}
