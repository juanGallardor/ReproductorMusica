const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

// Types
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

// API Client
class VinylAPI {
  // Playlist endpoints
  async getPlaylists(): Promise<Playlist[]> {
    const res = await fetch(`${API_URL}/playlists`);
    if (!res.ok) throw new Error('Failed to fetch playlists');
    return res.json();
  }

  async getPlaylist(id: string): Promise<Playlist> {
    const res = await fetch(`${API_URL}/playlists/${id}`);
    if (!res.ok) throw new Error('Failed to fetch playlist');
    return res.json();
  }

  async createPlaylist(name: string, description?: string): Promise<Playlist> {
    const res = await fetch(`${API_URL}/playlists`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, description }),
    });
    if (!res.ok) throw new Error('Failed to create playlist');
    return res.json();
  }

  async deletePlaylist(id: string): Promise<void> {
    const res = await fetch(`${API_URL}/playlists/${id}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error('Failed to delete playlist');
  }

  async addSongToPlaylist(playlistId: string, songId: string): Promise<void> {
    const res = await fetch(`${API_URL}/playlists/${playlistId}/songs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ song_id: songId }),
    });
    if (!res.ok) throw new Error('Failed to add song to playlist');
  }

  // Reemplaza el método uploadAndAddToPlaylist en tu api.ts

async uploadAndAddToPlaylist(playlistId: string, file: File, metadata?: {
  title?: string;
  artist?: string;
  album?: string;
  year?: number;
}): Promise<any> {
  const formData = new FormData();
  formData.append('file', file);
  
  // Agregar metadata solo si existe
  if (metadata?.title) formData.append('title', metadata.title);
  if (metadata?.artist) formData.append('artist', metadata.artist);
  if (metadata?.album) formData.append('album', metadata.album);
  if (metadata?.year) formData.append('year', metadata.year.toString());

  console.log(`[FRONTEND] Uploading ${file.name} to playlist ${playlistId}`);

  const res = await fetch(`${API_URL}/playlists/${playlistId}/upload-and-add`, {
    method: 'POST',
    body: formData,
  });
  
  if (!res.ok) {
    const errorText = await res.text();
    console.error('[FRONTEND] Upload error:', res.status, errorText);
    
    // Más información de debug
    console.error('Request details:', {
      url: `${API_URL}/playlists/${playlistId}/upload-and-add`,
      playlistId,
      fileName: file.name,
      fileSize: file.size,
      fileType: file.type
    });
    
    throw new Error(`Failed to upload song: ${res.status} - ${errorText}`);
  }
  
  const result = await res.json();
  console.log(`[FRONTEND] Upload successful:`, result);
  return result;
}


  async removeSongFromPlaylist(playlistId: string, songId: string): Promise<void> {
    const res = await fetch(`${API_URL}/playlists/${playlistId}/songs/${songId}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error('Failed to remove song');
  }

  async shufflePlaylist(playlistId: string): Promise<void> {
    const res = await fetch(`${API_URL}/playlists/${playlistId}/shuffle`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to shuffle playlist');
  }

  // Player endpoints
  async play(): Promise<void> {
    const res = await fetch(`${API_URL}/player/play`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to play');
  }

  async pause(): Promise<void> {
    const res = await fetch(`${API_URL}/player/pause`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to pause');
  }

  async stop(): Promise<void> {
    const res = await fetch(`${API_URL}/player/stop`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to stop');
  }

  async next(): Promise<void> {
    const res = await fetch(`${API_URL}/player/next`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to skip to next');
  }

  async previous(): Promise<void> {
    const res = await fetch(`${API_URL}/player/previous`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to skip to previous');
  }

  async setVolume(volume: number): Promise<void> {
    const res = await fetch(`${API_URL}/player/volume`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ volume }),
    });
    if (!res.ok) throw new Error('Failed to set volume');
  }

  async seek(position: number): Promise<void> {
    const res = await fetch(`${API_URL}/player/seek`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ position }),
    });
    if (!res.ok) throw new Error('Failed to seek');
  }

  async setRepeatMode(mode: 'off' | 'one' | 'all'): Promise<void> {
    const res = await fetch(`${API_URL}/player/repeat-mode`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mode }),
    });
    if (!res.ok) throw new Error('Failed to set repeat mode');
  }

  async setShuffleMode(enabled: boolean): Promise<void> {
    const res = await fetch(`${API_URL}/player/shuffle-mode`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ enabled }),
    });
    if (!res.ok) throw new Error('Failed to set shuffle mode');
  }

  async getPlayerStatus(): Promise<PlayerStatus> {
    const res = await fetch(`${API_URL}/player/status`);
    if (!res.ok) throw new Error('Failed to get player status');
    return res.json();
  }

  async setCurrentPlaylist(playlistId: string, position: number = 0): Promise<void> {
    const res = await fetch(`${API_URL}/player/playlist/${playlistId}?position=${position}`, {
      method: 'PUT',
    });
    if (!res.ok) throw new Error('Failed to set current playlist');
  }

  // Song endpoints
  async getSongs(): Promise<Song[]> {
    const res = await fetch(`${API_URL}/songs`);
    if (!res.ok) throw new Error('Failed to fetch songs');
    return res.json();
  }

  async uploadSong(file: File, metadata?: {
    title?: string;
    artist?: string;
    album?: string;
    year?: number;
  }): Promise<Song> {
    const formData = new FormData();
    formData.append('file', file);
    if (metadata?.title) formData.append('title', metadata.title);
    if (metadata?.artist) formData.append('artist', metadata.artist);
    if (metadata?.album) formData.append('album', metadata.album);
    if (metadata?.year) formData.append('year', metadata.year.toString());

    const res = await fetch(`${API_URL}/songs/upload`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) throw new Error('Failed to upload song');
    const data = await res.json();
    return data.song;
  }

  async updateSongMetadata(songId: string, metadata: {
    title?: string;
    artist?: string;
    album?: string;
    year?: number;
  }): Promise<Song> {
    const res = await fetch(`${API_URL}/songs/${songId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(metadata),
    });
    if (!res.ok) throw new Error('Failed to update song');
    return res.json();
  }

getSongStream(songId: string): string {
    return `${API_URL}/songs/${songId}/stream`;
  }
}

export const api = new VinylAPI();