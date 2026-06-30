const API_BASE = 'http://localhost:8000'

export const api = {
  aqi: {
    spatial: (date) => `${API_BASE}/api/aqi/spatial?date=${date}`,
    timeseries: (city, start, end) => 
      `${API_BASE}/api/aqi/timeseries?city=${city}&start=${start}&end=${end}`,
    summary: (date) => `${API_BASE}/api/aqi/national-summary?date=${date}`,
    ingest: `${API_BASE}/api/aqi/ingest`,
  },
  hcho: {
    spatial: (date) => `${API_BASE}/api/hcho/spatial?date=${date}`,
    hotspots: (date) => `${API_BASE}/api/hcho/hotspots?date=${date}`,
  },
  fire: {
    points: (start, end) => 
      `${API_BASE}/api/fire/points?start=${start}&end=${end}`,
    correlation: () => `${API_BASE}/api/fire/correlation`,
    ingest: `${API_BASE}/api/fire/ingest`,
  },
  model: {
    metrics: () => `${API_BASE}/api/model/metrics`,
  },
  ws: {
    live: 'ws://localhost:8000/ws/live',
  },
}