import { useEffect } from 'react'
import { useMap } from 'react-leaflet'
import L from 'leaflet'

// Mock wind data generator
const generateMockWindData = () => {
  const winds = []
  const cities = [
    { lat: 28.6139, lon: 77.2090 },
    { lat: 19.0760, lon: 72.8777 },
    { lat: 12.9716, lon: 77.5946 },
    { lat: 13.0827, lon: 80.2707 },
    { lat: 22.5726, lon: 88.3639 },
    { lat: 17.3850, lon: 78.4867 },
    { lat: 23.0225, lon: 72.5714 },
    { lat: 18.5204, lon: 73.8567 },
    { lat: 26.9124, lon: 75.7873 },
    { lat: 26.8467, lon: 80.9462 },
  ]
  
  cities.forEach(city => {
    const angle = Math.random() * 360
    const speed = Math.random() * 15 + 5
    winds.push({
      lat: city.lat,
      lon: city.lon,
      angle: angle,
      speed: speed,
      u: speed * Math.cos(angle * Math.PI / 180),
      v: speed * Math.sin(angle * Math.PI / 180),
    })
  })
  
  return winds
}

export default function WindLayer() {
  const map = useMap()

  useEffect(() => {
    if (!map) return

    // Clear existing wind layers
    map.eachLayer((layer) => {
      if (layer._windLayer) {
        map.removeLayer(layer)
      }
    })

    // Create a group for wind vectors
    const windGroup = L.layerGroup().addTo(map)
    windGroup._windLayer = true

    // Get wind data
    const windData = generateMockWindData()

    // Add wind arrows
    windData.forEach((wind) => {
      const angle = wind.angle
      const speed = wind.speed
      
      // Scale arrow length based on speed
      const length = 15 + speed * 2
      const arrowLength = Math.min(length, 40)
      
      // Create arrow path
      const endLat = wind.lat + (Math.sin(angle * Math.PI / 180) * 0.02)
      const endLon = wind.lon + (Math.cos(angle * Math.PI / 180) * 0.02)
      
      // Create a polyline for the arrow
      const arrow = L.polyline(
        [
          [wind.lat, wind.lon],
          [endLat, endLon]
        ],
        {
          color: speed > 10 ? '#FF6B35' : '#00D4FF',
          weight: 2 + speed / 10,
          opacity: 0.7,
          dashArray: null,
        }
      )
      
      // Add arrowhead (triangle at the end)
      const arrowhead = L.polyline(
        [
          [endLat, endLon],
          [endLat - 0.005, endLon - 0.005],
          [endLat - 0.005, endLon + 0.005],
          [endLat, endLon]
        ],
        {
          color: speed > 10 ? '#FF6B35' : '#00D4FF',
          weight: 1.5,
          opacity: 0.7,
          fillColor: speed > 10 ? '#FF6B35' : '#00D4FF',
          fillOpacity: 0.7,
        }
      )
      
      arrow.addTo(windGroup)
      arrowhead.addTo(windGroup)
      
      // Add speed label
      const label = L.marker([wind.lat + 0.005, wind.lon + 0.005], {
        icon: L.divIcon({
          html: `<span style="color: #94A3B8; font-size: 8px; font-family: monospace;">${Math.round(speed)} km/h</span>`,
          className: 'wind-label',
          iconSize: [30, 12],
          iconAnchor: [15, 6],
        })
      })
      label.addTo(windGroup)
    })

    return () => {
      map.eachLayer((layer) => {
        if (layer._windLayer) {
          map.removeLayer(layer)
        }
      })
    }
  }, [map])

  return null
}