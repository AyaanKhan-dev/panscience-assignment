import { FileText, Info } from 'lucide-react'

export default function Header() {
  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-primary-100 rounded-lg">
            <FileText className="w-6 h-6 text-primary-600" />
          </div>
          <div>
            <h1 className="text-xl font-semibold text-gray-900">
              AI Document Q&A System
            </h1>
            <p className="text-sm text-gray-500">
              Upload documents and media, ask questions, get answers
            </p>
          </div>
        </div>
        <button className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors">
          <Info className="w-5 h-5" />
        </button>
      </div>
    </header>
  )
}
