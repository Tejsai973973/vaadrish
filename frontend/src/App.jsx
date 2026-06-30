import Navbar from './components/layout/Navbar'
import LeftPanel from './components/layout/LeftPanel'
import RightPanel from './components/layout/RightPanel'
import IndiaMap from './components/map/IndiaMap'
import BottomPanel from './components/panels/BottomPanel'
import CitySearch from './components/ui/CitySearch'
import useWebSocket from './hooks/useWebSocket'

function App() {
  useWebSocket()
  
  return (
    <div className="h-screen w-screen bg-[#050810] flex flex-col overflow-hidden">
      <Navbar />
      
      <div className="flex flex-1 overflow-hidden">
        <aside className="w-[280px] shrink-0 glass-card m-2 mr-0 overflow-y-auto p-4">
          <LeftPanel />
        </aside>
        
        <main className="flex-1 relative m-2 mx-0 glass-card overflow-hidden">
          <IndiaMap />
        </main>
        
        <aside className="w-[320px] shrink-0 glass-card m-2 ml-0 overflow-y-auto p-4">
          <RightPanel />
        </aside>
      </div>
      
      <section className="h-[260px] shrink-0 glass-card m-2 mt-0 p-4">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-sm font-space font-semibold text-slate-400 uppercase tracking-wider">
            Analysis Charts
          </h2>
          <div className="flex items-center gap-3">
            <span className="text-xs text-slate-400 font-mono">City:</span>
            <CitySearch />
          </div>
        </div>
        <BottomPanel />
      </section>
    </div>
  )
}

export default App