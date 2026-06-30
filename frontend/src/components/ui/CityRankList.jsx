import { useAQISpatial } from '../../hooks/useAQIData'

export default function CityRankList() {
  const { data: spatialData, isLoading } = useAQISpatial()
  
  // Extract cities from spatial data and deduplicate
  const getCities = () => {
    if (!spatialData?.features) return []
    
    // Create a map to deduplicate cities (keep highest AQI for each city)
    const cityMap = new Map()
    
    spatialData.features.forEach(feature => {
      const props = feature.properties
      const cityName = props.city || 'Unknown'
      const aqi = props.aqi || props.aqi_predicted || 0
      const category = props.category || 'Unknown'
      
      // Keep the highest AQI for each city
      if (!cityMap.has(cityName) || cityMap.get(cityName).aqi < aqi) {
        cityMap.set(cityName, { city: cityName, aqi, category })
      }
    })
    
    // Convert map to array and sort by AQI descending
    return Array.from(cityMap.values())
      .filter(city => city.aqi > 0)
      .sort((a, b) => b.aqi - a.aqi)
      .slice(0, 10) // Top 10 unique cities
  }

  const cities = getCities()

  const getCategoryColor = (category) => {
    const colors = {
      'Good': 'text-aqi-good',
      'Satisfactory': 'text-aqi-sat',
      'Moderate': 'text-aqi-mod',
      'Poor': 'text-aqi-poor',
      'Very Poor': 'text-aqi-vpoor',
      'Severe': 'text-aqi-severe',
    }
    return colors[category] || 'text-slate-400'
  }

  const getCategoryColorHex = (category) => {
    const colors = {
      'Good': '#00E676',
      'Satisfactory': '#AEEA00',
      'Moderate': '#FFD600',
      'Poor': '#FF6D00',
      'Very Poor': '#DD2C00',
      'Severe': '#6A1B9A',
    }
    return colors[category] || '#94A3B8'
  }

  const maxAQI = cities.length > 0 ? Math.max(...cities.map(c => c.aqi || 0), 400) : 400

  if (isLoading) {
    return (
      <div className="bg-[#111827]/50 rounded-lg p-4">
        <p className="text-xs text-slate-400 font-mono mb-3">Top Polluted Cities</p>
        <div className="flex items-center justify-center h-24 text-slate-500 text-sm">
          Loading...
        </div>
      </div>
    )
  }

  if (cities.length === 0) {
    return (
      <div className="bg-[#111827]/50 rounded-lg p-4">
        <p className="text-xs text-slate-400 font-mono mb-3">Top Polluted Cities</p>
        <div className="flex items-center justify-center h-24 text-slate-500 text-sm">
          No data available
        </div>
      </div>
    )
  }

  return (
    <div className="bg-[#111827]/50 rounded-lg p-4">
      <p className="text-xs text-slate-400 font-mono mb-3">Top Polluted Cities</p>
      <div className="space-y-2">
        {cities.slice(0, 5).map((city, index) => {
          const aqi = city.aqi || 0
          const barWidth = Math.min((aqi / maxAQI) * 100, 100)
          const color = getCategoryColorHex(city.category)
          
          return (
            <div key={index} className="flex items-center gap-2">
              <span className="text-xs text-slate-500 font-mono w-6 text-right">
                #{index + 1}
              </span>
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium text-white truncate max-w-[100px]">
                    {city.city}
                  </span>
                  <span className={`text-xs font-mono ${getCategoryColor(city.category)}`}>
                    {aqi}
                  </span>
                </div>
                <div className="w-full h-1 bg-[#1a1a2e] rounded-full overflow-hidden mt-0.5">
                  <div 
                    className="h-full rounded-full transition-all duration-500"
                    style={{ 
                      width: `${barWidth}%`,
                      backgroundColor: color
                    }}
                  />
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}