import { create } from 'zustand'

const useAppStore = create((set) => ({
  // Mode
  mode: 'AQI',
  setMode: (mode) => set({ mode }),
  
  // Date range
  startDate: '2024-10-01',
  endDate: '2024-11-30',
  setDateRange: (start, end) => set({ startDate: start, endDate: end }),
  
  // Selected city
  selectedCity: 'Delhi',
  setSelectedCity: (city) => set({ selectedCity: city }),
  
  // Map layers
  layers: {
    aqiHeatmap: true,
    firePoints: true,
    cpcbStations: true,
    windVectors: false,
    hchoColumn: false,
    sourceRegions: false,
  },
  toggleLayer: (layer) =>
    set((s) => ({ layers: { ...s.layers, [layer]: !s.layers[layer] } })),
  
  // WebSocket live data
  liveData: null,
  lastUpdated: null,
  wsConnected: false,
  setLiveData: (data) => set({ liveData: data, lastUpdated: new Date() }),
  setWsConnected: (v) => set({ wsConnected: v }),
}))

export default useAppStore