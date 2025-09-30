"use client"

import { useState, useEffect, useRef, useCallback } from "react"
import { Button } from "@/components/ui/button"
import { api } from "@/lib/api"
import {
  Play,
  Pause,
  SkipBack,
  SkipForward,
  Menu,
  X,
  Plus,
  Repeat,
  Repeat1,
  Shuffle,
  Volume2,
  VolumeX,
  Upload,
  Trash2,
  ImageIcon,
  Edit3,
  GripVertical,
  Save,
  Settings,
} from "lucide-react"

import type { Song, Playlist, PlayerStatus } from "@/lib/api"

type RepeatMode = "off" | "all" | "one"

export default function VinylMusicPlayer() {
  const [isSwitchingPlaylist, setIsSwitchingPlaylist] = useState(false)
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentSong, setCurrentSong] = useState<Song | null>(null)
  const [currentPlaylist, setCurrentPlaylist] = useState<Playlist | null>(null)
  const [playlists, setPlaylists] = useState<Playlist[]>([])
  const [progress, setProgress] = useState(0)
  const [volume, setVolume] = useState(75)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [currentTime, setCurrentTime] = useState("0:00")
  const [totalTime, setTotalTime] = useState("3:45")
  const [audioData, setAudioData] = useState<number[]>([])
  const [showCreatePlaylist, setShowCreatePlaylist] = useState(false)
  const [showEditPlaylist, setShowEditPlaylist] = useState(false)
  const [showEditSong, setShowEditSong] = useState(false)
  const [editingSong, setEditingSong] = useState<Song | null>(null)
  const [newPlaylistName, setNewPlaylistName] = useState("")
  const [newPlaylistDescription, setNewPlaylistDescription] = useState("")
  const [repeatMode, setRepeatMode] = useState<RepeatMode>("off")
  const [shuffleMode, setShuffleMode] = useState(false)
  const [isMuted, setIsMuted] = useState(false)
  const [previousVolume, setPreviousVolume] = useState(75)
  const [error, setError] = useState<string | null>(null)
  const [isDraggingOver, setIsDraggingOver] = useState(false)
  const [success, setSuccess] = useState<string | null>(null)
  const [showVolumeSlider, setShowVolumeSlider] = useState(false)
  const [progressTooltip, setProgressTooltip] = useState({ visible: false, x: 0, time: "0:00" })
  const [volumeHoverTimeout, setVolumeHoverTimeout] = useState<NodeJS.Timeout | null>(null)
  const [coverPreview, setCoverPreview] = useState<string | null>(null)
  
  // Drag and drop states
  const [draggedSongIndex, setDraggedSongIndex] = useState<number | null>(null)
  const [dragOverIndex, setDragOverIndex] = useState<number | null>(null)
  
  // Edit states
  const [editSongTitle, setEditSongTitle] = useState("")
  const [editSongArtist, setEditSongArtist] = useState("")
  const [editSongAlbum, setEditSongAlbum] = useState("")
  const [editSongYear, setEditSongYear] = useState<number | undefined>()
  
  const fileInputRef = useRef<HTMLInputElement>(null)
  const playlistCoverInputRef = useRef<HTMLInputElement>(null)
  const songCoverInputRef = useRef<HTMLInputElement>(null)
  const statusIntervalRef = useRef<NodeJS.Timeout | null>(null)
  const progressBarRef = useRef<HTMLDivElement>(null)

  // CRÍTICO: Solo Backend Audio - No más elementos audio del frontend
  // Removemos audioRef completamente

  // Generar datos de audio falsos para visualización
  useEffect(() => {
    const generateAudioData = () => {
      return Array.from({ length: 35 }, (_, i) => {
        if (isPlaying) {
          return Math.random() * 100 + (Math.sin((Date.now() / 100) + i) * 20) + 30
        }
        return Math.random() * 10 + 5
      })
    }

    const interval = setInterval(() => {
      setAudioData(generateAudioData())
    }, 150)

    return () => clearInterval(interval)
  }, [isPlaying])

  // NUEVO: Sincronización constante con backend
  const syncWithBackend = useCallback(async () => {
  try {
    const status = await api.getPlayerStatus()
    
    setIsPlaying(status.is_playing)
    setVolume(status.volume)
    setRepeatMode(status.repeat_mode)
    setShuffleMode(status.shuffle_mode)
    
    // Actualizar progreso
    if (status.position_seconds && status.current_song) {
      const progressPercent = (status.position_seconds / status.current_song.duration) * 100
      setProgress(progressPercent)
      setCurrentTime(status.position_formatted)
      setTotalTime(status.current_song.duration_formatted)
    }
    
    // Actualizar canción actual
    if (status.current_song && status.current_song.id !== currentSong?.id) {
      setCurrentSong(status.current_song)
    }
    
    // CRÍTICO: Solo actualizar playlist si NO estamos cambiando manualmente
    if (!isSwitchingPlaylist && status.current_playlist && status.current_playlist.id !== currentPlaylist?.id) {
      const fullPlaylist = await api.getPlaylist(status.current_playlist.id)
      setCurrentPlaylist(fullPlaylist)
    }
    
  } catch (err) {
    console.error('Error syncing with backend:', err)
  }
}, [currentSong?.id, currentPlaylist?.id, isSwitchingPlaylist]) // AGREGAR isSwitchingPlaylist

  // Sincronización automática cada segundo
  useEffect(() => {
    statusIntervalRef.current = setInterval(syncWithBackend, 1000)
    
    return () => {
      if (statusIntervalRef.current) {
        clearInterval(statusIntervalRef.current)
      }
    }
  }, [syncWithBackend])

  // ATAJOS DE TECLADO
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return
      }

      if (e.key === 'ArrowRight') {
        e.preventDefault()
        seekRelative(10)
      } else if (e.key === 'ArrowLeft') {
        e.preventDefault()
        seekRelative(-10)
      } else if (e.key === ' ') {
        e.preventDefault()
        togglePlay()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  
const seekRelative = async (seconds: number) => {
  if (!currentSong) return

  try {
    console.log(`[FRONTEND] Relative seek: ${seconds}s`)
    
    const currentPos = (progress / 100) * currentSong.duration
    const newTime = Math.max(0, Math.min(currentSong.duration, currentPos + seconds))
    const newPercent = (newTime / currentSong.duration) * 100
    
    // Actualizar visualmente
    setProgress(newPercent)
    const minutes = Math.floor(newTime / 60)
    const secs = Math.floor(newTime % 60)
    setCurrentTime(`${minutes}:${secs.toString().padStart(2, '0')}`)
    
    // Seek en backend
    await api.seek(newTime)
    console.log(`[FRONTEND] Relative seek completed`)
    
    // Confirmar sincronización
    setTimeout(async () => {
      await syncWithBackend()
    }, 200)
    
  } catch (err) {
    console.error('[FRONTEND] Error in relative seek:', err)
    await syncWithBackend()
  }
}


const handleCoverSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
  const file = e.target.files?.[0]
  if (file) {
    const reader = new FileReader()
    reader.onloadend = () => {
      setCoverPreview(reader.result as string)
    }
    reader.readAsDataURL(file)
  }
}

  const seekToPosition = async (positionPercent: number) => {
  if (!currentSong) return

  try {
    console.log(`[FRONTEND] Seeking to ${positionPercent}%`)
    
    const newTime = (positionPercent / 100) * currentSong.duration
    console.log(`[FRONTEND] New time: ${newTime}s of ${currentSong.duration}s`)
    
    // Primero actualizar visualmente para respuesta inmediata
    setProgress(positionPercent)
    const minutes = Math.floor(newTime / 60)
    const seconds = Math.floor(newTime % 60)
    setCurrentTime(`${minutes}:${seconds.toString().padStart(2, '0')}`)
    
    // Luego hacer el seek en el backend
    await api.seek(newTime)
    console.log(`[FRONTEND] Backend seek completed`)
    
    // Sincronizar después de un pequeño delay para confirmar
    setTimeout(async () => {
      await syncWithBackend()
    }, 200)
    
  } catch (err) {
    console.error('[FRONTEND] Error seeking:', err)
    // Revertir cambios visuales si falla
    await syncWithBackend()
  }
}

  // Auto-hide messages
  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => setError(null), 5000)
      return () => clearTimeout(timer)
    }
  }, [error])

  useEffect(() => {
    if (success) {
      const timer = setTimeout(() => setSuccess(null), 3000)
      return () => clearTimeout(timer)
    }
  }, [success])

  const fetchPlaylists = async () => {
    try {
      const data = await api.getPlaylists()
      setPlaylists(data)
      
      if (data.length > 0 && !currentPlaylist) {
        const fullPlaylist = await api.getPlaylist(data[0].id)
        setCurrentPlaylist(fullPlaylist)
        if (fullPlaylist.songs && fullPlaylist.songs.length > 0) {
          setCurrentSong(fullPlaylist.songs[0])
          await api.setCurrentPlaylist(fullPlaylist.id, 0)
        }
      }
    } catch (err) {
      console.error('Error fetching playlists:', err)
      setError('Failed to load playlists')
    }
  }

  // CRÍTICO: Play/Pause SOLO backend - sin frontend audio
  const togglePlay = async () => {
    if (!currentSong) {
      setError('No song selected. Please click on a song first.')
      return
    }

    try {
      if (isPlaying) {
        await api.pause()
        console.log('[BACKEND] Paused')
      } else {
        await api.play()
        console.log('[BACKEND] Playing')
      }
      await syncWithBackend()
    } catch (err) {
      console.error('Error toggling play:', err)
      setError('Failed to control playback')
    }
  }


  const nextSong = async () => {
    try {
      await api.next()
      await syncWithBackend()
      console.log('[BACKEND] Next song')
    } catch (err) {
      console.error('Error skipping to next:', err)
      setError('Failed to skip to next song')
    }
  }

  const prevSong = async () => {
    try {
      await api.previous()
      await syncWithBackend()
      console.log('[BACKEND] Previous song')
    } catch (err) {
      console.error('Error skipping to previous:', err)
      setError('Failed to skip to previous song')
    }
  }

  const toggleRepeatMode = async () => {
    const modes: RepeatMode[] = ["off", "all", "one"]
    const currentIndex = modes.indexOf(repeatMode)
    const nextIndex = (currentIndex + 1) % modes.length
    const nextMode = modes[nextIndex]
    
    try {
      await api.setRepeatMode(nextMode)
      setRepeatMode(nextMode)
    } catch (err) {
      console.error('Error setting repeat mode:', err)
    }
  }

  const toggleShuffle = async () => {
    try {
      await api.setShuffleMode(!shuffleMode)
      setShuffleMode(!shuffleMode)
    } catch (err) {
      console.error('Error setting shuffle mode:', err)
    }
  }

  const handleVolumeChange = async (newVolume: number) => {
    try {
      setVolume(newVolume)
      
      if (newVolume === 0 && !isMuted) {
        setIsMuted(true)
      } else if (newVolume > 0 && isMuted) {
        setIsMuted(false)
      }
      
      await api.setVolume(newVolume)
    } catch (err) {
      console.error('Error setting volume:', err)
    }
  }

  const toggleMute = async () => {
    try {
      if (isMuted) {
        const volumeToRestore = previousVolume > 0 ? previousVolume : 50
        setVolume(volumeToRestore)
        setIsMuted(false)
        await api.setVolume(volumeToRestore)
      } else {
        setPreviousVolume(volume)
        setVolume(0)
        setIsMuted(true)
        await api.setVolume(0)
      }
    } catch (err) {
      console.error('Error toggling mute:', err)
    }
  }

  // CRÍTICO: Seleccionar canción - solo backend
  const selectSong = async (song: Song) => {
  try {
    console.log(`[BACKEND] Selecting song: ${song.title}`)
    
    // CRÍTICO: Marcar que estamos cambiando
    setIsSwitchingPlaylist(true)
    
    if (currentPlaylist && currentPlaylist.songs) {
      const songIndex = currentPlaylist.songs.findIndex(s => s.id === song.id)
      if (songIndex !== -1) {
        await api.setCurrentPlaylist(currentPlaylist.id, songIndex)
        await api.play()
        await syncWithBackend()
        
        setSuccess(`Playing: ${song.title}`)
      }
    }
    
    // Permitir sincronización después de 1 segundo
    setTimeout(() => {
      setIsSwitchingPlaylist(false)
    }, 1000)
    
  } catch (err) {
    console.error('Error selecting song:', err)
    setError('Failed to play song')
    setIsSwitchingPlaylist(false)
  }
}
  const selectPlaylist = async (playlist: Playlist) => {
  try {
    console.log(`[FRONTEND] Selecting playlist: ${playlist.name}`)
    
    // CRÍTICO: Marcar que estamos cambiando playlist
    setIsSwitchingPlaylist(true)
    
    const fullPlaylist = await api.getPlaylist(playlist.id)
    setCurrentPlaylist(fullPlaylist)
    
    if (fullPlaylist.songs && fullPlaylist.songs.length > 0) {
      await api.setCurrentPlaylist(fullPlaylist.id, 0)
      await syncWithBackend()
    }
    
    setSidebarOpen(false)
    
    // Después de 2 segundos, permitir sincronización normal
    setTimeout(() => {
      setIsSwitchingPlaylist(false)
    }, 2000)
    
  } catch (err) {
    console.error('Error selecting playlist:', err)
    setIsSwitchingPlaylist(false) // Reset en caso de error
  }
}

  // NUEVO: Manejo mejorado de imágenes de cover

const createPlaylist = async () => {
  if (newPlaylistName.trim()) {
    try {
      const playlist = await api.createPlaylist(newPlaylistName, newPlaylistDescription)
      
      // Subir imagen si está seleccionada
      if (playlistCoverInputRef.current?.files?.[0]) {
        const formData = new FormData()
        formData.append('cover_file', playlistCoverInputRef.current.files[0])
        
        console.log(`[FRONTEND] Uploading cover for playlist ${playlist.id}`)
        
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/playlists/${playlist.id}/cover`, {
          method: 'PUT',
          body: formData
        })
        
        if (response.ok) {
          console.log('Playlist cover uploaded successfully')
        } else {
          console.error('Failed to upload cover:', await response.text())
        }
      }
      
      await fetchPlaylists()
      setNewPlaylistName("")
      setNewPlaylistDescription("")
      setShowCreatePlaylist(false)
      setSuccess('Playlist created successfully!')
      
      // Refrescar playlist actual si es la nueva
      const fullPlaylist = await api.getPlaylist(playlist.id)
      setCurrentPlaylist(fullPlaylist)
    } catch (err) {
      console.error('Error creating playlist:', err)
      setError('Failed to create playlist')
    }
  }
}

  const editPlaylist = () => {
  if (currentPlaylist) {
    setNewPlaylistName(currentPlaylist.name)
    setNewPlaylistDescription(currentPlaylist.description || "")
    setCoverPreview(null) // AGREGAR ESTO
    setShowEditPlaylist(true)
  }
}

  const savePlaylistEdit = async () => {
    if (!currentPlaylist || !newPlaylistName.trim()) return

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/playlists/${currentPlaylist.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newPlaylistName,
          description: newPlaylistDescription
        })
      })

      if (response.ok) {
        // Subir nueva imagen si está seleccionada
        if (playlistCoverInputRef.current?.files?.[0]) {
          const formData = new FormData()
          formData.append('cover_file', playlistCoverInputRef.current.files[0])
          
          const coverResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/playlists/${currentPlaylist.id}/cover`, {
            method: 'PUT',
            body: formData
          })
          
          if (coverResponse.ok) {
            console.log('Playlist cover updated successfully')
          }
        }

        await fetchPlaylists()
        setShowEditPlaylist(false)
        setSuccess('Playlist updated successfully!')
        
        // Recargar playlist actual
        const updatedPlaylist = await api.getPlaylist(currentPlaylist.id)
        setCurrentPlaylist(updatedPlaylist)
      }
    } catch (err) {
      console.error('Error updating playlist:', err)
      setError('Failed to update playlist')
    }
  }

  const openEditSong = (song: Song) => {
    setEditingSong(song)
    setEditSongTitle(song.title)
    setEditSongArtist(song.artist || "")
    setEditSongAlbum(song.album || "")
    setEditSongYear(song.year)
    setShowEditSong(true)
  }

  const saveEditSong = async () => {
    if (!editingSong) return

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/songs/${editingSong.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: editSongTitle,
          artist: editSongArtist || null,
          album: editSongAlbum || null,
          year: editSongYear || null
        })
      })

      if (response.ok) {
        // Subir nueva imagen si está seleccionada
        if (songCoverInputRef.current?.files?.[0]) {
          const formData = new FormData()
          formData.append('cover_file', songCoverInputRef.current.files[0])
          
          const coverResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/songs/${editingSong.id}/cover`, {
            method: 'PUT',
            body: formData
          })
          
          if (coverResponse.ok) {
            console.log('Song cover updated successfully')
          }
        }

        setShowEditSong(false)
        setEditingSong(null)
        setSuccess('Song updated successfully!')
        
        // Recargar playlist para mostrar cambios
        if (currentPlaylist) {
          const updatedPlaylist = await api.getPlaylist(currentPlaylist.id)
          setCurrentPlaylist(updatedPlaylist)
          
          // Actualizar canción actual si es la que se editó
          if (currentSong?.id === editingSong.id) {
            const updatedSong = updatedPlaylist.songs?.find(s => s.id === editingSong.id)
            if (updatedSong) {
              setCurrentSong(updatedSong)
            }
          }
        }
      }
    } catch (err) {
      console.error('Error updating song:', err)
      setError('Failed to update song')
    }
  }

const deletePlaylist = async (playlistId: string) => {
  // DEBUG: Verificar URL
  console.log('API_URL being used:', process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api');
  
  if (window.confirm('Are you sure you want to delete this playlist?')) {
      try {
      await api.deletePlaylist(playlistId)
        await fetchPlaylists()
        
        if (currentPlaylist?.id === playlistId) {
          setCurrentPlaylist(null)
          setCurrentSong(null)
        }
        setSuccess('Playlist deleted successfully!')
      } catch (err) {
        console.error('Error deleting playlist:', err)
        setError('Failed to delete playlist')
      }
    }
  }

  const handleFileSelect = async (files: FileList | null) => {
    if (!files || files.length === 0 || !currentPlaylist) {
      setError('Please select a playlist first')
      return
    }

    try {
      let uploadedCount = 0
      for (const file of Array.from(files)) {
        if (file.type.startsWith('audio/')) {
          console.log(`Uploading ${file.name} to playlist ${currentPlaylist.id}`)
          await api.uploadAndAddToPlaylist(currentPlaylist.id, file)
          uploadedCount++
        }
      }
      
      if (uploadedCount > 0) {
        // Recargar playlist actual
        const fullPlaylist = await api.getPlaylist(currentPlaylist.id)
        setCurrentPlaylist(fullPlaylist)
        
        await fetchPlaylists()
        
        if (fullPlaylist.songs && fullPlaylist.songs.length === uploadedCount && !currentSong) {
          setCurrentSong(fullPlaylist.songs[0])
        }
        setSuccess(`${uploadedCount} song(s) uploaded successfully!`)
      }
    } catch (err) {
      console.error('Error uploading songs:', err)
      setError('Failed to upload songs. Please check file format and try again.')
    }
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDraggingOver(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDraggingOver(false)
  }

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault()
    setIsDraggingOver(false)
    
    const files = e.dataTransfer.files
    await handleFileSelect(files)
  }

  const removeSongFromPlaylist = async (songId: string) => {
    if (!currentPlaylist || !window.confirm('Remove this song from the playlist?')) return

    try {
      await api.removeSongFromPlaylist(currentPlaylist.id, songId)
      
      const fullPlaylist = await api.getPlaylist(currentPlaylist.id)
      setCurrentPlaylist(fullPlaylist)
      
      await fetchPlaylists()
      
      if (currentSong?.id === songId) {
        if (fullPlaylist.songs && fullPlaylist.songs.length > 0) {
          setCurrentSong(fullPlaylist.songs[0])
        } else {
          setCurrentSong(null)
        }
      }
      setSuccess('Song removed successfully!')
    } catch (err) {
      console.error('Error removing song:', err)
      setError('Failed to remove song')
    }
  }

  // Control de volumen
  const handleVolumeMouseEnter = () => {
    if (volumeHoverTimeout) {
      clearTimeout(volumeHoverTimeout)
    }
    setShowVolumeSlider(true)
  }

  const handleVolumeMouseLeave = () => {
    const timeout = setTimeout(() => {
      setShowVolumeSlider(false)
    }, 500)
    setVolumeHoverTimeout(timeout)
  }

  const handleSliderMouseEnter = () => {
    if (volumeHoverTimeout) {
      clearTimeout(volumeHoverTimeout)
    }
    setShowVolumeSlider(true)
  }

  const handleSliderMouseLeave = () => {
    const timeout = setTimeout(() => {
      setShowVolumeSlider(false)
    }, 200)
    setVolumeHoverTimeout(timeout)
  }

  // Drag and Drop para reordenar canciones
  const handleSongDragStart = (e: React.DragEvent, index: number) => {
    setDraggedSongIndex(index)
    e.dataTransfer.effectAllowed = 'move'
  }

  const handleSongDragOver = (e: React.DragEvent, index: number) => {
    e.preventDefault()
    setDragOverIndex(index)
  }

  const handleSongDragLeave = () => {
    setDragOverIndex(null)
  }

  const handleSongDrop = async (e: React.DragEvent, dropIndex: number) => {
    e.preventDefault()
    
    if (draggedSongIndex === null || draggedSongIndex === dropIndex || !currentPlaylist) {
      setDraggedSongIndex(null)
      setDragOverIndex(null)
      return
    }

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/playlists/${currentPlaylist.id}/songs/reorder`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          from_position: draggedSongIndex,
          to_position: dropIndex
        })
      })

      if (response.ok) {
        const fullPlaylist = await api.getPlaylist(currentPlaylist.id)
        setCurrentPlaylist(fullPlaylist)
        setSuccess('Song reordered successfully!')
      } else {
        setError('Failed to reorder song')
      }
    } catch (err) {
      console.error('Error reordering song:', err)
      setError('Failed to reorder song')
    }

    setDraggedSongIndex(null)
    setDragOverIndex(null)
  }

  // Progress bar interactiva
  const handleProgressMouseMove = (e: React.MouseEvent) => {
    if (!progressBarRef.current || !currentSong) return

    const rect = progressBarRef.current.getBoundingClientRect()
    const x = e.clientX - rect.left
    const percent = (x / rect.width) * 100
    const time = (percent / 100) * currentSong.duration
    
    const minutes = Math.floor(time / 60)
    const seconds = Math.floor(time % 60)
    const timeStr = `${minutes}:${seconds.toString().padStart(2, '0')}`

    setProgressTooltip({
      visible: true,
      x: e.clientX,
      time: timeStr
    })
  }

  const handleProgressMouseLeave = () => {
    setProgressTooltip({ visible: false, x: 0, time: "0:00" })
  }

  const handleProgressClick = (e: React.MouseEvent) => {
    if (!progressBarRef.current || !currentSong) return

    const rect = progressBarRef.current.getBoundingClientRect()
    const x = e.clientX - rect.left
    const percent = (x / rect.width) * 100
    
    seekToPosition(Math.max(0, Math.min(100, percent)))
  }

  const formatDuration = (seconds: number) => {
    const minutes = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${minutes}:${secs.toString().padStart(2, '0')}`
  }

  // Inicializar datos al cargar componente
  useEffect(() => {
    fetchPlaylists()
    syncWithBackend()
  }, [])

  return (
    <div className="h-screen w-full inverted-diagonal-split-gradient overflow-hidden relative">
      {/* Progress tooltip */}
      {progressTooltip.visible && (
        <div 
          className="progress-tooltip fixed z-[10000] bg-black/90 text-white px-3 py-1 rounded text-sm pointer-events-none"
          style={{ 
            left: progressTooltip.x - 20, 
            bottom: 120,
            opacity: 1,
            visibility: 'visible'
          }}
        >
          {progressTooltip.time}
        </div>
      )}

      {/* Background text overlay */}
      <div className="absolute inset-0 pointer-events-none z-0">
        <div className="absolute left-8 top-1/6 transform -translate-y-1/2 text-white/5 text-8xl font-bold whitespace-nowrap rotate-90 origin-left">
          {currentSong?.title || "VINYL"}
        </div>
        <div className="absolute right-8 top-1/6 transform -translate-y-1/2 text-black/5 text-9xl font-bold whitespace-nowrap -rotate-90 origin-right">
          {currentPlaylist?.name.split(" ").slice(0, 2).join(" ") || "PLAYER"}
        </div>
      </div>

      {/* Bottom progress bar */}
      <div className="absolute bottom-0 left-0 z-20">
        <div className="diagonal-progress-container bg-gradient-to-r from-gray-200 to-white shadow-lg">
          <div className="flex items-center gap-2 p-4 min-w-0">
            <div className="flex items-center gap-2 flex-shrink-0">
              <Button onClick={prevSong} className="bg-black/20 hover:bg-black/30 text-black p-2" size="icon">
                <SkipBack className="h-4 w-4" />
              </Button>
              <Button onClick={togglePlay} className="bg-red-600 hover:bg-red-700 text-white w-10 h-10" size="icon">
                {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
              </Button>
              <Button onClick={nextSong} className="bg-black/20 hover:bg-black/30 text-black p-2" size="icon">
                <SkipForward className="h-4 w-4" />
              </Button>
            </div>

            {/* Audio visualizer INTERACTIVO */}
            <div 
              ref={progressBarRef}
              className="h-10 flex items-end justify-center gap-1 px-2 flex-shrink-0 progress-bar-container"
              onMouseMove={handleProgressMouseMove}
              onMouseLeave={handleProgressMouseLeave}
              onClick={handleProgressClick}
            >
              {audioData.slice(0, 35).map((height, index) => {
                const barHeight = Math.max(4, height * 0.3)
                const progressPerBar = 100 / 35
                const barStartProgress = index * progressPerBar
                const barEndProgress = (index + 1) * progressPerBar

                let fillPercentage = 0
                if (isPlaying && progress > barStartProgress) {
                  if (progress >= barEndProgress) {
                    fillPercentage = 100
                  } else {
                    fillPercentage = ((progress - barStartProgress) / progressPerBar) * 100
                  }
                }

                return (
                  <div key={index} className="relative w-1 cursor-pointer">
                    <div
                      className="bg-gray-600 w-full transition-all duration-100 rounded-t"
                      style={{ height: `${barHeight}px` }}
                    />
                    <div
                      className="absolute bottom-0 left-0 w-full bg-red-600 transition-all duration-300 rounded-t"
                      style={{
                        height: `${(barHeight * fillPercentage) / 100}px`,
                      }}
                    />
                  </div>
                )
              })}
            </div>

            <div className="flex items-center gap-1 flex-shrink-0">
              <Button
                onClick={toggleRepeatMode}
                className={`p-2 ${repeatMode !== "off" ? "bg-red-600 text-white" : "bg-black/20 text-black"} hover:bg-red-700`}
                size="icon"
              >
                {repeatMode === "one" ? <Repeat1 className="h-3 w-3" /> : <Repeat className="h-3 w-3" />}
              </Button>
              <Button
                onClick={toggleShuffle}
                className={`p-2 ${shuffleMode ? "bg-red-600 text-white" : "bg-black/20 text-black"} hover:bg-red-700`}
                size="icon"
              >
                <Shuffle className="h-3 w-3" />
              </Button>
              
              {/* Volume Control MEJORADO */}
              <div 
                className="relative volume-control"
                onMouseEnter={handleVolumeMouseEnter}
                onMouseLeave={handleVolumeMouseLeave}
              >
                <Button 
                  onClick={toggleMute} 
                  className="bg-black/20 hover:bg-black/30 text-black p-2" 
                  size="icon"
                >
                  {isMuted || volume === 0 ? <VolumeX className="h-3 w-3" /> : <Volume2 className="h-3 w-3" />}
                </Button>
                
                <div 
                  className={`volume-slider ${showVolumeSlider ? 'show' : ''}`}
                  onMouseEnter={handleSliderMouseEnter}
                  onMouseLeave={handleSliderMouseLeave}
                  style={{
                    opacity: showVolumeSlider ? 1 : 0,
                    visibility: showVolumeSlider ? 'visible' : 'hidden',
                    pointerEvents: showVolumeSlider ? 'all' : 'none'
                  }}
                >
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={volume}
                    onChange={(e) => handleVolumeChange(Number(e.target.value))}
                    className="volume-range"
                  />
                  <div className="volume-text">{volume}%</div>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-1 text-xs text-black flex-shrink-0 ml-2">
              <span className="w-8">{currentTime}</span>
              <span className="text-black/50">/</span>
              <span className="w-8">{totalTime}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main 3-column layout */}
      <div className={`grid grid-cols-3 h-full relative z-10 transition-all duration-300 ${sidebarOpen ? "mr-80" : ""}`}>
        
        {/* Column 1 - Song List */}
        <div 
          className="h-full flex flex-col p-6 text-white"
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
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

          <div className="flex-1 overflow-hidden mb-4">
            {currentPlaylist ? (
              <div className="h-full overflow-y-auto custom-scrollbar pr-2">
                {currentPlaylist.songs && currentPlaylist.songs.length > 0 ? (
                  currentPlaylist.songs.map((song, index) => (
                    <div
                      key={song.id}
                      draggable
                      onDragStart={(e) => handleSongDragStart(e, index)}
                      onDragOver={(e) => handleSongDragOver(e, index)}
                      onDragLeave={handleSongDragLeave}
                      onDrop={(e) => handleSongDrop(e, index)}
                      className={`song-item song-item-draggable flex items-center p-3 rounded-lg cursor-pointer transition-all mb-2 ${
                        currentSong?.id === song.id ? "bg-red-600" : "hover:bg-red-600/20"
                      } ${draggedSongIndex === index ? "song-item-dragging" : ""} ${
                        dragOverIndex === index ? "song-item-drag-over" : ""
                      }`}
                    >
                      <div className="flex items-center gap-2 mr-3">
                        <GripVertical className="h-4 w-4 text-gray-400" />
                        <div className="w-6 h-6 rounded-full bg-red-600 flex items-center justify-center text-xs font-bold">
                          {String(index + 1).padStart(2, "0")}
                        </div>
                      </div>
                      
                      <div 
                        onClick={() => selectSong(song)}
                        className="flex items-center flex-1"
                      >
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
                          openEditSong(song);
                        }}
                        className="ml-2 bg-transparent hover:bg-blue-600/20 text-white p-1"
                        size="icon"
                      >
                        <Edit3 className="h-4 w-4" />
                      </Button>
                      
                      <Button
                        onClick={(e) => {
                          e.stopPropagation();
                          removeSongFromPlaylist(song.id);
                        }}
                        className="ml-1 bg-transparent hover:bg-red-600/20 text-white p-1"
                        size="icon"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  ))
                ) : (
                  <div className={`h-full flex items-center justify-center ${isDraggingOver ? 'bg-red-600/20' : ''} rounded-lg transition-colors`}>
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
                onChange={(e) => handleFileSelect(e.target.files)}
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

        {/* Column 2 - Vinyl Player */}
        <div className="h-full flex items-center justify-center relative">
          <div className={`absolute top-0 left-1/2 transform -translate-x-1/2 translate-x-2.5 z-30 vinyl-arm ${isPlaying ? "tonearm-playing" : ""}`}>
            <img src="/images/tonearm.png" alt="Tonearm" className="w-[36rem] h-auto object-contain" />
          </div>

          <div className="vinyl-container relative">
            <div className={`vinyl-disc relative ${isPlaying ? "vinyl-spinning vinyl-subtle-movement" : ""}`}>
              <img
                src="/images/new-vinyl-record.png"
                alt="Vinyl Record"
                className="w-[32rem] h-[32rem] object-contain"
              />

              {/* Song Cover in Center - WITH ROTATION */}
              <div className="absolute inset-0 flex items-center justify-center">
                <div className={`w-44 h-44 rounded-full overflow-hidden bg-black border-4 border-white ${isPlaying ? "vinyl-spinning" : ""}`}>
                  <img
                    src={currentPlaylist?.cover_image || currentSong?.cover_image || "/placeholder-album.jpg"}
                    alt="Album Cover"
                    className="w-full h-full object-cover"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Column 3 - Album Info */}
        <div className="h-full flex flex-col p-6 text-black relative">
          <div className="absolute top-6 right-6 flex items-center gap-4">
            <div className="flex gap-2">
              <div className="w-2 h-2 bg-black/50 rounded-full"></div>
              <div className="w-2 h-2 bg-black/50 rounded-full"></div>
              <div className="w-2 h-2 bg-black rounded-full"></div>
            </div>
            <Button
              onClick={() => setSidebarOpen(true)}
              className="bg-transparent hover:bg-black/10 text-black border-none shadow-none w-8 h-8"
              size="icon"
            >
              <Menu className="h-4 w-4" />
            </Button>
          </div>

          <div className="flex-1 flex flex-col justify-center items-center">
            <div className="mb-4">
              <h3 className="text-lg font-semibold text-black/70 text-center music-subtitle">Now Playing</h3>
              <h2 className="text-3xl font-bold text-black text-center mb-2 music-title">{currentPlaylist?.name || "No Playlist"}</h2>
            </div>

            <div className="flex gap-6 mb-8">
              <img
                src={currentPlaylist?.cover_image || "/placeholder-album.jpg"}
                alt="Album Cover"
                className="w-40 h-40 rounded-lg object-cover shadow-lg"
              />
              <div className="w-40 h-40 bg-black/10 rounded-lg flex items-center justify-center">
                <div className="text-black/30 text-5xl">♪</div>
              </div>
            </div>

            <div className="text-center max-w-md">
              <p className="text-sm text-black/70 mb-6 leading-relaxed">
                {currentPlaylist?.description || "Add a description to your playlist"}
              </p>

              <div className="flex gap-4 justify-center">
                <Button 
                  className="bg-black text-white hover:bg-gray-800 px-8 music-subtitle"
                  onClick={editPlaylist}
                  disabled={!currentPlaylist}
                >
                  <Edit3 className="h-4 w-4 mr-2" />
                  Editar Playlist
                </Button>
                <Button
                  variant="outline"
                  className="border-black text-black hover:bg-black/10 px-8 bg-transparent music-subtitle"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={!currentPlaylist}
                >
                  Add Songs
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Messages */}
      {error && (
        <div className="fixed bottom-20 right-4 bg-red-600 text-white px-6 py-3 rounded-lg shadow-lg z-50 flex items-center gap-2">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="ml-2 text-white/80 hover:text-white">✕</button>
        </div>
      )}

      {success && (
        <div className="fixed bottom-20 right-4 bg-green-600 text-white px-6 py-3 rounded-lg shadow-lg z-50 flex items-center gap-2">
          <span>{success}</span>
          <button onClick={() => setSuccess(null)} className="ml-2 text-white/80 hover:text-white">✕</button>
        </div>
      )}

      {/* Sidebar */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-50">
          <div
            className="sidebar-overlay absolute inset-0 bg-black/50 backdrop-blur-sm"
            onClick={() => setSidebarOpen(false)}
          />
          <div className="absolute top-0 right-0 h-full w-80 bg-black/80 backdrop-blur-lg border-l border-white/20 text-white p-6 overflow-y-auto custom-scrollbar shadow-2xl">
            <div className="flex items-center justify-between mb-8">
              <h2 className="text-xl font-bold music-title">Music Library</h2>
              <div className="flex gap-2">
                <Button
                  onClick={() => setShowCreatePlaylist(true)}
                  className="bg-white/20 hover:bg-white/30 text-white p-2 backdrop-blur-sm"
                  size="icon"
                >
                  <Plus className="h-4 w-4" />
                </Button>
                <Button
                  onClick={() => setSidebarOpen(false)}
                  className="bg-white/20 hover:bg-white/30 text-white p-2 backdrop-blur-sm"
                  size="icon"
                >
                  <X className="h-5 w-5" />
                </Button>
              </div>
            </div>

            <div className="space-y-8">
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
                          onClick={() => selectPlaylist(playlist)}
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
                            deletePlaylist(playlist.id);
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

              <div
                onClick={() => setShowCreatePlaylist(true)}
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
      )}

      {/* Modals */}
      {showCreatePlaylist && (
        <div className="fixed inset-0 z-[9999] flex items-center justify-center">
          <div 
            className="absolute inset-0 bg-black/80 backdrop-blur-sm" 
            onClick={() => setShowCreatePlaylist(false)} 
          />
          <div className="relative bg-black border border-white/20 rounded-lg p-6 w-96 text-white z-[10000]">
            <h3 className="text-xl font-bold mb-4 music-title">Crear Playlist</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2 music-subtitle">Nombre de la Playlist</label>
                <input
                  type="text"
                  value={newPlaylistName}
                  onChange={(e) => setNewPlaylistName(e.target.value)}
                  className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400"
                  placeholder="Ingresa el nombre..."
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2 music-subtitle">Descripción (opcional)</label>
                <textarea
                  value={newPlaylistDescription}
                  onChange={(e) => setNewPlaylistDescription(e.target.value)}
                  className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400"
                  placeholder="Describe tu playlist..."
                  rows={3}
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2 music-subtitle">Imagen de portada (opcional)</label>


                <input
                  ref={playlistCoverInputRef}
                  type="file"
                  accept="image/*"
                  className="hidden"
                />
                <Button
                  onClick={() => playlistCoverInputRef.current?.click()}
                  className="w-full bg-white/10 hover:bg-white/20 text-white border border-white/30"
                  variant="outline"
                >
                  <ImageIcon className="h-4 w-4 mr-2" />
                  Seleccionar imagen
                </Button>
              </div>
              <div className="flex gap-3">
                <Button
                  onClick={createPlaylist}
                  className="flex-1 bg-red-600 hover:bg-red-700 text-white music-subtitle"
                  disabled={!newPlaylistName.trim()}
                >
                  Crear Playlist
                </Button>
                <Button
                  onClick={() => {
                    setShowCreatePlaylist(false)
                    setNewPlaylistName("")
                    setNewPlaylistDescription("")
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

      {/* Edit Playlist Modal */}
      {showEditPlaylist && (
        <div className="fixed inset-0 z-[9999] flex items-center justify-center">
          <div 
            className="absolute inset-0 bg-black/80 backdrop-blur-sm" 
            onClick={() => {
                setShowEditPlaylist(false)
                setCoverPreview(null) // AGREGAR ESTO
              }}
            
          />
          <div className="relative bg-black border border-white/20 rounded-lg p-6 w-96 text-white z-[10000]">
            <h3 className="text-xl font-bold mb-4 music-title">Editar Playlist</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2 music-subtitle">Nombre de la Playlist</label>
                <input
                  type="text"
                  value={newPlaylistName}
                  onChange={(e) => setNewPlaylistName(e.target.value)}
                  className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400"
                  placeholder="Ingresa el nombre..."
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2 music-subtitle">Descripción (opcional)</label>
                <textarea
                  value={newPlaylistDescription}
                  onChange={(e) => setNewPlaylistDescription(e.target.value)}
                  className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400"
                  placeholder="Describe tu playlist..."
                  rows={3}
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2 music-subtitle">Nueva imagen de portada (opcional)</label>
                
                  
                  {/* AGREGAR PREVIEW AQUÍ */}
                  {(coverPreview || currentPlaylist?.cover_image) && (
                    <div className="mb-3 text-center">
                      <img 
                        src={coverPreview || `http://localhost:8000${currentPlaylist?.cover_image}`} 
                        alt="Preview" 
                        className="w-32 h-32 object-cover rounded-lg mx-auto border-2 border-white/20"
                      />
                      <p className="text-xs text-white/60 mt-2">
                        {coverPreview ? 'Nueva imagen seleccionada' : 'Imagen actual'}
                      </p>
                    </div>
                  )}
                  
                  <input
                    ref={playlistCoverInputRef}
                    type="file"
                    accept="image/*"
                    className="hidden"
                    onChange={handleCoverSelect} // CAMBIAR ESTO
                  />
                  <Button
                    onClick={() => playlistCoverInputRef.current?.click()}
                    className="w-full bg-white/10 hover:bg-white/20 text-white border border-white/30"
                    variant="outline"
                  >
                    <ImageIcon className="h-4 w-4 mr-2" />
                    {coverPreview ? 'Cambiar imagen' : 'Seleccionar imagen'}
                  </Button>
            

                <input
                  ref={playlistCoverInputRef}
                  type="file"
                  accept="image/*"
                  className="hidden"
                />
                <Button
                  onClick={() => playlistCoverInputRef.current?.click()}
                  className="w-full bg-white/10 hover:bg-white/20 text-white border border-white/30"
                  variant="outline"
                >
                  <ImageIcon className="h-4 w-4 mr-2" />
                  Cambiar imagen
                </Button>
              </div>
              <div className="flex gap-3">
                <Button
                  onClick={savePlaylistEdit}
                  className="flex-1 bg-red-600 hover:bg-red-700 text-white music-subtitle"
                  disabled={!newPlaylistName.trim()}
                >
                  <Save className="h-4 w-4 mr-2" />
                  Guardar
                </Button>
                <Button
                  onClick={() => setShowEditPlaylist(false)}
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

      {/* Edit Song Modal */}
      {showEditSong && editingSong && (
        <div className="fixed inset-0 z-[9999] flex items-center justify-center edit-song-modal">
          <div 
            className="absolute inset-0 bg-black/80 backdrop-blur-sm" 
            onClick={() => setShowEditSong(false)} 
          />
          <div className="relative bg-black border border-white/20 rounded-lg p-6 w-96 text-white z-[10000] modal-content">
            <h3 className="text-xl font-bold mb-4 music-title">Editar Canción</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2 music-subtitle">Título</label>
                <input
                  type="text"
                  value={editSongTitle}
                  onChange={(e) => setEditSongTitle(e.target.value)}
                  className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400"
                  placeholder="Título de la canción..."
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2 music-subtitle">Artista</label>
                <input
                  type="text"
                  value={editSongArtist}
                  onChange={(e) => setEditSongArtist(e.target.value)}
                  className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400"
                  placeholder="Nombre del artista..."
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2 music-subtitle">Álbum</label>
                <input
                  type="text"
                  value={editSongAlbum}
                  onChange={(e) => setEditSongAlbum(e.target.value)}
                  className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400"
                  placeholder="Nombre del álbum..."
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2 music-subtitle">Año</label>
                <input
                  type="number"
                  value={editSongYear || ""}
                  onChange={(e) => setEditSongYear(e.target.value ? Number(e.target.value) : undefined)}
                  className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400"
                  placeholder="Año de lanzamiento..."
                  min="1800"
                  max="2100"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2 music-subtitle">Imagen de portada (opcional)</label>
                <input
                  ref={songCoverInputRef}
                  type="file"
                  accept="image/*"
                  className="hidden"
                />
                <Button
                  onClick={() => songCoverInputRef.current?.click()}
                  className="w-full bg-white/10 hover:bg-white/20 text-white border border-white/30"
                  variant="outline"
                >
                  <ImageIcon className="h-4 w-4 mr-2" />
                  Cambiar imagen
                </Button>
              </div>
              <div className="flex gap-3">
                <Button
                  onClick={saveEditSong}
                  className="flex-1 bg-red-600 hover:bg-red-700 text-white music-subtitle"
                  disabled={!editSongTitle.trim()}
                >
                  <Save className="h-4 w-4 mr-2" />
                  Guardar
                </Button>
                <Button
                  onClick={() => setShowEditSong(false)}
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
    </div>
  )
}