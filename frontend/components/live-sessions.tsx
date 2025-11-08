'use client'

import * as React from 'react'
import { useState, useEffect } from 'react'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { getJSON } from '@/lib/api'
import { Radio, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'

function statusVariant(s?: string) {
  switch ((s || '').toLowerCase()) {
    case 'executing':
    case 'running':
      return 'default'
    case 'initializing':
    case 'planning':
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
    case 'executing':
    case 'running':
      return <span className="w-2 h-2 bg-primary rounded-full animate-pulse" />
    case 'initializing':
    case 'planning':
      return <span className="w-2 h-2 bg-secondary rounded-full animate-pulse" style={{ animationDuration: '2s' }} />
    case 'completed':
      return <span className="w-2 h-2 bg-success rounded-full" />
    case 'failed':
      return <span className="w-2 h-2 bg-destructive rounded-full" />
    default:
      return <span className="w-2 h-2 bg-muted rounded-full" />
  }
}

export default function LiveSessions({ refreshMs = 5000 }: { refreshMs?: number }) {
  const [rows, setRows] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date())

  async function load() {
    try {
      const data = await getJSON<any>('/api/v1/sessions')
      const items = Array.isArray(data) ? data : (data.items || data.data || [])
      setRows(items)
      setLastUpdate(new Date())
    } catch (e) {
      setRows([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
    const id = setInterval(load, refreshMs)
    const onRefresh = () => load()
    window.addEventListener('sessions:refresh', onRefresh as any)
    return () => {
      clearInterval(id)
      window.removeEventListener('sessions:refresh', onRefresh as any)
    }
  }, [refreshMs])

  const activeSessions = rows.filter(s => 
    ['executing', 'running', 'initializing', 'planning'].includes((s.status || '').toLowerCase())
  ).length

  return (
    <div className="rounded-xl border bg-gradient-to-br from-card to-card/50 backdrop-blur-sm shadow-lg overflow-hidden">
      <div className="p-6 border-b bg-background/50">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-success/10 relative">
              <Radio className="w-5 h-5 text-success" />
              {activeSessions > 0 && (
                <span className="absolute -top-1 -right-1 w-3 h-3 bg-success rounded-full animate-ping" />
              )}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-xl font-semibold">Live Sessions</h2>
                {activeSessions > 0 && (
                  <Badge variant="default" className="animate-pulse">
                    {activeSessions} Active
                  </Badge>
                )}
              </div>
              <p className="text-sm text-muted-foreground">
                Last updated: {lastUpdate.toLocaleTimeString()}
              </p>
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
              <TableHead className="font-semibold">Session ID</TableHead>
              <TableHead className="font-semibold">Task ID</TableHead>
              <TableHead className="font-semibold">Status</TableHead>
              <TableHead className="font-semibold">Progress</TableHead>
              <TableHead className="font-semibold">Started</TableHead>
              <TableHead className="text-right font-semibold">Duration</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map((s: any) => (
              <TableRow key={s.id} className="hover:bg-muted/30 transition-colors">
                <TableCell className="font-mono text-xs font-medium">
                  <span className="px-2 py-1 rounded bg-muted/50">
                    {s.id?.slice(0,8)}
                  </span>
                </TableCell>
                <TableCell className="font-mono text-xs font-medium">
                  <span className="px-2 py-1 rounded bg-primary/10">
                    {s.task_id?.slice(0,8)}
                  </span>
                </TableCell>
                <TableCell>
                  <Badge variant={statusVariant(s.status)} className="gap-2 font-medium">
                    {statusIcon(s.status)}
                    {s.status}
                  </Badge>
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-gradient-to-r from-success to-success/70 transition-all duration-500"
                        style={{ width: `${Math.round(s.progress || 0)}%` }}
                      />
                    </div>
                    <span className="text-xs font-medium text-muted-foreground min-w-[3ch]">
                      {Math.round(s.progress || 0)}%
                    </span>
                  </div>
                </TableCell>
                <TableCell className="text-sm text-muted-foreground">
                  {s.started_at ? new Date(s.started_at).toLocaleString('en-US', {
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                  }) : '-'}
                </TableCell>
                <TableCell className="text-right">
                  <span className="px-2 py-1 rounded-md bg-muted/50 text-xs font-mono font-medium">
                    {s.duration ?? '-'}
                  </span>
                </TableCell>
              </TableRow>
            ))}
            {!loading && rows.length === 0 && (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-12">
                  <div className="flex flex-col items-center gap-2 text-muted-foreground">
                    <Radio className="w-12 h-12 opacity-20" />
                    <p className="text-sm font-medium">No active sessions</p>
                    <p className="text-xs">Sessions will appear here when agents are running</p>
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
