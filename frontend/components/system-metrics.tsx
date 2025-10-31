import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { getJSON } from '@/lib/api'

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

export default async function SystemMetrics() {
  const health = await fetchHealth()

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">API Status</CardTitle>
          <CardDescription>Backend health</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{health?.status ?? 'unknown'}</div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Database</CardTitle>
          <CardDescription>Connectivity</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{health?.services?.database ?? 'n/a'}</div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">AI Service</CardTitle>
          <CardDescription>Provider status</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{health?.services?.ai_service ?? 'n/a'}</div>
        </CardContent>
      </Card>
    </div>
  )
}
