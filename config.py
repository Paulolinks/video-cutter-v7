# config.py
import os
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class VideoConfig:
    fonte: str = "Arial-Bold"
    cor: str = "white" 
    tamanho: int = 60
    altura: int = 1280
    largura: int = 720
    posicao: float = 0.2
    tempo_min: float = 15.0
    tempo_max: float = 53.0
    automatico: bool = True
    tema: str = ""
    rede_social: str = "instagram"
    modo_video: str = "crop"
    qualidade_video: str = "alta"

@dataclass
class AppConfig:
    # Paths
    FFMPEG_PATH: str = os.path.join(os.getcwd(), "bin")
    FFMPEG_EXECUTABLE: str = os.path.join(FFMPEG_PATH, "ffmpeg", "ffmpeg.exe") if os.path.exists(os.path.join(os.getcwd(), "bin", "ffmpeg")) else "ffmpeg"
    DATA_DIR: str = os.getenv("DATA_DIR", "data")
    UPLOAD_DIR: str = os.path.join(DATA_DIR, "uploads")
    FINAL_DIR: str = os.path.join(DATA_DIR, "final")
    CORTES_DIR: str = os.path.join("static", "final")
    
    # API Keys
    OPENAI_KEY: Optional[str] = os.getenv("OPENAI_KEY")
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
    
    # Security
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", 10 * 1024 * 1024))  # 10MB
    MAX_AUDIO_SIZE: int = int(os.getenv("MAX_AUDIO_SIZE", 50 * 1024 * 1024))  # 50MB
    ALLOWED_EXTENSIONS: set = field(default_factory=lambda: {"mp4", "wav", "mp3", "json", "xlsx", "xls", "m4a", "aac"})
    
    # Server
    PORT_RANGE: tuple = field(default_factory=lambda: (5500, 5600))
    DEBUG: bool = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    
    # Video processing
    video: VideoConfig = field(default_factory=VideoConfig)

config = AppConfig()
