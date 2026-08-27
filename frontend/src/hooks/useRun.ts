import { useState, useEffect, useCallback } from 'react'
import { apiClient, type TestRun } from '../utils/api'

interface UseRunResult {
  run: TestRun | null
  report: Record<string, unknown> | null
  loading: boolean
  error: string | null
  refetch: () => void
}

export function useRun(runId: string | undefined): UseRunResult {
  const [run, setRun] = useState<TestRun | null>(null)
  const [report, setReport] = useState<Record<string, unknown> | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchRun = useCallback(async () => {
    if (!runId) {
      setLoading(false)
      return
    }
    setLoading(true)
    setError(null)
    try {
      const [runData, reportData] = await Promise.all([
        apiClient.getRun(runId),
        apiClient.getRunReport(runId).catch(() => null),
      ])
      setRun(runData)
      setReport(reportData)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load run details')
    } finally {
      setLoading(false)
    }
  }, [runId])

  useEffect(() => {
    fetchRun()
  }, [fetchRun])

  return { run, report, loading, error, refetch: fetchRun }
}
