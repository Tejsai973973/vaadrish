import { useEffect } from 'react'
import { useMap } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet.heat'
import { useAQISpatial } from '../../hooks/useAQIData'

export default function AQIHeatLayer() {
  const map = useMap()
  const { data, isLoading, error } = useAQISpatial()
  
  useEffect(() => {
    if (!map || isLoading || !data) return
    
    // Clear existing heatmap layers
    map.eachLayer((layer) => {
      if (layer._heat) {
        map.removeLayer(layer)
      }
    })
    
    // Convert data to heatmap format: [lat, lon, intensity]
    const points = []
    
    // Check if data is GeoJSON or array
    if (data.features) {
      // GeoJSON format
      data.features.forEach((feature) => {
        const { coordinates } = feature.geometry
        const aqi = feature.properties?.aqi || feature.properties?.aqi_predicted || 50
        // Intensity: AQI / 500 (max AQI)
        const intensity = Math.min(aqi / 500, 1)
        points.push([coordinates[1], coordinates[0], intensity])
      })
    } else if (Array.isArray(data)) {
      // Array format
      data.forEach((item) => {
        const intensity = Math.min((item.aqi || 50) / 500, 1)
        points.push([item.lat, item.lon, intensity])
      })
    }
    
    // Only add heatmap if there are points
    if (points.length === 0) return
    
    // Add heatmap to map
    const heat = L.heatLayer(points, {
      radius: 25,
      blur: 15,
      maxZoom: 10,
      minOpacity: 0.3,
      gradient: {
        0.0: '#00E676',   // Good - Green
        0.2: '#AEEA00',   // Satisfactory - Light Green
        0.4: '#FFD600',   // Moderate - Yellow
        0.6: '#FF6D00',   // Poor - Orange
        0.8: '#DD2C00',   // Very Poor - Dark Orange
        1.0: '#6A1B9A'    // Severe - Purple
      }
    })
    
    heat.addTo(map)
    // Mark this layer as a heat layer for cleanup
    heat._heat = true
    
    return () => {
      map.eachLayer((layer) => {
        if (layer._heat) {
          map.removeLayer(layer)
        }
      })
    }
  }, [map, data, isLoading]) // ← Data is in dependencies, so it updates when date changes
  
  if (isLoading) return null
  if (error) {
    console.error('Error loading AQI heatmap:', error)
    return null
  }
  
  return null
}