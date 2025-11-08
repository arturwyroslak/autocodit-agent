import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { getJSON } from '@/lib/api'
import { Server, Database, Cpu, CheckCircle2, AlertCircle, XCircle } from 'lucide-react'

async function fetchHealth() {
  try {
    const data = await getJSON<any>('/api/v1/endpoints/health')
    return data
  } catch (e) {
    try {
      const ping = await getJSON<any>('/health')
      return { status: ping?.status || 'unknown' }
    } catch (e2) {
      return { status: 'unknown' }
    }
  }
}

function StatusIndicator({ status }: { status?: string }) {
  const normalizedStatus = (status || '').toLowerCase()
  
  if (normalizedStatus === 'healthy' || normalizedStatus === 'ok' || normalizedStatus === 'connected') {
    return (
      <div className="flex items-center gap-2">
        <CheckCircle2 className="w-5 h-5 text-success" />
        <span className="text-success font-medium">Healthy</span>
      </div>
    )
  }
  
  if (normalizedStatus === 'degraded' || normalizedStatus === 'warning') {
    return (
      <div className="flex items-center gap-2">
        <AlertCircle className="w-5 h-5 text-warning" />
        <span className="text-warning font-medium">Degraded</span>
      </div>
    )
  }
  
  if (normalizedStatus === 'unhealthy' || normalizedStatus === 'error' || normalizedStatus === 'disconnected') {
    return (
      <div className="flex items-center gap-2">
        <XCircle className="w-5 h-5 text-destructive" />
        <span className="text-destructive font-medium">Unhealthy</span>
      </div>
    )
  }
  
  return (
    <div className="flex items-center gap-2">
      <div className="w-5 h-5 rounded-full border-2 border-muted" />
      <span className="text-muted-foreground font-medium">Unknown</span>
    </div>
  )
}

export default async function SystemMetrics() {
  const health = await fetchHealth()
  const apiStatus = health?.status || 'unknown'
  const dbStatus = health?.services?.database || health?.database || 'n/a'
  const aiStatus = health?.services?.ai_service || health?.ai_service || 'n/a'

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      <Card className="card-hover border-l-4 border-l-primary overflow-hidden relative">
        <div className="absolute top-0 right-0 w-32 h-32 bg-primary/5 rounded-full -translate-y-16 translate-x-16" />
        <CardHeader className="relative">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-medium text-muted-foreground">API Status</CardTitle>
            <div className="p-2 rounded-lg bg-primary/10">
              <Server className="w-4 h-4 text-primary" />
            </div>
          </div>
          <CardDescription>Backend health</CardDescription>
        </CardHeader>
        <CardContent className="relative">
          <StatusIndicator status={apiStatus} />
          <div className="mt-4 flex items-center gap-2">
            <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden">
              <div className="h-full bg-gradient-to-r from-success to-success/70 w-full" />
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="card-hover border-l-4 border-l-info overflow-hidden relative">
        <div className="absolute top-0 right-0 w-32 h-32 bg-info/5 rounded-full -translate-y-16 translate-x-16" />
        <CardHeader className="relative">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-medium text-muted-foreground">Database</CardTitle>
            <div className="p-2 rounded-lg bg-info/10">
              <Database className="w-4 h-4 text-info" />
            </div>
          </div>
          <CardDescription>Connectivity status</CardDescription>
        </CardHeader>
        <CardContent className="relative">
          <StatusIndicator status={dbStatus} />
          <p className="text-xs text-muted-foreground mt-2">PostgreSQL</p>
        </CardContent>
      </Card>

      <Card className="card-hover border-l-4 border-l-success overflow-hidden relative">
        <div className="absolute top-0 right-0 w-32 h-32 bg-success/5 rounded-full -translate-y-16 translate-x-16" />
        <CardHeader className="relative">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-medium text-muted-foreground">AI Service</CardTitle>
            <div className="p-2 rounded-lg bg-success/10">
              <Cpu className="w-4 h-4 text-success" />
            </div>
          </div>
          <CardDescription>Provider status</CardDescription>
        </CardHeader>
        <CardContent className="relative">
          <StatusIndicator status={aiStatus} />
          <p className="text-xs text-muted-foreground mt-2">LLM Integration</p>
        </CardContent>
      </Card>
    </div>
  )
}
