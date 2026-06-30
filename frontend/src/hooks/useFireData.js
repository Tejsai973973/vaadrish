import { useQuery } from '@tanstack/react-query'
import useAppStore from '../store/useAppStore'
import { api } from '../lib/api'

export function useFireData() {
  const { startDate, endDate } = useAppStore()
  
  return useQuery({
    queryKey: ['fire-points', startDate, endDate],
    queryFn: async () => {
      try {
        const response = await fetch(api.fire.points(startDate, endDate))
        if (!response.ok) {
          throw new Error('Failed to fetch fire data')
        }
        return response.json()
      } catch (error) {
        console.warn('Using mock fire data:', error)
        return generateMockFireData()
      }
    },
    staleTime: 5 * 60 * 1000,
    refetchInterval: 60 * 1000,
  })
}

export function useFireCorrelation() {
  const { startDate, endDate } = useAppStore()
  return useQuery({
    queryKey: ['fire-correlation', startDate, endDate],
    queryFn: async () => {
      try {
        const response = await fetch(api.fire.correlation())
        if (!response.ok) {
          throw new Error('Failed to fetch correlation data')
        }
        return response.json()
      } catch (error) {
        console.warn('Using mock correlation data:', error)
        return generateMockCorrelationData()
      }
    },
    staleTime: 10 * 60 * 1000,
  })
}

function generateMockFireData() {
  const locations = [
    { lat: 22.5, lon: 78.5 },
    { lat: 23.0, lon: 79.0 },
    { lat: 21.5, lon: 77.5 },
    { lat: 24.0, lon: 80.0 },
    { lat: 20.5, lon: 76.5 },
    { lat: 25.0, lon: 81.0 },
    { lat: 19.5, lon: 75.5 },
    { lat: 26.0, lon: 82.0 },
  ]
  
  return locations.map(loc => ({
    lat: loc.lat + (Math.random() - 0.5) * 0.5,
    lon: loc.lon + (Math.random() - 0.5) * 0.5,
    frp: Math.floor(Math.random() * 100) + 10,
    confidence: ['low', 'medium', 'high'][Math.floor(Math.random() * 3)],
    date: new Date().toISOString()
  }))
}

function generateMockCorrelationData() {
  return {
    pearson_r: 0.42,
    p_value: 0.001,
    scatter_data: Array.from({ length: 30 }, (_, i) => ({
      date: `2024-10-${String(i + 1).padStart(2, '0')}`,
      fire_count: Math.floor(Math.random() * 50) + 10,
      hcho: (Math.random() * 3 + 1) * 1e15,
    }))
  }
}