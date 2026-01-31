import { useRef, useEffect, useState } from 'react'
import ReactPlayer from 'react-player'
import { Play, Pause, Volume2, VolumeX, SkipBack, SkipForward } from 'lucide-react'
import { useStore } from '../store/useStore'
import { getMediaStreamUrl } from '../services/api'
import type { TimestampReference } from '../types'
import { clsx } from 'clsx'

interface MediaPlayerProps {
  mediaId: string
  mediaType: 'audio' | 'video'
  timestamps?: TimestampReference[]
}

export default function MediaPlayer({
  mediaId,
  mediaType,
  timestamps = [],
}: MediaPlayerProps) {
  const playerRef = useRef<ReactPlayer>(null)
  const [duration, setDuration] = useState(0)
  const [played, setPlayed] = useState(0)
  const [volume, setVolume] = useState(0.8)
  const [muted, setMuted] = useState(false)

  const { currentTimestamp, isPlaying, setPlaying, setCurrentTimestamp } =
    useStore()

  const mediaUrl = getMediaStreamUrl(mediaId)

  useEffect(() => {
    if (currentTimestamp > 0 && playerRef.current) {
      playerRef.current.seekTo(currentTimestamp, 'seconds')
    }
  }, [currentTimestamp])

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const handleProgress = (state: { played: number; playedSeconds: number }) => {
    setPlayed(state.playedSeconds)
  }

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const time = parseFloat(e.target.value)
    setPlayed(time)
    playerRef.current?.seekTo(time, 'seconds')
  }

  const handleTimestampClick = (ts: TimestampReference) => {
    setCurrentTimestamp(ts.start_time)
    setPlaying(true)
  }

  const skip = (seconds: number) => {
    const newTime = Math.max(0, Math.min(played + seconds, duration))
    setPlayed(newTime)
    playerRef.current?.seekTo(newTime, 'seconds')
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      {/* Player */}
      <div
        className={clsx(
          'relative bg-gray-900',
          mediaType === 'video' ? 'aspect-video' : 'h-20'
        )}
      >
        <ReactPlayer
          ref={playerRef}
          url={mediaUrl}
          playing={isPlaying}
          volume={volume}
          muted={muted}
          width="100%"
          height="100%"
          onDuration={setDuration}
          onProgress={handleProgress}
          onPlay={() => setPlaying(true)}
          onPause={() => setPlaying(false)}
          config={{
            file: {
              attributes: {
                controlsList: 'nodownload',
              },
            },
          }}
        />
      </div>

      {/* Controls */}
      <div className="p-4 space-y-3">
        {/* Progress bar */}
        <div className="flex items-center gap-3">
          <span className="text-xs text-gray-500 w-12 text-right">
            {formatTime(played)}
          </span>
          <input
            type="range"
            min={0}
            max={duration}
            value={played}
            onChange={handleSeek}
            className="flex-1 h-2 bg-gray-200 rounded-full appearance-none cursor-pointer [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:h-4 [&::-webkit-slider-thumb]:bg-primary-500 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:cursor-pointer"
          />
          <span className="text-xs text-gray-500 w-12">
            {formatTime(duration)}
          </span>
        </div>

        {/* Playback controls */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <button
              onClick={() => skip(-10)}
              className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <SkipBack className="w-5 h-5" />
            </button>
            <button
              onClick={() => setPlaying(!isPlaying)}
              className="p-3 bg-primary-500 text-white rounded-full hover:bg-primary-600 transition-colors"
            >
              {isPlaying ? (
                <Pause className="w-6 h-6" />
              ) : (
                <Play className="w-6 h-6 ml-0.5" />
              )}
            </button>
            <button
              onClick={() => skip(10)}
              className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <SkipForward className="w-5 h-5" />
            </button>
          </div>

          {/* Volume */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setMuted(!muted)}
              className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            >
              {muted ? (
                <VolumeX className="w-5 h-5" />
              ) : (
                <Volume2 className="w-5 h-5" />
              )}
            </button>
            <input
              type="range"
              min={0}
              max={1}
              step={0.1}
              value={muted ? 0 : volume}
              onChange={(e) => {
                setVolume(parseFloat(e.target.value))
                setMuted(false)
              }}
              className="w-20 h-1.5 bg-gray-200 rounded-full appearance-none cursor-pointer [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:h-3 [&::-webkit-slider-thumb]:bg-primary-500 [&::-webkit-slider-thumb]:rounded-full"
            />
          </div>
        </div>
      </div>

      {/* Timestamps */}
      {timestamps.length > 0 && (
        <div className="px-4 pb-4">
          <p className="text-sm font-medium text-gray-700 mb-2">
            Jump to timestamp:
          </p>
          <div className="flex flex-wrap gap-2">
            {timestamps.map((ts, idx) => (
              <button
                key={idx}
                onClick={() => handleTimestampClick(ts)}
                className="px-3 py-1.5 bg-gray-100 hover:bg-primary-100 text-sm text-gray-700 hover:text-primary-700 rounded-lg transition-colors"
              >
                {formatTime(ts.start_time)} - {ts.text.slice(0, 30)}...
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
