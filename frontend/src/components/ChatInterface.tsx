import { useState, useRef, useEffect } from 'react'
import { Send, Loader2, Clock } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { useStore } from '../store/useStore'
import { sendMessage } from '../services/api'
import type { TimestampReference } from '../types'
import { clsx } from 'clsx'

interface ChatInterfaceProps {
  fileId: string
  fileType: 'document' | 'audio' | 'video'
  onTimestampClick?: (timestamp: TimestampReference) => void
}

export default function ChatInterface({
  fileId,
  fileType,
  onTimestampClick,
}: ChatInterfaceProps) {
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const { messages, addMessage, sessionId, setSessionId, isTyping, setTyping } =
    useStore()

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isTyping) return

    const userMessage = input.trim()
    setInput('')

    // Add user message
    addMessage({
      id: Date.now().toString(),
      role: 'user',
      content: userMessage,
      created_at: new Date().toISOString(),
    })

    setTyping(true)

    try {
      const response = await sendMessage(
        userMessage,
        fileId,
        fileType,
        sessionId || undefined
      )

      setSessionId(response.session_id)

      // Add assistant message
      addMessage({
        id: Date.now().toString(),
        role: 'assistant',
        content: response.message,
        metadata: {
          sources: response.sources,
          timestamps: response.timestamps,
        },
        created_at: new Date().toISOString(),
      })
    } catch (error) {
      addMessage({
        id: Date.now().toString(),
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        created_at: new Date().toISOString(),
      })
    } finally {
      setTyping(false)
    }
  }

  return (
    <div className="flex flex-col h-full bg-white rounded-xl border border-gray-200 overflow-hidden">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <p className="text-lg font-medium">Start a conversation</p>
            <p className="text-sm mt-1">
              Ask questions about the uploaded content
            </p>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={clsx(
                'flex',
                message.role === 'user' ? 'justify-end' : 'justify-start'
              )}
            >
              <div
                className={clsx(
                  'max-w-[80%] rounded-2xl px-4 py-3',
                  message.role === 'user'
                    ? 'bg-primary-500 text-white'
                    : 'bg-gray-100 text-gray-800'
                )}
              >
                <div className="markdown-content">
                  <ReactMarkdown>{message.content}</ReactMarkdown>
                </div>

                {/* Timestamps for media files */}
                {message.metadata?.timestamps &&
                  message.metadata.timestamps.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-gray-200">
                      <p className="text-xs font-medium text-gray-500 mb-2">
                        Relevant timestamps:
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {message.metadata.timestamps.map((ts, idx) => (
                          <button
                            key={idx}
                            onClick={() => onTimestampClick?.(ts)}
                            className="inline-flex items-center gap-1 px-2 py-1 bg-white rounded-lg text-xs font-medium text-primary-600 hover:bg-primary-50 transition-colors"
                          >
                            <Clock className="w-3 h-3" />
                            {formatTime(ts.start_time)}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
              </div>
            </div>
          ))
        )}

        {isTyping && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-2xl px-4 py-3">
              <div className="flex items-center gap-2 text-gray-500">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span className="text-sm">Thinking...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <form
        onSubmit={handleSubmit}
        className="p-4 border-t border-gray-200 bg-gray-50"
      >
        <div className="flex items-center gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question about the content..."
            className="flex-1 px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            disabled={isTyping}
          />
          <button
            type="submit"
            disabled={!input.trim() || isTyping}
            className="p-3 bg-primary-500 text-white rounded-xl hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isTyping ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </button>
        </div>
      </form>
    </div>
  )
}
