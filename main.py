"""
Главная точка входа для системы аналитики ресторанных столиков.
"""

import argparse
import logging
import sys
from pathlib import Path

import cv2

from core.config import settings
from core.detector import PersonDetector
from core.tracker import TableTracker
from core.analytics import calculate_average_turnover_time

# Настройка логгера
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)

def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Аналитика занятости ресторанных столиков")
    parser.add_argument("-v", "--video", type=str, required=True, help="Путь к входному видеофайлу")
    parser.add_argument("-o", "--output", type=str, default="output.mp4", help="Путь для сохранения")
    return parser.parse_args()

def select_table_roi(first_frame) -> tuple:
    logger.info("Пожалуйста, выделите зону столика в открывшемся окне и нажмите ENTER.")
    window_name = "Select Table"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 1280, 720)
    
    roi = cv2.selectROI(window_name, first_frame, showCrosshair=True, fromCenter=False)
    cv2.destroyWindow(window_name)
    
    if roi == (0, 0, 0, 0):
        logger.warning("Выделение зоны отменено пользователем.")
        sys.exit(0)
        
    x, y, w, h = roi
    return (x, y, x + w, y + h)

def main():
    args = parse_arguments()
    video_path = Path(args.video)

    if not video_path.exists():
        logger.error(f"Входной видеофайл не найден: {video_path}")
        sys.exit(1)

    logger.info("Инициализация нейросети и модуля трекинга...")
    detector = PersonDetector()
    tracker = TableTracker()

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        logger.error("Не удалось открыть видеопоток.")
        sys.exit(1)

    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    ret, first_frame = cap.read()
    if not ret:
        logger.error("Не удалось прочитать первый кадр.")
        sys.exit(1)

    table_box = select_table_roi(first_frame)
    logger.info(f"Координаты целевого стола зафиксированы: {table_box}")

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(args.output, fourcc, fps, (width, height))

    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    frame_count = 0

    logger.info("Запуск пайплайна обработки видео...")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            current_time_sec = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0

            people_boxes = detector.get_people_boxes(frame)
            tracker.update(people_boxes, table_box, current_time_sec)

            for p_box in people_boxes:
                cv2.rectangle(frame, (p_box[0], p_box[1]), (p_box[2], p_box[3]), settings.COLOR_PERSON, settings.BOX_THICKNESS)

            table_color = settings.COLOR_EMPTY if tracker.is_empty else settings.COLOR_OCCUPIED
            cv2.rectangle(frame, (table_box[0], table_box[1]), (table_box[2], table_box[3]), table_color, settings.BOX_THICKNESS + 1)
            
            status_text = "EMPTY" if tracker.is_empty else "OCCUPIED"
            cv2.putText(frame, status_text, (table_box[0], table_box[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, table_color, 2)

            out.write(frame)
            frame_count += 1

    except KeyboardInterrupt:
        logger.info("Обработка прервана пользователем.")
    finally:
        cap.release()
        out.release()
        cv2.destroyAllWindows()
        logger.info(f"Обработка видео завершена. Результат сохранен в {args.output}")

    logger.info("Формирование аналитики оборачиваемости...")
    df_events = tracker.get_events_dataframe()
    avg_time = calculate_average_turnover_time(df_events)

    if avg_time is not None:
        logger.info(f"УСПЕХ: Среднее время оборачиваемости стола составляет {avg_time:.2f} сек.")
    else:
        logger.warning("НЕДОСТАТОЧНО ДАННЫХ: Невозможно рассчитать время оборачиваемости (нет полных циклов).")

if __name__ == "__main__":
    main()