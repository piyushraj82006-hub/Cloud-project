import { useState, useEffect, useCallback } from 'react'
import { apiClient, type TestRun } from '../utils/api'

interface UseRunsOptions {
  statusFilter?: string
  faultFilter?: string
}

interface UseRunsResult {
  runs: TestRun[]
  loading: boolean
  error: string | null
  refetch: () => void
}

export function useRuns(options: UseRunsOptions = {}): UseRunsResult {
  const [runs, setRuns] = useState<TestRun[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchRuns = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await apiClient.getRuns()
      let filtered = result.runs
      if (options.statusFilter) {
        filtered = filtered.filter(r => r.status === options.statusFilter)
      }
      if (options.faultFilter) {
        filtered = filtered.filter(r => r.fault_type === options.faultFilter)
      }
      setRuns(filtered)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load runs')
    } finally {
      setLoading(false)
    }
  }, [options.statusFilter, options.faultFilter])

  useEffect(() => {
    fetchRuns()
  }, [fetchRuns])

  return { runs, loading, error, refetch: fetchRuns }
}
