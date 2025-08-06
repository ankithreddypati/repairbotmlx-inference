'use client'

import { useEffect, useRef, useState } from 'react'

interface BackendVideoFeedProps {
  className?: string
  width?: number
  height?: number
  autoStart?: boolean
}

export function BackendVideoFeed({ 
  className = '', 
  width = 1280, 
  height = 720,
  autoStart = true 
}: BackendVideoFeedProps) {
  const imgRef = useRef<HTMLImageElement>(null)
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [status, setStatus] = useState<any>(null)

  useEffect(() => {
    if (!autoStart) return

    const checkStatus = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/video/status')
        if (response.ok) {
          const data = await response.json()
          setStatus(data)
          if (data.webcam_available) {
            startStream()
          } else {
            setError('Webcam not available on backend')
          }
        } else {
          setError('Backend video service unavailable')
        }
      } catch (err) {
        console.error('Error checking video status:', err)
        setError('Cannot connect to backend video service')
      }
    }

    const startStream = () => {
      if (imgRef.current) {
        imgRef.current.src = 'http://localhost:8000/api/video/stream'
        setIsStreaming(true)
        setError(null)
      }
    }

    checkStatus()

    return () => {
      if (imgRef.current) {
        imgRef.current.src = ''
      }
    }
  }, [autoStart])

  // Add error boundary for network issues
  useEffect(() => {
    const handleOnline = () => {
      if (error && error.includes('connect')) {
        setError(null)
        // Retry connection
        setTimeout(() => {
          if (imgRef.current) {
            imgRef.current.src = 'http://localhost:8000/api/video/stream'
          }
        }, 1000)
      }
    }

    window.addEventListener('online', handleOnline)
    return () => window.removeEventListener('online', handleOnline)
  }, [error])

  const handleImageLoad = () => {
    setIsStreaming(true)
    setError(null)
  }

  const handleImageError = () => {
    setIsStreaming(false)
    setError('Failed to load video stream')
  }

  const startStream = () => {
    if (imgRef.current) {
      imgRef.current.src = 'http://localhost:8000/api/video/stream'
    }
  }

  const stopStream = () => {
    if (imgRef.current) {
      imgRef.current.src = ''
      setIsStreaming(false)
    }
  }

  return (
    <div className={`relative ${className}`}>
      <img
        ref={imgRef}
        onLoad={handleImageLoad}
        onError={handleImageError}
        className="w-full h-full object-cover rounded-lg border-2 border-gray-200"
        style={{ width, height }}
        alt="Backend video feed"
      />
      
      {!isStreaming && !error && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-100 rounded-lg">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-2"></div>
            <p className="text-sm text-gray-600">Connecting to backend...</p>
          </div>
        </div>
      )}
      
      {error && (
        <div className="absolute inset-0 flex items-center justify-center bg-red-50 rounded-lg border-2 border-red-200">
          <div className="text-center">
            <p className="text-sm text-red-600 mb-2">⚠️ Connection Error</p>
            <p className="text-xs text-red-500">{error}</p>
          </div>
          {/* Small round retry button */}
          <button
            onClick={startStream}
            className="absolute top-2 right-2 w-8 h-8 bg-blue-500 hover:bg-blue-600 text-white rounded-full flex items-center justify-center shadow-lg transition-colors"
            title="Retry connection"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>
        </div>
      )}
      
      {isStreaming && (
        <div className="absolute top-2 right-2">
          <div className="flex items-center space-x-1 bg-green-500 text-white px-2 py-1 rounded-full text-xs">
            <div className="w-2 h-2 bg-white rounded-full animate-pulse"></div>
            <span>Live</span>
          </div>
        </div>
      )}

      {status && (
        <div className="absolute bottom-2 left-2">
          <div className="bg-black bg-opacity-50 text-white px-2 py-1 rounded text-xs">
            {status.resolution && (
              <span>{status.resolution.width}x{status.resolution.height} @ {status.resolution.fps}fps</span>
            )}
          </div>
        </div>
      )}
    </div>
  )
} 