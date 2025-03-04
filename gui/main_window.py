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
import time
from datetime import datetime
from typing import Optional, Dict, Any

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                          QLabel, QPushButton, QTextEdit, QGroupBox, QGridLayout,
                          QLineEdit, QSpinBox, QComboBox, QStatusBar, QCheckBox, QSplitter,
                          QAction, QMenu, QToolBar, QApplication, QMessageBox, QFileDialog,
                          QTabWidget)
from PyQt5.QtCore import Qt, QTimer, QSettings
from PyQt5.QtGui import QTextCursor, QIcon

from gui.dashboard_panel import DashboardPanel
from gui.log_panel import LogPanel
from gui.shogun_panel import ShogunPanel
from gui.components.settings_panel import SettingsPanel
from gui.components.dashboard_panel import DashboardPanel as OldDashboardPanel
from shogun.shogun_client import ShogunWorker
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
            self.setWindowTitle(f"ShogunOSC GUI v{config.APP_VERSION}")
            
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
            
            self.logger.info(f"Приложение запущено (версия {config.APP_VERSION})")
            
        except Exception as e:
            error_msg = f"Ошибка при инициализации главного окна: {str(e)}"
            error_details = traceback.format_exc()
            print(f"КРИТИЧЕСКАЯ ОШИБКА: {error_msg}")
            print(error_details)
            try:
                if hasattr(self, 'logger'):
                    self.logger.critical(error_msg)
                    self.logger.critical(error_details)
            except:
                pass
            self.show_error_dialog("Ошибка инициализации", error_msg, error_details)
            raise
    
    def init_components(self):
        """Инициализация компонентов приложения"""
        try:
            # Инициализация рабочих потоков
            self.shogun_worker = ShogunWorker()
            
            # Инициализация HyperDeck только если включено
            self.hyperdeck_worker = None
            if config.HYPERDECK_ENABLED:
                try:
                    self.logger.info("Инициализация HyperDeck worker")
                    from hyperdeck.hyperdeck_worker import HyperDeckWorker
                    self.hyperdeck_worker = HyperDeckWorker()
                    self.logger.info("HyperDeck worker успешно создан")
                except Exception as e:
                    self.logger.error(f"Ошибка при инициализации HyperDeck worker: {e}")
                    config.HYPERDECK_ENABLED = False  # Отключаем HyperDeck при ошибке
            
            # Initialize OSC server with default IP and port
            self.osc_server = OSCServer(config.DEFAULT_OSC_IP, config.DEFAULT_OSC_PORT)
            
            # New components
            self.dashboard = DashboardPanel()
            self.settings_panel = SettingsPanel()
            
            # Connect logger to dashboard
            add_text_widget_handler(self.dashboard.log_panel.log_text)
            
            # Инициализация панелей
            self.shogun_panel = ShogunPanel()
            self.log_panel = LogPanel()
            
            # Создаем панели HyperDeck только если включена поддержка
            self.hyperdeck_panel = None
            self.hyperdeck_status_panel = None
            if config.HYPERDECK_ENABLED:
                self.logger.info("Инициализация HyperDeck панелей")
                try:
                    from gui.hyperdeck_panel import HyperDeckPanel
                    from gui.hyperdeck_status_panel import HyperDeckStatusPanel
                    
                    self.hyperdeck_panel = HyperDeckPanel()
                    self.hyperdeck_status_panel = HyperDeckStatusPanel()
                    self.logger.info("HyperDeck панели успешно созданы")
                except Exception as e:
                    self.logger.error(f"Ошибка при создании HyperDeck панелей: {e}")
                    config.HYPERDECK_ENABLED = False  # Отключаем HyperDeck при ошибке
            
        except Exception as e:
            self.logger.critical(f"Ошибка при инициализации компонентов: {e}")
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
            if config.HYPERDECK_ENABLED and self.hyperdeck_panel:
                self.tabs.addTab(self.hyperdeck_panel, "HyperDeck")
            
            layout.addWidget(self.tabs)
            
            # Status Bar
            self.status_bar = self.statusBar()
            self.status_bar.showMessage("Ready")
            
            # Add status indicators to status bar
            if config.HYPERDECK_ENABLED and self.hyperdeck_status_panel:
                self.status_bar.addPermanentWidget(self.hyperdeck_status_panel)
            
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
        try:
            # Status updates для Shogun
            if self.shogun_worker:
                self.shogun_worker.status_signal.connect(
                    lambda status: self.dashboard.update_status("shogun", status == config.STATUS_CONNECTED)
                )
                self.shogun_worker.connection_signal.connect(
                    lambda connected: self.dashboard.update_status("shogun", connected)
                )
                self.shogun_worker.recording_signal.connect(
                    lambda is_recording: self.dashboard.status_panel.update_shogun_recording(is_recording)
                    if hasattr(self.dashboard, 'status_panel') and 
                    hasattr(self.dashboard.status_panel, 'update_shogun_recording') else None
                )
                self.shogun_worker.take_name_signal.connect(
                    self.dashboard.status_panel.update_take_name
                    if hasattr(self.dashboard, 'status_panel') and 
                    hasattr(self.dashboard.status_panel, 'update_take_name') else None
                )
                self.shogun_worker.capture_name_changed_signal.connect(
                    self.dashboard.status_panel.update_capture_name
                    if hasattr(self.dashboard, 'status_panel') and 
                    hasattr(self.dashboard.status_panel, 'update_capture_name') else None
                )
                self.shogun_worker.capture_error_signal.connect(
                    lambda error: self.log_error(f"Ошибка Shogun: {error}")
                )
            
            # Status updates для HyperDeck
            if config.HYPERDECK_ENABLED and self.hyperdeck_worker:
                # Сигнал для обновления статуса в dashboard
                self.hyperdeck_worker.device_status_signal.connect(
                    lambda device_id, status: self.dashboard.update_status(f"hyperdeck_{device_id+1}", status)
                )
                
                # Сигналы для панели HyperDeck если она есть
                if self.hyperdeck_panel and hasattr(self.hyperdeck_panel, 'update_device_status'):
                    self.hyperdeck_worker.device_status_signal.connect(
                        self.hyperdeck_panel.update_device_status
                    )
                
                if self.hyperdeck_panel and hasattr(self.hyperdeck_panel, 'update_device_recording'):
                    self.hyperdeck_worker.device_recording_signal.connect(
                        self.hyperdeck_panel.update_device_recording
                    )
                
                # Сигналы для статусов в DeviceStatusPanel
                if hasattr(self.dashboard, 'status_panel') and hasattr(self.dashboard.status_panel, 'update_hyperdeck_connection'):
                    self.hyperdeck_worker.device_status_signal.connect(
                        self.dashboard.status_panel.update_hyperdeck_connection
                    )
                
                if hasattr(self.dashboard, 'status_panel') and hasattr(self.dashboard.status_panel, 'update_hyperdeck_recording'):
                    self.hyperdeck_worker.device_recording_signal.connect(
                        self.dashboard.status_panel.update_hyperdeck_recording
                    )
                
                # Статус для панели статуса HyperDeck если она доступна
                if self.hyperdeck_status_panel:
                    if hasattr(self.hyperdeck_status_panel, 'update_device_status'):
                        self.hyperdeck_worker.device_status_signal.connect(
                            self.hyperdeck_status_panel.update_device_status
                        )
                    
                    if hasattr(self.hyperdeck_status_panel, 'update_device_recording'):
                        self.hyperdeck_worker.device_recording_signal.connect(
                            self.hyperdeck_status_panel.update_device_recording
                        )
                
                # Обработка ошибок HyperDeck
                self.hyperdeck_worker.error_signal.connect(
                    lambda error: self.log_error(f"Ошибка HyperDeck: {error}")
                )
            
            # Recording controls - сигналы из dashboard
            if hasattr(self.dashboard, 'start_all_recording_signal'):
                self.dashboard.start_all_recording_signal.connect(
                    self.start_all_recordings
                )
            
            if hasattr(self.dashboard, 'stop_all_recording_signal'):
                self.dashboard.stop_all_recording_signal.connect(
                    self.stop_all_recordings
                )
            
            # Settings changes
            if hasattr(self.settings_panel, 'settings_changed'):
                self.settings_panel.settings_changed.connect(self.handle_settings_changed)
            
            # OSC server status
            if self.osc_server:
                self.osc_server.set_status_callback(
                    lambda status: self.dashboard.update_status("osc", status)
                )
                
                # Регистрация OSC обработчиков
                self.register_osc_handlers()
            
            self.logger.info("Signals connected")
        except Exception as e:
            self.logger.error(f"Ошибка при подключении сигналов: {e}")
    
    def register_osc_handlers(self):
        """Регистрация обработчиков OSC-сообщений"""
        if not self.osc_server:
            return
            
        # Обработчики для Shogun Live
        self.osc_server.register_handler(config.OSC_START_RECORDING, self.osc_start_shogun)
        self.osc_server.register_handler(config.OSC_STOP_RECORDING, self.osc_stop_shogun)
        
        # Обработчики для HyperDeck
        if config.HYPERDECK_ENABLED:
            self.osc_server.register_handler(config.OSC_HYPERDECK_START_RECORDING, self.osc_start_hyperdeck)
            self.osc_server.register_handler(config.OSC_HYPERDECK_STOP_RECORDING, self.osc_stop_hyperdeck)
        
        # Обработчики для синхронизированного управления
        self.osc_server.register_handler(config.OSC_START_ALL_RECORDING, self.osc_start_all)
        self.osc_server.register_handler(config.OSC_STOP_ALL_RECORDING, self.osc_stop_all)
        
        self.logger.info("OSC handlers registered")
    
    def osc_start_shogun(self, address, *args):
        """Обработчик OSC-сообщения для начала записи в Shogun"""
        self.logger.info(f"Получено OSC-сообщение: {address}")
        if self.shogun_worker and self.shogun_worker.connected:
            self.shogun_worker.start_recording()
        else:
            self.logger.error("Не удалось начать запись в Shogun: нет подключения")
    
    def osc_stop_shogun(self, address, *args):
        """Обработчик OSC-сообщения для остановки записи в Shogun"""
        self.logger.info(f"Получено OSC-сообщение: {address}")
        if self.shogun_worker and self.shogun_worker.connected:
            self.shogun_worker.stop_recording()
        else:
            self.logger.error("Не удалось остановить запись в Shogun: нет подключения")
    
    def osc_start_hyperdeck(self, address, *args):
        """Обработчик OSC-сообщения для начала записи на HyperDeck"""
        self.logger.info(f"Получено OSC-сообщение: {address}")
        if config.HYPERDECK_ENABLED and self.hyperdeck_worker:
            self.hyperdeck_worker.start_recording()
        else:
            self.logger.error("Не удалось начать запись на HyperDeck: поддержка отключена или отсутствует")
    
    def osc_stop_hyperdeck(self, address, *args):
        """Обработчик OSC-сообщения для остановки записи на HyperDeck"""
        self.logger.info(f"Получено OSC-сообщение: {address}")
        if config.HYPERDECK_ENABLED and self.hyperdeck_worker:
            self.hyperdeck_worker.stop_recording()
        else:
            self.logger.error("Не удалось остановить запись на HyperDeck: поддержка отключена или отсутствует")
    
    def osc_start_all(self, address, *args):
        """Обработчик OSC-сообщения для начала записи на всех устройствах"""
        self.logger.info(f"Получено OSC-сообщение: {address}")
        self.start_all_recordings()
    
    def osc_stop_all(self, address, *args):
        """Обработчик OSC-сообщения для остановки записи на всех устройствах"""
        self.logger.info(f"Получено OSC-сообщение: {address}")
        self.stop_all_recordings()
    
    def start_all_recordings(self):
        """Handle synchronized recording start"""
        try:
            # Check if Shogun is connected
            if not self.shogun_worker or not self.shogun_worker.connected:
                self.logger.error("Cannot start recording - Shogun Live is not connected")
                if hasattr(self.dashboard, 'add_log_message'):
                    self.dashboard.add_log_message("Error: Shogun Live is not connected", level='ERROR')
                return
            
            # Check if HyperDeck is available (if enabled)
            if config.HYPERDECK_ENABLED and self.hyperdeck_worker and not self.hyperdeck_worker.has_devices():
                self.logger.warning("No HyperDeck devices available - starting only Shogun recording")
                if hasattr(self.dashboard, 'add_log_message'):
                    self.dashboard.add_log_message("Warning: No HyperDeck devices available", level='WARNING')
            
            # Генерируем имя записи на основе текущего времени
            capture_name = time.strftime("Capture_%Y%m%d_%H%M%S")
            
            # Start Shogun recording first
            self.logger.info(f"Starting recording with name: {capture_name}")
            self.shogun_worker.start_recording()
            
            # Start HyperDeck recording if enabled
            if config.HYPERDECK_ENABLED and self.hyperdeck_worker:
                self.hyperdeck_worker.start_recording()
                
            if hasattr(self.dashboard, 'add_log_message'):
                self.dashboard.add_log_message(f"Started recording on all devices: {capture_name}")
            
            # Отправляем OSC-уведомление о начале записи
            if self.osc_server:
                self.osc_server.send_message(config.OSC_START_ALL_RECORDING, 1)
            
        except Exception as e:
            self.logger.error(f"Error starting recordings: {e}")
            if hasattr(self.dashboard, 'add_log_message'):
                self.dashboard.add_log_message(f"Error starting recordings: {e}", level='ERROR')
            
    def stop_all_recordings(self):
        """Handle synchronized recording stop"""
        try:
            # Stop Shogun recording first
            if self.shogun_worker and self.shogun_worker.connected:
                self.shogun_worker.stop_recording()
            
            # Stop HyperDeck recording if enabled
            if config.HYPERDECK_ENABLED and self.hyperdeck_worker:
                self.hyperdeck_worker.stop_recording()
                
            if hasattr(self.dashboard, 'add_log_message'):
                self.dashboard.add_log_message("Stopped recording on all devices")
            
            # Отправляем OSC-уведомление об остановке записи
            if self.osc_server:
                self.osc_server.send_message(config.OSC_STOP_ALL_RECORDING, 1)
            
        except Exception as e:
            self.logger.error(f"Error stopping recordings: {e}")
            if hasattr(self.dashboard, 'add_log_message'):
                self.dashboard.add_log_message(f"Error stopping recordings: {e}", level='ERROR')
    
    def log_error(self, message):
        """Логирование ошибки в журнал и панель логов"""
        self.logger.error(message)
        if hasattr(self.dashboard, 'add_log_message'):
            self.dashboard.add_log_message(message, level='ERROR')

    def handle_settings_changed(self, new_settings):
        """Update application settings"""
        try:
            # Update OSC server settings
            osc_settings_changed = False
            
            if 'osc_ip' in new_settings or 'osc_port' in new_settings or new_settings.get('restart_osc', False):
                osc_settings_changed = True
                try:
                    # Останавливаем текущий сервер
                    if self.osc_server:
                        self.osc_server.stop()
                    
                    # Создаем новый сервер с обновленными настройками
                    osc_ip = new_settings.get('osc_ip', config.DEFAULT_OSC_IP)
                    osc_port = new_settings.get('osc_port', config.DEFAULT_OSC_PORT)
                    self.osc_server = OSCServer(osc_ip, osc_port)
                    
                    # Обновляем обработчики и статус
                    self.osc_server.set_status_callback(
                        lambda status: self.dashboard.update_status("osc", status)
                    )
                    self.register_osc_handlers()
                    
                    # Запускаем сервер
                    self.osc_server.start()
                    self.logger.info(f"OSC server restarted on {osc_ip}:{osc_port}")
                except Exception as e:
                    self.logger.error(f"Failed to restart OSC server: {e}")
            
            # Обновляем настройки широковещательной рассылки
            if 'osc_broadcast_ip' in new_settings or 'osc_broadcast_port' in new_settings:
                if self.osc_server:
                    broadcast_ip = new_settings.get('osc_broadcast_ip', config.DEFAULT_OSC_BROADCAST_IP)
                    broadcast_port = new_settings.get('osc_broadcast_port', config.DEFAULT_OSC_BROADCAST_PORT)
                    self.osc_server.set_broadcast_settings(broadcast_ip, broadcast_port)
                    self.logger.info(f"OSC broadcast settings updated: {broadcast_ip}:{broadcast_port}")
            
            # Update HyperDeck settings
            hyperdeck_settings_changed = False
            
            if 'hyperdeck_devices' in new_settings:
                hyperdeck_settings_changed = True
                # Обновляем настройки в конфиге
                config.HYPERDECK_DEVICES = new_settings['hyperdeck_devices']
            
            # Если есть изменение статуса включения HyperDeck
            if 'hyperdeck_enabled' in new_settings:
                old_enabled = config.HYPERDECK_ENABLED
                new_enabled = bool(new_settings.get('hyperdeck_enabled', True))
                
                if old_enabled != new_enabled:
                    hyperdeck_settings_changed = True
                    config.HYPERDECK_ENABLED = new_enabled
                    
                    # Если HyperDeck был выключен, а теперь включен - создаем объекты
                    if not old_enabled and new_enabled:
                        self.logger.info("HyperDeck support enabled - initializing components")
                        try:
                            if not hasattr(self, 'hyperdeck_panel') or not self.hyperdeck_panel:
                                from gui.hyperdeck_panel import HyperDeckPanel
                                self.hyperdeck_panel = HyperDeckPanel()
                                self.tabs.addTab(self.hyperdeck_panel, "HyperDeck")
                            
                            if not hasattr(self, 'hyperdeck_status_panel') or not self.hyperdeck_status_panel:
                                from gui.hyperdeck_status_panel import HyperDeckStatusPanel
                                self.hyperdeck_status_panel = HyperDeckStatusPanel()
                                self.status_bar.addPermanentWidget(self.hyperdeck_status_panel)
                            
                            if not self.hyperdeck_worker:
                                from hyperdeck.hyperdeck_worker import HyperDeckWorker
                                self.hyperdeck_worker = HyperDeckWorker()
                                self.hyperdeck_worker.start()
                            
                            # Переподключаем сигналы
                            self.connect_signals()
                        except Exception as e:
                            self.logger.error(f"Failed to initialize HyperDeck components: {e}")
                            config.HYPERDECK_ENABLED = False
                    
                    # Если HyperDeck был включен, а теперь выключен - останавливаем и удаляем объекты
                    elif old_enabled and not new_enabled:
                        self.logger.info("HyperDeck support disabled - stopping components")
                        try:
                            # Останавливаем worker
                            if self.hyperdeck_worker:
                                self.hyperdeck_worker.stop()
                                self.hyperdeck_worker = None
                            
                            # Удаляем вкладку HyperDeck
                            if self.hyperdeck_panel:
                                for i in range(self.tabs.count()):
                                    if self.tabs.tabText(i) == "HyperDeck":
                                        self.tabs.removeTab(i)
                                        break
                                self.hyperdeck_panel = None
                            
                            # Удаляем панель статуса
                            if self.hyperdeck_status_panel:
                                self.status_bar.removeWidget(self.hyperdeck_status_panel)
                                self.hyperdeck_status_panel = None
                        except Exception as e:
                            self.logger.error(f"Error disabling HyperDeck components: {e}")
            
            # Настройка синхронизации
            if 'hyperdeck_sync_with_shogun' in new_settings:
                config.HYPERDECK_SYNC_WITH_SHOGUN = new_settings.get('hyperdeck_sync_with_shogun', True)
                hyperdeck_settings_changed = True
            
            # Обновляем настройки в HyperDeck worker если он существует
            if hyperdeck_settings_changed and config.HYPERDECK_ENABLED and self.hyperdeck_worker:
                try:
                    self.hyperdeck_worker.update_devices(config.HYPERDECK_DEVICES)
                    self.logger.info("HyperDeck devices updated")
                except Exception as e:
                    self.logger.error(f"Error updating HyperDeck devices: {e}")
            
            # Update dashboard info
            if hasattr(self.dashboard, 'status_widget') and hasattr(self.dashboard.status_widget, 'update_info'):
                self.dashboard.status_widget.update_info()
                self.logger.info("Dashboard information updated")
            
            # Обновление темной темы
            if 'dark_mode' in new_settings and new_settings['dark_mode'] != config.DARK_MODE:
                config.DARK_MODE = new_settings['dark_mode']
                self.apply_theme(config.DARK_MODE)
                self.logger.info(f"Theme updated: dark_mode={config.DARK_MODE}")
            
            # Save settings
            config.save_settings(new_settings)
            self.logger.info("Settings saved successfully")
            
        except Exception as e:
            self.logger.error(f"Error updating settings: {e}")
            if hasattr(self.dashboard, 'add_log_message'):
                self.dashboard.add_log_message(f"Error updating settings: {e}", level='ERROR')
    
    def start_workers(self):
        """Запуск рабочих потоков"""
        try:
            # Запускаем Shogun worker
            if self.shogun_worker:
                self.shogun_worker.start()
                self.logger.info("Shogun worker запущен")
            
            # Запускаем HyperDeck worker если он доступен
            if config.HYPERDECK_ENABLED and self.hyperdeck_worker:
                self.hyperdeck_worker.start()
                self.logger.info("HyperDeck worker запущен")
            
            # Запускаем OSC сервер
            if self.osc_server:
                self.osc_server.start()
                self.logger.info("OSC сервер запущен")
            
            self.logger.info("Все рабочие потоки успешно запущены")
        except Exception as e:
            self.logger.critical(f"Ошибка при запуске рабочих потоков: {e}")
            raise
    
    def show_error_dialog(self, title, message, details=None):
        """Показывает диалоговое окно с ошибкой"""
        try:
            error_dialog = QMessageBox(self)
            error_dialog.setIcon(QMessageBox.Critical)
            error_dialog.setWindowTitle(title)
            error_dialog.setText(message)
            if details:
                error_dialog.setDetailedText(details)
            error_dialog.setStandardButtons(QMessageBox.Ok)
            error_dialog.exec_()
        except:
            # Если не удалось создать диалог, выводим в консоль
            print(f"ERROR: {title} - {message}")
            if details:
                print(f"DETAILS: {details}")
    
    def load_settings(self):
        """Загрузка настроек приложения"""
        try:
            # Применяем тему при запуске если нужно
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
                self.logger.info(f"Тема оформления {'темная' if dark_mode else 'светлая'} применена")
        except Exception as e:
            self.logger.error(f"Ошибка при применении темы: {e}")
    
    def closeEvent(self, event):
        """Обработчик закрытия окна"""
        try:
            self.logger.info("Закрытие приложения...")
            
            # Останавливаем рабочие потоки
            if hasattr(self, 'shogun_worker') and self.shogun_worker:
                self.logger.debug("Останавливаем Shogun worker")
                self.shogun_worker.stop()
            
            if hasattr(self, 'hyperdeck_worker') and self.hyperdeck_worker:
                self.logger.debug("Останавливаем HyperDeck worker")
                self.hyperdeck_worker.stop()
            
            if hasattr(self, 'osc_server') and self.osc_server:
                self.logger.debug("Останавливаем OSC сервер")
                self.osc_server.stop()
            
            # Сохраняем настройки
            self.save_settings()
            
            self.logger.info("Приложение закрыто корректно")
            event.accept()
            
        except Exception as e:
            self.logger.error(f"Ошибка при закрытии приложения: {e}")
            event.accept()  # Все равно закрываем окно