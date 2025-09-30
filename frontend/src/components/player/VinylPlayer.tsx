import type { Song, Playlist } from '@/lib/api'

interface VinylPlayerProps {
  isPlaying: boolean
  currentSong: Song | null
  currentPlaylist: Playlist | null
}

export function VinylPlayer({ isPlaying, currentSong, currentPlaylist }: VinylPlayerProps) {
  return (
    <div className="h-full flex items-center justify-center relative">
      <div
        className={`absolute top-0 left-1/2 transform -translate-x-1/2 translate-x-2.5 z-30 vinyl-arm ${isPlaying ? "tonearm-playing" : ""}`}
      >
        <img src="/images/tonearm.png" alt="Tonearm" className="w-[36rem] h-auto object-contain" />
      </div>

      {/* Vinyl Container */}
      <div className="vinyl-container relative">
        <div className={`vinyl-disc relative ${isPlaying ? "vinyl-spinning vinyl-subtle-movement" : ""}`}>
          <img
            src={
              currentPlaylist?.cover_image 
                ? `http://localhost:8000${currentPlaylist.cover_image}` 
                : currentSong?.cover_image || "/placeholder-album.jpg"
            }
            alt="Album Cover"
            className="w-full h-full object-cover"
          />

          {/* Song Cover in Center */}
          <div className="absolute inset-0 flex items-center justify-center">
            <div className={`w-44 h-44 rounded-full overflow-hidden bg-black border-4 border-white ${isPlaying ? "vinyl-spinning" : ""}`}>
              <img
                src={
                  currentPlaylist?.cover_image 
                    ? `http://localhost:8000${currentPlaylist.cover_image}` 
                    : "/placeholder-album.jpg"
                }
                alt="Album Cover"
                className="w-full h-full object-cover"
                onError={(e) => {
                  // Fallback si la imagen falla al cargar
                  (e.target as HTMLImageElement).src = "/placeholder-album.jpg"
                }}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}