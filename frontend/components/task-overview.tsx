'use client'

import * as React from 'react'
import { useEffect, useState } from 'react'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { getJSON } from '@/lib/api'
import { ClipboardList, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'

async function fetchTasksOnce() {
  try {
    const data = await getJSON<{ items?: any[]; data?: any[] }>('/api/v1/tasks')
    const items = Array.isArray(data) ? (data as any) : (data.items || data.data || [])
    return items
  } catch (e) {
    return []
  }
}

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

function statusIcon(s?: string) {
  switch ((s || '').toLowerCase()) {
    case 'running':
      return '●'
    case 'queued':
      return '○'
    case 'completed':
      return '✓'
    case 'failed':
      return '✗'
    default:
      return '○'
  }
}

export default function TaskOverview() {
  const [tasks, setTasks] = useState<any[]>([])
  const [loading, setLoading] = useState(false)

  async function load() {
    setLoading(true)
    const items = await fetchTasksOnce()
    setTasks(items)
    setLoading(false)
  }

  useEffect(() => {
    load()
    const onRefresh = () => load()
    window.addEventListener('tasks:refresh', onRefresh as any)
    return () => window.removeEventListener('tasks:refresh', onRefresh as any)
  }, [])

  return (
    <div className="rounded-xl border bg-gradient-to-br from-card to-card/50 backdrop-blur-sm shadow-lg overflow-hidden">
      <div className="p-6 border-b bg-background/50">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-primary/10">
              <ClipboardList className="w-5 h-5 text-primary" />
            </div>
            <div>
              <h2 className="text-xl font-semibold">Recent Tasks</h2>
              <p className="text-sm text-muted-foreground">Latest agent activities</p>
            </div>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={load}
            disabled={loading}
            className="gap-2"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>
      
      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow className="bg-muted/50 hover:bg-muted/50">
              <TableHead className="font-semibold">ID</TableHead>
              <TableHead className="font-semibold">Title</TableHead>
              <TableHead className="font-semibold">Status</TableHead>
              <TableHead className="font-semibold">Progress</TableHead>
              <TableHead className="font-semibold">Repository</TableHead>
              <TableHead className="text-right font-semibold">Created</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {tasks.map((t: any) => (
              <TableRow key={t.id} className="hover:bg-muted/30 transition-colors">
                <TableCell className="font-mono text-xs font-medium">
                  <span className="px-2 py-1 rounded bg-muted/50">
                    {t.id?.slice(0,8)}
                  </span>
                </TableCell>
                <TableCell className="font-medium">{t.title}</TableCell>
                <TableCell>
                  <Badge variant={statusVariant(t.status)} className="gap-1 font-medium">
                    <span className="text-sm">{statusIcon(t.status)}</span>
                    {t.status}
                  </Badge>
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-gradient-to-r from-primary to-primary/70 transition-all duration-500"
                        style={{ width: `${Math.round((t.progress || 0) * 100)}%` }}
                      />
                    </div>
                    <span className="text-xs font-medium text-muted-foreground min-w-[3ch]">
                      {Math.round((t.progress || 0) * 100)}%
                    </span>
                  </div>
                </TableCell>
                <TableCell>
                  <span className="px-2 py-1 rounded-md bg-muted/50 text-xs font-mono">
                    {t.repository || t.repository_name || '-'}
                  </span>
                </TableCell>
                <TableCell className="text-right text-muted-foreground text-sm">
                  {t.created_at ? new Date(t.created_at).toLocaleString('en-US', {
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                  }) : '-'}
                </TableCell>
              </TableRow>
            ))}
            {tasks.length === 0 && (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-12">
                  <div className="flex flex-col items-center gap-2 text-muted-foreground">
                    <ClipboardList className="w-12 h-12 opacity-20" />
                    <p className="text-sm font-medium">No tasks found</p>
                    <p className="text-xs">Create a new task to get started</p>
                  </div>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}
