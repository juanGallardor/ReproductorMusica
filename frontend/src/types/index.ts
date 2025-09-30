import * as React from "react"

// Tipos principales (copiados directamente para evitar import circular)
export interface Song {
  id: string;
  title: string;
  artist?: string;
  album?: string;
  year?: number;
  duration: number;
  duration_formatted: string;
  format: string;
  filename: string;
  play_count: number;
  cover_image?: string;
}

export interface Playlist {
  id: string;
  name: string;
  description?: string;
  cover_image?: string;
  song_count: number;
  total_duration: number;
  total_duration_formatted: string;
  songs?: Song[];
  current_position?: number;
}

export interface PlayerStatus {
  is_playing: boolean;
  is_paused: boolean;
  volume: number;
  repeat_mode: 'off' | 'one' | 'all';
  shuffle_mode: boolean;
  position_seconds: number;
  position_formatted: string;
  current_song?: Song;
  current_playlist?: Playlist;
}

// Component props types
export interface SliderProps {
  value: number[]
  onValueChange: (value: number[]) => void
  max?: number
  min?: number
  step?: number
  disabled?: boolean
  className?: string
}

// Player state types
export type RepeatMode = "off" | "all" | "one"

export interface PlayerState {
  isPlaying: boolean
  currentSong: Song | null
  currentPlaylist: Playlist | null
  progress: number
  volume: number
  currentTime: string
  totalTime: string
  repeatMode: RepeatMode
  shuffleMode: boolean
  isMuted: boolean
  previousVolume: number
}

// Audio visualization types
export interface AudioData {
  frequencies: number[]
  waveform: number[]
}

// File upload types
export interface UploadMetadata {
  title?: string
  artist?: string
  album?: string
  year?: number
}

export interface FileUpload {
  file: File
  metadata?: UploadMetadata
}

// Playlist creation types
export interface CreatePlaylistData {
  name: string
  description?: string
  cover_image?: string
}

// UI component types
export interface VinylPlayerProps {
  initialPlaylist?: Playlist
  autoPlay?: boolean
  className?: string
}

export interface PlaylistItemProps {
  playlist: Playlist
  isActive: boolean
  onClick: (playlist: Playlist) => void
}

export interface SongItemProps {
  song: Song
  index: number
  isActive: boolean
  onClick: (song: Song) => void
}

// Modal types
export interface ModalProps {
  isOpen: boolean
  onClose: () => void
  title: string
  children: React.ReactNode
}

// Sidebar types
export interface SidebarProps {
  isOpen: boolean
  onClose: () => void
  playlists: Playlist[]
  currentPlaylist: Playlist | null
  onPlaylistSelect: (playlist: Playlist) => void
  onCreatePlaylist: (data: CreatePlaylistData) => void
}

// Audio control types
export interface AudioControlsProps {
  isPlaying: boolean
  onPlay: () => void
  onPause: () => void
  onNext: () => void
  onPrevious: () => void
  onRepeatToggle: () => void
  onShuffleToggle: () => void
  repeatMode: RepeatMode
  shuffleMode: boolean
}

// Progress bar types
export interface ProgressBarProps {
  progress: number
  duration: number
  onSeek: (position: number) => void
  audioData: number[]
  isPlaying: boolean
}

// Volume control types
export interface VolumeControlProps {
  volume: number
  isMuted: boolean
  onVolumeChange: (volume: number) => void
  onMuteToggle: () => void
}

// Error types
export interface ApiError {
  message: string
  status?: number
  code?: string
}

export interface ErrorBoundaryState {
  hasError: boolean
  error?: Error
}

// Event types
export interface PlayerEvent {
  type: 'play' | 'pause' | 'stop' | 'next' | 'previous' | 'seek' | 'volume'
  data?: any
}

// Settings types
export interface PlayerSettings {
  crossfadeEnabled: boolean
  crossfadeDuration: number
  gaplessPlayback: boolean
  normalizeVolume: boolean
  theme: 'dark' | 'light' | 'auto'
}

// Search types
export interface SearchResults {
  songs: Song[]
  playlists: Playlist[]
  artists: string[]
  albums: string[]
}

export interface SearchFilters {
  query: string
  type?: 'songs' | 'playlists' | 'artists' | 'albums' | 'all'
  sortBy?: 'relevance' | 'title' | 'artist' | 'date'
  order?: 'asc' | 'desc'
}