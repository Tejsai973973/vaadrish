import { ScatterChart, Scatter, XAxis, YAxis, Tooltip, ResponsiveContainer, ZAxis } from 'recharts'
import { useFireCorrelation } from '../../hooks/useFireData'

export default function FireHCHOScatter() {
  const { data, isLoading } = useFireCorrelation()

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full text-slate-500">
        Loading correlation data...
      </div>
    )
  }

  if (!data || !data.scatter_data || data.scatter_data.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-slate-500 text-sm">
        No correlation data available
      </div>
    )
  }

  const scatterData = data.scatter_data.map(item => ({
    x: item.fire_count,
    y: item.hcho,
    date: item.date,
  }))

  return (
    <div className="w-full h-full">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-xs text-slate-400 font-space uppercase tracking-wider">
          Fire vs HCHO Correlation
        </h3>
        <span className="text-[10px] text-slate-500 font-mono">
          R = {data.pearson_r}
        </span>
      </div>
      
      <ResponsiveContainer width="100%" height="85%">
        <ScatterChart>
          <XAxis 
            dataKey="x" 
            stroke="#94A3B8" 
            tick={{ fontSize: 10 }}
            name="Fire Count"
            label={{ 
              value: 'Fire Count', 
              position: 'bottom',
              style: { fill: '#94A3B8', fontSize: 10 }
            }}
          />
          <YAxis 
            dataKey="y" 
            stroke="#94A3B8" 
            tick={{ fontSize: 10 }}
            name="HCHO (mol/cm²)"
            label={{ 
              value: 'HCHO', 
              angle: -90, 
              position: 'insideLeft',
              style: { fill: '#94A3B8', fontSize: 10 }
            }}
          />
          <ZAxis range={[50, 200]} />
          <Tooltip 
            contentStyle={{ 
              background: '#111827', 
              border: '1px solid #FF6B3540',
              borderRadius: '8px'
            }}
            labelFormatter={(_, data) => `Date: ${data[0]?.payload?.date || 'N/A'}`}
          />
          <Scatter 
            data={scatterData} 
            fill="#FF6B35" 
            opacity={0.6}
          />
        </ScatterChart>
      </ResponsiveContainer>
      
      <div className="text-[10px] text-slate-500 font-mono text-center mt-1">
        Pearson R: {data.pearson_r} | p-value: {data.p_value}
      </div>
    </div>
  )
}