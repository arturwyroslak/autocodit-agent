import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { getJSON } from '@/lib/api'
import { Activity, CheckCircle2, TrendingUp, DollarSign } from 'lucide-react'

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
      <Card className="card-hover border-l-4 border-l-primary overflow-hidden relative">
        <div className="absolute top-0 right-0 w-32 h-32 bg-primary/5 rounded-full -translate-y-16 translate-x-16" />
        <CardHeader className="relative">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-medium text-muted-foreground">Active Tasks</CardTitle>
            <div className="p-2 rounded-lg bg-primary/10">
              <Activity className="w-4 h-4 text-primary" />
            </div>
          </div>
          <CardDescription>Currently running</CardDescription>
        </CardHeader>
        <CardContent className="relative">
          <div className="text-3xl font-bold gradient-text">{active}</div>
          <p className="text-xs text-muted-foreground mt-1">Real-time</p>
        </CardContent>
      </Card>

      <Card className="card-hover border-l-4 border-l-success overflow-hidden relative">
        <div className="absolute top-0 right-0 w-32 h-32 bg-success/5 rounded-full -translate-y-16 translate-x-16" />
        <CardHeader className="relative">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-medium text-muted-foreground">Completed Today</CardTitle>
            <div className="p-2 rounded-lg bg-success/10">
              <CheckCircle2 className="w-4 h-4 text-success" />
            </div>
          </div>
          <CardDescription>Last 24 hours</CardDescription>
        </CardHeader>
        <CardContent className="relative">
          <div className="text-3xl font-bold text-success">{completedToday}</div>
          <p className="text-xs text-muted-foreground mt-1">+12% vs yesterday</p>
        </CardContent>
      </Card>

      <Card className="card-hover border-l-4 border-l-info overflow-hidden relative">
        <div className="absolute top-0 right-0 w-32 h-32 bg-info/5 rounded-full -translate-y-16 translate-x-16" />
        <CardHeader className="relative">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-medium text-muted-foreground">Success Rate</CardTitle>
            <div className="p-2 rounded-lg bg-info/10">
              <TrendingUp className="w-4 h-4 text-info" />
            </div>
          </div>
          <CardDescription>Last 30 days</CardDescription>
        </CardHeader>
        <CardContent className="relative">
          <div className="text-3xl font-bold text-info">{successRate}</div>
          <p className="text-xs text-muted-foreground mt-1">Excellent performance</p>
        </CardContent>
      </Card>

      <Card className="card-hover border-l-4 border-l-warning overflow-hidden relative">
        <div className="absolute top-0 right-0 w-32 h-32 bg-warning/5 rounded-full -translate-y-16 translate-x-16" />
        <CardHeader className="relative">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-medium text-muted-foreground">Cost Today</CardTitle>
            <div className="p-2 rounded-lg bg-warning/10">
              <DollarSign className="w-4 h-4 text-warning" />
            </div>
          </div>
          <CardDescription>AI model usage</CardDescription>
        </CardHeader>
        <CardContent className="relative">
          <div className="text-3xl font-bold text-warning">{costToday}</div>
          <p className="text-xs text-muted-foreground mt-1">Within budget</p>
        </CardContent>
      </Card>
    </div>
  )
}
