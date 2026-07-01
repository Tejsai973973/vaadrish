import { useEffect, useRef } from 'react'
import useAppStore from '../store/useAppStore'

export default function useWebSocket() {
  const setLiveData = useAppStore((state) => state.setLiveData)
  const setWsConnected = useAppStore((state) => state.setWsConnected)
  const ws = useRef(null)
  const reconnectTimeout = useRef(null)
  const isMounted = useRef(true)

  useEffect(() => {
    isMounted.current = true

    const connectWebSocket = () => {
      // Don't connect if component unmounted
      if (!isMounted.current) return

      try {
        // Close existing connection
        if (ws.current?.readyState === WebSocket.OPEN || 
            ws.current?.readyState === WebSocket.CONNECTING) {
          ws.current.close()
        }

        // Create new connection
        ws.current = new WebSocket('ws://localhost:8001/ws/live')

        ws.current.onopen = () => {
          if (isMounted.current) {
            setWsConnected(true)
            console.log('🔗 WebSocket connected')
          }
        }

        ws.current.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            console.log('📡 Live data received:', data)
            if (isMounted.current) {
              setLiveData(data)
            }
          } catch (error) {
            console.error('Error parsing WebSocket message:', error)
          }
        }

        ws.current.onclose = () => {
          if (isMounted.current) {
            setWsConnected(false)
            console.log('🔌 WebSocket disconnected')
          }
          
          // Clear any existing reconnect timeout
          if (reconnectTimeout.current) {
            clearTimeout(reconnectTimeout.current)
          }
          
          // Auto-reconnect after 5 seconds (only if mounted)
          reconnectTimeout.current = setTimeout(() => {
            if (isMounted.current) {
              console.log('🔄 Attempting to reconnect...')
              connectWebSocket()
            }
          }, 5000)
        }

        ws.current.onerror = (error) => {
          console.error('WebSocket error:', error)
          // Close the connection on error to trigger reconnect
          ws.current?.close()
        }
      } catch (error) {
        console.error('Failed to create WebSocket:', error)
      }
    }

    // Connect when component mounts
    connectWebSocket()

    // Cleanup on unmount
    return () => {
      isMounted.current = false
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current)
      }
      if (ws.current) {
        ws.current.close()
      }
    }
  }, []) // Empty dependency array = run once

  // Return connection status
  return { 
    wsConnected: ws.current?.readyState === WebSocket.OPEN 
  }
}