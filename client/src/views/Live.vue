<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import { useTelemetry } from '../stores/telemetry'
import { useWs } from '../stores/ws'
import HourlySummary from '../components/HourlySummary.vue'

const telemetry = useTelemetry()
const ws = useWs()

const KPIS = [
  { k: 'oil_temp',  sensor: 12, label: 'Oil temperature', unit: '°C',  d: 1 },
  { k: 'delta_t',   sensor: 32, label: 'Delta T',          unit: '°C',  d: 1 },
  { k: 'burner',    sensor: 1,  label: 'Burner load',       unit: '%',   d: 1 },
  { k: 'moisture',  sensor: 25, label: 'Moisture',          unit: '',    d: 2 },
  { k: 'paddle',    sensor: 30, label: 'Paddle speed',      unit: 'rpm', d: 1 },
  { k: 'oil_level', sensor: 5,  label: 'Oil level',         unit: '',    d: 1 },
]

const STATS_CARDS = [
  { sensor: 12, label: 'Oil temperature', unit: '°C',  d: 1 },
  { sensor: 32, label: 'Delta T',          unit: '°C',  d: 1 },
  { sensor: 1,  label: 'Burner load',       unit: '%',   d: 1 },
  { sensor: 25, label: 'Moisture',          unit: '',    d: 2 },
  { sensor: 30, label: 'Paddle speed',      unit: 'rpm', d: 1 },
  { sensor: 5,  label: 'Oil level',         unit: '',    d: 1 },
]

const CHARTS = [
  { id: 'deltat',   title: 'Chart 1 · Delta T',               sub: 'Sheet1 chart 1',                      sensors: [{ id: 32, name: 'Delta T °C', color: '#DC2626' }] },
  { id: 'dt_sp',    title: 'Chart 2 · Delta T vs Burner SP',  sub: 'Set temp should not rise with speed', sensors: [{ id: 32, name: 'Delta T °C', color: '#DC2626' }, { id: 3, name: 'Burner SP', color: '#2563EB' }] },
  { id: 'dt_oil',   title: 'Chart 3 · Delta T vs Oil level',  sub: 'Sheet1 chart 3',                      sensors: [{ id: 32, name: 'Delta T °C', color: '#DC2626' }, { id: 5, name: 'Oil level', color: '#D97706' }] },
  { id: 'burner',   title: 'Chart 4 · Burner load',            sub: 'Sheet1 chart 4',                      sensors: [{ id: 1,  name: 'Burner load %', color: '#16A34A' }] },
  { id: 'moisture', title: 'Chart 5 · Moisture',               sub: 'Sheet1 chart 5',                      sensors: [{ id: 25, name: 'Moisture', color: '#7C3AED' }] },
]

const WINDOWS = [
  { id: 'full', label: 'Full run', minutes: null },
]

let chartInstances = []
let resizeObserver = null
let pollTimer = null
let initScheduled = false
const activeWindow = ref('full')

const fmt = (n, d = 2) => (n == null || Number.isNaN(Number(n))) ? '—' : Number(n).toFixed(d)
const fmtInt = (n) => (n == null) ? '—' : Number(n).toLocaleString()
const hms = (ts) => ts ? new Date(ts).toLocaleTimeString('en-GB', { hour12: false }) : '—'

const kpiValues = computed(() => KPIS.map((k) => {
  const row = telemetry.latestById.get(k.sensor)
  return { ...k, value: row?.value, ts: row?.ts }
}))

const statsCards = computed(() => {
  const agg = new Map()
  const st = telemetry.stats
  if (st && Array.isArray(st.sensors_by_id)) {
    for (const r of st.sensors_by_id) if (r.source === 1) agg.set(r.sensor_id, r)
  }
  return STATS_CARDS.map((s) => {
    const a = agg.get(s.sensor)
    return { ...s, avg: a?.avg, min: a?.min, max: a?.max }
  })
})

function chartEmptyOption(text) {
  return {
    title: { text, left: 'center', top: 'middle', textStyle: { color: '#9AA5B1', fontSize: 12, fontWeight: 400 } },
    xAxis: { show: false },
    yAxis: { show: false },
    series: [],
  }
}

function windowToRange() {
  const hs = telemetry.hourlySummary.data
  if (!hs || !hs.length) return null
  return { from: hs[0].first_ts, to: hs[hs.length - 1].last_ts }
}

function tryInitCharts() {
  if (chartInstances.length === CHARTS.length) return true
  const els = CHARTS.map((_, i) => document.getElementById(`chart-${i}`))
  if (els.some((el) => !el)) return false
  for (const el of els) {
    if (el.clientWidth < 100 || el.clientHeight < 100) return false
  }
  chartInstances = els.map((el) => echarts.init(el, null, { renderer: 'canvas' }))
  return true
}

async function renderCharts() {
  await nextTick()
  if (!tryInitCharts()) {
    if (!initScheduled) {
      initScheduled = true
      setTimeout(() => { initScheduled = false; renderCharts() }, 300)
    }
    return
  }
  const rows = telemetry.range.data
  for (let i = 0; i < CHARTS.length; i++) {
    const cfg = CHARTS[i]
    const inst = chartInstances[i]
    if (!inst) continue
    if (!rows.length) {
      inst.setOption(chartEmptyOption('No data in window'), { notMerge: true })
      continue
    }
    const times = []
    const seen = new Set()
    for (const r of rows) if (!seen.has(r.ts)) { seen.add(r.ts); times.push(r.ts) }
    const series = cfg.sensors.map((s) => {
      const byTs = new Map()
      for (const r of rows) if (r.sensor_id === s.id) byTs.set(r.ts, r.value)
      return {
        name: s.name,
        type: 'line',
        showSymbol: false,
        smooth: false,
        color: s.color,
        data: times.map((t) => [new Date(t).getTime(), byTs.has(t) ? byTs.get(t) : null]),
      }
    })
    inst.setOption({
      grid: { left: 52, right: 20, top: 36, bottom: 36 },
      tooltip: { trigger: 'axis' },
      legend: { top: 4, textStyle: { fontSize: 11 } },
      xAxis: { type: 'time', axisLabel: { fontSize: 10, formatter: (v) => hms(new Date(v).toISOString()) } },
      yAxis: { type: 'value', scale: true, axisLabel: { fontSize: 10 } },
      series,
    }, { notMerge: true })
  }
}

async function refreshAll() {
  const win = windowToRange()
  if (!win) return
  const ids = [...new Set(CHARTS.flatMap((c) => c.sensors.map((s) => s.id)))]
  await telemetry.refreshRange(ids, win.from, win.to, 20000)
  await telemetry.refreshHourlySummary()
  await renderCharts()
}

onMounted(async () => {
  await nextTick()
  resizeObserver = new ResizeObserver(() => {
    for (const inst of chartInstances) if (inst) inst.resize()
  })
  for (let i = 0; i < CHARTS.length; i++) {
    const el = document.getElementById(`chart-${i}`)
    if (el) resizeObserver.observe(el)
  }

  // Wait for hourly summary to be populated, then call refreshAll
  // Use a watch that fires when hourlySummary.data.length > 0
  const ready = new Promise((resolve) => {
    if (telemetry.hourlySummary.data.length > 0) {
      resolve()
      return
    }
    const stop = watch(
      () => telemetry.hourlySummary.data.length,
      (len) => {
        if (len > 0) {
          stop()
          resolve()
        }
      }
    )
  })
  await ready

  await refreshAll()
  setTimeout(() => {
    for (const inst of chartInstances) if (inst) inst.resize()
    renderCharts()
  }, 400)
  pollTimer = setInterval(() => {
    if (ws.state !== 'connected') {
      telemetry.refreshCore()
      refreshAll()
    }
  }, 15000)
})

onBeforeUnmount(() => {
  if (pollTimer) clearInterval(pollTimer)
  if (resizeObserver) { resizeObserver.disconnect(); resizeObserver = null }
  for (const inst of chartInstances) if (inst) inst.dispose()
  chartInstances = []
})

watch(() => ws.lastHint, () => { refreshAll() })
watch(activeWindow, () => { refreshAll() })
</script>

<template>
  <div class="title-row">
    <div>
      <h1>Line Speed 30 · Process Overview</h1>
      <div class="meta">
        <span style="color:#2563EB">&#9679;</span>
        Historical · Apr 17, 12:09–18:06 ·
        {{ (telemetry.stats?.sources?.['1'] || 0).toLocaleString() }} readings
      </div>
    </div>
    <div class="toolbar">
      <div class="seg">
        <button
          v-for="w in WINDOWS" :key="w.id"
          :aria-pressed="activeWindow === w.id"
          @click="setWindow(w.id)"
        >{{ w.label }}</button>
      </div>
    </div>
  </div>

  <div class="kpi-row">
    <div class="kpi" v-for="k in kpiValues" :key="k.k">
      <div class="lbl">{{ k.label }}</div>
      <div class="val-row">
        <span class="val" :class="{ placeholder: k.value == null }">{{ fmt(k.value, k.d) }}<span v-if="k.value != null" class="unit">{{ k.unit }}</span></span>
      </div>
      <div class="status">
        <span class="dot" style="background:var(--muted)"></span>
        <span class="lbl2" style="color:var(--muted)">No limit set</span>
        <span class="base" v-if="k.ts">· {{ hms(k.ts) }}</span>
      </div>
    </div>
  </div>

  <HourlySummary :rows="telemetry.hourlySummary.data" />

  <div class="chart-grid">
    <div
      v-for="(c, i) in CHARTS" :key="c.id"
      :class="['chart-panel', i === CHARTS.length - 1 && CHARTS.length % 2 === 1 ? 'wide' : '']"
    >
      <div class="ph">
        <div>
          <div class="ptitle">{{ c.title }}</div>
          <div class="psub">{{ c.sub }}</div>
        </div>
        <div class="card-h" style="margin:0">
          <div class="legend">
            <span v-for="s in c.sensors" :key="s.id"><i :style="{ background: s.color }"></i>{{ s.name }}</span>
          </div>
        </div>
      </div>
      <div class="pbody" :id="`chart-${i}`"></div>
    </div>
  </div>

  <div class="card" style="margin-bottom:12px">
    <div class="card-h">
      <span class="t">Active Alarms</span>
      <span style="font-size:11px;color:var(--muted)">Block 9 will wire this</span>
    </div>
    <div style="padding:20px;text-align:center;color:var(--muted);font-size:11.5px">No active alarms</div>
  </div>

  <div class="sec-h">Statistics<span>over the current window</span></div>
  <div class="kpi-row">
    <div class="kpi" v-for="s in statsCards" :key="s.sensor">
      <div class="lbl">{{ s.label }}</div>
      <div class="val-row">
        <span class="val" :class="{ placeholder: s.avg == null }">{{ fmt(s.avg, s.d) }}<span v-if="s.avg != null" class="unit">{{ s.unit || 'avg' }}</span></span>
      </div>
      <div class="hrow" style="margin-top:6px"><span class="k">min</span><span class="v">{{ fmt(s.min, s.d) }}</span></div>
      <div class="hrow"><span class="k">max</span><span class="v">{{ fmt(s.max, s.d) }}</span></div>
    </div>
  </div>

  <div class="bottom-row" style="margin-top:18px">
    <div class="card">
      <div class="card-h">
        <span class="t">Historical Readings · Last 12 samples</span>
        <span style="font-size:11px;color:var(--muted)">{{ telemetry.historyPivot.data.length }} timestamps</span>
      </div>
      <table class="hist-table">
        <thead>
          <tr>
            <th>TIMESTAMP</th><th>BURNER PV</th><th>ΔT</th><th>OIL LVL</th>
            <th>STACK</th><th>MOIST</th><th>PADDLE</th><th>XV6601</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="!telemetry.historyPivot.data.length">
            <td colspan="8" style="text-align:center;color:var(--muted);padding:20px">No readings</td>
          </tr>
          <tr v-for="r in telemetry.historyPivot.data" :key="r.ts">
            <td class="ts">{{ hms(r.ts) }}</td>
            <td>{{ fmt(r.sensors['2'], 2) }}</td>
            <td>{{ fmt(r.sensors['32'], 2) }}</td>
            <td>{{ fmt(r.sensors['5'], 2) }}</td>
            <td>{{ fmt(r.sensors['9'], 1) }}</td>
            <td>{{ fmt(r.sensors['25'], 3) }}</td>
            <td>{{ fmt(r.sensors['30'], 1) }}</td>
            <td>{{ r.sensors['31'] ? 'OPEN' : 'CLOSED' }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <div class="card">
      <div class="card-h">
        <span class="t">Event History</span>
        <span style="font-size:11px;font-weight:600;color:#2563EB">● Historical</span>
      </div>
      <div class="event-feed">
        <div style="padding:20px;text-align:center;color:var(--muted);font-size:11.5px">
          Source=1 is static — no live events
        </div>
      </div>
    </div>
  </div>
</template>