import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as api from '../services/api'

export const useTelemetry = defineStore('telemetry', () => {
  const lineId = ref(30)
  const lines = ref([])
  const sensors = ref([])
  const latest = ref([])
  const stats = ref(null)
  const range = ref({ data: [], meta: null })
  const hourly = ref({ data: [], meta: null })
  const hourlySummary = ref({ data: [], meta: null })
  const history = ref({ data: [], meta: null })
  const historyPivot = ref({ data: [], meta: null })
  const lastUpdated = ref(null)
  const loading = ref(false)

  const sensorById = computed(() => {
    const m = new Map()
    for (const s of sensors.value) m.set(s.sensor_id, s)
    return m
  })
  const latestById = computed(() => {
    const m = new Map()
    for (const r of latest.value) m.set(r.sensor_id, r)
    return m
  })

  async function bootstrap(id = 30) {
    lineId.value = id
    loading.value = true
    try {
      const [ls, sens] = await Promise.all([api.getLines(), api.getSensors(id)])
      lines.value = ls.data || []
      sensors.value = sens.data || []
      await refreshCore()
      await refreshHourlySummary()
    } finally {
      loading.value = false
    }
  }

  async function refreshCore() {
    const [l, st, hist] = await Promise.all([
      api.getLatest(lineId.value, 2),
      api.getStats(lineId.value),
      api.getHistory(lineId.value, 12, 0, null, 2),
    ])
    latest.value = l.data || []
    stats.value = st.data || null
    history.value = { data: hist.data || [], meta: hist.meta || null }
    lastUpdated.value = new Date()
    try {
      const hp = await api.getHistoryPivot(lineId.value, 12, 2)
      historyPivot.value = { data: hp.data || [], meta: hp.meta || null }
    } catch (e) { /* ignore */ }
  }

  async function refreshHourlySummary() {
    const r = await api.getHourlySummary(lineId.value, 2)
    hourlySummary.value = { data: r.data || [], meta: r.meta || null }
    return hourlySummary.value
  }

  async function refreshRange(sensorIds, from, to, limit = 5000) {
    const r = await api.getRange(lineId.value, sensorIds, from, to, limit, 2)
    range.value = { data: r.data || [], meta: r.meta || null }
    return range.value
  }

  async function refreshHourly(sensorId, from = null, to = null) {
    const r = await api.getHourly(lineId.value, sensorId, from, to, 2)
    hourly.value = { data: r.data || [], meta: r.meta || null }
    return hourly.value
  }

  async function applyHint(hint) {
    if (!hint || hint.line_id !== lineId.value) return
    await refreshCore()
  }

  return {
    lineId, lines, sensors, latest, stats, range, hourly, hourlySummary, history, historyPivot,
    lastUpdated, loading, sensorById, latestById,
    bootstrap, refreshCore, refreshHourlySummary, refreshRange, refreshHourly, applyHint,
  }
})