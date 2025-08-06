// components/HiddenAudioPlayer.tsx - Plays IMMEDIATELY with text
'use client'

import { useEffect, useRef, useState } from 'react'

interface AudioChunk {
  audio_data: string
  chunk_index?: number
  is_final: boolean
  text: string
  duration: number
}

interface HiddenAudioPlayerProps {
  audioChunks: AudioChunk[]
  onPlay?: () => void
  onEnd?: () => void
  autoPlay?: boolean
}

export function HiddenAudioPlayer({
  audioChunks,
  onPlay,
  onEnd,
  autoPlay = true
}: HiddenAudioPlayerProps) {
  const audioRef = useRef<HTMLAudioElement>(null)
  const [playedChunkIds, setPlayedChunkIds] = useState<string[]>([])

  useEffect(() => {
    if (audioChunks.length > 0 && autoPlay) {
      const chunk = audioChunks[0]
      const chunkId = `${chunk.text}_${chunk.duration}` // Unique ID for this chunk
      
      // Only play if we haven't played this exact chunk before
      if (!playedChunkIds.includes(chunkId)) {
        console.log('🔊 Playing NEW audio chunk:', chunk.text)
        setPlayedChunkIds(prev => [...prev, chunkId])
        
        try {
          const audioBlob = base64ToBlob(chunk.audio_data, 'audio/wav')
          const audioUrl = URL.createObjectURL(audioBlob)
          
          if (audioRef.current) {
            audioRef.current.src = audioUrl
            
            audioRef.current.play()
              .then(() => {
                console.log(' Audio playing')
                onPlay?.()
              })
              .catch(err => {
                console.error(' Audio play failed:', err)
              })
          }
          
          // Cleanup
          return () => URL.revokeObjectURL(audioUrl)
          
        } catch (error) {
          console.error(' Audio error:', error)
        }
      } else {
        console.log('🔇 Skipping already played chunk:', chunk.text)
      }
    }
  }, [audioChunks, autoPlay, onPlay, playedChunkIds])

  const base64ToBlob = (base64: string, mimeType: string): Blob => {
    try {
      // Remove data URL prefix if present
      const cleanBase64 = base64.replace(/^data:audio\/[^;]+;base64,/, '')
      
      // Decode base64 - browser compatible
      const byteString = window.atob(cleanBase64)
      const arrayBuffer = new ArrayBuffer(byteString.length)
      const uint8Array = new Uint8Array(arrayBuffer)
      
      for (let i = 0; i < byteString.length; i++) {
        uint8Array[i] = byteString.charCodeAt(i)
      }
      
      return new Blob([arrayBuffer], { type: mimeType })
    } catch (error) {
      console.error(' Base64 decode error:', error)
      throw error
    }
  }

  const handleEnded = () => {
    console.log('🔇 Audio ended')
    onEnd?.()
    // Don't reset anything - just signal end
  }

  const handleError = (e: any) => {
    console.error(' Audio error:', e)
    onEnd?.()
  }

  return (
    <audio
      ref={audioRef}
      onEnded={handleEnded}
      onError={handleError}
      preload="none"
      style={{ display: 'none' }}
    />
  )
}