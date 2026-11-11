<script setup>
import { onMounted, onBeforeUnmount, computed, ref } from 'vue'
import { useTelemetry } from './stores/telemetry'
import { useWs } from './stores/ws'

const telemetry = useTelemetry()
const ws = useWs()

const now = ref(Date.now())
let clock = null

const liveCount = computed(() => (telemetry.stats?.sources?.['2']) || 0)
const maxTs = computed(() => telemetry.stats?.max_ts || null)
const streamState = computed(() => {
  if (!maxTs.value || liveCount.value === 0) return 'awaiting'
  const age = now.value - new Date(maxTs.value).getTime()
  if (age < 10_000) return 'live'
  return 'stale'
})
const stateLabel = computed(() => ({
  awaiting: 'Awaiting data',
  live: 'Live stream',
  stale: 'No recent data',
}[streamState.value]))
const stateColor = computed(() => ({
  awaiting: '#94A3B8',
  live: '#22C55E',
  stale: '#D97706',
}[streamState.value]))
const lastPollLabel = computed(() => telemetry.lastUpdated
  ? telemetry.lastUpdated.toLocaleTimeString('en-GB', { hour12: false })
  : '—')
const sourceTimeLabel = computed(() => maxTs.value
  ? new Date(maxTs.value).toLocaleTimeString('en-GB', { hour12: false })
  : '—')

onMounted(async () => {
  await telemetry.bootstrap(30)
  ws.start(30)
  clock = setInterval(() => { now.value = Date.now() }, 2000)
})
onBeforeUnmount(() => { if (clock) clearInterval(clock) })
</script>

<template>
  <div class="app-bar">
    <div class="logo">PLANTVIEW</div>
    <div class="crumb">Line_Speed_30 &gt; <b>Process Overview</b></div>
    <div class="right">
      <span>
        <span class="dot" :style="{ background: stateColor }"></span>
        <span>{{ stateLabel }}</span>
      </span>
      <span>WS {{ ws.state }}</span>
      <span>Last poll <b style="color:#E2E8F0;font-weight:500">{{ lastPollLabel }}</b></span>
      <span>Source time <b style="color:#E2E8F0;font-weight:500">{{ sourceTimeLabel }}</b></span>
      <span>Readings <b style="color:#E2E8F0;font-weight:500">{{ liveCount.toLocaleString() }}</b></span>
    </div>
  </div>

  <main class="page">
    <RouterView />
  </main>

  <div class="status-bar">
    <span><span :style="{ color: stateColor }">●</span> {{ streamState }} · WS {{ ws.state }}</span>
    <span>Hints: {{ ws.hintCount }}</span>
    <span v-if="ws.lastHint">Last hint: seq {{ ws.lastHint.last_seq }} · {{ ws.lastHint.inserted }} rows</span>
    <span class="right">
      <span>API 127.0.0.1:8000</span>
      <span>{{ (telemetry.stats?.rows ?? 0).toLocaleString() }} rows total</span>
      <span>{{ telemetry.sensors.length }} sensors</span>
    </span>
  </div>
</template>