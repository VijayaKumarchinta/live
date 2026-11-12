<script setup>
import { onMounted, onBeforeUnmount, computed, ref } from 'vue'
import { RouterLink, RouterView } from 'vue-router'
import { useTelemetry } from './stores/telemetry'
import { useWs } from './stores/ws'

const telemetry = useTelemetry()
const ws = useWs()

const source1Count = computed(() => (telemetry.stats?.sources?.['1']) || 0)
const lastPollLabel = computed(() => telemetry.lastUpdated
  ? telemetry.lastUpdated.toLocaleTimeString('en-GB', { hour12: false })
  : '—')

onMounted(async () => {
  await telemetry.bootstrap(30)
  ws.start(30)
})
onBeforeUnmount(() => { ws.stop() })
</script>

<template>
  <div class="app-bar">
    <div class="logo">PLANTVIEW</div>
    <div class="crumb">Line_Speed_30 &gt; <b>Process Overview</b></div>
    <div class="right">
      <span>
        <span class="dot" style="background:#2563EB"></span>
        <span>Historical · Apr 17</span>
      </span>
      <span>WS {{ ws.state }}</span>
      <span>Last poll <b style="color:#E2E8F0;font-weight:500">{{ lastPollLabel }}</b></span>
      <span>Readings <b style="color:#E2E8F0;font-weight:500">{{ source1Count.toLocaleString() }}</b></span>
    </div>
  </div>

  <main class="page">
    <RouterView />
  </main>

  <div class="status-bar">
    <span style="color:#2563EB">&#9679; Historical view · source=1</span>
    <span>WS {{ ws.state }}</span>
    <span>Hints: {{ ws.hintCount }}</span>
    <span class="right">
      <span>API 127.0.0.1:8000</span>
      <span>{{ (telemetry.stats?.rows ?? 0).toLocaleString() }} rows total</span>
      <span>{{ telemetry.sensors.length }} sensors</span>
    </span>
  </div>
</template>