import { Button } from "@/components/ui/button"
import { Plus, X, Trash2 } from "lucide-react"
import type { Playlist } from '@/lib/api'

interface PlaylistSidebarProps {
  sidebarOpen: boolean
  onCloseSidebar: () => void
  playlists: Playlist[]
  currentPlaylist: Playlist | null
  onSelectPlaylist: (playlist: Playlist) => Promise<void>
  onDeletePlaylist: (playlistId: string) => Promise<void>
  showCreatePlaylist: boolean
  onShowCreatePlaylist: (show: boolean) => void
  newPlaylistName: string
  onSetNewPlaylistName: (name: string) => void
  newPlaylistDescription: string
  onSetNewPlaylistDescription: (desc: string) => void
  onCreatePlaylist: () => Promise<void>
}

export function PlaylistSidebar({
  sidebarOpen,
  onCloseSidebar,
  playlists,
  currentPlaylist,
  onSelectPlaylist,
  onDeletePlaylist,
  showCreatePlaylist,
  onShowCreatePlaylist,
  newPlaylistName,
  onSetNewPlaylistName,
  newPlaylistDescription,
  onSetNewPlaylistDescription,
  onCreatePlaylist
}: PlaylistSidebarProps) {
  if (!sidebarOpen) return null

  return (
    <>
      {/* Sidebar */}
      <div className="fixed inset-0 z-50">
        <div
          className="sidebar-overlay absolute inset-0 bg-black/50 backdrop-blur-sm"
          onClick={onCloseSidebar}
        />
        <div className="absolute top-0 right-0 h-full w-80 bg-black/80 backdrop-blur-lg border-l border-white/20 text-white p-6 overflow-y-auto custom-scrollbar shadow-2xl">
          <div className="flex items-center justify-between mb-8">
            <h2 className="text-xl font-bold music-title">Music Library</h2>
            <div className="flex gap-2">
              <Button
                onClick={() => onShowCreatePlaylist(true)}
                className="bg-white/20 hover:bg-white/30 text-white p-2 backdrop-blur-sm"
                size="icon"
              >
                <Plus className="h-4 w-4" />
              </Button>
              <Button
                onClick={onCloseSidebar}
                className="bg-white/20 hover:bg-white/30 text-white p-2 backdrop-blur-sm"
                size="icon"
              >
                <X className="h-5 w-5" />
              </Button>
            </div>
          </div>

          <div className="space-y-8">
            {/* Playlists Section */}
            <div>
              <h3 className="text-lg font-semibold mb-4 text-white drop-shadow-lg music-subtitle">Playlists</h3>
              <div className="space-y-4">
                {playlists.map((playlist) => (
                  <div
                    key={playlist.id}
                    className={`cursor-pointer transition-all duration-300 hover:scale-105 ${
                      currentPlaylist?.id === playlist.id ? "opacity-100" : "opacity-80 hover:opacity-100"
                    }`}
                  >
                    <div className="flex items-center gap-4">
                      <div
                        onClick={() => onSelectPlaylist(playlist)}
                        className="flex items-center gap-4 flex-1"
                      >
                        <img
                          src={playlist.cover_image || "/placeholder-album.jpg"}
                          alt={playlist.name}
                          className="w-16 h-16 rounded-lg object-cover shadow-lg"
                        />
                        <div className="flex-1">
                          <h3 className="font-bold text-lg text-white drop-shadow-lg music-title">{playlist.name}</h3>
                          <p className="text-white/80 text-sm drop-shadow-md">{playlist.song_count} songs</p>
                        </div>
                      </div>
                      <Button
                        onClick={(e) => {
                          e.stopPropagation();
                          onDeletePlaylist(playlist.id);
                        }}
                        className="bg-transparent hover:bg-red-600/20 text-white p-1"
                        size="icon"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Settings Section */}
            <div>
              <h3 className="text-lg font-semibold mb-4 text-white drop-shadow-lg music-subtitle">Actions</h3>
              
              {/* Create Playlist */}
              <div
                onClick={() => onShowCreatePlaylist(true)}
                className="cursor-pointer transition-all duration-300 hover:scale-105 opacity-80 hover:opacity-100"
              >
                <div className="flex items-center gap-4">
                  <div className="w-16 h-16 rounded-lg bg-white/20 backdrop-blur-sm flex items-center justify-center shadow-lg">
                    <Plus className="h-8 w-8 text-white" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-bold text-lg text-white drop-shadow-lg music-subtitle">Create Playlist</h3>
                    <p className="text-white/80 text-sm drop-shadow-md">Add new playlist</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Create Playlist Modal */}
      {showCreatePlaylist && (
        <div className="fixed inset-0 z-60 flex items-center justify-center">
          <div className="absolute inset-0 bg-black/80 backdrop-blur-sm" onClick={() => onShowCreatePlaylist(false)} />
          <div className="relative bg-black border border-white/20 rounded-lg p-6 w-96 text-white">
            <h3 className="text-xl font-bold mb-4 music-title">Añadir Playlist</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2 music-subtitle">Nombre de la Playlist</label>
                <input
                  type="text"
                  value={newPlaylistName}
                  onChange={(e) => onSetNewPlaylistName(e.target.value)}
                  className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400"
                  placeholder="Ingresa el nombre..."
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2 music-subtitle">Descripción (opcional)</label>
                <textarea
                  value={newPlaylistDescription}
                  onChange={(e) => onSetNewPlaylistDescription(e.target.value)}
                  className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400"
                  placeholder="Describe tu playlist..."
                  rows={3}
                />
              </div>
              <div className="flex gap-3">
                <Button
                  onClick={onCreatePlaylist}
                  className="flex-1 bg-red-600 hover:bg-red-700 text-white music-subtitle"
                >
                  Crear Playlist
                </Button>
                <Button
                  onClick={() => {
                    onShowCreatePlaylist(false)
                    onSetNewPlaylistName("")
                    onSetNewPlaylistDescription("")
                  }}
                  variant="outline"
                  className="flex-1 border-white/20 text-white hover:bg-white/10 bg-transparent music-subtitle"
                >
                  Cancelar
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  )
}