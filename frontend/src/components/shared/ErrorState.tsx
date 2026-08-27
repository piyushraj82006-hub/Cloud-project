import { Warning, ArrowClockwise } from '@phosphor-icons/react'

interface ErrorStateProps {
  title?: string
  description?: string
  onRetry?: () => void
  retryLabel?: string
}

export function ErrorState({
  title = "Couldn't load this data",
  description = 'Check your connection and try again.',
  onRetry,
  retryLabel = 'Retry',
}: ErrorStateProps) {
  return (
    <div className="empty-state">
      <div className="empty-state-icon" style={{
        background: 'rgba(244, 63, 94, 0.08)',
        border: '1px solid rgba(244, 63, 94, 0.15)',
        color: 'var(--status-fail)',
      }}>
        <Warning size={28} weight="regular" />
      </div>
      <div className="empty-state-title">{title}</div>
      <div className="empty-state-desc">{description}</div>
      {onRetry && (
        <button
          onClick={onRetry}
          className="btn btn-secondary"
          style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '10px 20px' }}
        >
          <ArrowClockwise size={14} weight="regular" />
          {retryLabel}
        </button>
      )}
    </div>
  )
}
