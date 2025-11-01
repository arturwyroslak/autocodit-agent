import { useEffect } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useWebSocketStore } from '@/services/websocketStore'

export function useWebSocket(sessionId?: string) {
  const queryClient = useQueryClient()
  const { connect, disconnect, subscribe } = useWebSocketStore()

  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
    const wsUrl = `${protocol}://${window.location.host}/ws`
    connect(wsUrl)
    return () => disconnect()
  }, [connect, disconnect])

  useEffect(() => {
    if (!sessionId) return
    const unsub = subscribe('session', (message) => {
      switch (message.type) {
        case 'session:event':
          queryClient.invalidateQueries({ queryKey: ['sessionLogs', sessionId] })
          break
        case 'session:filemodified':
          queryClient.invalidateQueries({ queryKey: ['sessionDiff', sessionId] })
          break
        case 'task:progress':
          queryClient.invalidateQueries({ queryKey: ['session', sessionId] })
          break
        case 'task:completed':
          queryClient.invalidateQueries({ queryKey: ['tasks'] })
          break
      }
    })
    return () => unsub()
  }, [sessionId, subscribe, queryClient])

  return { subscribe }
}
