"""
Панель главного экрана приложения с отображением состояния всех компонентов.
"""

import logging
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QGroupBox, QGridLayout, QSplitter
)
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot

import config
from gui.components.status_indicator import StatusIndicator
from gui.log_panel import LogPanel

class DeviceStatusPanel(QGroupBox):
    """Панель статусов всех подключенных устройств"""
    
    # Сигналы для управления записью
    start_all_recording_signal = pyqtSignal()
    stop_all_recording_signal = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__("Статус устройств", parent)
        self.logger = logging.getLogger('ShogunOSC.DeviceStatusPanel')
        self.init_ui()
    
    def init_ui(self):
        """Инициализация интерфейса панели статусов устройств"""
        layout = QVBoxLayout(self)
        
        # Создаем сетку для индикаторов статуса
        grid = QGridLayout()
        grid.setSpacing(15)
        
        # === Индикаторы для Shogun Live ===
        grid.addWidget(QLabel("<b>Shogun Live:</b>"), 0, 0)
        
        # Соединение с Shogun
        self.shogun_connection = StatusIndicator("Соединение:")
        grid.addWidget(self.shogun_connection, 1, 0)
        
        # Статус записи Shogun
        self.shogun_recording = StatusIndicator("Запись:")
        grid.addWidget(self.shogun_recording, 2, 0)
        
        # === Индикаторы для OSC сервера ===
        grid.addWidget(QLabel("<b>OSC Сервер:</b>"), 0, 1)
        
        # Статус OSC сервера
        self.osc_status = StatusIndicator("Статус:")
        grid.addWidget(self.osc_status, 1, 1)
        
        # === Индикаторы для HyperDeck ===
        grid.addWidget(QLabel("<b>HyperDeck:</b>"), 0, 2)
        
        # Статусы устройств HyperDeck
        self.hyperdeck_status = []
        for i in range(3):
            status = StatusIndicator(f"Устройство {i+1}:")
            self.hyperdeck_status.append(status)
            grid.addWidget(status, i+1, 2)
        
        layout.addLayout(grid)
        
        # Добавляем разделитель
        layout.addSpacing(10)
        
        # Кнопки управления записью
        buttons_layout = QHBoxLayout()
        
        # Информация о текущем тейке
        take_layout = QVBoxLayout()
        take_layout.addWidget(QLabel("<b>Информация о захвате:</b>"))
        
        capture_layout = QHBoxLayout()
        capture_layout.addWidget(QLabel("Имя захвата:"))
        self.capture_name = QLabel("Нет данных")
        self.capture_name.setStyleSheet("font-weight: bold;")
        capture_layout.addWidget(self.capture_name, 1)  # 1 = stretch
        take_layout.addLayout(capture_layout)
        
        take_info_layout = QHBoxLayout()
        take_info_layout.addWidget(QLabel("Текущий тейк:"))
        self.take_name = QLabel("Нет данных")
        self.take_name.setStyleSheet("font-weight: bold;")
        take_info_layout.addWidget(self.take_name, 1)  # 1 = stretch
        take_layout.addLayout(take_info_layout)
        
        buttons_layout.addLayout(take_layout, 2)  # 2 = stretch для баланса с кнопками
        
        # Разделитель между информацией и кнопками
        buttons_layout.addSpacing(20)
        
        # Кнопки записи
        self.start_all_button = QPushButton("НАЧАТЬ ЗАПИСЬ")
        self.start_all_button.setMinimumHeight(50)
        self.start_all_button.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.start_all_button.clicked.connect(self.start_all_recording_signal)
        
        self.stop_all_button = QPushButton("ОСТАНОВИТЬ ЗАПИСЬ")
        self.stop_all_button.setMinimumHeight(50)
        self.stop_all_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.stop_all_button.clicked.connect(self.stop_all_recording_signal)
        
        # Изначально кнопка остановки не активна
        self.stop_all_button.setEnabled(False)
        
        record_buttons_layout = QVBoxLayout()
        record_buttons_layout.addWidget(self.start_all_button)
        record_buttons_layout.addWidget(self.stop_all_button)
        
        buttons_layout.addLayout(record_buttons_layout, 1)  # 1 = stretch
        
        layout.addLayout(buttons_layout)
    
    @pyqtSlot(bool)
    def update_shogun_connection(self, connected):
        """Обновление индикатора соединения с Shogun"""
        if connected:
            self.shogun_connection.set_status(StatusIndicator.STATUS_OK, "Подключено")
        else:
            self.shogun_connection.set_status(StatusIndicator.STATUS_ERROR, "Отключено")
    
    @pyqtSlot(bool)
    def update_shogun_recording(self, is_recording):
        """Обновление индикатора записи Shogun"""
        if is_recording:
            self.shogun_recording.set_status(StatusIndicator.STATUS_RECORDING, "Активна")
            self.start_all_button.setEnabled(False)
            self.stop_all_button.setEnabled(True)
        else:
            self.shogun_recording.set_status(StatusIndicator.STATUS_INACTIVE, "Не активна")
            self.start_all_button.setEnabled(True)
            self.stop_all_button.setEnabled(False)
    
    @pyqtSlot(str)
    def update_take_name(self, name):
        """Обновление имени текущего тейка"""
        self.take_name.setText(name)
    
    @pyqtSlot(str)
    def update_capture_name(self, name):
        """Обновление имени захвата"""
        self.capture_name.setText(name)
    
    @pyqtSlot(bool)
    def update_osc_status(self, running):
        """Обновление индикатора статуса OSC сервера"""
        if running:
            self.osc_status.set_status(StatusIndicator.STATUS_OK, "Работает")
        else:
            self.osc_status.set_status(StatusIndicator.STATUS_ERROR, "Остановлен")
    
    @pyqtSlot(int, bool)
    def update_hyperdeck_connection(self, device_id, connected):
        """Обновление индикатора соединения с HyperDeck"""
        if 0 <= device_id < len(self.hyperdeck_status):
            if connected:
                self.hyperdeck_status[device_id].set_status(
                    StatusIndicator.STATUS_OK, "Подключено")
            else:
                self.hyperdeck_status[device_id].set_status(
                    StatusIndicator.STATUS_ERROR, "Отключено")
    
    @pyqtSlot(int, bool)
    def update_hyperdeck_recording(self, device_id, is_recording):
        """Обновление индикатора записи HyperDeck"""
        if 0 <= device_id < len(self.hyperdeck_status):
            if is_recording:
                self.hyperdeck_status[device_id].set_status(
                    StatusIndicator.STATUS_RECORDING, "Запись")
            else:
                # Если устройство подключено, но не записывает
                self.hyperdeck_status[device_id].set_status(
                    StatusIndicator.STATUS_OK, "Подключено")


class DashboardPanel(QWidget):
    """
    Главная панель приложения с отображением статусов всех компонентов
    и панелью логов.
    """
    
    # Сигналы для управления записью
    start_all_recording_signal = pyqtSignal()
    stop_all_recording_signal = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger('ShogunOSC.DashboardPanel')
        
        # Инициализация интерфейса
        self.init_ui()
    
    def init_ui(self):
        """Инициализация интерфейса главной панели"""
        layout = QVBoxLayout(self)
        
        # Панель статуса устройств
        self.status_panel = DeviceStatusPanel()
        
        # Подключаем сигналы от панели статуса
        self.status_panel.start_all_recording_signal.connect(
            self.start_all_recording_signal)
        self.status_panel.stop_all_recording_signal.connect(
            self.stop_all_recording_signal)
        
        # Панель логов
        self.log_panel = LogPanel()
        
        # Создаем сплиттер для возможности изменения размеров панелей
        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(self.status_panel)
        splitter.addWidget(self.log_panel)
        
        # Устанавливаем начальные размеры сплиттера
        splitter.setSizes([400, 200])
        
        layout.addWidget(splitter)
