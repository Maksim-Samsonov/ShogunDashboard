"""
Модуль настройки логирования для приложения.
Включает кастомный форматтер для цветного отображения логов в QTextEdit.
"""

import logging
import queue
import os
import sys
from datetime import datetime
from typing import Optional, Dict, Any
import time

from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import QTextEdit
from PyQt5.QtGui import QTextCursor

import config

class ColoredFormatter(logging.Formatter):
    """Форматтер логов с цветами для отображения в HTML"""
    COLORS = {
        'DEBUG': 'gray',
        'INFO': 'darkgreen',
        'WARNING': 'darkorange',
        'ERROR': 'red',
        'CRITICAL': 'purple',
    }

    def format(self, record):
        log_message = super().format(record)
        color = self.COLORS.get(record.levelname, 'black')
        return f'<span style="color:{color};">{log_message}</span>'

class QTextEditLogger(logging.Handler):
    """Хендлер логов для вывода в QTextEdit с использованием очереди"""
    def __init__(self, text_widget, max_batch_size=20):
        super().__init__()
        self.text_widget = text_widget
        self.queue = queue.Queue()
        self.setFormatter(ColoredFormatter(config.LOG_FORMAT))
        self.max_batch_size = max_batch_size
        self.batch_buffer = []
        self.last_update_time = time.time()
        self.min_update_interval = 0.2  # Минимальный интервал обновления (200 мс)
        self.max_update_interval = 1.0   # Максимальный интервал обновления (1 сек)
        
        # Создаем таймер для обновления интерфейса
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_logs)
        self.update_timer.start(100)  # Обновление каждые 100 мс
        
    def emit(self, record):
        """Добавляет запись лога в очередь"""
        # Фильтрация по уровню для оптимизации
        if record.levelno < logging.INFO and not config.app_settings.get("debug_mode", False):
            return
        self.queue.put(record)
        
    def update_logs(self):
        """Обновляет текстовый виджет логами из очереди с оптимизацией производительности"""
        current_time = time.time()
        time_since_last_update = current_time - self.last_update_time
        
        # Проверяем, нужно ли обновлять логи сейчас
        queue_size = self.queue.qsize()
        
        # Если очередь пуста и буфер пуст, нечего обновлять
        if queue_size == 0 and not self.batch_buffer:
            return
            
        # Определяем, нужно ли обновлять на основе размера очереди и времени
        should_update = (
            queue_size >= self.max_batch_size or  # Много записей - обновляем немедленно
            (self.batch_buffer and time_since_last_update >= self.max_update_interval) or  # Прошло максимальное время
            (queue_size > 0 and time_since_last_update >= self.min_update_interval)  # Есть записи и прошло минимальное время
        )
        
        if not should_update:
            return
            
        # Ограничиваем количество обрабатываемых записей за один раз
        records_to_process = min(queue_size, self.max_batch_size)
        
        try:
            # Извлекаем записи из очереди в буфер
            for _ in range(records_to_process):
                try:
                    record = self.queue.get_nowait()
                    self.batch_buffer.append(self.format(record))
                except queue.Empty:
                    break
                    
            # Если буфер не пуст, обновляем UI
            if self.batch_buffer:
                # Объединяем все сообщения в одну HTML-строку для оптимизации обновления UI
                batch_html = "<br>".join(self.batch_buffer)
                self.text_widget.append(batch_html)
                self.text_widget.moveCursor(QTextCursor.End)
                
                # Очищаем буфер
                self.batch_buffer = []
                self.last_update_time = current_time
                
        except Exception as e:
            # Логируем ошибку в консоль, так как логгер может быть недоступен
            print(f"Ошибка при обновлении логов: {e}", file=sys.stderr)
            
def setup_logging(log_to_file: bool = False, log_dir: Optional[str] = None) -> logging.Logger:
    """
    Настраивает базовое логирование для приложения
    
    Args:
        log_to_file: Включить логирование в файл
        log_dir: Директория для файлов логов
        
    Returns:
        logging.Logger: Настроенный логгер
    """
    # Настраиваем базовое логирование
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Очищаем существующие обработчики, чтобы избежать дублирования
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)
    
    # Добавляем обработчик для вывода в консоль
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(config.LOG_FORMAT))
    root_logger.addHandler(console_handler)
    
    # Настройка логирования в файл, если требуется
    if log_to_file:
        try:
            if log_dir is None:
                log_dir = os.path.join(config.CONFIG_DIR, "logs")
            
            # Создаем директорию для логов, если не существует
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            # Создаем файл лога с датой и временем
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = os.path.join(log_dir, f"shogun_osc_{timestamp}.log")
            
            # Добавляем обработчик для записи в файл с ротацией по размеру
            # Максимальный размер файла 5 МБ, хранить до 3 резервных копий
            from logging.handlers import RotatingFileHandler
            file_handler = RotatingFileHandler(
                log_file, 
                maxBytes=5*1024*1024,  # 5 МБ
                backupCount=3,
                encoding='utf-8'
            )
            file_handler.setFormatter(logging.Formatter(config.LOG_FORMAT))
            root_logger.addHandler(file_handler)
            
            # Логируем информацию о начале логирования в файл
            root_logger.info(f"Логирование в файл включено: {log_file}")
        except Exception as e:
            root_logger.error(f"Не удалось настроить логирование в файл: {e}")
    
    # Настройка логгеров для различных модулей
    loggers = {
        'ShogunOSC': logging.INFO,
        'WebUI': logging.INFO,
        'HyperDeck': logging.INFO,
        'aiohttp': logging.ERROR,
        'asyncio': logging.WARNING,  # Уменьшаем вывод от asyncio
        'pythonosc': logging.WARNING,  # Уменьшаем вывод от pythonosc
    }
    
    for name, level in loggers.items():
        logger = logging.getLogger(name)
        logger.setLevel(level)
    
    # Возвращаем основной логгер приложения
    return logging.getLogger('ShogunOSC')

def add_text_widget_handler(text_widget) -> QTextEditLogger:
    """
    Добавляет обработчик для вывода логов в текстовый виджет
    
    Args:
        text_widget: Виджет QTextEdit для вывода логов
        
    Returns:
        QTextEditLogger: Созданный обработчик логов
    """
    logger = logging.getLogger('ShogunOSC')
    
    # Удаляем предыдущие QTextEditLogger, если они были
    for handler in list(logger.handlers):
        if isinstance(handler, QTextEditLogger):
            logger.removeHandler(handler)
    
    # Создаем и добавляем новый обработчик
    handler = QTextEditLogger(text_widget, max_batch_size=30)
    handler.setLevel(logging.INFO)
    logger.addHandler(handler)
    return handler

def get_system_info() -> Dict[str, Any]:
    """
    Собирает информацию о системе для диагностики
    
    Returns:
        Dict[str, Any]: Словарь с информацией о системе
    """
    import platform
    
    system_info = {
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "processor": platform.processor(),
        "machine": platform.machine(),
        "app_version": config.APP_VERSION
    }
    
    # Добавляем информацию о PyQt
    try:
        from PyQt5.QtCore import QT_VERSION_STR, PYQT_VERSION_STR
        system_info["qt_version"] = QT_VERSION_STR
        system_info["pyqt_version"] = PYQT_VERSION_STR
    except ImportError:
        system_info["qt_version"] = "unknown"
        system_info["pyqt_version"] = "unknown"
    
    return system_info

def log_system_info(logger: logging.Logger) -> None:
    """
    Логирует информацию о системе
    
    Args:
        logger: Логгер для записи информации
    """
    system_info = get_system_info()
    logger.info("=== Информация о системе ===")
    for key, value in system_info.items():
        logger.info(f"{key}: {value}")
    logger.info("===========================")