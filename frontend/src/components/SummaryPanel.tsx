import { useState, useEffect } from 'react'
import { FileText, Loader2, RefreshCw } from 'lucide-react'
import { summarizeDocument, summarizeMedia } from '../services/api'
import type { UploadedFile } from '../types'

interface SummaryPanelProps {
  file: UploadedFile
}

export default function SummaryPanel({ file }: SummaryPanelProps) {
  const [summary, setSummary] = useState<string | null>(file.summary || null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (file.summary) {
      setSummary(file.summary)
    }
  }, [file.summary])

  const generateSummary = async () => {
    setIsLoading(true)
    setError(null)

    try {
      let result
      if (file.file_type === 'document') {
        result = await summarizeDocument(file.id)
      } else {
        result = await summarizeMedia(file.id)
      }
      setSummary(result.summary)
    } catch (err) {
      setError('Failed to generate summary. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <FileText className="w-5 h-5 text-primary-600" />
          <h3 className="font-semibold text-gray-800">Summary</h3>
        </div>
        <button
          onClick={generateSummary}
          disabled={isLoading || file.status !== 'completed'}
          className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isLoading ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <RefreshCw className="w-4 h-4" />
          )}
          {summary ? 'Regenerate' : 'Generate'}
        </button>
      </div>

      {file.status !== 'completed' ? (
        <div className="py-8 text-center text-gray-500">
          <Loader2 className="w-8 h-8 mx-auto mb-2 animate-spin text-gray-400" />
          <p className="text-sm">File is still being processed...</p>
        </div>
      ) : isLoading ? (
        <div className="py-8 text-center text-gray-500">
          <Loader2 className="w-8 h-8 mx-auto mb-2 animate-spin text-primary-500" />
          <p className="text-sm">Generating summary...</p>
        </div>
      ) : error ? (
        <div className="py-4 text-center">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      ) : summary ? (
        <div className="prose prose-sm max-w-none text-gray-700">
          {summary.split('\n').map((paragraph, idx) => (
            <p key={idx} className="mb-2 last:mb-0">
              {paragraph}
            </p>
          ))}
        </div>
      ) : (
        <div className="py-8 text-center text-gray-500">
          <p className="text-sm">
            Click "Generate" to create a summary of this content.
          </p>
        </div>
      )}
    </div>
  )
}
