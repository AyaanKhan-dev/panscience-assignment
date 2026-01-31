import { create } from 'zustand'
import type { UploadedFile, ChatMessage, TimestampReference } from '../types'

interface AppState {
  // Files
  files: UploadedFile[]
  selectedFile: UploadedFile | null
  isLoading: boolean

  // Chat
  messages: ChatMessage[]
  sessionId: string | null
  isTyping: boolean

  // Media player
  currentTimestamp: number
  isPlaying: boolean
  activeTimestamps: TimestampReference[]

  // Actions
  setFiles: (files: UploadedFile[]) => void
  addFile: (file: UploadedFile) => void
  updateFile: (id: string, updates: Partial<UploadedFile>) => void
  removeFile: (id: string) => void
  setSelectedFile: (file: UploadedFile | null) => void
  setLoading: (loading: boolean) => void

  setMessages: (messages: ChatMessage[]) => void
  addMessage: (message: ChatMessage) => void
  setSessionId: (id: string | null) => void
  setTyping: (typing: boolean) => void
  clearChat: () => void

  setCurrentTimestamp: (time: number) => void
  setPlaying: (playing: boolean) => void
  setActiveTimestamps: (timestamps: TimestampReference[]) => void
  seekToTimestamp: (time: number) => void
}

export const useStore = create<AppState>((set) => ({
  // Initial state
  files: [],
  selectedFile: null,
  isLoading: false,

  messages: [],
  sessionId: null,
  isTyping: false,

  currentTimestamp: 0,
  isPlaying: false,
  activeTimestamps: [],

  // File actions
  setFiles: (files) => set({ files }),
  addFile: (file) => set((state) => ({ files: [file, ...state.files] })),
  updateFile: (id, updates) =>
    set((state) => ({
      files: state.files.map((f) => (f.id === id ? { ...f, ...updates } : f)),
      selectedFile:
        state.selectedFile?.id === id
          ? { ...state.selectedFile, ...updates }
          : state.selectedFile,
    })),
  removeFile: (id) =>
    set((state) => ({
      files: state.files.filter((f) => f.id !== id),
      selectedFile: state.selectedFile?.id === id ? null : state.selectedFile,
    })),
  setSelectedFile: (file) => set({ selectedFile: file }),
  setLoading: (loading) => set({ isLoading: loading }),

  // Chat actions
  setMessages: (messages) => set({ messages }),
  addMessage: (message) =>
    set((state) => ({ messages: [...state.messages, message] })),
  setSessionId: (id) => set({ sessionId: id }),
  setTyping: (typing) => set({ isTyping: typing }),
  clearChat: () => set({ messages: [], sessionId: null }),

  // Media player actions
  setCurrentTimestamp: (time) => set({ currentTimestamp: time }),
  setPlaying: (playing) => set({ isPlaying: playing }),
  setActiveTimestamps: (timestamps) => set({ activeTimestamps: timestamps }),
  seekToTimestamp: (time) => set({ currentTimestamp: time, isPlaying: true }),
}))
