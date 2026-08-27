import { useState, useEffect, useCallback } from 'react'
import { apiClient, type TestRun } from '../utils/api'

interface CompareDeltas {
  score: number
  rto: number
  rpo: number
}

interface UseCompareResult {
  runA: TestRun | null
  runB: TestRun | null
  deltas: CompareDeltas | null
  loading: boolean
  error: string | null
  refetch: () => void
}

export function useCompare(runIdA: string | undefined, runIdB: string | undefined): UseCompareResult {
  const [runA, setRunA] = useState<TestRun | null>(null)
  const [runB, setRunB] = useState<TestRun | null>(null)
  const [deltas, setDeltas] = useState<CompareDeltas | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchCompare = useCallback(async () => {
    if (!runIdA || !runIdB) {
      setLoading(false)
      return
    }
    setLoading(true)
    setError(null)
    try {
      const [a, b] = await Promise.all([
        apiClient.getRun(runIdA),
        apiClient.getRun(runIdB),
      ])
      setRunA(a)
      setRunB(b)
      setDeltas({
        score: b.resilience_score - a.resilience_score,
        rto: b.rto_seconds - a.rto_seconds,
        rpo: b.rpo_seconds - a.rpo_seconds,
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to compare runs')
    } finally {
      setLoading(false)
    }
  }, [runIdA, runIdB])

  useEffect(() => {
    fetchCompare()
  }, [fetchCompare])

  return { runA, runB, deltas, loading, error, refetch: fetchCompare }
}
