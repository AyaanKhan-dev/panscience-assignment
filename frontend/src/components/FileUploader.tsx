import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, FileText, Music, Video, Loader2, CheckCircle, XCircle } from 'lucide-react'
import { uploadFile, getUploadStatus } from '../services/api'
import { useStore } from '../store/useStore'
import { clsx } from 'clsx'

interface UploadingFile {
  name: string
  progress: number
  status: 'uploading' | 'processing' | 'completed' | 'error'
  error?: string
}

export default function FileUploader() {
  const [uploadingFiles, setUploadingFiles] = useState<UploadingFile[]>([])
  const { addFile } = useStore()

  const pollStatus = async (
    fileId: string,
    fileType: string,
    fileName: string
  ) => {
    const maxAttempts = 60 // 5 minutes max
    let attempts = 0

    const poll = async (): Promise<void> => {
      try {
        const status = await getUploadStatus(fileId, fileType)

        if (status.status === 'completed') {
          setUploadingFiles((prev) =>
            prev.map((f) =>
              f.name === fileName ? { ...f, status: 'completed', progress: 100 } : f
            )
          )
          // Fetch the full file data and add to store
          const fileData = {
            id: fileId,
            filename: fileName,
            original_filename: fileName,
            file_type: fileType as 'document' | 'audio' | 'video',
            status: 'completed' as const,
            file_size: 0,
            mime_type: '',
            created_at: new Date().toISOString(),
          }
          addFile(fileData)
          return
        }

        if (status.status === 'failed') {
          setUploadingFiles((prev) =>
            prev.map((f) =>
              f.name === fileName
                ? { ...f, status: 'error', error: status.error_message }
                : f
            )
          )
          return
        }

        attempts++
        if (attempts < maxAttempts) {
          setTimeout(poll, 5000) // Poll every 5 seconds
        }
      } catch {
        setUploadingFiles((prev) =>
          prev.map((f) =>
            f.name === fileName
              ? { ...f, status: 'error', error: 'Failed to check status' }
              : f
          )
        )
      }
    }

    poll()
  }

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    for (const file of acceptedFiles) {
      setUploadingFiles((prev) => [
        ...prev,
        { name: file.name, progress: 0, status: 'uploading' },
      ])

      try {
        const result = await uploadFile(file, (progress) => {
          setUploadingFiles((prev) =>
            prev.map((f) =>
              f.name === file.name ? { ...f, progress } : f
            )
          )
        })

        setUploadingFiles((prev) =>
          prev.map((f) =>
            f.name === file.name ? { ...f, status: 'processing', progress: 100 } : f
          )
        )

        // Start polling for processing status
        pollStatus(result.id, result.file_type, file.name)
      } catch (error) {
        setUploadingFiles((prev) =>
          prev.map((f) =>
            f.name === file.name
              ? { ...f, status: 'error', error: 'Upload failed' }
              : f
          )
        )
      }
    }
  }, [addFile])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'audio/*': ['.mp3', '.wav', '.m4a', '.ogg'],
      'video/*': ['.mp4', '.webm'],
    },
    maxSize: 100 * 1024 * 1024, // 100MB
  })

  const getFileIcon = (fileName: string) => {
    const ext = fileName.split('.').pop()?.toLowerCase()
    if (ext === 'pdf') return <FileText className="w-5 h-5" />
    if (['mp3', 'wav', 'm4a', 'ogg'].includes(ext || ''))
      return <Music className="w-5 h-5" />
    if (['mp4', 'webm'].includes(ext || '')) return <Video className="w-5 h-5" />
    return <FileText className="w-5 h-5" />
  }

  const removeUploadingFile = (name: string) => {
    setUploadingFiles((prev) => prev.filter((f) => f.name !== name))
  }

  return (
    <div className="space-y-4">
      <div
        {...getRootProps()}
        className={clsx(
          'border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all',
          isDragActive
            ? 'border-primary-500 bg-primary-50'
            : 'border-gray-300 hover:border-primary-400 hover:bg-gray-50'
        )}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center gap-3">
          <div
            className={clsx(
              'p-4 rounded-full',
              isDragActive ? 'bg-primary-100' : 'bg-gray-100'
            )}
          >
            <Upload
              className={clsx(
                'w-8 h-8',
                isDragActive ? 'text-primary-600' : 'text-gray-400'
              )}
            />
          </div>
          <div>
            <p className="text-lg font-medium text-gray-700">
              {isDragActive ? 'Drop files here' : 'Drag & drop files here'}
            </p>
            <p className="text-sm text-gray-500 mt-1">
              or click to select files
            </p>
          </div>
          <p className="text-xs text-gray-400">
            Supports PDF, MP3, WAV, M4A, MP4, WebM (max 100MB)
          </p>
        </div>
      </div>

      {uploadingFiles.length > 0 && (
        <div className="space-y-2">
          {uploadingFiles.map((file) => (
            <div
              key={file.name}
              className="flex items-center gap-3 p-3 bg-white rounded-lg border border-gray-200"
            >
              <div className="p-2 bg-gray-100 rounded-lg">
                {getFileIcon(file.name)}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-700 truncate">
                  {file.name}
                </p>
                {file.status === 'uploading' && (
                  <div className="mt-1">
                    <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-primary-500 transition-all duration-300"
                        style={{ width: `${file.progress}%` }}
                      />
                    </div>
                  </div>
                )}
                {file.status === 'processing' && (
                  <p className="text-xs text-yellow-600 mt-1">
                    Processing...
                  </p>
                )}
                {file.status === 'error' && (
                  <p className="text-xs text-red-600 mt-1">{file.error}</p>
                )}
              </div>
              <div className="flex-shrink-0">
                {file.status === 'uploading' && (
                  <Loader2 className="w-5 h-5 text-primary-500 animate-spin" />
                )}
                {file.status === 'processing' && (
                  <Loader2 className="w-5 h-5 text-yellow-500 animate-spin" />
                )}
                {file.status === 'completed' && (
                  <CheckCircle className="w-5 h-5 text-green-500" />
                )}
                {file.status === 'error' && (
                  <button onClick={() => removeUploadingFile(file.name)}>
                    <XCircle className="w-5 h-5 text-red-500" />
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
