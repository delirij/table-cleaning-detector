import logging
import pandas as pd
from typing import Tuple, List, Dict, Union

logger = logging.getLogger(__name__)

BoundingBox = Tuple[int, int, int, int]

class TableTracker:

    def __init__(self, buffer_frame: int = 10, **kwargs):
        self.is_empty: bool = True
        self.buffer_frame: int = buffer_frame
        self.empty_count: int = 0
        self.occupied_count: int = 0
        self._events_log: List[Dict[str, Union[str, float]]] = []
        
        self._is_initialized: bool = False
        self._init_frames_limit: int = 15  # Даем 15 кадров на "раздумья" при старте
        self._init_frame_counter: int = 0
        self._found_person_during_init: bool = False

    def _is_person_at_table(self, person_box: BoundingBox, table_box: BoundingBox) -> bool:
        px1, py1, px2, py2 = person_box
        tx1, ty1, tx2, ty2 = table_box
        person_center_x = px1 + (px2 - px1) // 2
        # Точка "ног" для сидящего человека
        person_bottom_y = py2 - int((py2 - py1) * 0.1) 

        return (tx1 <= person_center_x <= tx2) and (ty1 <= person_bottom_y <= ty2)
        
    def update(self, person_boxes: List[BoundingBox], table_box: BoundingBox, current_time: float) -> None:
        is_occupied_now = any(self._is_person_at_table(p, table_box) for p in person_boxes)
        
        if not self._is_initialized:
            self._init_frame_counter += 1
            if is_occupied_now:
                self._found_person_during_init = True
            
            # Когда накопили достаточно кадров для вердикта
            if self._init_frame_counter >= self._init_frames_limit:
                self.is_empty = not self._found_person_during_init
                # Заполняем счетчики, чтобы не было резкого переключения сразу после интиализации
                if not self.is_empty:
                    self.occupied_count = self.buffer_frame
                else:
                    self.empty_count = self.buffer_frame
                
                self._is_initialized = True
                status_str = "ЗАНЯТ" if not self.is_empty else "СВОБОДЕН"
                logger.info(f"Начальный статус стола определен: {status_str}")
            return

        if is_occupied_now:
            self.occupied_count += 1
            self.empty_count = 0
        else:
            self.empty_count += 1
            self.occupied_count = 0

        # Смена статуса (с защитой от моргания)
        if self.is_empty and self.occupied_count >= self.buffer_frame:
            self.is_empty = False
            self._events_log.append({"event": "approach", "time_sec": current_time})
            logger.info(f"Событие: Стол ЗАНЯТ на {current_time:.2f} сек")

        elif not self.is_empty and self.empty_count >= self.buffer_frame:
            self.is_empty = True
            self._events_log.append({"event": "empty", "time_sec": current_time})
            logger.info(f"Событие: Стол ОСВОБОДИЛСЯ на {current_time:.2f} сек")

    def get_events_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(self._events_log)