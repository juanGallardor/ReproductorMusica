import { useRef } from "react"
import { Button } from "@/components/ui/button"
import { Upload, Trash2, Plus } from "lucide-react"
import type { Song, Playlist } from '@/lib/api'
import { cn } from "@/lib/utils"

interface SongListProps {
  currentPlaylist: Playlist | null
  currentSong: Song | null
  onSongSelect: (song: Song) => Promise<void>
  onRemoveSong: (songId: string) => Promise<void>
  onFileSelect: (files: FileList | null) => Promise<void>
  isDraggingOver: boolean
  onDragOver: (e: React.DragEvent) => void
  onDragLeave: (e: React.DragEvent) => void
  onDrop: (e: React.DragEvent) => Promise<void>
}

export function SongList({
  currentPlaylist,
  currentSong,
  onSongSelect,
  onRemoveSong,
  onFileSelect,
  isDraggingOver,
  onDragOver,
  onDragLeave,
  onDrop
}: SongListProps) {
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Format duration for display
  const formatDuration = (seconds: number) => {
    const minutes = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${minutes}:${secs.toString().padStart(2, '0')}`
  }

  return (
    <div 
      className="h-full flex flex-col p-6 text-white"
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
      onDrop={onDrop}
    >
      <div className="mb-6">
        <div className="flex items-center gap-4 mb-4">
          <div className="w-10 h-10 bg-white rounded-lg flex items-center justify-center p-1">
            <img src="/images/logo.png" alt="Logo" className="w-full h-full object-contain filter brightness-0" />
          </div>
          <h1 className="text-xl font-bold music-title">
            vinyl<span className="text-red-500">list</span>
          </h1>
        </div>
        <h2 className="text-4xl font-bold mb-2 text-balance music-title">
          {currentSong?.title || "Select a song"}
        </h2>
        <p className="text-gray-300 text-lg music-subtitle">{currentSong?.artist || "Unknown Artist"}</p>
      </div>

      {/* Song List */}
      <div className="flex-1 overflow-hidden mb-4">
        {currentPlaylist ? (
          <div className="h-full overflow-y-auto custom-scrollbar pr-2">
            {currentPlaylist.songs && currentPlaylist.songs.length > 0 ? (
              currentPlaylist.songs.map((song, index) => (
                <div
                  key={song.id}
                  className={`song-item flex items-center p-3 rounded-lg cursor-pointer transition-all mb-2 ${
                    currentSong?.id === song.id ? "bg-red-600" : "hover:bg-red-600/20"
                  }`}
                >
                  <div 
                    onClick={() => onSongSelect(song)}
                    className="flex items-center flex-1"
                  >
                    <div className="w-6 h-6 rounded-full bg-red-600 flex items-center justify-center mr-3 text-xs font-bold">
                      {String(index + 1).padStart(2, "0")}
                    </div>
                    <div className="w-8 h-8 rounded-lg bg-gray-700 mr-3 flex items-center justify-center">
                      {song.cover_image ? (
                        <img src={song.cover_image} alt="" className="w-full h-full object-cover rounded-lg" />
                      ) : (
                        <div className="w-4 h-4 bg-red-600 rounded"></div>
                      )}
                    </div>
                    <div className="flex-1">
                      <h3 className="font-semibold text-sm music-subtitle">{song.title}</h3>
                      <p className="text-gray-400 text-xs">{song.artist || "Unknown Artist"}</p>
                    </div>
                    <span className="text-gray-400 text-xs">{song.duration_formatted || formatDuration(song.duration)}</span>
                  </div>
                  <Button
                    onClick={(e) => {
                      e.stopPropagation();
                      onRemoveSong(song.id);
                    }}
                    className="ml-2 bg-transparent hover:bg-red-600/20 text-white p-1"
                    size="icon"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              ))
            ) : (
              <div className={cn(
                "h-full flex items-center justify-center rounded-lg transition-colors",
                isDraggingOver ? 'bg-red-600/20' : ''
              )}>
                <div className="text-center text-gray-400">
                  <Upload className="h-12 w-12 mx-auto mb-2 opacity-50" />
                  <p>No songs in playlist</p>
                  <p className="text-sm mt-2">Drag & drop audio files or click below to add</p>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="h-full flex items-center justify-center">
            <div className="text-center text-gray-400">
              <p>No playlist selected</p>
              <p className="text-sm mt-2">Create or select a playlist to start</p>
            </div>
          </div>
        )}

        <div className="mt-4 pt-4 border-t border-white/20">
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept="audio/*"
            className="hidden"
            onChange={(e) => onFileSelect(e.target.files)}
          />
          <Button
            className="w-full bg-white/10 hover:bg-white/20 text-white border border-white/30 backdrop-blur-sm music-subtitle"
            onClick={() => fileInputRef.current?.click()}
            disabled={!currentPlaylist}
          >
            <Plus className="h-4 w-4 mr-2" />
            Añadir Canción
          </Button>
        </div>
      </div>
    </div>
  )
}