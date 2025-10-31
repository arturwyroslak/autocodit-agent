import TaskOverview from '@/components/task-overview'
import LiveSessions from '@/components/live-sessions'
import SystemMetrics from '@/components/system-metrics'
import TaskCreator from '@/components/task-creator'
import SummaryCards from '@/components/summary-cards'
import SessionsSummaryCards from '@/components/sessions-summary-cards'

export default async function DashboardPage() {
  return (
    <main className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Mission Control</h1>
          <p className="text-muted-foreground">Monitor and manage your autonomous coding agents</p>
        </div>
      </div>

      <SummaryCards />
      <SessionsSummaryCards />

      <TaskCreator />

      <div className="grid gap-6 lg:grid-cols-2">
        <TaskOverview />
        <LiveSessions />
      </div>

      <SystemMetrics />
    </main>
  )
}
