import TaskOverview from '@/components/task-overview'
import LiveSessions from '@/components/live-sessions'
import SystemMetrics from '@/components/system-metrics'
import TaskCreator from '@/components/task-creator'
import SummaryCards from '@/components/summary-cards'
import SessionsSummaryCards from '@/components/sessions-summary-cards'
import { Activity, Sparkles } from 'lucide-react'

export default async function DashboardPage() {
  return (
    <main className="min-h-screen relative">
      {/* Subtle background pattern */}
      <div className="absolute inset-0 opacity-5" style={{
        backgroundImage: 'radial-gradient(circle at 1px 1px, hsl(var(--foreground)) 1px, transparent 0)',
        backgroundSize: '32px 32px'
      }} />

      <div className="relative z-10 p-6 space-y-8">
        {/* Header Section */}
        <div className="animate-fade-in">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div className="space-y-2">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-gradient-to-br from-primary/20 to-primary/10 backdrop-blur-sm">
                  <Activity className="w-6 h-6 text-primary" />
                </div>
                <h1 className="text-4xl font-bold tracking-tight gradient-text">Mission Control</h1>
              </div>
              <p className="text-muted-foreground text-lg">Monitor and manage your autonomous coding agents in real-time</p>
            </div>
            
            <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-success/10 border border-success/20 backdrop-blur-sm">
              <div className="w-2 h-2 rounded-full bg-success animate-pulse" />
              <span className="text-sm font-medium text-success">System Operational</span>
            </div>
          </div>
        </div>

        {/* Summary Cards */}
        <div className="animate-slide-up" style={{ animationDelay: '0.1s' }}>
          <SummaryCards />
        </div>
        
        {/* Sessions Summary */}
        <div className="animate-slide-up" style={{ animationDelay: '0.2s' }}>
          <SessionsSummaryCards />
        </div>

        {/* Task Creator */}
        <div className="animate-slide-up" style={{ animationDelay: '0.3s' }}>
          <TaskCreator />
        </div>

        {/* Main Grid - Tasks and Sessions */}
        <div className="grid gap-6 lg:grid-cols-2 animate-slide-up" style={{ animationDelay: '0.4s' }}>
          <TaskOverview />
          <LiveSessions />
        </div>

        {/* System Metrics */}
        <div className="animate-slide-up" style={{ animationDelay: '0.5s' }}>
          <div className="mb-4 flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-primary" />
            <h2 className="text-2xl font-semibold">System Health</h2>
          </div>
          <SystemMetrics />
        </div>
      </div>
    </main>
  )
}
