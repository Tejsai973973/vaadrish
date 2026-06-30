import TimeSeriesChart from '../charts/TimeSeriesChart'
import FireHCHOScatter from '../charts/FireHCHOScatter'
import SourceRegionBar from '../charts/SourceRegionBar'

export default function BottomPanel() {
  return (
    <div className="h-[calc(100%-2rem)]">
      <div className="grid grid-cols-3 gap-4 h-full">
        <div className="bg-[#111827]/50 rounded-lg p-3">
          <TimeSeriesChart />
        </div>
        <div className="bg-[#111827]/50 rounded-lg p-3">
          <FireHCHOScatter />
        </div>
        <div className="bg-[#111827]/50 rounded-lg p-3">
          <SourceRegionBar />
        </div>
      </div>
    </div>
  )
}