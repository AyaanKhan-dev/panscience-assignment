import { useNavigate, useLocation } from 'react-router-dom'
import { FileText, Music, Video, Trash2, Loader2 } from 'lucide-react'
import { useStore } from '../store/useStore'
import { deleteDocument, deleteMedia } from '../services/api'
import { clsx } from 'clsx'

export default function Sidebar() {
  const navigate = useNavigate()
  const location = useLocation()
  const { files, selectedFile, setSelectedFile, removeFile } = useStore()

  const handleFileClick = (file: typeof files[0]) => {
    setSelectedFile(file)
    navigate(`/chat/${file.id}`)
  }

  const handleDelete = async (e: React.MouseEvent, file: typeof files[0]) => {
    e.stopPropagation()
    if (!confirm('Are you sure you want to delete this file?')) return

    try {
      if (file.file_type === 'document') {
        await deleteDocument(file.id)
      } else {
        await deleteMedia(file.id)
      }
      removeFile(file.id)
      if (selectedFile?.id === file.id) {
        navigate('/')
      }
    } catch (error) {
      console.error('Failed to delete file:', error)
    }
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

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-700'
      case 'processing':
        return 'bg-yellow-100 text-yellow-700'
      case 'failed':
        return 'bg-red-100 text-red-700'
      default:
        return 'bg-gray-100 text-gray-700'
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  return (
    <aside className="w-72 bg-white border-r border-gray-200 flex flex-col">
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wider">
          Uploaded Files
        </h2>
      </div>

      <nav className="flex-1 overflow-y-auto p-2">
        {files.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <FileText className="w-12 h-12 mx-auto mb-3 text-gray-300" />
            <p className="text-sm">No files uploaded yet</p>
            <p className="text-xs mt-1">Upload a file to get started</p>
          </div>
        ) : (
          <ul className="space-y-1">
            {files.map((file) => {
              const isActive = location.pathname === `/chat/${file.id}`
              return (
                <li key={file.id}>
                  <button
                    onClick={() => handleFileClick(file)}
                    className={clsx(
                      'w-full flex items-start gap-3 p-3 rounded-lg text-left transition-colors group',
                      isActive
                        ? 'bg-primary-50 text-primary-700'
                        : 'hover:bg-gray-50 text-gray-700'
                    )}
                  >
                    <div
                      className={clsx(
                        'p-2 rounded-lg',
                        isActive ? 'bg-primary-100' : 'bg-gray-100'
                      )}
                    >
                      {file.status === 'processing' ? (
                        <Loader2 className="w-5 h-5 animate-spin" />
                      ) : (
                        getFileIcon(file.file_type)
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">
                        {file.original_filename}
                      </p>
                      <div className="flex items-center gap-2 mt-1">
                        <span
                          className={clsx(
                            'text-xs px-1.5 py-0.5 rounded',
                            getStatusColor(file.status)
                          )}
                        >
                          {file.status}
                        </span>
                        <span className="text-xs text-gray-400">
                          {formatFileSize(file.file_size)}
                        </span>
                      </div>
                    </div>
                    <button
                      onClick={(e) => handleDelete(e, file)}
                      className="p-1 opacity-0 group-hover:opacity-100 hover:bg-red-100 hover:text-red-600 rounded transition-all"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </button>
                </li>
              )
            })}
          </ul>
        )}
      </nav>
    </aside>
  )
}
