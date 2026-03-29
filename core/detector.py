import logging
from typing import List, Tuple

from ultralytics import YOLO

from core.config import settings

logger = logging.getLogger(__name__)

# Удобный тип данных для координат
BoundigBox = Tuple[int, int, int, int]

class PersonDetector:
    def __init__(self):
        # Загружаем модель
        self.model: YOLO = YOLO(f"{settings.YOLO_MODEL_PATH}")


    def get_people_boxes(self, frame) -> List[BoundigBox]:

        # Передаем один кадр
        results = self.model.predict(
            source=frame,
            classes = [0], # Ищем только людей
            conf = settings.CONFIDENCE,
            verbose = False # Отключаем спам в консоль
        )

        people_boxes: List[BoundigBox] = []

        # Достаем координаты
        for result in results:
            for box in result.boxes:
                # Извлекаем координаты углов рамки
                x1, y1, x2, y2 = box.xyxy[0].tolist()

                # Округляем до целых пикселей
                people_boxes.append((int(x1), int(y1), int(x2), int(y2)))
        # Возращаем список чисел
        return people_boxes






        