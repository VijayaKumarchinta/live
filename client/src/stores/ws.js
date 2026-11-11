import { defineStore } from 'pinia'
import { ref } from 'vue'
import { createLiveSocket } from '../services/websocket'
import { useTelemetry } from './telemetry'

export const useWs = defineStore('ws', () => {
  const state = ref('idle')
  const lastHint = ref(null)
  const hintCount = ref(0)
  let socket = null

  function start(lineId = 30) {
    if (socket) return
    const telemetry = useTelemetry()
    socket = createLiveSocket({
      lineId,
      onStatus: (s) => { state.value = s },
      onMessage: (msg) => {
        if (msg.type === 'telemetry') {
          lastHint.value = msg
          hintCount.value += 1
          telemetry.applyHint(msg)
        }
      },
    })
  }

  function stop() {
    if (socket) { socket.stop(); socket = null }
    state.value = 'idle'
  }

  return { state, lastHint, hintCount, start, stop }
})