import SummaryCards from '@/components/summary-cards'
import SessionsSummaryCards from '@/components/sessions-summary-cards'
import TaskOverview from '@/components/task-overview'
import LiveSessions from '@/components/live-sessions'
import { BarChart3 } from 'lucide-react'

export default function StatisticsPage() {
  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="border-b bg-gradient-to-br from-card to-card/50 backdrop-blur-sm">
        <div className="container mx-auto px-6 py-8">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 rounded-lg bg-primary/10">
              <BarChart3 className="w-6 h-6 text-primary" />
            </div>
            <h1 className="text-3xl font-bold gradient-text">Statistics</h1>
          </div>
          <p className="text-muted-foreground text-lg">Comprehensive metrics and analytics for your tasks</p>
        </div>
      </div>

      {/* Content */}
      <div className="container mx-auto px-6 py-8 space-y-8">
        {/* Task Statistics */}
        <div className="space-y-4">
          <div>
            <h2 className="text-xl font-semibold mb-1">Task Metrics</h2>
            <p className="text-sm text-muted-foreground">Overview of task completion and performance</p>
          </div>
          <SummaryCards />
        </div>

        {/* Session Statistics */}
        <div className="space-y-4">
          <div>
            <h2 className="text-xl font-semibold mb-1">Session Metrics</h2>
            <p className="text-sm text-muted-foreground">Active and completed sessions statistics</p>
          </div>
          <SessionsSummaryCards />
        </div>

        {/* Detailed Views */}
        <div className="grid gap-6 lg:grid-cols-2">
          <TaskOverview />
          <LiveSessions />
        </div>
      </div>
    </div>
  )
}
