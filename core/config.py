from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    

    CONFIDENCE: float = 0.5
    BUFFER_FRAMES: int = 30


    YOLO_MODEL_PATH: str = "yolov8n.pt"


    COLOR_EMPTY: tuple[int, int, int] = (0, 255, 0)
    COLOR_OCCUPIED: tuple[int, int, int] = (0, 0, 255)
    BOX_THICKNESS: int = 2

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="igonre"
    ) 

settigns = Settings()