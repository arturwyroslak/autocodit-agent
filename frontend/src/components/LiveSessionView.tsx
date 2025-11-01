'use client'

import * as React from 'react'
import { useEffect, useMemo, useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useWebSocket } from '@/hooks/useWebSocket'
import { getJSON } from '@/lib/api'

function TimelineItem({ item }: { item: any }) {
  return (
    <div className="py-1">
      <div className="text-xs text-muted-foreground">{new Date(item.timestamp).toLocaleTimeString()}</div>
      <div className="text-sm">
        <span className="font-medium">{item.type}</span> {item.message}
      </div>
    </div>
  )
}

function CodeDiff({ sessionId }: { sessionId: string }) {
  const { data } = useQuery({
    queryKey: ['sessionDiff', sessionId],
    queryFn: async () => getJSON(`/api/v1/sessions/${sessionId}/diff`),
    refetchInterval: 15000,
  })
  if (!data || !data.files?.length) return <div className="text-sm text-muted-foreground">No changes yet</div>
  return (
    <div className="space-y-3">
      {data.files.map((f: any) => (
        <div key={f.path} className="border rounded p-2">
          <div className="font-mono text-xs mb-1">{f.path}</div>
          <pre className="whitespace-pre-wrap text-xs overflow-auto max-h-64">
            {f.unified}
          </pre>
        </div>
      ))}
    </div>
  )
}

function Metrics({ sessionId }: { sessionId: string }) {
  const { data } = useQuery({
    queryKey: ['session', sessionId],
    queryFn: async () => getJSON(`/api/v1/sessions/${sessionId}`),
    refetchInterval: 10000,
  })
  const s = data || {}
  return (
    <div className="grid grid-cols-2 gap-3">
      <div className="rounded border p-2"><div className="text-xs text-muted-foreground">Status</div><div className="text-sm font-medium">{s.status || '-'}</div></div>
      <div className="rounded border p-2"><div className="text-xs text-muted-foreground">Iteration</div><div className="text-sm font-medium">{s.current_step || 0}/{s.total_steps || 0}</div></div>
      <div className="rounded border p-2"><div className="text-xs text-muted-foreground">Tokens</div><div className="text-sm font-medium">{s.prompt_tokens || 0}+{s.completion_tokens || 0}</div></div>
      <div className="rounded border p-2"><div className="text-xs text-muted-foreground">Files Modified</div><div className="text-sm font-medium">{s.files_modified || 0}</div></div>
    </div>
  )
}

export default function LiveSessionView({ sessionId }: { sessionId: string }) {
  const { subscribe } = useWebSocket(sessionId)
  const containerRef = useRef<HTMLDivElement>(null)

  const { data: timeline, refetch } = useQuery({
    queryKey: ['sessionLogs', sessionId],
    queryFn: async () => getJSON(`/api/v1/sessions/${sessionId}/events`),
    refetchInterval: 15000,
  })

  useEffect(() => {
    const unsub = subscribe('session', () => refetch())
    return () => unsub()
  }, [subscribe, refetch])

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight
    }
  }, [timeline])

  const items = useMemo(() => timeline?.items || [], [timeline])

  return (
    <div className="grid gap-4 md:grid-cols-12">
      <div className="md:col-span-3 space-y-3">
        <Metrics sessionId={sessionId} />
      </div>
      <div className="md:col-span-6">
        <div className="rounded border h-[560px] overflow-auto p-3" ref={containerRef}>
          {items.length === 0 && (
            <div className="text-sm text-muted-foreground">Waiting for events...</div>
          )}
          {items.map((it: any, idx: number) => (
            <TimelineItem key={idx} item={it} />
          ))}
        </div>
      </div>
      <div className="md:col-span-3">
        <CodeDiff sessionId={sessionId} />
      </div>
    </div>
  )
}
