import { useEffect, useRef } from 'react'

interface UsePollingOptions {
  enabled: boolean
  interval: number
  onPoll: () => Promise<boolean> // Return true to stop polling
}

export function usePolling({ enabled, interval, onPoll }: UsePollingOptions) {
  const timeoutRef = useRef<NodeJS.Timeout | null>(null)
  const mountedRef = useRef(true)

  useEffect(() => {
    mountedRef.current = true

    const poll = async () => {
      if (!mountedRef.current || !enabled) return

      try {
        const shouldStop = await onPoll()
        if (shouldStop || !mountedRef.current) return

        timeoutRef.current = setTimeout(poll, interval)
      } catch (error) {
        console.error('Polling error:', error)
        if (mountedRef.current) {
          timeoutRef.current = setTimeout(poll, interval)
        }
      }
    }

    if (enabled) {
      poll()
    }

    return () => {
      mountedRef.current = false
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
    }
  }, [enabled, interval, onPoll])
}
