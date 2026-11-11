<script setup>
import { computed } from 'vue'

const props = defineProps({
  rows: { type: Array, default: () => [] },
  busy: { type: Boolean, default: false },
})

const fmt = (n, d = 2) => (n == null || Number.isNaN(Number(n))) ? '—' : Number(n).toFixed(d)
const fmtInt = (n) => (n == null) ? '—' : Number(n).toLocaleString()

function hhmm(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleTimeString('en-GB', { hour12: false, hour: '2-digit', minute: '2-digit' })
}

const displayRows = computed(() => props.rows.map((r, i) => ({
  n: i + 1,
  hour_bucket: r.hour_bucket,
  window: `${hhmm(r.first_ts)}–${hhmm(r.last_ts)}`,
  status: r.n_samples > 60 ? 'COMPLETE' : 'IN PROGRESS',
  delta_t_avg: r.delta_t_avg,
  oil_temp_avg: r.oil_temp_avg,
  burner_avg: r.burner_avg,
  moisture_avg: r.moisture_avg,
  moisture_min: r.moisture_min,
  moisture_max: r.moisture_max,
  out_of_band: r.out_of_band,
  burner_at_100: r.burner_at_100,
  alarms: 0,
})))
</script>

<template>
  <div class="card" style="margin-bottom:12px">
    <div class="card-h">
      <span class="t">Hourly Summary</span>
      <span style="font-size:11px;color:var(--muted)">
        {{ busy ? 'loading…' : `${displayRows.length} bucket${displayRows.length === 1 ? '' : 's'}` }}
      </span>
    </div>
    <div class="hour-wrap">
      <table class="hour-table">
        <thead>
          <tr>
            <th>HOUR</th><th>WINDOW</th><th>STATUS</th>
            <th>AVG ΔT °C</th><th>OIL TEMP °C</th><th>BURNER %</th>
            <th>MOISTURE AVG</th><th>MOISTURE RANGE</th>
            <th>OUT OF BAND</th><th>BURNER @100%</th><th>ALARMS</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="!displayRows.length">
            <td colspan="11" style="text-align:center;color:var(--muted);padding:20px">
              Awaiting plant data
            </td>
          </tr>
          <tr v-for="r in displayRows" :key="r.hour_bucket" :class="{ cur: r.status === 'IN PROGRESS' }">
            <td class="hn">Hour {{ r.n }}</td>
            <td class="win">{{ r.window }}</td>
            <td><span class="flag" :class="r.status === 'COMPLETE' ? 'ok' : 'info'">{{ r.status }}</span></td>
            <td>{{ fmt(r.delta_t_avg, 2) }}</td>
            <td>{{ fmt(r.oil_temp_avg, 2) }}</td>
            <td>{{ fmt(r.burner_avg, 1) }}</td>
            <td>{{ fmt(r.moisture_avg, 3) }}</td>
            <td>{{ fmt(r.moisture_min, 2) }}–{{ fmt(r.moisture_max, 2) }}</td>
            <td :class="{ bad: r.out_of_band > 0 }">{{ fmtInt(r.out_of_band) }}</td>
            <td>{{ fmtInt(r.burner_at_100) }}</td>
            <td>{{ r.alarms }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>