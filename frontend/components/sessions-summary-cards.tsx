import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { getJSON } from '@/lib/api'
import { Play, PauseCircle, Clock, Zap } from 'lucide-react'

async function fetchSessionsSummary() {
  try {
    return await getJSON<any>('/api/v1/sessions/summary')
  } catch (e) {
    return null
  }
}

export default async function SessionsSummaryCards() {
  const s = await fetchSessionsSummary()
  const activeSessions = s?.active_count ?? '—'
  const avgDuration = s?.avg_duration ?? '—'
  const completedToday = s?.completed_today ?? '—'
  const totalToday = s?.total_today ?? '—'

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      <Card className="card-hover border-l-4 border-l-success overflow-hidden relative">
        <div className="absolute top-0 right-0 w-32 h-32 bg-success/5 rounded-full -translate-y-16 translate-x-16" />
        <CardHeader className="relative">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-medium text-muted-foreground">Active Sessions</CardTitle>
            <div className="p-2 rounded-lg bg-success/10 relative">
              <Play className="w-4 h-4 text-success" />
              {activeSessions !== '—' && activeSessions > 0 && (
                <span className="absolute -top-1 -right-1 w-2 h-2 bg-success rounded-full animate-ping" />
              )}
            </div>
          </div>
          <CardDescription>Currently running</CardDescription>
        </CardHeader>
        <CardContent className="relative">
          <div className="text-3xl font-bold text-success">{activeSessions}</div>
          {activeSessions !== '—' && activeSessions > 0 && (
            <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
              <span className="w-1.5 h-1.5 bg-success rounded-full animate-pulse" />
              Live
            </p>
          )}
        </CardContent>
      </Card>

      <Card className="card-hover border-l-4 border-l-primary overflow-hidden relative">
        <div className="absolute top-0 right-0 w-32 h-32 bg-primary/5 rounded-full -translate-y-16 translate-x-16" />
        <CardHeader className="relative">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-medium text-muted-foreground">Completed Today</CardTitle>
            <div className="p-2 rounded-lg bg-primary/10">
              <PauseCircle className="w-4 h-4 text-primary" />
            </div>
          </div>
          <CardDescription>Finished sessions</CardDescription>
        </CardHeader>
        <CardContent className="relative">
          <div className="text-3xl font-bold gradient-text">{completedToday}</div>
          <p className="text-xs text-muted-foreground mt-1">Last 24h</p>
        </CardContent>
      </Card>

      <Card className="card-hover border-l-4 border-l-info overflow-hidden relative">
        <div className="absolute top-0 right-0 w-32 h-32 bg-info/5 rounded-full -translate-y-16 translate-x-16" />
        <CardHeader className="relative">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-medium text-muted-foreground">Avg Duration</CardTitle>
            <div className="p-2 rounded-lg bg-info/10">
              <Clock className="w-4 h-4 text-info" />
            </div>
          </div>
          <CardDescription>Per session</CardDescription>
        </CardHeader>
        <CardContent className="relative">
          <div className="text-3xl font-bold text-info">{avgDuration}</div>
          <p className="text-xs text-muted-foreground mt-1">Average time</p>
        </CardContent>
      </Card>

      <Card className="card-hover border-l-4 border-l-warning overflow-hidden relative">
        <div className="absolute top-0 right-0 w-32 h-32 bg-warning/5 rounded-full -translate-y-16 translate-x-16" />
        <CardHeader className="relative">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Today</CardTitle>
            <div className="p-2 rounded-lg bg-warning/10">
              <Zap className="w-4 h-4 text-warning" />
            </div>
          </div>
          <CardDescription>All sessions</CardDescription>
        </CardHeader>
        <CardContent className="relative">
          <div className="text-3xl font-bold text-warning">{totalToday}</div>
          <p className="text-xs text-muted-foreground mt-1">Including queued</p>
        </CardContent>
      </Card>
    </div>
  )
}
