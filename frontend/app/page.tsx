'use client'

import {
  ChatInput,
  ChatMessage,
  ChatMessages,
  ChatSection,
  useChatUI,
  useFile,
} from '@llamaindex/chat-ui'
import { useChat } from 'ai/react'
import { motion, AnimatePresence } from 'framer-motion'
import { HiddenAudioPlayer } from '../components/HiddenAudioPlayer'
import { useEffect, useState } from 'react'

const initialMessages = [
  {
    id: '1',
    content: "Hello, I'm at your service. What are we working on today, boss?",
    role: 'assistant' as const,
  },
]

export default function Page(): JSX.Element {
  const [isAISpeaking, setIsAISpeaking] = useState(false)

  return (
    <div className="flex h-screen flex-col">
      <header className="w-full border-b p-4 text-center relative bg-white">
        <h1 className="text-2xl font-bold">
           LE_REPAIRBOT 
        </h1>
       {isAISpeaking && (
          <div className="absolute top-4 right-4 flex items-center gap-2 bg-blue-100 px-3 py-1 rounded-full">
            <div className="flex items-center gap-1">
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" style={{ animationDelay: '0ms' }}></div>
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" style={{ animationDelay: '150ms' }}></div>
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" style={{ animationDelay: '300ms' }}></div>
            </div>
            {/* <span className="text-sm text-blue-700 font-medium">Speaking</span> */}
          </div>
        )}
      </header>
      
      {/* 50/50 Split Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left 50% - Chat */}
        <div className="w-1/2 flex flex-col">
          <CustomChat onAISpeakingChange={setIsAISpeaking} />
        </div>
        
        {/* Right 50% - Camera Feeds */}
        <div className="w-1/2 border-l bg-gray-50 p-4 flex flex-col justify-center items-center">
          <div className="space-y-6">
            {/* Camera 0 */}
            <div className="text-center">
              <div className="text-sm text-gray-600 mb-2 font-medium">local wrist view</div>
              <img 
                src="http://localhost:8000/api/video/stream?camera_index=0" 
                alt="Camera 0"
                className="rounded-lg border-2 border-gray-200 shadow-sm mx-auto"
                style={{ maxHeight: '360px', maxWidth: '360px' }}
              />
            </div>
            
            {/* Camera 1 */}
            <div className="text-center">
              <div className="text-sm text-gray-600 mb-2 font-medium">global top view</div>
              <img 
                src="http://localhost:8000/api/video/stream?camera_index=1" 
                alt="Camera 1"
                className="rounded-lg border-2 border-gray-200 shadow-sm mx-auto"
                style={{ maxHeight: '360px', maxWidth: '360px' }}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function CustomChat({ onAISpeakingChange }: { onAISpeakingChange: (speaking: boolean) => void }) {
  const [processedMessageIds, setProcessedMessageIds] = useState<Set<string>>(new Set())
  const [hasPlayedInitial, setHasPlayedInitial] = useState(false)
  
  const handler = useChat({
    api: 'http://localhost:8000/api/chat/realtime',
    initialMessages,
  })
  
  // Play initial message audio on page load
  useEffect(() => {
    if (!hasPlayedInitial) {
      console.log('🎵 Playing intro audio file')
      setHasPlayedInitial(true)
      
      setTimeout(() => {
        // Play your custom intro audio file instead of TTS
        playCustomIntroAudio()
      }, 1000) // Give page time to load
    }
  }, [hasPlayedInitial])
  
  const playCustomIntroAudio = () => {
    try {
      onAISpeakingChange(true)
      
      // Play your intro.wav file directly
      const audio = new Audio('/intro.wav') 
      audio.onended = () => {
        console.log('🔊 Intro audio finished')
        onAISpeakingChange(false)
      }
      audio.onerror = () => {
        console.log('🔊 Intro audio failed')
        onAISpeakingChange(false)
      }
      
      audio.play().catch(e => {
        console.log('🔊 Audio blocked - user needs to click first')
        onAISpeakingChange(false)
      })
      
    } catch (e) {
      console.error('🔊 Intro audio error:', e)
      onAISpeakingChange(false)
    }
  }
  
  // Play audio for new assistant messages
  useEffect(() => {
    const lastMessage = handler.messages[handler.messages.length - 1]
    
    if (lastMessage && 
        lastMessage.role === 'assistant' && 
        !handler.isLoading && 
        !processedMessageIds.has(lastMessage.id) &&
        lastMessage.id !== '1') { // Skip initial message (already played)
      
      const messageText = lastMessage.content.trim()
      if (messageText && messageText.length > 10) {
        console.log('🔊 Playing audio for new message:', messageText)
        
        setProcessedMessageIds(prev => new Set(prev).add(lastMessage.id))
        
        // Play immediately after text finishes streaming
        setTimeout(() => {
          playAudioForText(messageText)
        }, 200) // Much shorter delay - almost immediate
      }
    }
  }, [handler.messages, handler.isLoading, processedMessageIds])
  
  const playAudioForText = (text: string) => {
    fetch('http://localhost:8000/api/chat/tts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        text: text,
        voice: 'am_michael',
        speed: '1.2'
      }),
    })
    .then(r => r.json())
    .then(data => {
      if (data.success && data.audio_data) {
        playAudio(data.audio_data)
      }
    })
    .catch(console.error)
  }
  
  const playAudio = (audioData: string) => {
    try {
      onAISpeakingChange(true)
      
      const audio = new Audio(`data:audio/wav;base64,${audioData}`)
      audio.onended = () => {
        console.log('🔊 Audio finished')
        onAISpeakingChange(false)
      }
      audio.onerror = () => {
        console.log('🔊 Audio failed')
        onAISpeakingChange(false)
      }
      
      audio.play().catch(e => {
        console.log('🔊 Audio blocked - user needs to interact with page first')
        onAISpeakingChange(false)
      })
      
    } catch (e) {
      console.error('🔊 Audio error:', e)
      onAISpeakingChange(false)
    }
  }
  
  const { imageUrl, getAnnotations, uploadFile, reset } = useFile({
    uploadAPI: '/chat/upload',
  })
  
  const annotations = getAnnotations()
  
  const handleUpload = async (file: File) => {
    try {
      await uploadFile(file)
    } catch (error) {
      console.error('Upload failed:', error)
    }
  }

  return (
    <ChatSection
      handler={handler}
      className="h-full flex flex-col overflow-hidden"
    >
      <CustomChatMessages onAISpeakingChange={onAISpeakingChange} />
      
      <ChatInput annotations={annotations} resetUploadedFiles={reset}>
        <div className="p-2">
          {imageUrl ? (
            <img
              className="max-h-[100px] object-contain rounded border"
              src={imageUrl}
              alt="uploaded"
            />
          ) : null}
        </div>
        <ChatInput.Form>
          <ChatInput.Field placeholder="Ask me about what I can see..." />
          <ChatInput.Upload onUpload={handleUpload} />
          <ChatInput.Submit />
        </ChatInput.Form>
      </ChatInput>
    </ChatSection>
  )
}

function CustomChatMessages({ onAISpeakingChange }: { onAISpeakingChange: (speaking: boolean) => void }) {
  const { messages, isLoading, append } = useChatUI()
  
  return (
    <ChatMessages>
      <ChatMessages.List className="px-4 py-6 flex-1 overflow-y-auto">
        <AnimatePresence>
          {messages.map((message, index) => {
            return (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3, delay: index * 0.1 }}
              >
                <ChatMessage
                  message={message}
                  isLast={index === messages.length - 1}
                  className="items-start mb-4"
                >
                  <ChatMessage.Avatar />
                  
                  <ChatMessage.Content isLoading={isLoading} append={append}>
                    <ChatMessage.Content.Image />
                    <ChatMessage.Content.Markdown />
                    <ChatMessage.Content.DocumentFile />
                  </ChatMessage.Content>
                  
                  <ChatMessage.Actions />
                </ChatMessage>
              </motion.div>
            )
          })}
        </AnimatePresence>
      </ChatMessages.List>
    </ChatMessages>
  )
}