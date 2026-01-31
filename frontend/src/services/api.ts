import axios from 'axios'
import type {
  UploadedFile,
  ChatResponse,
  ChatSession,
  Transcript,
  TimestampQueryResult
} from '../types'

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

// File Upload
export async function uploadFile(
  file: File,
  onProgress?: (progress: number) => void
): Promise<{ id: string; file_type: string; status: string }> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await api.post('/upload/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      if (progressEvent.total && onProgress) {
        const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
        onProgress(progress)
      }
    },
  })

  return response.data
}

export async function getUploadStatus(
  fileId: string,
  fileType: string
): Promise<{ id: string; status: string; error_message?: string }> {
  const response = await api.get(`/upload/status/${fileId}?file_type=${fileType}`)
  return response.data
}

// Documents
export async function getDocuments(): Promise<{ documents: UploadedFile[]; total: number }> {
  const response = await api.get('/documents/')
  return response.data
}

export async function getDocument(documentId: string): Promise<UploadedFile> {
  const response = await api.get(`/documents/${documentId}`)
  return response.data
}

export async function summarizeDocument(documentId: string): Promise<{ summary: string }> {
  const response = await api.post(`/documents/${documentId}/summarize`)
  return response.data
}

export async function deleteDocument(documentId: string): Promise<void> {
  await api.delete(`/documents/${documentId}`)
}

// Media
export async function getMediaFiles(): Promise<{ media_files: UploadedFile[]; total: number }> {
  const response = await api.get('/media/')
  return response.data
}

export async function getMediaFile(mediaId: string): Promise<UploadedFile> {
  const response = await api.get(`/media/${mediaId}`)
  return response.data
}

export async function getTranscript(mediaId: string): Promise<Transcript> {
  const response = await api.get(`/media/${mediaId}/transcript`)
  return response.data
}

export async function queryTimestamps(
  mediaId: string,
  query: string
): Promise<TimestampQueryResult> {
  const response = await api.post(`/media/${mediaId}/timestamps`, { query })
  return response.data
}

export async function summarizeMedia(mediaId: string): Promise<{ summary: string }> {
  const response = await api.post(`/media/${mediaId}/summarize`)
  return response.data
}

export async function deleteMedia(mediaId: string): Promise<void> {
  await api.delete(`/media/${mediaId}`)
}

export function getMediaStreamUrl(mediaId: string): string {
  return `/api/media/${mediaId}/stream`
}

// Chat
export async function sendMessage(
  message: string,
  sourceId?: string,
  sourceType?: string,
  sessionId?: string
): Promise<ChatResponse> {
  const response = await api.post('/chat/', {
    message,
    source_id: sourceId,
    source_type: sourceType,
    session_id: sessionId,
  })
  return response.data
}

export async function getChatSessions(): Promise<{ sessions: ChatSession[]; total: number }> {
  const response = await api.get('/chat/sessions')
  return response.data
}

export async function getChatSession(sessionId: string): Promise<ChatSession> {
  const response = await api.get(`/chat/sessions/${sessionId}`)
  return response.data
}

export async function deleteChatSession(sessionId: string): Promise<void> {
  await api.delete(`/chat/sessions/${sessionId}`)
}

// Health check
export async function healthCheck(): Promise<{ status: string }> {
  const response = await api.get('/health')
  return response.data
}

export default api
