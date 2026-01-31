export interface UploadedFile {
  id: string
  filename: string
  original_filename: string
  file_type: 'document' | 'audio' | 'video'
  status: 'pending' | 'processing' | 'completed' | 'failed'
  file_size: number
  mime_type: string
  duration?: number
  page_count?: number
  summary?: string
  error_message?: string
  created_at: string
  processed_at?: string
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  metadata?: {
    sources?: SourceReference[]
    timestamps?: TimestampReference[]
  }
  created_at: string
}

export interface ChatSession {
  id: string
  title?: string
  source_type?: string
  source_id?: string
  messages: ChatMessage[]
  created_at: string
  updated_at: string
}

export interface SourceReference {
  content: string
  page_number?: number
  start_time?: number
  end_time?: number
}

export interface TimestampReference {
  text: string
  start_time: number
  end_time: number
}

export interface ChatResponse {
  message: string
  session_id: string
  sources: SourceReference[]
  timestamps: TimestampReference[]
}

export interface TranscriptSegment {
  id: string
  text: string
  start_time: number
  end_time: number
}

export interface Transcript {
  id: string
  media_file_id: string
  full_text: string
  segments: TranscriptSegment[]
  created_at: string
}

export interface TimestampQueryResult {
  query: string
  results: Array<{
    text: string
    start_time: number
    end_time: number
    relevance_score: number
  }>
  answer: string
}
