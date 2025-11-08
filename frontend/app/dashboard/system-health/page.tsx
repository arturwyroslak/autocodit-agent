import SystemMetrics from '@/components/system-metrics'
import { Activity, Server, Database, Cpu, AlertTriangle } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

export default function SystemHealthPage() {
  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="border-b bg-gradient-to-br from-card to-card/50 backdrop-blur-sm">
        <div className="container mx-auto px-6 py-8">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 rounded-lg bg-success/10">
              <Activity className="w-6 h-6 text-success" />
            </div>
            <h1 className="text-3xl font-bold gradient-text">System Health</h1>
          </div>
          <p className="text-muted-foreground text-lg">Monitor system status and service health</p>
        </div>
      </div>

      {/* Content */}
      <div className="container mx-auto px-6 py-8 space-y-8">
        {/* Status Overview */}
        <div className="space-y-4">
          <div>
            <h2 className="text-xl font-semibold mb-1">Service Status</h2>
            <p className="text-sm text-muted-foreground">Real-time health monitoring of all services</p>
          </div>
          <SystemMetrics />
        </div>

        {/* Additional Information */}
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          <Card className="card-hover">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-medium text-muted-foreground">Uptime</CardTitle>
                <Server className="w-4 h-4 text-primary" />
              </div>
              <CardDescription>System availability</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-success">99.9%</div>
              <p className="text-xs text-muted-foreground mt-1">Last 30 days</p>
            </CardContent>
          </Card>

          <Card className="card-hover">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-medium text-muted-foreground">Response Time</CardTitle>
                <Cpu className="w-4 h-4 text-info" />
              </div>
              <CardDescription>Average API latency</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-info">45ms</div>
              <p className="text-xs text-muted-foreground mt-1">p95 response time</p>
            </CardContent>
          </Card>

          <Card className="card-hover">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-medium text-muted-foreground">Error Rate</CardTitle>
                <AlertTriangle className="w-4 h-4 text-warning" />
              </div>
              <CardDescription>Request failure rate</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-success">0.1%</div>
              <p className="text-xs text-muted-foreground mt-1">Last 24 hours</p>
            </CardContent>
          </Card>

          <Card className="card-hover">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-medium text-muted-foreground">Database Connections</CardTitle>
                <Database className="w-4 h-4 text-primary" />
              </div>
              <CardDescription>Active connections</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold gradient-text">42</div>
              <p className="text-xs text-muted-foreground mt-1">Pool size: 100</p>
            </CardContent>
          </Card>

          <Card className="card-hover">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-medium text-muted-foreground">Memory Usage</CardTitle>
                <Cpu className="w-4 h-4 text-info" />
              </div>
              <CardDescription>System memory</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-info">68%</div>
              <p className="text-xs text-muted-foreground mt-1">5.4GB / 8GB</p>
            </CardContent>
          </Card>

          <Card className="card-hover">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-medium text-muted-foreground">CPU Usage</CardTitle>
                <Cpu className="w-4 h-4 text-success" />
              </div>
              <CardDescription>Processor load</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-success">34%</div>
              <p className="text-xs text-muted-foreground mt-1">4 cores average</p>
            </CardContent>
          </Card>
        </div>

        {/* System Logs Preview */}
        <Card>
          <CardHeader>
            <CardTitle>Recent System Logs</CardTitle>
            <CardDescription>Latest system events and notifications</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {[
                { time: '4:42 AM', level: 'info', message: 'Database connection pool optimized' },
                { time: '4:35 AM', level: 'success', message: 'Task #8a3742a5 completed successfully' },
                { time: '4:20 AM', level: 'info', message: 'AI service health check passed' },
                { time: '4:10 AM', level: 'warning', message: 'High memory usage detected (85%)' },
                { time: '3:55 AM', level: 'info', message: 'Backup completed successfully' },
              ].map((log, i) => (
                <div key={i} className="flex items-center gap-3 p-3 rounded-lg bg-muted/30 hover:bg-muted/50 transition-colors">
                  <div className="text-xs text-muted-foreground min-w-[4rem]">{log.time}</div>
                  <div className={`px-2 py-0.5 rounded text-xs font-medium ${
                    log.level === 'success' ? 'bg-success/10 text-success' :
                    log.level === 'warning' ? 'bg-warning/10 text-warning' :
                    'bg-info/10 text-info'
                  }`}>
                    {log.level}
                  </div>
                  <div className="text-sm flex-1">{log.message}</div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
