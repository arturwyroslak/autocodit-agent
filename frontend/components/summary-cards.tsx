import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { getJSON } from '@/lib/api'

async function fetchSummary() {
  try {
    return await getJSON<any>('/api/v1/tasks/summary')
  } catch (e) {
    return null
  }
}

export default async function SummaryCards() {
  const s = await fetchSummary()
  const active = s?.active_count ?? '—'
  const completedToday = s?.completed_today ?? '—'
  const successRate = s?.success_rate_30d != null ? `${s.success_rate_30d}%` : '—'
  const costToday = s?.cost_today != null ? `$${s.cost_today.toFixed(2)}` : '—'

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Active Tasks</CardTitle>
          <CardDescription>Currently running</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{active}</div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Completed Today</CardTitle>
          <CardDescription>Last 24h</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{completedToday}</div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
          <CardDescription>Last 30 days</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{successRate}</div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Cost Today</CardTitle>
          <CardDescription>AI model usage</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{costToday}</div>
        </CardContent>
      </Card>
    </div>
  )
}
