'use client'

import { BackendVideoFeed } from './BackendVideoFeed'

interface VideoChatCanvasProps {
  className?: string
  children?: React.ReactNode
}

export function VideoChatCanvas({ className = '', children }: VideoChatCanvasProps) {
  return (
    <div className={`relative ${className}`}>
      {/* Video feed overlay */}
      <div className="absolute top-4 right-4 z-10">
        <div className="bg-white rounded-lg shadow-lg p-2">
          <div className="text-xs text-gray-600 mb-1 text-center">Live Feed</div>
          <BackendVideoFeed width={200} height={150} />
        </div>
      </div>
      
      {/* Chat canvas content */}
      <div className="w-full h-full">
        {children}
      </div>
    </div>
  )
} 