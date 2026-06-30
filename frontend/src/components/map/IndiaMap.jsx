import { MapContainer, TileLayer } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import useAppStore from '../../store/useAppStore'
import AQIHeatLayer from './AQIHeatLayer'
import FireLayer from './FireLayer'
import StationLayer from './StationLayer'
import HCHOLayer from './HCHOLayer'
import WindLayer from './WindLayer'
import SourceRegionLayer from './SourceRegionLayer'

const INDIA_CENTER = [22.5, 82.0]
const INDIA_BOUNDS = [[6, 68], [37, 97]]
const DARK_TILE = 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png'

export default function IndiaMap() {
  const { layers } = useAppStore()

  return (
    <MapContainer
      center={INDIA_CENTER}
      zoom={5}
      maxBounds={INDIA_BOUNDS}
      className="w-full h-full"
      zoomControl={false}
    >
      <TileLayer url={DARK_TILE} attribution="©CartoDB" />
      
      {layers.aqiHeatmap && <AQIHeatLayer />}
      {layers.firePoints && <FireLayer />}
      {layers.cpcbStations && <StationLayer />}
      {layers.hchoColumn && <HCHOLayer />}
      {layers.windVectors && <WindLayer />}
      {layers.sourceRegions && <SourceRegionLayer />}
    </MapContainer>
  )
}