import { Activity } from 'lucide-react'
import useAppStore from '../../store/useAppStore'

export default function Navbar() {
  const { wsConnected, mode, setMode, liveData } = useAppStore()
  
  return (
    <nav className="h-16 px-6 glass-card m-2 mb-0 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <Activity className="text-[#FF6B35]" size={28} />
        <h1 className="text-xl font-space font-bold text-white">
          Vaadrish
        </h1>
      </div>
      
      <div className="flex items-center gap-4">
        {/* Live Indicator */}
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-green-400 animate-pulse' : 'bg-red-500'}`} />
          <span className="text-xs text-slate-400 font-mono">
            {wsConnected ? 'LIVE' : 'OFFLINE'}
          </span>
        </div>
        
        {/* Mode Toggle */}
        <div className="flex rounded-lg border border-[#FF6B35]/40 p-0.5 gap-0.5">
          {['AQI', 'HCHO'].map(m => (
            <button 
              key={m}
              onClick={() => setMode(m)}
              className={`px-4 py-1.5 rounded-md text-sm font-space font-medium transition-all duration-300
                ${mode === m 
                  ? 'bg-[#FF6B35] text-white shadow-[0_0_12px_rgba(255,107,53,0.4)]' 
                  : 'text-slate-400 hover:text-white'}`}
            >
              {m}
            </button>
          ))}
        </div>
      </div>
    </nav>
  )
}