import { useQuery } from '@tanstack/react-query'
import { getJSON } from '@/lib/api'

function Stat({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="rounded border p-2">
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="text-sm font-medium">{value}</div>
    </div>
  )
}

export default function TaskReview({ taskId }: { taskId: string }) {
  const { data } = useQuery({
    queryKey: ['task', taskId],
    queryFn: async () => getJSON(`/api/v1/tasks/${taskId}`),
    refetchInterval: 10000,
  })

  const t = data || {}
  const results = t.test_results || {}

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Stat label="Status" value={t.status || '-'} />
        <Stat label="Branch" value={t.branch_name || '-'} />
        <Stat label="PR" value={t.pull_request_number || '-'} />
        <Stat label="Tokens" value={`${t.tokens_used || 0}`} />
      </div>

      <div className="rounded border p-3">
        <div className="text-sm font-medium mb-2">Summary</div>
        <div className="text-sm whitespace-pre-wrap">{t.result_summary || '—'}</div>
      </div>

      <div className="grid md:grid-cols-2 gap-3">
        <div className="rounded border p-3">
          <div className="text-sm font-medium mb-2">Tests</div>
          <div className="text-sm">{results.passed ?? 0} passed / {results.failed ?? 0} failed</div>
        </div>
        <div className="rounded border p-3">
          <div className="text-sm font-medium mb-2">Coverage</div>
          <div className="text-sm">{results.coverage ?? '-'}%</div>
        </div>
      </div>
    </div>
  )
}
