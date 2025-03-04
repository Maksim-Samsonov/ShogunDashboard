"""
Основное окно приложения ShogunOSC.
Собирает и координирует работу всех компонентов интерфейса,
обрабатывает сигналы между компонентами.
"""

import asyncio
import logging
import threading
import os
import traceback
from datetime import datetime
from typing import Optional

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QLabel, QPushButton, QTextEdit, QGroupBox, QGridLayout,
                           QLineEdit, QSpinBox, QComboBox, QStatusBar, QCheckBox, QSplitter,
                           QAction, QMenu, QToolBar, QApplication, QMessageBox, QFileDialog,
                           QTabWidget)
from PyQt5.QtCore import Qt, QTimer, QSettings
from PyQt5.QtGui import QTextCursor, QIcon

from gui.status_panel import StatusPanel
from gui.log_panel import LogPanel
from gui.hyperdeck_panel import HyperDeckPanel
from gui.hyperdeck_status_panel import HyperDeckStatusPanel
from gui.shogun_panel import ShogunPanel
from gui.components.settings_panel import SettingsPanel
from gui.components.dashboard_panel import DashboardPanel
from shogun.shogun_client import ShogunWorker
from hyperdeck.hyperdeck_worker import HyperDeckWorker
from osc.osc_server import OSCServer
from logger.custom_logger import add_text_widget_handler
from styles.app_styles import get_palette, get_stylesheet, set_status_style
import config


class ShogunOSCApp(QMainWindow):
    """Главное окно приложения. Отвечает за организацию 
    интерфейса и координацию работы всех компонентов."""
    
    def __init__(self):
        try:
            super().__init__()
            self.setWindowTitle("ShogunOSC GUI")
            
            # Configure logging
            self.logger = logging.getLogger('ShogunOSC')
            self.logger.setLevel(logging.INFO)
            
            # Add file handler for system logs
            log_file = os.path.join(config.CONFIG_DIR, 'shogun_osc.log')
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(logging.Formatter(config.LOG_FORMAT))
            self.logger.addHandler(file_handler)
            
            # Инициализация компонентов
            self.init_components()
            
            # Инициализация интерфейса
            self.init_ui()
            
            # Подключение сигналов
            self.connect_signals()
            
            # Загрузка настроек
            self.load_settings()
            
            # Запуск рабочих потоков
            self.start_workers()
            
            self.logger.info("Application started")
            
        except Exception as e:
            error_msg = f"Ошибка при инициализации главного окна: {str(e)}"
            error_details = traceback.format_exc()
            self.logger.critical(error_msg)
            self.logger.critical(error_details)
            self.show_error_dialog("Ошибка инициализации", error_msg, error_details)
            raise
    
    def init_components(self):
        """Инициализация компонентов приложения"""
        try:
            # Инициализация рабочих потоков
            self.shogun_worker = ShogunWorker()
            self.hyperdeck_worker = HyperDeckWorker()
            
            # Initialize OSC server with default IP and port
            self.osc_server = OSCServer(config.DEFAULT_OSC_IP, config.DEFAULT_OSC_PORT)
            
            # New components
            self.dashboard = DashboardPanel()
            self.settings_panel = SettingsPanel()
            
            # Connect logger to dashboard
            add_text_widget_handler(self.dashboard.log_text)
            
            # Инициализация панелей
            self.shogun_panel = ShogunPanel()
            self.log_panel = LogPanel()
            self.status_panel = StatusPanel(self.shogun_worker)
            
            # Создаем панели HyperDeck только если включена поддержка
            if config.HYPERDECK_ENABLED:
                print("DEBUG: Creating HyperDeck panels")
                self.logger.info("Creating HyperDeck panels")
                self.hyperdeck_panel = HyperDeckPanel()
                self.hyperdeck_status_panel = HyperDeckStatusPanel()
                print(f"DEBUG: HyperDeck panels created: panel={self.hyperdeck_panel}, status_panel={self.hyperdeck_status_panel}")
            else:
                print("DEBUG: HyperDeck is DISABLED")
                self.logger.info("HyperDeck support is disabled")
                self.hyperdeck_panel = None
                self.hyperdeck_status_panel = None
            
            # Добавляем обработчик логов в текстовый виджет
            add_text_widget_handler(self.log_panel.log_text)
            
        except Exception as e:
            self.logger.critical(f"Ошибка при инициализации компонентов: {e}")
            print(f"ERROR: {e}")
            raise
    
    def init_ui(self):
        """Инициализация пользовательского интерфейса"""
        try:
            # Create central widget
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            
            # Create main layout
            layout = QVBoxLayout()
            central_widget.setLayout(layout)
            
            # Create tabbed interface
            self.tabs = QTabWidget()
            
            # Dashboard Tab
            self.tabs.addTab(self.dashboard, "Dashboard")
            
            # Settings Tab
            self.tabs.addTab(self.settings_panel, "Settings")
            
            # HyperDeck Tab (if enabled)
            if config.HYPERDECK_ENABLED:
                self.tabs.addTab(self.hyperdeck_panel, "HyperDeck")
            
            layout.addWidget(self.tabs)
            
            # Status Bar
            self.statusBar().showMessage("Ready")
            
            # Connect signals
            self.connect_signals()
            
            # Apply theme
            self.apply_theme()

            # Set window size and show
            self.resize(1200, 800)
            self.show()
            
            self.logger.info("UI initialized")
            
        except Exception as e:
            self.logger.critical(f"Ошибка при инициализации интерфейса: {e}")
            raise

    def connect_signals(self):
        """Подключение сигналов между компонентами"""
        # Status updates
        self.shogun_worker.status_signal.connect(
            lambda status: self.dashboard.update_status("shogun", status == config.STATUS_CONNECTED)
        )
        self.hyperdeck_worker.device_status_signal.connect(
            lambda i, status: self.dashboard.update_status(f"hyperdeck_{i+1}", status)
        )
        
        # Recording controls
        self.dashboard.recording_controls.start_recording.connect(
            self.start_all_recordings
        )
        self.dashboard.recording_controls.stop_recording.connect(
            self.stop_all_recordings
        )
        
        # Settings changes
        self.settings_panel.settings_changed.connect(self.handle_settings_changed)
        
        # OSC server status
        self.osc_server.set_status_callback(
            lambda status: self.dashboard.update_status("osc", status)
        )

    def start_all_recordings(self):
        """Handle synchronized recording start"""
        try:
            # Check if Shogun is connected
            if not self.shogun_worker.connected:
                self.logger.error("Cannot start recording - Shogun Live is not connected")
                self.dashboard.add_log_message("Error: Shogun Live is not connected")
                return
            
            # Check if HyperDeck is available (if enabled)
            if config.HYPERDECK_ENABLED and not self.hyperdeck_worker.has_devices():
                self.logger.error("Cannot start recording - No HyperDeck devices available")
                self.dashboard.add_log_message("Error: No HyperDeck devices available")
                return
            
            # Start Shogun recording first
            self.shogun_worker.start_recording()
            
            # Start HyperDeck recording if enabled
            if config.HYPERDECK_ENABLED:
                self.hyperdeck_worker.start_recording()
                
            self.dashboard.add_log_message("Started recording on all devices")
            
        except Exception as e:
            self.logger.error(f"Error starting recordings: {e}")
            self.dashboard.add_log_message(f"Error starting recordings: {e}")
            
    def stop_all_recordings(self):
        """Handle synchronized recording stop"""
        try:
            # Stop Shogun recording first
            if self.shogun_worker.connected:
                self.shogun_worker.stop_recording()
            
            # Stop HyperDeck recording if enabled
            if config.HYPERDECK_ENABLED:
                self.hyperdeck_worker.stop_recording()
                
            self.dashboard.add_log_message("Stopped recording on all devices")
            
        except Exception as e:
            self.logger.error(f"Error stopping recordings: {e}")
            self.dashboard.add_log_message(f"Error stopping recordings: {e}")
            
    def handle_settings_changed(self, new_settings):
        """Update application settings"""
        try:
            # Update OSC server settings
            if 'osc_ip' in new_settings or 'osc_port' in new_settings or new_settings.get('restart_osc', False):
                self.osc_server.stop()
                self.osc_server = OSCServer(
                    new_settings.get('osc_ip', config.DEFAULT_OSC_IP),
                    new_settings.get('osc_port', config.DEFAULT_OSC_PORT)
                )
                self.osc_server.set_status_callback(
                    lambda status: self.dashboard.update_status("osc", status)
                )
                self.osc_server.start()
                self.logger.info(f"OSC server restarted on {new_settings.get('osc_ip')}:{new_settings.get('osc_port')}")
            
            # Update HyperDeck settings
            if 'hyperdeck_devices' in new_settings:
                config.HYPERDECK_DEVICES = new_settings['hyperdeck_devices']
                config.HYPERDECK_ENABLED = new_settings.get('hyperdeck_enabled', True)
                config.HYPERDECK_SYNC_WITH_SHOGUN = new_settings.get('hyperdeck_sync_with_shogun', True)
                
                # Update HyperDeck worker
                self.hyperdeck_worker.update_devices(config.HYPERDECK_DEVICES)
                
                # Update dashboard info
                self.dashboard.status_widget.update_info()
                
                self.logger.info("HyperDeck settings updated")
            
            # Save settings
            config.save_settings(new_settings)
            self.logger.info("Settings saved successfully")
            
        except Exception as e:
            self.logger.error(f"Error updating settings: {e}")
            self.dashboard.add_log_message(f"Error updating settings: {e}")
    
    def start_workers(self):
        """Запуск рабочих потоков"""
        try:
            self.shogun_worker.start()
            if self.hyperdeck_worker:
                self.hyperdeck_worker.start()
            self.osc_server.start()
            self.logger.info("Рабочие потоки запущены")
        except Exception as e:
            self.logger.critical(f"Ошибка при запуске рабочих потоков: {e}")
            raise
    
    def show_error_dialog(self, title, message, details=None):
        """Показывает диалоговое окно с ошибкой"""
        error_dialog = QMessageBox(self)
        error_dialog.setIcon(QMessageBox.Critical)
        error_dialog.setWindowTitle(title)
        error_dialog.setText(message)
        if details:
            error_dialog.setDetailedText(details)
        error_dialog.setStandardButtons(QMessageBox.Ok)
        error_dialog.exec_()
    
    def load_settings(self):
        """Загрузка настроек приложения"""
        try:
            # Применяем тему
            if config.DARK_MODE:
                self.apply_theme(True)
            
            self.logger.info("Настройки загружены успешно")
        except Exception as e:
            self.logger.error(f"Ошибка при загрузке настроек: {e}")
    
    def save_settings(self):
        """Сохранение настроек приложения"""
        try:
            # Сохраняем настройки в конфиг
            config.save_settings(config.app_settings)
            self.logger.info("Настройки сохранены успешно")
        except Exception as e:
            self.logger.error(f"Ошибка при сохранении настроек: {e}")
    
    def apply_theme(self, dark_mode=False):
        """Применение темы оформления"""
        try:
            app = QApplication.instance()
            if app:
                app.setPalette(get_palette(dark_mode))
                app.setStyleSheet(get_stylesheet(dark_mode))
        except Exception as e:
            self.logger.error(f"Ошибка при применении темы: {e}")
    
    def closeEvent(self, event):
        """Обработчик закрытия окна"""
        try:
            # Останавливаем рабочие потоки
            if self.shogun_worker:
                self.shogun_worker.stop()
            if self.hyperdeck_worker:
                self.hyperdeck_worker.stop()
            if self.osc_server:
                self.osc_server.stop()
            
            # Сохраняем настройки
            self.save_settings()
            
            self.logger.info("Приложение закрыто корректно")
            event.accept()
            
        except Exception as e:
            self.logger.error(f"Ошибка при закрытии приложения: {e}")
            event.accept()  # Все равно закрываем окно