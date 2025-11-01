import { create } from 'zustand'

type SessionEvent = {
  timestamp: string
  type: string
  message?: string
  file?: string
  diff?: { added: string[]; removed: string[] }
}

type WebSocketMessage = {
  type: string
  data: any
}

type WebSocketState = {
  ws: WebSocket | null
  isConnected: boolean
  subscribers: Map<string, Set<(msg: WebSocketMessage) => void>>
  connect: (url: string) => void
  disconnect: () => void
  subscribe: (channel: string, cb: (msg: WebSocketMessage) => void) => () => void
  publish: (channel: string, message: WebSocketMessage) => void
}

export const useWebSocketStore = create<WebSocketState>((set, get) => ({
  ws: null,
  isConnected: false,
  subscribers: new Map(),
  connect: (url: string) => {
    const ws = new WebSocket(url)
    ws.onopen = () => set({ ws, isConnected: true })
    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data) as WebSocketMessage
        const subs = get().subscribers
        // deliver to channel and channel prefix
        subs.forEach((callbacks, channel) => {
          if (message.type === channel || message.type.startsWith(channel)) {
            callbacks.forEach((cb) => cb(message))
          }
        })
      } catch (e) {
        console.error('WS parse error', e)
      }
    }
    ws.onerror = (e) => {
      console.error('WebSocket error', e)
      set({ isConnected: false })
    }
    ws.onclose = () => {
      set({ isConnected: false, ws: null })
      setTimeout(() => get().connect(url), 5000)
    }
  },
  disconnect: () => {
    const ws = get().ws
    if (ws) ws.close()
  },
  subscribe: (channel, cb) => {
    const subs = get().subscribers
    if (!subs.has(channel)) subs.set(channel, new Set())
    subs.get(channel)!.add(cb)
    return () => {
      subs.get(channel)?.delete(cb)
    }
  },
  publish: (channel, message) => {
    const ws = get().ws
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ channel, ...message }))
    }
  },
}))
