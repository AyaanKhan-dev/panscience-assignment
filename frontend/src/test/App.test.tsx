import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import App from '../App'

// Mock API calls
vi.mock('../services/api', () => ({
  getDocuments: vi.fn().mockResolvedValue({ documents: [], total: 0 }),
  getMediaFiles: vi.fn().mockResolvedValue({ media_files: [], total: 0 }),
}))

describe('App', () => {
  it('renders the application', () => {
    render(<App />)
    expect(screen.getByText(/AI Document Q&A System/i)).toBeInTheDocument()
  })

  it('shows welcome message on home page', () => {
    render(<App />)
    expect(screen.getByText(/Welcome to AI Document Q&A/i)).toBeInTheDocument()
  })

  it('displays file upload area', () => {
    render(<App />)
    expect(screen.getByText(/Drag & drop files here/i)).toBeInTheDocument()
  })
})
