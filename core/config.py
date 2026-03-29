from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    

    CONFIDENCE: float = 0.2 # порог уверенности нейросети
    BUFFER_FRAMES: int = 5 # задержка для защиты от моргания

    YOLO_MODEL_PATH: str = "yolov8s.pt" # Путь к весам модели по умолчанию

    COLOR_EMPTY: tuple[int, int, int] = (0, 255, 0) # Цвет для пустого стола
    COLOR_OCCUPIED: tuple[int, int, int] = (0, 0, 255) # Цвет для занятого стола
    COLOR_PERSON: tuple[int, int, int] = (255, 0, 0)
    BOX_THICKNESS: int = 2 # Толщина линий
    IOU_THRESHOLD: float = 0.05
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    ) 

settings = Settings()