import type { ReactNode } from 'react'

interface SkeletonProps {
  width?: number | string
  height?: number | string
  variant?: 'text' | 'heading' | 'card' | 'score' | 'metric' | 'pill'
  borderRadius?: number | string
  style?: React.CSSProperties
  className?: string
  children?: ReactNode
}

const variantStyles: Record<string, React.CSSProperties> = {
  text: { height: 12, borderRadius: 4, marginBottom: 8 },
  heading: { height: 28, width: '60%', borderRadius: 6, marginBottom: 12 },
  card: {},
  score: { width: 120, height: 72, borderRadius: 8 },
  metric: { height: 64, borderRadius: 'var(--radius-lg)' },
  pill: { height: 56, borderRadius: 'var(--radius-lg)' },
}

export function Skeleton({
  width,
  height,
  variant = 'text',
  borderRadius,
  style,
  className = '',
  children,
}: SkeletonProps) {
  const base = variantStyles[variant] || {}

  if (variant === 'card') {
    return (
      <div
        className={`skeleton-card ${className}`}
        style={{ ...style, ...(width !== undefined ? { width } : {}), ...(height !== undefined ? { height } : {}) }}
      >
        {children}
      </div>
    )
  }

  return (
    <div
      className={`skeleton skeleton-${variant} ${className}`}
      style={{
        ...base,
        ...style,
        ...(width !== undefined ? { width } : {}),
        ...(height !== undefined ? { height } : {}),
        ...(borderRadius !== undefined ? { borderRadius } : {}),
      }}
    />
  )
}
