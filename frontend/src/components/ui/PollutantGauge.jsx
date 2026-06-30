import { useEffect, useRef } from 'react'

export default function PollutantGauge({ value, label, max = 200, color = '#FF6B35', unit = 'µg/m³' }) {
  const canvasRef = useRef(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    const width = canvas.width
    const height = canvas.height
    const centerX = width / 2
    const centerY = height / 2 - 5
    const radius = Math.min(width, height) / 2 - 18

    // Clear canvas
    ctx.clearRect(0, 0, width, height)

    // Background arc (full circle)
    ctx.beginPath()
    ctx.arc(centerX, centerY, radius, 0, Math.PI * 2)
    ctx.strokeStyle = '#1a1a2e'
    ctx.lineWidth = 6
    ctx.stroke()

    // Value arc (from -90 degrees to +90 degrees)
    const startAngle = -Math.PI / 2
    const endAngle = startAngle + (Math.min(value, max) / max) * Math.PI
    ctx.beginPath()
    ctx.arc(centerX, centerY, radius, startAngle, endAngle)
    ctx.strokeStyle = color
    ctx.lineWidth = 6
    ctx.lineCap = 'round'
    ctx.stroke()

    // Value text
    ctx.fillStyle = '#ffffff'
    ctx.font = 'bold 14px Space Grotesk, sans-serif'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    ctx.fillText(Math.round(value), centerX, centerY - 6)

    // Unit text
    ctx.fillStyle = '#94A3B8'
    ctx.font = '7px JetBrains Mono, monospace'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    ctx.fillText(unit, centerX, centerY + 14)

    // Label text
    ctx.fillStyle = '#94A3B8'
    ctx.font = '8px Inter, sans-serif'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'bottom'
    ctx.fillText(label, centerX, height - 2)
  }, [value, label, max, color, unit])

  return (
    <div className="flex flex-col items-center">
      <canvas
        ref={canvasRef}
        width={70}
        height={85}
        className="w-full h-auto"
      />
    </div>
  )
}