import { describe, it, expect } from 'vitest'
import { formatTimestamp, formatFileSize, truncateText } from '../utils/format'

describe('formatTimestamp', () => {
  it('formats zero seconds', () => {
    expect(formatTimestamp(0)).toBe('0:00')
  })

  it('formats seconds only', () => {
    expect(formatTimestamp(45)).toBe('0:45')
  })

  it('formats minutes and seconds', () => {
    expect(formatTimestamp(125)).toBe('2:05')
  })

  it('formats hours', () => {
    expect(formatTimestamp(3665)).toBe('1:01:05')
  })

  it('handles negative values', () => {
    expect(formatTimestamp(-5)).toBe('0:00')
  })
})

describe('formatFileSize', () => {
  it('formats bytes', () => {
    expect(formatFileSize(500)).toBe('500 B')
  })

  it('formats kilobytes', () => {
    expect(formatFileSize(1536)).toBe('1.5 KB')
  })

  it('formats megabytes', () => {
    expect(formatFileSize(1048576)).toBe('1 MB')
  })

  it('formats zero', () => {
    expect(formatFileSize(0)).toBe('0 B')
  })
})

describe('truncateText', () => {
  it('returns short text unchanged', () => {
    expect(truncateText('hello', 10)).toBe('hello')
  })

  it('truncates long text', () => {
    expect(truncateText('hello world', 8)).toBe('hello...')
  })

  it('handles exact length', () => {
    expect(truncateText('hello', 5)).toBe('hello')
  })
})
