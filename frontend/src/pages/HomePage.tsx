import { useEffect } from 'react'
import FileUploader from '../components/FileUploader'
import { useStore } from '../store/useStore'
import { getDocuments, getMediaFiles } from '../services/api'
import type { UploadedFile } from '../types'

export default function HomePage() {
  const { setFiles, setLoading } = useStore()

  useEffect(() => {
    const fetchFiles = async () => {
      setLoading(true)
      try {
        const [docsResponse, mediaResponse] = await Promise.all([
          getDocuments(),
          getMediaFiles(),
        ])

        const allFiles: UploadedFile[] = [
          ...docsResponse.documents.map((doc) => ({
            ...doc,
            file_type: 'document' as const,
          })),
          ...mediaResponse.media_files.map((media) => ({
            ...media,
            file_type: media.media_type as 'audio' | 'video',
          })),
        ].sort(
          (a, b) =>
            new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        )

        setFiles(allFiles)
      } catch (error) {
        console.error('Failed to fetch files:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchFiles()
  }, [setFiles, setLoading])

  return (
    <div className="max-w-3xl mx-auto">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Welcome to AI Document Q&A
        </h2>
        <p className="text-gray-600">
          Upload your documents, audio, or video files to start asking questions
          about their content.
        </p>
      </div>

      <FileUploader />

      <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-4 bg-white rounded-xl border border-gray-200">
          <div className="text-3xl mb-2">📄</div>
          <h3 className="font-semibold text-gray-800">PDF Documents</h3>
          <p className="text-sm text-gray-500 mt-1">
            Upload PDFs and ask questions about their content
          </p>
        </div>
        <div className="p-4 bg-white rounded-xl border border-gray-200">
          <div className="text-3xl mb-2">🎵</div>
          <h3 className="font-semibold text-gray-800">Audio Files</h3>
          <p className="text-sm text-gray-500 mt-1">
            Transcribe audio and get answers with timestamps
          </p>
        </div>
        <div className="p-4 bg-white rounded-xl border border-gray-200">
          <div className="text-3xl mb-2">🎬</div>
          <h3 className="font-semibold text-gray-800">Video Files</h3>
          <p className="text-sm text-gray-500 mt-1">
            Extract insights from videos with playback
          </p>
        </div>
      </div>
    </div>
  )
}
