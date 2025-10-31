'use client'

import * as React from 'react'
import { useState, useEffect } from 'react'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { getJSON } from '@/lib/api'

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

export default function LiveSessions({ refreshMs = 5000 }: { refreshMs?: number }) {
  const [rows, setRows] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  async function load() {
    try {
      const data = await getJSON<any>('/api/v1/sessions')
      const items = Array.isArray(data) ? data : (data.items || data.data || [])
      setRows(items)
    } catch (e) {
      setRows([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
    const id = setInterval(load, refreshMs)
    return () => clearInterval(id)
  }, [refreshMs])

  return (
    <div className="rounded-lg border bg-card">
      <div className="p-4 border-b">
        <h2 className="text-lg font-semibold">Live Sessions</h2>
      </div>
      <div className="p-4">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>ID</TableHead>
              <TableHead>Task</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Progress</TableHead>
              <TableHead>Started</TableHead>
              <TableHead className="text-right">Duration</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map((s: any) => (
              <TableRow key={s.id}>
                <TableCell className="font-mono text-xs">{s.id?.slice(0,8)}</TableCell>
                <TableCell className="font-mono text-xs">{s.task_id?.slice(0,8)}</TableCell>
                <TableCell><Badge variant={statusVariant(s.status)}>{s.status}</Badge></TableCell>
                <TableCell>{Math.round(s.progress || 0)}%</TableCell>
                <TableCell>{s.started_at ? new Date(s.started_at).toLocaleString() : '-'}</TableCell>
                <TableCell className="text-right">{s.duration ?? '-'}</TableCell>
              </TableRow>
            ))}
            {!loading && rows.length === 0 && (
              <TableRow>
                <TableCell colSpan={6} className="text-center text-muted-foreground">No active sessions</TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}
