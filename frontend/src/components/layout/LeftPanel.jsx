import useAppStore from '../../store/useAppStore'

export default function LeftPanel() {
  const { layers, toggleLayer } = useAppStore()
  
  return (
    <div>
      <h2 className="text-sm font-space font-semibold text-slate-400 uppercase tracking-wider">
        Controls
      </h2>
      <div className="h-px w-full bg-gradient-to-r from-transparent via-[#FF6B35]/30 to-transparent my-3" />
      
      <div className="space-y-3">
        <p className="text-sm text-slate-300 font-space">Map Layers</p>
        
        {Object.entries(layers).map(([key, value]) => (
          <label key={key} className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={value}
              onChange={() => toggleLayer(key)}
              className="w-4 h-4 accent-[#FF6B35]"
            />
            <span className="text-sm text-slate-400 font-inter capitalize">
              {key.replace(/([A-Z])/g, ' $1').trim()}
            </span>
          </label>
        ))}
      </div>
    </div>
  )
}