import { FloppyDisk } from '@phosphor-icons/react'

interface ThresholdFormProps {
  rtoTarget: string
  rpoTarget: string
  scoreThreshold: string
  onRtoChange: (v: string) => void
  onRpoChange: (v: string) => void
  onScoreChange: (v: string) => void
  onSave: () => void
}

export function ThresholdForm({ rtoTarget, rpoTarget, scoreThreshold, onRtoChange, onRpoChange, onScoreChange, onSave }: ThresholdFormProps) {
  return (
    <div className="card animate-in animate-in-delay-1" style={{ marginBottom: 'var(--space-6)' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 'var(--space-5)' }}>
        <span style={{ color: 'var(--accent-primary)' }}><FloppyDisk size={14} weight="regular" /></span>
        <h3 style={{ fontSize: 10, fontWeight: 500, color: 'var(--text-muted)', letterSpacing: '0.12em', textTransform: 'uppercase' }}>
          THRESHOLDS
        </h3>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 'var(--space-4)', marginBottom: 'var(--space-5)' }}>
        <div>
          <label style={{ display: 'block', fontSize: 11, color: 'var(--text-muted)', marginBottom: 6, letterSpacing: '0.08em' }}>
            RTO TARGET (SECONDS)
          </label>
          <input type="number" value={rtoTarget} onChange={e => onRtoChange(e.target.value)} className="form-input form-input-mono" />
        </div>
        <div>
          <label style={{ display: 'block', fontSize: 11, color: 'var(--text-muted)', marginBottom: 6, letterSpacing: '0.08em' }}>
            RPO TARGET (SECONDS)
          </label>
          <input type="number" value={rpoTarget} onChange={e => onRpoChange(e.target.value)} className="form-input form-input-mono" />
        </div>
        <div>
          <label style={{ display: 'block', fontSize: 11, color: 'var(--text-muted)', marginBottom: 6, letterSpacing: '0.08em' }}>
            SCORE THRESHOLD
          </label>
          <input type="number" value={scoreThreshold} onChange={e => onScoreChange(e.target.value)} className="form-input form-input-mono" />
        </div>
      </div>

      <button onClick={onSave} className="btn btn-primary" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
        <FloppyDisk size={14} weight="regular" />
        Save Changes
      </button>
    </div>
  )
}
