import logging
import pandas as pd
from typing import Tuple, List, Dict, Union

# Настройка базового логгера
logger = logging.getLogger(__name__)

# Создаем алиас типа для удобства чтения
BoundingBox = Tuple[int, int, int, int]

def calculate_iou(box_a: BoundingBox, box_b: BoundingBox) -> float:
    """
    Вычисляет метрику Intersection over Union (IoU) для двух прямоугольников.
    
    Args:
        box_a: Координаты первого объекта (x_min, y_min, x_max, y_max).
        box_b: Координаты второго объекта (x_min, y_min, x_max, y_max).
        
    Returns:
        float: Значение IoU от 0.0 до 1.0. Если пересечения нет, возвращает 0.0.
    """

    x_a = max(box_a[0], box_b[0])
    y_a = max(box_a[1], box_b[1])
    x_b = min(box_a[2], box_b[2])
    y_b = min(box_a[3], box_b[3])

    # Вычисляем ширину и высоту пересечения
    inter_width = max(0, x_b - x_a)
    inter_height = max(0, y_b - y_a)
    inter_area = inter_width * inter_height

    # Если пересечения нет, IoU равен 0
    if inter_area == 0:
        return 0.0

    # Вычисляем площади исходных прямоугольников
    box_a_area = (box_a[2] - box_a[0]) * (box_a[3] - box_a[1])
    box_b_area = (box_b[2] - box_b[0]) * (box_b[3] - box_b[1])

    # Считаем итоговый IoU
    iou = inter_area / float(box_a_area + box_b_area - inter_area)
    return iou


class TableTracker:

    def __init__(self, buffer_frame: int = 30, iou_threshold: float = 0.05):
        self.is_empty: bool = True

        self.buffer_frame: int = buffer_frame
        self.iou_threshold: float = iou_threshold

        self.empty_count: int = 0
        self.occupied_count: int = 0

        self._events_log: List[Dict[str, Union[str, float]]] = []
        
    def update(
            self,
            person_boxes: List[BoundingBox],
            table_box: BoundingBox,
            current_time: float
            ) -> None:
        """
        Обновляет статус столика на осове текущего кадра
        """
        # Проверяем, есть ли хотябы один человек в зоне стола
        is_occupated_now = False
        for person in person_boxes:
            iou = calculate_iou(person, table_box)
            if iou > self.iou_threshold:
                is_occupated_now = True
                break # Если нашли человека, то останавливаем поиск
        
        # Логика счетчиков
        if is_occupated_now:
            self.occupied_count += 1
            self.empty_count = 0
        else:
            self.empty_count += 1
            self.occupied_count = 0

        # Смена статуса
        # Человек подошел к столу
        if self.is_empty and self.occupied_count >= self.buffer_frame:
            self.is_empty = False
            
            self._events_log.append({"event": "approach", "time_sec": current_time})
            logger.info(f"Событие: стол стал пустым на {current_time:.2f} сек")

        # Человек ушел, стол свободен
        elif not self.is_empty and self.empty_count >= self.buffer_frame:
            self.is_empty = True
            self._events_log.append({"event": "empty", "time_sec": current_time})
            logger.info(f"Событие: Стол стал пустым на {current_time:.2f} сек")
        

    def get_events_dataframe(self) -> pd.DataFrame:
        """
        Возращает историю событий в виде Pandas DataFrame
        """
        df = pd.DataFrame(self._events_log)
        if not df.empty:
            logger.info(f"Сформирован DataFrame с {len(df)} записями")
        else:
            logger.warning("Сформирован пустой Dataframe")
        return df
        

        


