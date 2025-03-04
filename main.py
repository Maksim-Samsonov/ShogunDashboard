#!/usr/bin/env python3
"""
Точка входа в приложение ShogunOSC GUI.
Запускает основное окно и инициализирует необходимые компоненты.
"""

import sys
import traceback
import logging
import argparse
import os
import platform
from PyQt5.QtWidgets import QApplication, QMessageBox, QSplashScreen
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QTimer

from logger.custom_logger import setup_logging, log_system_info
import config

def parse_arguments():
    """Парсинг аргументов командной строки"""
    parser = argparse.ArgumentParser(description='ShogunOSC GUI - приложение для управления Shogun Live через OSC')
    parser.add_argument('--log-file', action='store_true', help='Включить логирование в файл')
    parser.add_argument('--log-dir', type=str, help='Директория для файлов логов')
    parser.add_argument('--debug', action='store_true', help='Включить отладочный режим')
    return parser.parse_args()

def show_error_message(message, details=None):
    """Показывает диалоговое окно с ошибкой"""
    error_dialog = QMessageBox()
    error_dialog.setIcon(QMessageBox.Critical)
    error_dialog.setWindowTitle("Ошибка")
    error_dialog.setText(message)
    if details:
        error_dialog.setDetailedText(details)
    error_dialog.setStandardButtons(QMessageBox.Ok)
    error_dialog.exec_()

def main():
    """Основная функция запуска приложения"""
    app = QApplication(sys.argv)
    try:
        # Парсим аргументы командной строки
        args = parse_arguments()
        
        # Настройка логирования
        log_level = logging.DEBUG if args.debug else logging.INFO
        logger = setup_logging(args.log_file, args.log_dir)
        logger.setLevel(log_level)
        
        # Логируем информацию о системе
        log_system_info(logger)
        
        # Проверяем успешность импорта библиотек в config
        if not config.IMPORT_SUCCESS:
            error_msg = f"Ошибка импорта библиотек: {config.IMPORT_ERROR}"
            logger.critical(error_msg)
            print(error_msg)
            print("Убедитесь, что установлены необходимые библиотеки:")
            print("pip install vicon-core-api shogun-live-api python-osc psutil PyQt5")
            
            # Создаем приложение только для показа ошибки
            show_error_message(
                "Ошибка импорта необходимых библиотек", 
                f"Ошибка: {config.IMPORT_ERROR}\n\n"
                "Убедитесь, что установлены необходимые библиотеки:\n"
                "pip install vicon-core-api shogun-live-api python-osc psutil PyQt5"
            )
            return
        
        # Выводим информацию о системе
        logger.info("=== Информация о системе ===")
        logger.info(f"platform: {platform.platform()}")
        logger.info(f"python_version: {platform.python_version()}")
        logger.info(f"processor: {platform.processor()}")
        
        logger.info(f"HYPERDECK_ENABLED: {config.HYPERDECK_ENABLED}")
        print(f"HYPERDECK_ENABLED: {config.HYPERDECK_ENABLED}")
        
        # Импортируем GUI только после проверки зависимостей
        from gui.main_window import ShogunOSCApp
        
        # app = QApplication(sys.argv)
        app.setStyle('Fusion')
        app.setApplicationName("ShogunOSC")
        app.setApplicationVersion(config.APP_VERSION)
        
        # Создаем заставку при запуске
        splash = None
        splash_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "splash.png")
        if os.path.exists(splash_path):
            splash_pixmap = QPixmap(splash_path)
            splash = QSplashScreen(splash_pixmap)
            splash.show()
            app.processEvents()
        
        # Создаем главное окно
        window = ShogunOSCApp()
        
        # Применяем тему при запуске если нужно
        if config.DARK_MODE:
            from styles.app_styles import get_palette, get_stylesheet
            app.setPalette(get_palette(True))
            app.setStyleSheet(get_stylesheet(True))
        
        # Закрываем заставку и показываем главное окно
        if splash:
            # Небольшая задержка для отображения заставки
            QTimer.singleShot(1500, lambda: (splash.finish(window), window.show()))
        else:
            window.show()
        
        # Запускаем главный цикл приложения
        sys.exit(app.exec_())
        
    except Exception as e:
        # Получаем полный стек ошибки
        error_details = traceback.format_exc()
        error_message = f"Ошибка при запуске приложения: {str(e)}"
        
        # Логируем ошибку если логгер уже настроен
        try:
            logger = logging.getLogger('ShogunOSC')
            logger.critical(error_message)
            logger.critical(error_details)
        except:
            # Если логгер еще не настроен, выводим в консоль
            print(error_message)
            print(error_details)
        
        # Создаем приложение только для показа ошибки
        show_error_message(error_message, error_details)
        sys.exit(1)

if __name__ == "__main__":
    main()