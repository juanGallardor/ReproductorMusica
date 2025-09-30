
**Reproductor Musical Académico con Patrones de Software y Estructuras de Datos**

Un reproductor de música moderno desarrollado como proyecto académico para la materia de **Patrones de Software y Estructuras de Datos** de 4to semestre de Ingeniería de Software.

---

## 📋 Tabla de Contenidos

- [Descripción](#descripción)
- [Características Principales](#características-principales)
- [Arquitectura del Sistema](#arquitectura-del-sistema)
- [Patrones de Diseño Implementados](#patrones-de-diseño-implementados)
- [Estructuras de Datos](#estructuras-de-datos)
- [Tecnologías Utilizadas](#tecnologías-utilizadas)
- [Instalación y Configuración](#instalación-y-configuración)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [API Documentation](#api-documentation)
- [Funcionalidades](#funcionalidades)
- [Capturas de Pantalla](#capturas-de-pantalla)

---

## 📖 Descripción

**Vinyl Music Player** es un reproductor de música completo que simula la experiencia de un tocadiscos de vinilo. El proyecto está diseñado para demostrar la implementación práctica de patrones de diseño de software y estructuras de datos eficientes en un sistema real.

### 🎯 Objetivo Académico

Este proyecto implementa conceptos fundamentales de:
- **Patrones de Diseño**: Singleton, Abstract Factory
- **Estructuras de Datos**: Lista Doblemente Enlazada para navegación eficiente

---

## ✨ Características Principales

### 🎶 Gestión Musical
- **Reproducción de Audio**: Control completo de reproducción (play, pause, stop, seek)
- **Formatos Soportados**: MP3, WAV, FLAC
- **Gestión de Playlists**: Crear, editar y eliminar
- **Metadata Avanzada**: Extracción y edición de metadatos (título, artista, álbum, año)

### 🎛️ Controles Avanzados
- **Modos de Repetición**: Off, One (repetir canción), All (repetir playlist)
- **Modo Aleatorio**: Reproducción aleatoria con algoritmo de shuffle
- **Control de Volumen**: Ajuste preciso con indicador visual
- **Navegación**: Anterior/Siguiente con soporte para atajos de teclado

### 🎨 Interfaz de Usuario
- **Diseño Inspirado en Vinilo**: Animaciones de tocadiscos con brazo fonocaptor
- **Visualizador de Audio**: Barras de frecuencia animadas en tiempo real
- **Drag & Drop**: Reordenamiento de canciones y carga de archivos
- **Responsive Design**: Optimizado para diferentes tamaños de pantalla

### 🔧 Características Técnicas
- **API RESTful**: Backend completo con documentación automática
- **Validación de Datos**: Validación robusta con Pydantic
- **Gestión de Archivos**: Carga, validación y organización automática
- **Persistencia**: Almacenamiento JSON con respaldo automático

---

### Componentes Principales

#### Frontend (Next.js + TypeScript)
- **Components**: Componentes React reutilizables y modulares
- **Services**: Servicios para comunicación con API
- **State Management**: Manejo de estado local y sincronización
- **Utils**: Utilidades y helpers compartidos

#### Backend (FastAPI + Python)
- **API Endpoints**: Rutas RESTful organizadas por funcionalidad
- **Services**: Lógica de negocio encapsulada
- **Models**: Modelos de datos con validación
- **Patterns**: Implementación de patrones de diseño

---

## 🔧 Patrones de Diseño Implementados

### 1. **Singleton Pattern**
**Archivo**: `patterns/singleton.py`

```python
class MusicPlayerManager:
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```

**Propósito**: Garantizar una única instancia del controlador de reproductor musical en todo el sistema.

**Beneficios**:
- Estado global consistente
- Control centralizado de la reproducción
- Evita conflictos entre múltiples instancias

### 2. **Abstract Factory Pattern**
**Archivo**: `patterns/abstract_factory.py`

```python
class AudioElementFactory(ABC):
    @abstractmethod
    def create_song(self, file_path: str) -> Song:
        pass
    
    @abstractmethod
    def validate_file_format(self, file_path: str) -> bool:
        pass

class MP3Factory(AudioElementFactory):
    # Implementación específica para MP3
    
class WAVFactory(AudioElementFactory):
    # Implementación específica para WAV
```

**Propósito**: Crear objetos Song específicos según el formato de audio sin acoplar el código cliente.

**Beneficios**:
- Extensibilidad para nuevos formatos
- Encapsulación de lógica específica por formato
- Principio abierto/cerrado

### 3. **Dependency Injection**
**Archivo**: `api/dependencies.py`

```python
def get_playlist_service() -> PlaylistService:
    global _playlist_service
    if _playlist_service is None:
        _playlist_service = PlaylistService()
    return _playlist_service
```

**Propósito**: Inyectar dependencias en los endpoints de FastAPI para mejor testabilidad y desacoplamiento.

**Beneficios**:
- Testabilidad mejorada
- Acoplamiento reducido
- Configuración centralizada

---

## 📊 Estructuras de Datos

### Lista Doblemente Enlazada
**Archivo**: `models/doubly_linked_list.py`

```python
class Node:
    def __init__(self, data):
        self.data = data
        self.next = None
        self.prev = None

class DoublyLinkedList:
    def __init__(self):
        self.head = None
        self.tail = None
        self.current = None
```

**Propósito**: Navegación eficiente entre canciones con soporte bidireccional.

**Operaciones Implementadas**:
- `next()`: O(1) - Avanzar a la siguiente canción
- `previous()`: O(1) - Retroceder a la canción anterior
- `insert_at_position()`: O(n) - Insertar canción en posición específica
- `delete_at_position()`: O(n) - Eliminar canción de posición específica
- `shuffle()`: O(n) - Reordenamiento aleatorio

**Ventajas en el Contexto Musical**:
- **Navegación Fluida**: Cambio instantáneo entre canciones
- **Modo Aleatorio**: Reordenamiento eficiente sin reconstruir estructura
- **Inserción Dinámica**: Agregar canciones en cualquier posición
- **Memory Efficiency**: No requiere arrays redimensionables

---

## 🛠️ Tecnologías Utilizadas

### Frontend
- **Framework**: Next.js 14 con App Router
- **Lenguaje**: TypeScript
- **Styling**: Tailwind CSS + CSS personalizado
- **UI Components**: Componentes personalizados + Radix UI
- **Iconos**: Lucide React
- **Validación**: Zod para validación de formularios

### Backend
- **Framework**: FastAPI 0.104+
- **Lenguaje**: Python 3.8+
- **Audio Processing**: pygame para reproducción
- **Metadata**: mutagen para extracción/edición
- **Validación**: Pydantic para modelos de datos
- **Documentación**: OpenAPI/Swagger automática

### Audio & Multimedia
- **Reproducción**: pygame.mixer
- **Formatos**: MP3, WAV, FLAC
- **Metadata**: mutagen (ID3, FLAC, etc.)
- **Seeking**: VLC Python para control preciso

### Desarrollo
- **Control de Versiones**: Git
- **Package Manager**: npm (frontend), pip (backend)
- **Environment**: Archivo .env para configuración
- **CORS**: Configurado para desarrollo local

---

## 🚀 Instalación y Configuración

### Prerrequisitos
- Node.js 18+ y npm
- Python 3.8+
- Git

### 1. Clonar el Repositorio
```bash
git clone https://github.com/tu-usuario/vinyl-music-player.git
cd vinyl-music-player
```

### 2. Configurar Backend
```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Instalar dependencias
pip install fastapi uvicorn pygame mutagen python-vlc pydantic

# Ejecutar servidor de desarrollo
python backend/main.py
```

### 3. Configurar Frontend
```bash
# Instalar dependencias
npm install

# Ejecutar servidor de desarrollo
npm run dev
```

### 4. Acceder a la Aplicación
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Documentación API**: http://localhost:8000/docs

---



## 📚 API Documentation

### Endpoints Principales

#### 🎵 Songs (`/api/songs`)
- `GET /` - Listar todas las canciones
- `GET /{song_id}` - Obtener canción específica
- `GET /{song_id}/stream` - Stream de audio
- `POST /upload` - Subir nueva canción
- `PUT /{song_id}` - Actualizar metadatos
- `DELETE /{song_id}` - Eliminar canción

#### 📝 Playlists (`/api/playlists`)
- `GET /` - Listar playlists
- `POST /` - Crear nueva playlist
- `GET /{playlist_id}` - Obtener playlist específica
- `PUT /{playlist_id}` - Actualizar playlist
- `DELETE /{playlist_id}` - Eliminar playlist
- `POST /{playlist_id}/upload-and-add` - Subir y agregar canción
- `PUT /{playlist_id}/songs/reorder` - Reordenar canciones
- `POST /{playlist_id}/shuffle` - Mezclar playlist

#### 🎛️ Player (`/api/player`)
- `POST /play` - Iniciar reproducción
- `POST /pause` - Pausar reproducción
- `POST /stop` - Detener reproducción
- `POST /next` - Siguiente canción
- `POST /previous` - Canción anterior
- `PUT /volume` - Ajustar volumen
- `PUT /seek` - Buscar posición
- `GET /status` - Estado del reproductor

### Modelos de Datos

#### Song Model
```python
class Song(BaseModel):
    id: str
    title: str
    artist: Optional[str]
    album: Optional[str]
    year: Optional[int]
    duration: float
    file_size: int
    format: str
    filename: str
    file_path: str
    play_count: int
    cover_image: Optional[str]
    created_at: datetime
```

#### Playlist Model
```python
class Playlist:
    id: str
    name: str
    description: Optional[str]
    cover_image: Optional[str]
    songs: DoublyLinkedList
    current_position: int
    created_at: datetime
    total_duration: float
    song_count: int
```

---

## 🎯 Funcionalidades

### Reproducción de Audio
- **Control Básico**: Play, pause, stop con retroalimentación visual
- **Navegación**: Siguiente/anterior canción con lista doblemente enlazada
- **Búsqueda**: Seek a posición específica en la canción
- **Volumen**: Control de volumen con mute/unmute

### Gestión de Playlists
- **CRUD Completo**: Crear, leer, actualizar, eliminar playlists
- **Drag & Drop**: Reordenamiento visual de canciones
- **Shuffle**: Algoritmo de mezcla preservando estructura de datos
- **Metadatos**: Gestión de información de playlist (nombre, descripción, cover)

### Carga de Archivos
- **Formatos Múltiples**: Soporte para MP3, WAV, FLAC
- **Validación**: Verificación de formato y integridad
- **Metadata Extraction**: Extracción automática de metadatos
- **Cover Art**: Soporte para imágenes de portada

### Interfaz de Usuario
- **Vinyl Simulation**: Animación de tocadiscos con físicas realistas
- **Audio Visualizer**: Visualización de frecuencias en tiempo real
- **Responsive**: Adaptación a diferentes dispositivos
- **Keyboard Shortcuts**: Atajos de teclado para control rápido

---

## 🎓 Aspectos Académicos

### Patrones de Diseño Demostrados

1. **Singleton**: Control único del estado del reproductor
2. **Abstract Factory**: Creación polimórfica de objetos Song según formato
3. **Dependency Injection**: Desacoplamiento en arquitectura de servicios

### Estructuras de Datos Aplicadas

1. **Lista Doblemente Enlazada**: Navegación eficiente en playlists
2. **Hash Tables**: Búsqueda rápida de canciones por ID
3. **Arrays Dinámicos**: Gestión de metadatos y configuraciones

### Principios SOLID

- **Single Responsibility**: Cada servicio tiene una responsabilidad específica
- **Open/Closed**: Extensible para nuevos formatos de audio
- **Liskov Substitution**: Interfaces consistentes entre factories
- **Interface Segregation**: APIs específicas por funcionalidad
- **Dependency Inversion**: Dependencias inyectadas, no hardcoded

### Conceptos de Ingeniería de Software

- **Separación de Responsabilidades**: Frontend/Backend claramente definidos
- **API Design**: RESTful con documentación automática
- **Error Handling**: Manejo robusto de errores y validaciones
- **Testing**: Estructura preparada para testing unitario

---

## 👨‍💻 Autor

**Proyecto Académico**
Juan Pablo Gallardo  
Materia: Patrones de Software y Estructuras de Datos  
Semestre: 4to - Ingeniería de Software  
