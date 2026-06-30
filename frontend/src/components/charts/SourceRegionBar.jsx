import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'

// Mock data - will be replaced with real API data
const mockData = [
  { region: 'Delhi NCR', aqi: 351 },
  { region: 'UP-East', aqi: 328 },
  { region: 'Punjab', aqi: 308 },
  { region: 'West Bengal', aqi: 323 },
  { region: 'Maharashtra', aqi: 201 },
  { region: 'Tamil Nadu', aqi: 207 },
  { region: 'Karnataka', aqi: 160 },
  { region: 'Rajasthan', aqi: 283 },
]

export default function SourceRegionBar() {
  // Sort by AQI descending
  const sortedData = [...mockData].sort((a, b) => b.aqi - a.aqi)

  return (
    <div className="w-full h-full">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-xs text-slate-400 font-space uppercase tracking-wider">
          Regional AQI
        </h3>
        <span className="text-[10px] text-slate-500 font-mono">
          Top Polluted Regions
        </span>
      </div>
      
      <ResponsiveContainer width="100%" height="85%">
        <BarChart
          data={sortedData}
          layout="vertical"
          margin={{ top: 5, right: 10, left: 10, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" horizontal={false} />
          <XAxis 
            type="number" 
            stroke="#94A3B8" 
            tick={{ fontSize: 10 }}
            domain={[0, 400]}
          />
          <YAxis 
            type="category" 
            dataKey="region" 
            stroke="#94A3B8" 
            tick={{ fontSize: 9 }}
            width={70}
          />
          <Tooltip 
            contentStyle={{ 
              background: '#111827', 
              border: '1px solid #FF6B3540',
              borderRadius: '8px',
              padding: '8px 12px'
            }}
            formatter={(value) => [`${value} AQI`, '']}
            labelStyle={{ color: '#94A3B8', fontSize: 11 }}
          />
          <Bar 
            dataKey="aqi" 
            fill="#FF6B35"
            radius={[0, 4, 4, 0]}
            barSize={20}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}