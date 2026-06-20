from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "智慧物流分拨中心-快递面单扫描拦截系统"

    DATABASE_URL: str = "sqlite:///./logistics.db"

    CRNN_MODEL_PATH: str = "./models/crnn.pth"
    CRNN_IMAGE_WIDTH: int = 200
    CRNN_IMAGE_HEIGHT: int = 32
    CRNN_NUM_CLASSES: int = 6556
    CRNN_HIDDEN_SIZE: int = 256
    CRNN_NUM_LAYERS: int = 2

    VALVE_GPIO_PIN: int = 18
    VALVE_ACTIVE_DURATION: float = 2.0

    INTERCEPT_LEVEL_THREE: list[str] = ["客户拦截", "疑似违禁品"]

    MAX_IMAGE_SIZE: int = 10 * 1024 * 1024

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()
