import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { getJSON } from '@/lib/api'

async function fetchSessionsSummary() {
  try {
    return await getJSON<any>('/api/v1/sessions/summary')
  } catch (e) {
    return null
  }
}

export default async function SessionsSummaryCards() {
  const s = await fetchSessionsSummary()
  const active = s?.active_count ?? '—'
  const avg = s?.avg_duration_seconds_24h != null ? `${Math.round(s.avg_duration_seconds_24h)}s` : '—'

  return (
    <div className="grid gap-4 md:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Active Sessions</CardTitle>
          <CardDescription>Running containers</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{active}</div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Avg Duration (24h)</CardTitle>
          <CardDescription>Completed sessions</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{avg}</div>
        </CardContent>
      </Card>
    </div>
  )
}
