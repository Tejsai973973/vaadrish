import { useEffect } from 'react'
import { useMap } from 'react-leaflet'
import L from 'leaflet'
import { useFireData } from '../../hooks/useFireData'

// Custom fire icon
const fireIcon = L.divIcon({
  html: '🔥',
  className: 'fire-marker',
  iconSize: [24, 24],
  iconAnchor: [12, 12]
})

export default function FireLayer() {
  const map = useMap()
  const { data, isLoading } = useFireData()
  
  useEffect(() => {
    if (!map || isLoading || !data) return
    
    // Clear existing fire markers
    map.eachLayer((layer) => {
      if (layer._fireLayer) {
        map.removeLayer(layer)
      }
    })
    
    // Create a group for fire markers
    const fireGroup = L.layerGroup().addTo(map)
    fireGroup._fireLayer = true
    
    // Get fire points from data
    let fires = []
    if (Array.isArray(data)) {
      fires = data
    } else if (data.features) {
      fires = data.features.map(f => ({
        lat: f.geometry.coordinates[1],
        lon: f.geometry.coordinates[0],
        frp: f.properties?.frp || 0,
        confidence: f.properties?.confidence || 'medium'
      }))
    }
    
    // Add markers for each fire
    fires.forEach((fire) => {
      const marker = L.marker([fire.lat, fire.lon], {
        icon: fireIcon,
        riseOnHover: true
      })
      
      // Add popup with fire info
      marker.bindPopup(`
        <div style="color:#333;font-family:sans-serif;padding:4px;">
          <strong>🔥 Fire Detected</strong><br>
          FRP: ${fire.frp || 'N/A'}<br>
          Confidence: ${fire.confidence || 'medium'}<br>
          ${new Date().toLocaleString()}
        </div>
      `)
      
      marker.addTo(fireGroup)
    })
    
    return () => {
      map.eachLayer((layer) => {
        if (layer._fireLayer) {
          map.removeLayer(layer)
        }
      })
    }
  }, [map, data, isLoading])
  
  return null
}