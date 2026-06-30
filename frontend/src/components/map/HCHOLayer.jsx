import { useEffect } from 'react'
import { useMap } from 'react-leaflet'
import L from 'leaflet'
import { useHCHOSpatial, useHCHOHotspots } from '../../hooks/useHCHOData'
import useAppStore from '../../store/useAppStore'

export default function HCHOLayer() {
  const map = useMap()
  const { mode } = useAppStore()
  const { data: spatialData, isLoading: spatialLoading } = useHCHOSpatial()
  const { data: hotspotsData, isLoading: hotspotsLoading } = useHCHOHotspots()

  useEffect(() => {
    if (!map || mode !== 'HCHO') return
    if (spatialLoading || hotspotsLoading) return
    
    // Clear existing HCHO layers
    map.eachLayer((layer) => {
      if (layer._hchoLayer) {
        map.removeLayer(layer)
      }
    })
    
    const hchoGroup = L.layerGroup().addTo(map)
    hchoGroup._hchoLayer = true

    // Add HCHO spatial data as colored circles
    if (spatialData?.features) {
      spatialData.features.forEach((feature) => {
        const { coordinates } = feature.geometry
        const hcho = feature.properties?.hcho || 0
        const intensity = Math.min(hcho / 5e15, 1)
        
        const color = `rgba(255, 107, 53, ${intensity * 0.8})`
        const radius = 10 + intensity * 30
        
        const circle = L.circle([coordinates[1], coordinates[0]], {
          radius: radius * 1000,
          color: color,
          fillColor: color,
          fillOpacity: 0.6,
          weight: 1,
        })
        
        circle.bindPopup(`
          <div style="color:#333;font-family:sans-serif;padding:4px;">
            <strong>HCHO Detection</strong><br>
            City: ${feature.properties?.city || 'Unknown'}<br>
            HCHO: ${(hcho / 1e15).toFixed(2)} × 10¹⁵ mol/cm²
          </div>
        `)
        
        circle.addTo(hchoGroup)
      })
    }

    // Add HCHO hotspots
    if (hotspotsData && hotspotsData.length > 0) {
      hotspotsData.forEach((hotspot) => {
        const intensity = hotspot.intensity || 0.5
        const color = intensity > 0.7 ? '#FF6B35' : '#FFA86B'
        
        const marker = L.circleMarker([hotspot.lat, hotspot.lon], {
          radius: 8 + intensity * 12,
          color: color,
          fillColor: color,
          fillOpacity: 0.8,
          weight: 2,
          className: 'hcho-hotspot'
        })
        
        marker.bindPopup(`
          <div style="color:#333;font-family:sans-serif;padding:4px;">
            <strong>🔥 HCHO Hotspot</strong><br>
            Intensity: ${(intensity * 100).toFixed(0)}%<br>
            Cluster: ${hotspot.cluster_id || 'N/A'}
          </div>
        `)
        
        marker.addTo(hchoGroup)
      })
    }
    
    return () => {
      map.eachLayer((layer) => {
        if (layer._hchoLayer) {
          map.removeLayer(layer)
        }
      })
    }
  }, [map, mode, spatialData, hotspotsData, spatialLoading, hotspotsLoading])

  if (mode !== 'HCHO') return null
  return null
}