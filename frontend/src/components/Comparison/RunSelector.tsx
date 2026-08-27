import type { TestRun } from '../../utils/api'

interface RunSelectorProps {
  runs: TestRun[]
  selectedA: string
  selectedB: string
  onChangeA: (id: string) => void
  onChangeB: (id: string) => void
}

export function RunSelector({ runs, selectedA, selectedB, onChangeA, onChangeB }: RunSelectorProps) {
  return (
    <div style={{ display: 'flex', gap: 'var(--space-4)', marginBottom: 'var(--space-6)', alignItems: 'center' }} className="animate-in animate-in-delay-1">
      <select
        value={selectedA}
        onChange={e => onChangeA(e.target.value)}
        className="select-input"
        style={{ flex: 1, fontFamily: 'var(--font-mono)', fontSize: 13 }}
      >
        {runs.map(r => (
          <option key={r.run_id} value={r.run_id}>{r.run_id} - {r.status}</option>
        ))}
      </select>

      <span style={{ fontSize: 14, color: 'var(--text-muted)', fontWeight: 500 }}>vs</span>

      <select
        value={selectedB}
        onChange={e => onChangeB(e.target.value)}
        className="select-input"
        style={{ flex: 1, fontFamily: 'var(--font-mono)', fontSize: 13 }}
      >
        {runs.map(r => (
          <option key={r.run_id} value={r.run_id}>{r.run_id} - {r.status}</option>
        ))}
      </select>
    </div>
  )
}
