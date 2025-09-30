"""
FastAPI Main Application for Vinyl Music Player
Academic Project - Software Patterns and Data Structures

Main application configuration with routers, CORS, error handling,
and service initialization for the vinyl music player backend.
"""

import os
import uvicorn
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager

# Import routers
from api.endpoints import songs, playlists, player
from api.dependencies import (
    get_playlist_service,
    get_audio_service,
    get_file_service,
    get_metadata_service,
    cleanup_services,
    health_check_dependencies
)


# Application lifespan events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    """
    # Startup
    print("🎵 Starting Vinyl Music Player Backend...")
    
    try:
        # Create necessary directories
        create_directories()
        
        # Initialize services
        initialize_services()
        
        print("✅ Vinyl Music Player Backend started successfully!")
        print("📖 API Documentation: http://localhost:8000/docs")
        print("🔄 Alternative docs: http://localhost:8000/redoc")
        
    except Exception as e:
        print(f"❌ Error during startup: {e}")
        raise
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Vinyl Music Player Backend...")
    try:
        cleanup_services()
        print("✅ Cleanup completed successfully!")
    except Exception as e:
        print(f"⚠️ Error during cleanup: {e}")


# Create FastAPI application
app = FastAPI(
    title="Vinyl Music Player API",
    description="""
    🎵 **Vinyl Music Player Backend API**
    
    A modern music player backend implementing academic software patterns:
    - **Singleton Pattern** for player state management
    - **Abstract Factory Pattern** for audio format handling
    - **Doubly Linked List** for efficient playlist navigation
    
    **Features:**
    - Complete playlist management with CRUD operations
    - Professional audio playback control with pygame
    - Advanced metadata extraction and editing with mutagen
    - Real-time player state management
    - Support for MP3, WAV, and FLAC formats
    - Cover art management and embedding
    
    **Academic Project** - Software Patterns and Data Structures
    """,
    version="1.0.0",
    contact={
        "name": "Vinyl Music Player",
        "url": "http://localhost:8000",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    lifespan=lifespan
)

# Configure CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js development server
        "http://127.0.0.1:3000",
        "http://localhost:5000",  # Flask frontend (si lo usas)
        "http://127.0.0.1:5000",
        "*"  # Para desarrollo - cambiar en producción
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "Accept",
        "Origin",
        "X-Requested-With",
        "Access-Control-Allow-Origin",
        "Access-Control-Allow-Headers",
    ],
    expose_headers=["*"],
    max_age=3600,
)

# Include API routers
app.include_router(songs.router, prefix="/api")
app.include_router(playlists.router, prefix="/api")
app.include_router(player.router, prefix="/api")


# Basic endpoints
@app.get("/", tags=["root"])
async def root():
    """
    Welcome endpoint for the Vinyl Music Player API.
    
    Returns basic information about the API and available endpoints.
    """
    return {
        "message": "🎵 Welcome to Vinyl Music Player API",
        "version": "1.0.0",
        "description": "Modern music player with academic software patterns",
        "features": [
            "Playlist management with Doubly Linked Lists",
            "Audio playback control with pygame",
            "Metadata extraction with mutagen",
            "Singleton pattern for state management",
            "Abstract Factory for audio formats"
        ],
        "endpoints": {
            "documentation": "/docs",
            "alternative_docs": "/redoc",
            "health_check": "/health",
            "api_routes": {
                "songs": "/api/songs",
                "playlists": "/api/playlists",
                "player": "/api/player"
            }
        },
        "supported_formats": ["mp3", "wav", "flac"],
        "frontend_url": "http://localhost:5000"
    }


@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint for monitoring system status.
    
    Returns the status of all services and dependencies.
    """
    try:
        # Check service health
        service_health = health_check_dependencies()
        
        # Check directories
        directories_status = check_directories()
        
        # Overall health assessment
        all_services_healthy = all(
            "error" not in status.lower() 
            for status in service_health.values()
        )
        
        overall_status = "healthy" if all_services_healthy else "degraded"
        
        return {
            "status": overall_status,
            "timestamp": "2024-01-20T12:00:00Z",  # In real app, use datetime.utcnow()
            "services": service_health,
            "directories": directories_status,
            "uptime": "Service running",
            "version": "1.0.0"
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": "2024-01-20T12:00:00Z"
            }
        )


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Handle HTTP exceptions with consistent error format.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": "HTTPException",
                "status_code": exc.status_code,
                "message": exc.detail,
                "path": str(request.url.path),
                "method": request.method
            }
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle Pydantic validation errors with detailed information.
    """
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "type": "ValidationError",
                "status_code": 422,
                "message": "Request validation failed",
                "details": exc.errors(),
                "path": str(request.url.path),
                "method": request.method
            }
        }
    )


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """
    Handle 404 Not Found errors.
    """
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": {
                "type": "NotFound",
                "status_code": 404,
                "message": f"Endpoint not found: {request.method} {request.url.path}",
                "available_endpoints": {
                    "api_docs": "/docs",
                    "health_check": "/health",
                    "songs_api": "/api/songs",
                    "playlists_api": "/api/playlists",
                    "player_api": "/api/player"
                }
            }
        }
    )


@app.exception_handler(500)
async def internal_server_error_handler(request: Request, exc):
    """
    Handle 500 Internal Server Error.
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "type": "InternalServerError",
                "status_code": 500,
                "message": "An unexpected error occurred",
                "path": str(request.url.path),
                "method": request.method,
                "suggestion": "Please check the logs or contact support"
            }
        }
    )


# Utility functions
def create_directories():
    """
    Create necessary directories for the application.
    """
    directories = [
        "data",
        "frontend/static/uploads",
        "frontend/static/uploads/covers",
        "logs"
    ]
    
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            print(f"✅ Created/verified directory: {directory}")
        except Exception as e:
            print(f"⚠️ Error creating directory {directory}: {e}")


def check_directories():
    """
    Check if all required directories exist.
    
    Returns:
        dict: Status of each directory
    """
    directories = {
        "data": "data",
        "uploads": "frontend/static/uploads",
        "covers": "frontend/static/uploads/covers",
        "logs": "logs"
    }
    
    status_dict = {}
    for name, path in directories.items():
        status_dict[name] = "exists" if os.path.exists(path) else "missing"
    
    return status_dict

def initialize_services():
    """
    Initialize all services and load existing data - VERSIÓN CORREGIDA.
    """
    try:
        # CRÍTICO: Importar e inicializar servicios globales
        from api.dependencies import initialize_global_services, get_playlist_service, get_audio_service, get_file_service, get_metadata_service
        
        print("🔧 Inicializando servicios globales...")
        initialize_global_services()
        
        # Obtener las instancias ya inicializadas
        playlist_service = get_playlist_service()
        audio_service = get_audio_service()
        file_service = get_file_service()
        metadata_service = get_metadata_service()
        
        print("✅ Playlist service initialized")
        print("✅ Audio service initialized")
        print("✅ File service initialized")
        print("✅ Metadata service initialized")
        
        # Verificar carga de playlists
        playlists = playlist_service.get_all_playlists()
        print(f"📁 Loaded {len(playlists)} existing playlists")
        
        # Set up error callbacks for audio service
        def on_playback_error(error_msg):
            print(f"🔊 Audio error: {error_msg}")
        
        def on_song_finished():
            print("🎵 Song finished playing")
        
        audio_service.set_error_callback(on_playback_error)
        audio_service.set_song_finished_callback(on_song_finished)
        
        print("🔧 Service callbacks configured")
        
    except Exception as e:
        print(f"❌ Error initializing services: {e}")
        raise


# Additional utility endpoints
@app.get("/api/info", tags=["system"])
async def get_api_info():
    """
    Get detailed API information and configuration.
    """
    return {
        "api_name": "Vinyl Music Player API",
        "version": "1.0.0",
        "framework": "FastAPI",
        "python_version": "3.8+",
        "audio_backend": "pygame",
        "metadata_library": "mutagen",
        "supported_formats": ["mp3", "wav", "flac"],
        "design_patterns": [
            "Singleton (MusicPlayerManager)",
            "Abstract Factory (AudioElementFactory)",
            "Dependency Injection (FastAPI)"
        ],
        "data_structures": [
            "Doubly Linked List (Playlist navigation)"
        ],
        "features": {
            "playlist_management": True,
            "audio_playback": True,
            "metadata_editing": True,
            "cover_art_support": True,
            "search_functionality": True,
            "file_validation": True
        },
        "endpoints_count": {
            "songs": 12,
            "playlists": 15,
            "player": 18,
            "total": 45
        }
    }


@app.get("/api/stats", tags=["system"])
async def get_system_stats():
    """
    Get current system statistics and usage information.
    """
    try:
        playlist_service = get_playlist_service()
        
        # Get basic stats
        total_playlists = playlist_service.get_playlist_count()
        total_songs = playlist_service.get_total_songs_count()
        
        # Get directory sizes (simplified)
        data_dir_exists = os.path.exists("data")
        uploads_dir_exists = os.path.exists("frontend/static/uploads")
        
        return {
            "playlists": {
                "total_playlists": total_playlists,
                "total_songs": total_songs,
                "average_songs_per_playlist": round(total_songs / total_playlists, 2) if total_playlists > 0 else 0
            },
            "storage": {
                "data_directory": "available" if data_dir_exists else "missing",
                "uploads_directory": "available" if uploads_dir_exists else "missing"
            },
            "system": {
                "api_status": "running",
                "cors_enabled": True,
                "documentation_available": True
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting system stats: {str(e)}"
        )


# Development server configuration
if __name__ == "__main__":
    print("🎵 Starting Vinyl Music Player Backend in Development Mode")
    print("📖 API Documentation will be available at: http://localhost:8000/docs")
    print("🎯 Frontend should connect to: http://localhost:8000/api")
    
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True,
        reload_excludes=["*.pyc", "__pycache__"]
    )

    