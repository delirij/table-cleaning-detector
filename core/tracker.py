import logging
import pandas as pd
from typing import List, Dict, Union

from core.types import BoundingBox
from core.config import settings

logger = logging.getLogger(__name__)

class TableTracker:
    def __init__(self, buffer_approach: int = None, buffer_empty: int = None):
        self.is_empty: bool = True
        
        # --- НАСТРОЙКИ ГИСТЕРЕЗИСА ---
        self.buffer_approach: int = buffer_approach if buffer_approach is not None else settings.BUFFER_APPROACH
        self.buffer_empty: int = buffer_empty if buffer_empty is not None else settings.BUFFER_EMPTY
        # -----------------------------

        self.empty_count: int = 0
        self.occupied_count: int = 0
        self._events_log: List[Dict[str, Union[str, float]]] = []
        self._is_initialized: bool = False

    def _is_person_at_table(self, person_box: BoundingBox, table_box: BoundingBox) -> bool:
        px1, py1, px2, py2 = person_box
        tx1, ty1, tx2, ty2 = table_box
        
        person_center_x = px1 + (px2 - px1) // 2
        # Сдвигаем точку чуть выше пяток, чтобы лучше ловить сидящих
        person_bottom_y = py2 - int((py2 - py1) * 0.15) 

        return (tx1 <= person_center_x <= tx2) and (ty1 <= person_bottom_y <= ty2)
        
    def update(self, person_boxes: List[BoundingBox], table_box: BoundingBox, current_time: float) -> None:
        is_occupied_now = any(self._is_person_at_table(p, table_box) for p in person_boxes)
        
        # Инициализация на старте
        if not self._is_initialized:
            self.is_empty = not is_occupied_now
            self.occupied_count = self.buffer_approach if is_occupied_now else 0
            self.empty_count = self.buffer_empty if not is_occupied_now else 0
            self._is_initialized = True
            return

        # Накапливаем счетчики
        if is_occupied_now:
            self.occupied_count += 1
            self.empty_count = 0  # Сбрасываем ожидание ухода, если увидели хотя бы одного
        else:
            self.empty_count += 1
            self.occupied_count = 0 # Сбрасываем ожидание прихода

        # Логика переключения
        if self.is_empty and self.occupied_count >= self.buffer_approach:
            self.is_empty = False
            self._events_log.append({"event": "approach", "time_sec": current_time})
            logger.info(f"Событие: Стол ЗАНЯТ на {current_time:.2f} сек")

        elif not self.is_empty and self.empty_count >= self.buffer_empty:
            self.is_empty = True
            self._events_log.append({"event": "empty", "time_sec": current_time})
            logger.info(f"Событие: Стол ОСВОБОДИЛСЯ на {current_time:.2f} сек")

    def get_events_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(self._events_log)