'use client'

import { useEffect, useRef, useState } from 'react'

interface VideoFeedProps {
  className?: string
  width?: number
  height?: number
}

export function VideoFeed({ className = '', width = 640, height = 480 }: VideoFeedProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const startVideoStream = async () => {
      try {
        // Request webcam access
        const stream = await navigator.mediaDevices.getUserMedia({
          video: {
            width: { ideal: width },
            height: { ideal: height },
            facingMode: 'user'
          }
        })

        if (videoRef.current) {
          videoRef.current.srcObject = stream
          setIsStreaming(true)
          setError(null)
        }
      } catch (err) {
        console.error('Error accessing webcam:', err)
        setError('Unable to access webcam. Please check permissions.')
        setIsStreaming(false)
      }
    }

    startVideoStream()

    // Cleanup function
    return () => {
      if (videoRef.current && videoRef.current.srcObject) {
        const stream = videoRef.current.srcObject as MediaStream
        stream.getTracks().forEach(track => track.stop())
      }
    }
  }, [width, height])

  return (
    <div className={`relative ${className}`}>
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        className="w-full h-full object-cover rounded-lg border-2 border-gray-200"
        style={{ width, height }}
      />
      
      {!isStreaming && !error && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-100 rounded-lg">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-2"></div>
            <p className="text-sm text-gray-600">Initializing camera...</p>
          </div>
        </div>
      )}
      
      {error && (
        <div className="absolute inset-0 flex items-center justify-center bg-red-50 rounded-lg border-2 border-red-200">
          <div className="text-center">
            <p className="text-sm text-red-600 mb-2">⚠️ Camera Error</p>
            <p className="text-xs text-red-500">{error}</p>
          </div>
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
    </div>
  )
} 