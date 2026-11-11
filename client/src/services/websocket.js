export function createLiveSocket({ lineId = 30, onMessage, onStatus }) {
  let ws = null
  let stopped = false
  let retry = 0
  let retryTimer = null

  function url() {
    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:'
    return `${proto}//${location.host}/ws/live?line_id=${lineId}`
  }

  function connect() {
    if (stopped) return
    onStatus?.('connecting')
    ws = new WebSocket(url())

    ws.onopen = () => { retry = 0; onStatus?.('connected') }
    ws.onmessage = (ev) => {
      try { onMessage?.(JSON.parse(ev.data)) } catch (e) { /* ignore */ }
    }
    ws.onclose = () => {
      onStatus?.('disconnected')
      if (stopped) return
      const delay = Math.min(15000, 500 * Math.pow(2, retry))
      retry += 1
      retryTimer = setTimeout(connect, delay)
    }
    ws.onerror = () => { try { ws.close() } catch (e) {} }
  }

  connect()

  return {
    stop() {
      stopped = true
      if (retryTimer) clearTimeout(retryTimer)
      if (ws) { try { ws.close() } catch (e) {} }
    },
  }
}