import { useEffect } from 'react'
import { useMap } from 'react-leaflet'
import L from 'leaflet'
import { useAQISpatial } from '../../hooks/useAQIData'

// Custom marker icon for CPCB stations
const stationIcon = L.divIcon({
  html: '📍',
  className: 'station-marker',
  iconSize: [20, 20],
  iconAnchor: [10, 20]
})

export default function StationLayer() {
  const map = useMap()
  const { data, isLoading } = useAQISpatial()
  
  useEffect(() => {
    if (!map || isLoading || !data) return
    
    // Clear existing station markers
    map.eachLayer((layer) => {
      if (layer._stationLayer) {
        map.removeLayer(layer)
      }
    })
    
    // Create a group for station markers
    const stationGroup = L.layerGroup().addTo(map)
    stationGroup._stationLayer = true
    
    // Get stations from data
    let stations = []
    if (data.features) {
      stations = data.features.map(f => ({
        lat: f.geometry.coordinates[1],
        lon: f.geometry.coordinates[0],
        city: f.properties?.city || 'Unknown',
        aqi: f.properties?.aqi || 0,
        category: f.properties?.category || 'Unknown',
        pm25: f.properties?.pm25 || 0,
        no2: f.properties?.no2 || 0,
        so2: f.properties?.so2 || 0,
        co: f.properties?.co || 0,
        o3: f.properties?.o3 || 0,
      }))
    }
    
    // Add markers for each station
    stations.forEach((station) => {
      // Color based on AQI category
      const categoryColors = {
        'Good': '#00E676',
        'Satisfactory': '#AEEA00',
        'Moderate': '#FFD600',
        'Poor': '#FF6D00',
        'Very Poor': '#DD2C00',
        'Severe': '#6A1B9A',
        'Unknown': '#94A3B8'
      }
      
      const color = categoryColors[station.category] || '#94A3B8'
      
      // Create a custom marker with AQI color
      const coloredIcon = L.divIcon({
        html: `<div style="
          width: 12px;
          height: 12px;
          background-color: ${color};
          border-radius: 50%;
          border: 2px solid white;
          box-shadow: 0 0 10px ${color}80;
        "></div>`,
        className: 'aqi-marker',
        iconSize: [12, 12],
        iconAnchor: [6, 6]
      })
      
      const marker = L.marker([station.lat, station.lon], {
        icon: coloredIcon,
        riseOnHover: true
      })
      
      // Add popup with station info
      marker.bindPopup(`
        <div style="color:#333;font-family:sans-serif;padding:8px;min-width:180px;">
          <strong style="font-size:14px;">${station.city}</strong><br>
          <span style="font-size:12px;">📍 CPCB Station</span><br><br>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:4px;font-size:12px;">
            <span><strong>AQI:</strong> ${station.aqi}</span>
            <span><strong>Category:</strong> ${station.category}</span>
            <span><strong>PM2.5:</strong> ${station.pm25} µg/m³</span>
            <span><strong>NO₂:</strong> ${station.no2} ppb</span>
            <span><strong>SO₂:</strong> ${station.so2} ppb</span>
            <span><strong>CO:</strong> ${station.co} ppm</span>
            <span><strong>O₃:</strong> ${station.o3} ppb</span>
          </div>
        </div>
      `)
      
      marker.addTo(stationGroup)
    })
    
    return () => {
      map.eachLayer((layer) => {
        if (layer._stationLayer) {
          map.removeLayer(layer)
        }
      })
    }
  }, [map, data, isLoading])
  
  return null
}