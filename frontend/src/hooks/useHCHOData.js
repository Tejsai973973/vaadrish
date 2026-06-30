import { useQuery } from '@tanstack/react-query'
import useAppStore from '../store/useAppStore'
import { api } from '../lib/api'

export function useHCHOSpatial() {
  const { startDate } = useAppStore()
  return useQuery({
    queryKey: ['hcho-spatial', startDate],
    queryFn: async () => {
      try {
        const response = await fetch(api.hcho.spatial(startDate))
        if (!response.ok) {
          throw new Error('Failed to fetch HCHO data')
        }
        return response.json()
      } catch (error) {
        console.warn('Falling back to mock HCHO data:', error)
        return generateMockHCHOData()
      }
    },
    staleTime: 5 * 60 * 1000,
    refetchInterval: 60 * 1000,
  })
}

export function useHCHOHotspots() {
  const { startDate } = useAppStore()
  return useQuery({
    queryKey: ['hcho-hotspots', startDate],
    queryFn: async () => {
      try {
        const response = await fetch(api.hcho.hotspots(startDate))
        if (!response.ok) {
          throw new Error('Failed to fetch HCHO hotspots')
        }
        return response.json()
      } catch (error) {
        console.warn('Falling back to mock HCHO hotspots:', error)
        return generateMockHCHOHotspots()
      }
    },
    staleTime: 5 * 60 * 1000,
  })
}

// Mock data generators (fallback when API fails)
function generateMockHCHOData() {
  const cities = [
    { name: 'Delhi', lat: 28.6139, lon: 77.2090, hcho: 3.2e15 },
    { name: 'Mumbai', lat: 19.0760, lon: 72.8777, hcho: 2.5e15 },
    { name: 'Bangalore', lat: 12.9716, lon: 77.5946, hcho: 1.8e15 },
    { name: 'Chennai', lat: 13.0827, lon: 80.2707, hcho: 2.0e15 },
    { name: 'Kolkata', lat: 22.5726, lon: 88.3639, hcho: 2.8e15 },
    { name: 'Hyderabad', lat: 17.3850, lon: 78.4867, hcho: 2.2e15 },
    { name: 'Ahmedabad', lat: 23.0225, lon: 72.5714, hcho: 2.4e15 },
    { name: 'Pune', lat: 18.5204, lon: 73.8567, hcho: 1.9e15 },
    { name: 'Jaipur', lat: 26.9124, lon: 75.7873, hcho: 2.1e15 },
    { name: 'Lucknow', lat: 26.8467, lon: 80.9462, hcho: 2.6e15 },
  ]
  
  return {
    type: 'FeatureCollection',
    features: cities.map(city => ({
      type: 'Feature',
      geometry: {
        type: 'Point',
        coordinates: [city.lon, city.lat]
      },
      properties: {
        city: city.name,
        hcho: city.hcho,
        hcho_formatted: (city.hcho / 1e15).toFixed(2),
      }
    }))
  }
}

function generateMockHCHOHotspots() {
  return [
    { lat: 28.6139, lon: 77.2090, intensity: 0.85, cluster_id: 1 },
    { lat: 28.5, lon: 77.3, intensity: 0.75, cluster_id: 1 },
    { lat: 28.7, lon: 77.1, intensity: 0.70, cluster_id: 1 },
    { lat: 19.0760, lon: 72.8777, intensity: 0.65, cluster_id: 2 },
    { lat: 19.2, lon: 72.9, intensity: 0.55, cluster_id: 2 },
    { lat: 22.5726, lon: 88.3639, intensity: 0.70, cluster_id: 3 },
    { lat: 22.6, lon: 88.4, intensity: 0.60, cluster_id: 3 },
    { lat: 26.8467, lon: 80.9462, intensity: 0.80, cluster_id: 4 },
    { lat: 26.9, lon: 80.9, intensity: 0.70, cluster_id: 4 },
    { lat: 17.3850, lon: 78.4867, intensity: 0.50, cluster_id: 5 },
  ]
}