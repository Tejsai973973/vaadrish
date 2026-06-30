import { useEffect } from 'react'
import { useMap } from 'react-leaflet'
import L from 'leaflet'

// Mock source regions data
const generateMockRegions = () => {
  return [
    { 
      name: 'Industrial Zone - Delhi NCR',
      lat: 28.6139, 
      lon: 77.2090,
      radius: 1.2,
      color: '#FF6B35',
      pollutant: 'PM2.5',
      level: 'High'
    },
    { 
      name: 'Industrial Zone - Mumbai',
      lat: 19.0760, 
      lon: 72.8777,
      radius: 1.0,
      color: '#FF8A50',
      pollutant: 'NO₂',
      level: 'Medium'
    },
    { 
      name: 'Industrial Zone - Kolkata',
      lat: 22.5726, 
      lon: 88.3639,
      radius: 0.8,
      color: '#DD2C00',
      pollutant: 'SO₂',
      level: 'High'
    },
    { 
      name: 'Thermal Power - Uttar Pradesh',
      lat: 26.8467, 
      lon: 80.9462,
      radius: 1.5,
      color: '#6A1B9A',
      pollutant: 'CO₂',
      level: 'Severe'
    },
    { 
      name: 'Agricultural Burning - Punjab',
      lat: 30.7333, 
      lon: 76.7794,
      radius: 1.3,
      color: '#FFD600',
      pollutant: 'PM10',
      level: 'High'
    },
    { 
      name: 'Industrial Hub - Chennai',
      lat: 13.0827, 
      lon: 80.2707,
      radius: 0.7,
      color: '#FF6D00',
      pollutant: 'O₃',
      level: 'Medium'
    },
    { 
      name: 'Mining Region - Jharkhand',
      lat: 23.3441, 
      lon: 85.3096,
      radius: 0.9,
      color: '#7B2FBE',
      pollutant: 'Heavy Metals',
      level: 'High'
    },
  ]
}

export default function SourceRegionLayer() {
  const map = useMap()

  useEffect(() => {
    if (!map) return

    // Clear existing source region layers
    map.eachLayer((layer) => {
      if (layer._sourceRegionLayer) {
        map.removeLayer(layer)
      }
    })

    // Create a group for source regions
    const regionGroup = L.layerGroup().addTo(map)
    regionGroup._sourceRegionLayer = true

    // Get region data
    const regions = generateMockRegions()

    // Add region circles with labels
    regions.forEach((region) => {
      // Create circle for region
      const circle = L.circle([region.lat, region.lon], {
        radius: region.radius * 50000,
        color: region.color,
        fillColor: region.color,
        fillOpacity: 0.15,
        weight: 2,
        opacity: 0.6,
        dashArray: '5, 5',
      })
      
      // Add popup with region info
      circle.bindPopup(`
        <div style="color:#333;font-family:sans-serif;padding:8px;min-width:160px;">
          <strong style="font-size:14px;">${region.name}</strong><br>
          <span style="font-size:12px;">📍 Source Region</span><br><br>
          <div style="font-size:12px;">
            <span><strong>Pollutant:</strong> ${region.pollutant}</span><br>
            <span><strong>Level:</strong> ${region.level}</span><br>
          </div>
        </div>
      `)
      
      circle.addTo(regionGroup)
      
      // Add label for region
      const label = L.marker([region.lat - 0.3, region.lon], {
        icon: L.divIcon({
          html: `<span style="
            color: white; 
            font-size: 9px; 
            font-family: 'Space Grotesk', sans-serif;
            background: rgba(0,0,0,0.7);
            padding: 2px 8px;
            border-radius: 4px;
            border-left: 2px solid ${region.color};
            white-space: nowrap;
          ">${region.name}</span>`,
          className: 'region-label',
          iconSize: [120, 20],
          iconAnchor: [60, 10],
        })
      })
      label.addTo(regionGroup)
    })

    return () => {
      map.eachLayer((layer) => {
        if (layer._sourceRegionLayer) {
          map.removeLayer(layer)
        }
      })
    }
  }, [map])

  return null
}