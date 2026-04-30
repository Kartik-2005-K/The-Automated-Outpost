/**
 * engine/WebSocketClient.js — Manages WebSocket connection to the FastAPI backend.
 * Reconnects automatically with exponential backoff.
 */
import { useGameStore } from '../store/useGameStore'

const WS_URL = 'ws://localhost:8000/ws'
const MAX_BACKOFF_MS = 8000

let socket = null
let reconnectTimeout = null
let backoff = 500

export function connectWebSocket() {
  if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) {
    return
  }

  console.log(`[WS] Connecting to ${WS_URL}`)
  socket = new WebSocket(WS_URL)

  socket.onopen = () => {
    console.log('[WS] Connected')
    backoff = 500
    useGameStore.getState().setConnected(true)
  }

  socket.onmessage = (evt) => {
    try {
      const data = JSON.parse(evt.data)
      useGameStore.getState().applyWorldState(data)
    } catch (e) {
      console.warn('[WS] Parse error', e)
    }
  }

  socket.onerror = (err) => {
    console.warn('[WS] Error', err)
  }

  socket.onclose = () => {
    console.log(`[WS] Closed. Reconnecting in ${backoff}ms`)
    useGameStore.getState().setConnected(false)
    socket = null
    clearTimeout(reconnectTimeout)
    reconnectTimeout = setTimeout(() => {
      connectWebSocket()
      backoff = Math.min(backoff * 2, MAX_BACKOFF_MS)
    }, backoff)
  }
}

export function disconnectWebSocket() {
  clearTimeout(reconnectTimeout)
  socket?.close()
  socket = null
}
