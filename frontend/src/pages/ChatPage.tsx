import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, FileText, Music, Video } from 'lucide-react'
import ChatInterface from '../components/ChatInterface'
import MediaPlayer from '../components/MediaPlayer'
import SummaryPanel from '../components/SummaryPanel'
import { useStore } from '../store/useStore'
import { getDocument, getMediaFile } from '../services/api'
import type { UploadedFile, TimestampReference } from '../types'

export default function ChatPage() {
  const { fileId } = useParams<{ fileId: string }>()
  const navigate = useNavigate()
  const { selectedFile, setSelectedFile, clearChat, setCurrentTimestamp, setActiveTimestamps } = useStore()
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchFile = async () => {
      if (!fileId) {
        navigate('/')
        return
      }

      setIsLoading(true)
      setError(null)
      clearChat()

      try {
        // Try document first
        try {
          const doc = await getDocument(fileId)
          setSelectedFile({ ...doc, file_type: 'document' })
          setIsLoading(false)
          return
        } catch {
          // Not a document, try media
        }

        // Try media
        const media = await getMediaFile(fileId)
        setSelectedFile({
          ...media,
          file_type: media.media_type as 'audio' | 'video',
        })
      } catch {
        setError('File not found')
      } finally {
        setIsLoading(false)
      }
    }

    fetchFile()
  }, [fileId, navigate, setSelectedFile, clearChat])

  const handleTimestampClick = (timestamp: TimestampReference) => {
    setCurrentTimestamp(timestamp.start_time)
  }

  const getFileIcon = (fileType: string) => {
    switch (fileType) {
      case 'document':
        return <FileText className="w-5 h-5" />
      case 'audio':
        return <Music className="w-5 h-5" />
      case 'video':
        return <Video className="w-5 h-5" />
      default:
        return <FileText className="w-5 h-5" />
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
      </div>
    )
  }

  if (error || !selectedFile) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-gray-500">
        <p className="text-xl mb-4">{error || 'File not found'}</p>
        <button
          onClick={() => navigate('/')}
          className="flex items-center gap-2 px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Home
        </button>
      </div>
    )
  }

  const isMedia = selectedFile.file_type === 'audio' || selectedFile.file_type === 'video'

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center gap-4 mb-4">
        <button
          onClick={() => navigate('/')}
          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <ArrowLeft className="w-5 h-5 text-gray-600" />
        </button>
        <div className="flex items-center gap-3">
          <div className="p-2 bg-primary-100 rounded-lg">
            {getFileIcon(selectedFile.file_type)}
          </div>
          <div>
            <h2 className="font-semibold text-gray-900">
              {selectedFile.original_filename}
            </h2>
            <p className="text-sm text-gray-500 capitalize">
              {selectedFile.file_type} • {selectedFile.status}
            </p>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-3 gap-4 min-h-0">
        {/* Chat section */}
        <div className="lg:col-span-2 flex flex-col min-h-0">
          <ChatInterface
            fileId={selectedFile.id}
            fileType={selectedFile.file_type}
            onTimestampClick={isMedia ? handleTimestampClick : undefined}
          />
        </div>

        {/* Right sidebar */}
        <div className="space-y-4 overflow-y-auto">
          {/* Media player for audio/video */}
          {isMedia && (
            <MediaPlayer
              mediaId={selectedFile.id}
              mediaType={selectedFile.file_type as 'audio' | 'video'}
            />
          )}

          {/* Summary panel */}
          <SummaryPanel file={selectedFile} />
        </div>
      </div>
    </div>
  )
}
