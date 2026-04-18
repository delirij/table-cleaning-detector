import logging
import pandas as pd
from typing import Optional

logger = logging.getLogger(__name__)

def calculate_average_turnover_time(df: pd.DataFrame) -> Optional[float]:
    """
    Анализирует лог событий и вычисляет среднее время
    между освобождением стола и подходом новых гостей

    Args:
        df: Pandas DataFrame со столбцами 'event' и 'time_sec'.
    
    Returns:
        float: Среднее время в секундах. 
        None: Если полных циклов (уход -> приход) не найдено.
    """

    # Защита от пустоты
    if df is None or df.empty:
        logger.warning("DataFrame пуст, нет данных для расчета")
        return None

    delays = []
    last_empty_time = None

    # Проходимся по всем строкам таблицы событий
    for index, row in df.iterrows():
        event = row['event']
        current_time = row['time_sec']
        
        if event == 'empty':
            # Запоминаем время, когда стол освободился
            last_empty_time = current_time

        elif event == 'approach' and last_empty_time is not None:
            # Человек подошел и есть информация когда стол освободился
            # Считаем разницу во времени
            delay = current_time - last_empty_time
            delays.append(delay)

            # Сбрасываем время ухода
            last_empty_time = None
    
    if not delays:
        logger.warning("На видео не найдено полных циклов (Уход -> приход нового)")
        return None
    
    # Среднее время
    average_delay = sum(delays) / len(delays)

    logger.info(f"Найдено циклов уборки: {len(delays)}")
    logger.info(f"Среднее время задержки: {average_delay:.2f} сек.")

    return average_delay
