import { LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer, Legend } from 'recharts'
import { useTimeSeries } from '../../hooks/useAQIData'
import useAppStore from '../../store/useAppStore'

export default function TimeSeriesChart() {
  const { selectedCity, startDate, endDate } = useAppStore()
  const { data, isLoading } = useTimeSeries(selectedCity, startDate, endDate)

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full text-slate-500">
        Loading data...
      </div>
    )
  }

  if (!data || !data.dates || data.dates.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-slate-500 text-sm">
        No data available for {selectedCity}
      </div>
    )
  }

  // Format data for Recharts
  const chartData = data.dates.map((date, index) => ({
    date: new Date(date).toLocaleDateString(),
    Satellite: data.satellite[index],
    'Ground Truth': data.ground_truth[index],
  }))

  return (
    <div className="w-full h-full">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-xs text-slate-400 font-space uppercase tracking-wider">
          AQI Time Series — {selectedCity}
        </h3>
        <span className="text-[10px] text-slate-500 font-mono">
          Satellite vs Ground Truth
        </span>
      </div>
      
      <ResponsiveContainer width="100%" height="85%">
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" />
          <XAxis 
            dataKey="date" 
            stroke="#94A3B8" 
            tick={{ fontSize: 10 }}
            interval="preserveStartEnd"
          />
          <YAxis 
            stroke="#94A3B8" 
            tick={{ fontSize: 10 }}
            label={{ 
              value: 'AQI', 
              angle: -90, 
              position: 'insideLeft',
              style: { fill: '#94A3B8', fontSize: 10 }
            }}
          />
          <Tooltip 
            contentStyle={{ 
              background: '#111827', 
              border: '1px solid #FF6B3540',
              borderRadius: '8px',
              padding: '8px 12px'
            }}
            labelStyle={{ color: '#94A3B8', fontSize: 11 }}
            itemStyle={{ fontSize: 11 }}
          />
          <Legend 
            wrapperStyle={{ fontSize: 10 }}
            iconType="circle"
          />
          <Line 
            type="monotone" 
            dataKey="Satellite" 
            stroke="#FF6B35" 
            strokeWidth={2} 
            dot={false}
            activeDot={{ r: 4 }}
          />
          <Line 
            type="monotone" 
            dataKey="Ground Truth" 
            stroke="#00D4FF" 
            strokeWidth={2} 
            dot={false}
            activeDot={{ r: 4 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}