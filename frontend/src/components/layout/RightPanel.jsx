import { useModelMetrics, useNationalSummary, useAQISpatial } from '../../hooks/useAQIData'
import PollutantGauge from '../ui/PollutantGauge'
import CityRankList from '../ui/CityRankList'
import useAppStore from '../../store/useAppStore'

export default function RightPanel() {
  const { data: metrics, isLoading: metricsLoading } = useModelMetrics()
  const { data: summary, isLoading: summaryLoading } = useNationalSummary()
  const { data: spatialData } = useAQISpatial()
  const { liveData } = useAppStore()

  // Get latest city data from multiple sources
  const getCityData = () => {
    // Try to get data from spatial API (most detailed)
    if (spatialData?.features && spatialData.features.length > 0) {
      // Find the city with highest AQI
      let bestCity = null
      let maxAQI = 0
      
      spatialData.features.forEach(feature => {
        const props = feature.properties
        const aqi = props.aqi || props.aqi_predicted || 0
        if (aqi > maxAQI) {
          maxAQI = aqi
          bestCity = {
            aqi: aqi,
            pm25: props.pm25 || props.pm25_predicted || 0,
            no2: props.no2 || 0,
            so2: props.so2 || 0,
            co: props.co || 0,
            o3: props.o3 || 0,
            city: props.city || 'Unknown'
          }
        }
      })
      
      if (bestCity) return bestCity
    }
    
    // Fallback to WebSocket data
    if (liveData?.cities && liveData.cities.length > 0) {
      const city = liveData.cities[0]
      return {
        aqi: city.aqi || city.aqi_predicted || 0,
        pm25: city.pm25 || city.pm25_predicted || 0,
        no2: city.no2 || 0,
        so2: city.so2 || 0,
        co: city.co || 0,
        o3: city.o3 || 0,
        city: city.city || 'Unknown'
      }
    }
    
    // Fallback to summary data
    if (summary?.top_5_polluted && summary.top_5_polluted.length > 0) {
      const city = summary.top_5_polluted[0]
      return {
        aqi: city.aqi || city.aqi_predicted || 0,
        pm25: city.pm25 || 0,
        no2: 0,
        so2: 0,
        co: 0,
        o3: 0,
        city: city.city || 'Unknown'
      }
    }
    
    return null
  }

  const cityData = getCityData()

  const formatNumber = (num) => {
    if (num === undefined || num === null) return '--'
    return Number(num).toFixed(2)
  }

  return (
    <div className="space-y-3">
      <div>
        <h2 className="text-sm font-space font-semibold text-slate-400 uppercase tracking-wider">
          Live Stats
        </h2>
        <div className="h-px w-full bg-gradient-to-r from-transparent via-[#FF6B35]/30 to-transparent my-2" />
      </div>

      {/* National Avg AQI */}
      <div className="bg-[#FF6B35]/10 border border-[#FF6B35]/20 rounded-lg p-3">
        <p className="text-xs text-slate-400 font-mono">National Avg AQI</p>
        <p className="text-2xl font-space font-bold text-[#FF6B35]">
          {summaryLoading ? '...' : summary?.national_avg || 239}
        </p>
        <p className="text-[10px] text-slate-500 mt-0.5">Updated: Live</p>
      </div>

      {/* Pollutant Gauges */}
      <div className="bg-[#111827]/50 rounded-lg p-2">
        <p className="text-xs text-slate-400 font-mono mb-1">
          Pollutant Levels {cityData?.city ? `— ${cityData.city}` : ''}
        </p>
        <div className="grid grid-cols-3 gap-0">
          <PollutantGauge 
            value={cityData?.aqi || 0} 
            label="AQI" 
            max={500} 
            color="#FF6B35"
            unit=""
          />
          <PollutantGauge 
            value={cityData?.pm25 || 0} 
            label="PM2.5" 
            max={300} 
            color="#00D4FF"
            unit="µg/m³"
          />
          <PollutantGauge 
            value={cityData?.no2 || 0} 
            label="NO₂" 
            max={200} 
            color="#7B2FBE"
            unit="ppb"
          />
          <PollutantGauge 
            value={cityData?.so2 || 0} 
            label="SO₂" 
            max={100} 
            color="#FFD600"
            unit="ppb"
          />
          <PollutantGauge 
            value={cityData?.co || 0} 
            label="CO" 
            max={20} 
            color="#FF6B35"
            unit="ppm"
          />
          <PollutantGauge 
            value={cityData?.o3 || 0} 
            label="O₃" 
            max={200} 
            color="#00B4D8"
            unit="ppb"
          />
        </div>
      </div>

      {/* City Rank List */}
      <CityRankList />

      {/* Model Performance */}
      <div className="bg-[#111827]/50 rounded-lg p-3">
        <p className="text-xs text-slate-400 font-mono">Model Performance</p>
        <div className="grid grid-cols-2 gap-2 mt-1">
          <div>
            <p className="text-lg font-space font-bold text-[#00D4FF]">
              {metricsLoading ? '...' : formatNumber(metrics?.r2)}
            </p>
            <p className="text-[10px] text-slate-500">R² Score</p>
          </div>
          <div>
            <p className="text-lg font-space font-bold text-[#00D4FF]">
              {metricsLoading ? '...' : formatNumber(metrics?.rmse)}
            </p>
            <p className="text-[10px] text-slate-500">RMSE</p>
          </div>
        </div>
      </div>
    </div>
  )
}