import { useQuery } from '@tanstack/react-query'
import useAppStore from '../store/useAppStore'
import { api } from '../lib/api'

export function useAQISpatial() {
  const { startDate } = useAppStore()
  return useQuery({
    queryKey: ['aqi-spatial', startDate],
    queryFn: async () => {
      try {
        const response = await fetch(api.aqi.spatial(startDate))
        if (!response.ok) {
          throw new Error('Failed to fetch AQI data')
        }
        return response.json()
      } catch (error) {
        console.warn('Using mock AQI data:', error)
        return generateMockAQIData()
      }
    },
    staleTime: 0,
    refetchInterval: 60 * 1000,
  })
}

export function useModelMetrics() {
  return useQuery({
    queryKey: ['model-metrics'],
    queryFn: async () => {
      const response = await fetch(api.model.metrics())
      if (!response.ok) return null
      return response.json()
    },
    staleTime: Infinity,
  })
}

export function useTimeSeries(city, start, end) {
  return useQuery({
    queryKey: ['timeseries', city, start, end],
    queryFn: async () => {
      try {
        const response = await fetch(api.aqi.timeseries(city, start, end))
        if (!response.ok) {
          throw new Error('Failed to fetch time series')
        }
        return response.json()
      } catch (error) {
        console.warn('Using mock time series data:', error)
        const dates = []
        const satellite = []
        const ground_truth = []
        const startDate = new Date(start)
        const endDate = new Date(end)
        
        for (let d = new Date(startDate); d <= endDate; d.setDate(d.getDate() + 5)) {
          dates.push(d.toISOString().split('T')[0])
          satellite.push(Math.floor(Math.random() * 200) + 50)
          ground_truth.push(Math.floor(Math.random() * 200) + 50)
        }
        
        return { dates, satellite, ground_truth }
      }
    },
    staleTime: 0,
  })
}

export function useNationalSummary() {
  const { startDate } = useAppStore()
  return useQuery({
    queryKey: ['national-summary', startDate],
    queryFn: async () => {
      try {
        const response = await fetch(api.aqi.summary(startDate))
        if (!response.ok) {
          throw new Error('Failed to fetch national summary')
        }
        return response.json()
      } catch (error) {
        console.warn('Using mock national summary:', error)
        return {
          national_avg: 239,
          max_aqi: 394,
          min_aqi: 65,
          top_5_polluted: [
            { city: 'Kanpur', aqi_predicted: 394, category: 'Very Poor' },
            { city: 'Faridabad', aqi_predicted: 379, category: 'Very Poor' },
            { city: 'Ghaziabad', aqi_predicted: 376, category: 'Very Poor' },
            { city: 'Gurgaon', aqi_predicted: 365, category: 'Very Poor' },
            { city: 'Varanasi', aqi_predicted: 358, category: 'Very Poor' },
          ],
          category_counts: { 'Very Poor': 20, 'Poor': 15, 'Moderate': 10, 'Satisfactory': 8 }
        }
      }
    },
    staleTime: 0,
  })
}

// Mock data generator for testing
function generateMockAQIData() {
  const cities = [
    { name: 'Delhi', lat: 28.6139, lon: 77.2090 },
    { name: 'Mumbai', lat: 19.0760, lon: 72.8777 },
    { name: 'Bangalore', lat: 12.9716, lon: 77.5946 },
    { name: 'Chennai', lat: 13.0827, lon: 80.2707 },
    { name: 'Kolkata', lat: 22.5726, lon: 88.3639 },
    { name: 'Hyderabad', lat: 17.3850, lon: 78.4867 },
    { name: 'Ahmedabad', lat: 23.0225, lon: 72.5714 },
    { name: 'Pune', lat: 18.5204, lon: 73.8567 },
    { name: 'Jaipur', lat: 26.9124, lon: 75.7873 },
    { name: 'Lucknow', lat: 26.8467, lon: 80.9462 },
  ]
  
  return {
    features: cities.map(city => ({
      type: 'Feature',
      geometry: {
        type: 'Point',
        coordinates: [city.lon, city.lat]
      },
      properties: {
        city: city.name,
        aqi: Math.floor(Math.random() * 200) + 50,
        category: ['Good', 'Satisfactory', 'Moderate', 'Poor'][Math.floor(Math.random() * 4)]
      }
    }))
  }
}