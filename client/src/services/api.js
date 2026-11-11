import axios from 'axios'

const http = axios.create({ baseURL: '/', timeout: 15000 })

function unwrap(promise) {
  return promise.then((r) => r.data)
}

export function getLines() {
  return unwrap(http.get('/api/lines'))
}
export function getSensors(lineId) {
  return unwrap(http.get('/api/sensors', { params: { line_id: lineId } }))
}
export function getLatest(lineId, source = 2) {
  return unwrap(http.get('/api/latest', { params: { line_id: lineId, source } }))
}
export function getStats(lineId) {
  return unwrap(http.get('/api/stats', { params: { line_id: lineId } }))
}
export function getHistory(lineId, limit = 12, offset = 0, sensorId = null, source = 2) {
  const params = { line_id: lineId, limit, offset, source }
  if (sensorId != null) params.sensor_id = sensorId
  return unwrap(http.get('/api/history', { params }))
}
export function getHourly(lineId, sensorId, from = null, to = null, source = 2) {
  const params = { line_id: lineId, sensor_id: sensorId, source }
  if (from) params.from = from
  if (to) params.to = to
  return unwrap(http.get('/api/hourly', { params }))
}
export function getHourlySummary(lineId, source = 2) {
  return unwrap(http.get('/api/hourly-summary', { params: { line_id: lineId, source } }))
}
export function getHistoryPivot(lineId, limit = 12, source = 2) {
  return unwrap(http.get('/api/history-pivot', { params: { line_id: lineId, limit, source } }))
}
export function getRange(lineId, sensorIds, from, to, limit = 5000, source = 2) {
  const params = { line_id: lineId, from, to, limit, source }
  if (sensorIds && sensorIds.length) params.sensor_ids = sensorIds.join(',')
  return unwrap(http.get('/api/range', { params }))
}