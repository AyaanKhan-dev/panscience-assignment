import { describe, it, expect, beforeEach } from 'vitest'
import { useStore } from '../store/useStore'

describe('useStore', () => {
  beforeEach(() => {
    // Reset store between tests
    useStore.setState({
      files: [],
      selectedFile: null,
      isLoading: false,
      messages: [],
      sessionId: null,
      isTyping: false,
      currentTimestamp: 0,
      isPlaying: false,
      activeTimestamps: [],
    })
  })

  describe('file actions', () => {
    it('adds a file', () => {
      const file = {
        id: '1',
        filename: 'test.pdf',
        original_filename: 'test.pdf',
        file_type: 'document' as const,
        status: 'completed' as const,
        file_size: 1024,
        mime_type: 'application/pdf',
        created_at: new Date().toISOString(),
      }

      useStore.getState().addFile(file)
      expect(useStore.getState().files).toHaveLength(1)
      expect(useStore.getState().files[0].id).toBe('1')
    })

    it('removes a file', () => {
      const file = {
        id: '1',
        filename: 'test.pdf',
        original_filename: 'test.pdf',
        file_type: 'document' as const,
        status: 'completed' as const,
        file_size: 1024,
        mime_type: 'application/pdf',
        created_at: new Date().toISOString(),
      }

      useStore.getState().addFile(file)
      useStore.getState().removeFile('1')
      expect(useStore.getState().files).toHaveLength(0)
    })

    it('updates a file', () => {
      const file = {
        id: '1',
        filename: 'test.pdf',
        original_filename: 'test.pdf',
        file_type: 'document' as const,
        status: 'pending' as const,
        file_size: 1024,
        mime_type: 'application/pdf',
        created_at: new Date().toISOString(),
      }

      useStore.getState().addFile(file)
      useStore.getState().updateFile('1', { status: 'completed' })
      expect(useStore.getState().files[0].status).toBe('completed')
    })
  })

  describe('chat actions', () => {
    it('adds a message', () => {
      const message = {
        id: '1',
        role: 'user' as const,
        content: 'Hello',
        created_at: new Date().toISOString(),
      }

      useStore.getState().addMessage(message)
      expect(useStore.getState().messages).toHaveLength(1)
    })

    it('clears chat', () => {
      const message = {
        id: '1',
        role: 'user' as const,
        content: 'Hello',
        created_at: new Date().toISOString(),
      }

      useStore.getState().addMessage(message)
      useStore.getState().setSessionId('session-1')
      useStore.getState().clearChat()

      expect(useStore.getState().messages).toHaveLength(0)
      expect(useStore.getState().sessionId).toBeNull()
    })
  })

  describe('media player actions', () => {
    it('seeks to timestamp', () => {
      useStore.getState().seekToTimestamp(30)
      expect(useStore.getState().currentTimestamp).toBe(30)
      expect(useStore.getState().isPlaying).toBe(true)
    })

    it('sets playing state', () => {
      useStore.getState().setPlaying(true)
      expect(useStore.getState().isPlaying).toBe(true)
    })
  })
})
