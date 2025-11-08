'use client'

import * as React from 'react'
import { useEffect, useState } from 'react'
import { getJSON } from '@/lib/api'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { ClipboardList, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'

function statusVariant(s?: string) {
  switch ((s || '').toLowerCase()) {
    case 'running':
      return 'default'
    case 'queued':
      return 'secondary'
    case 'completed':
      return 'outline'
    case 'failed':
      return 'destructive'
    default:
      return 'secondary'
  }
}

export function TasksSidebar() {
  const [tasks, setTasks] = useState<any[]>([])
  const [loading, setLoading] = useState(false)

  async function loadTasks() {
    setLoading(true)
    try {
      const data = await getJSON<{ items?: any[]; data?: any[] }>('/api/v1/tasks')
      const items = Array.isArray(data) ? data : (data.items || data.data || [])
      setTasks(items.slice(0, 20)) // Show last 20 tasks
    } catch (e) {
      setTasks([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadTasks()
    const interval = setInterval(loadTasks, 30000) // Refresh every 30s
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between p-4 border-b">
        <div className="flex items-center gap-2">
          <ClipboardList className="w-4 h-4" />
          <span className="font-semibold">Recent Tasks</span>
        </div>
        <Button
          variant="ghost"
          size="icon"
          onClick={loadTasks}
          disabled={loading}
          className="h-7 w-7"
        >
          <RefreshCw className={`w-3 h-3 ${loading ? 'animate-spin' : ''}`} />
        </Button>
      </div>
      
      <ScrollArea className="flex-1">
        <div className="p-2 space-y-1">
          {tasks.map((task) => (
            <div
              key={task.id}
              className="p-3 rounded-lg hover:bg-accent cursor-pointer transition-colors border border-transparent hover:border-border"
            >
              <div className="flex items-start justify-between gap-2 mb-2">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{task.title || 'Untitled'}</p>
                  <p className="text-xs text-muted-foreground truncate">{task.repository || '-'}</p>
                </div>
                <Badge variant={statusVariant(task.status)} className="text-xs shrink-0">
                  {task.status}
                </Badge>
              </div>
              <div className="flex items-center gap-2">
                <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden">
                  <div
                    className="h-full bg-primary transition-all"
                    style={{ width: `${Math.round((task.progress || 0) * 100)}%` }}
                  />
                </div>
                <span className="text-xs text-muted-foreground">
                  {Math.round((task.progress || 0) * 100)}%
                </span>
              </div>
            </div>
          ))}
          {tasks.length === 0 && !loading && (
            <div className="p-8 text-center text-sm text-muted-foreground">
              No tasks yet
            </div>
          )}
        </div>
      </ScrollArea>
    </div>
  )
}
