"""
Панель управления Shogun Live.
"""

import logging
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                           QLabel, QPushButton, QGroupBox)
from PyQt5.QtCore import pyqtSignal, Qt

import config

class ShogunPanel(QGroupBox):
    """Панель управления Shogun Live"""
    
    # Сигналы
    start_capture_signal = pyqtSignal()
    stop_capture_signal = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__("Управление Shogun Live", parent)
        self.logger = logging.getLogger('ShogunOSC.ShogunPanel')
        
        # Состояние
        self.is_connected = False
        self.is_recording = False
        self.current_capture = ""
        
        # Инициализация интерфейса
        self.init_ui()
    
    def init_ui(self):
        """Инициализация интерфейса панели"""
        layout = QVBoxLayout(self)
        
        # Статус подключения
        status_group = QGroupBox("Статус")
        status_layout = QHBoxLayout(status_group)
        
        self.connection_label = QLabel("Статус подключения:")
        self.connection_status = QLabel(config.STATUS_DISCONNECTED)
        status_layout.addWidget(self.connection_label)
        status_layout.addWidget(self.connection_status)
        status_layout.addStretch()
        
        layout.addWidget(status_group)
        
        # Управление записью
        recording_group = QGroupBox("Управление записью")
        recording_layout = QVBoxLayout(recording_group)
        
        # Статус записи
        recording_status_layout = QHBoxLayout()
        self.recording_label = QLabel("Статус записи:")
        self.recording_status = QLabel(config.STATUS_RECORDING_INACTIVE)
        recording_status_layout.addWidget(self.recording_label)
        recording_status_layout.addWidget(self.recording_status)
        recording_status_layout.addStretch()
        recording_layout.addLayout(recording_status_layout)
        
        # Имя текущего захвата
        capture_name_layout = QHBoxLayout()
        self.capture_name_label = QLabel("Текущий захват:")
        self.capture_name = QLabel("-")
        capture_name_layout.addWidget(self.capture_name_label)
        capture_name_layout.addWidget(self.capture_name)
        capture_name_layout.addStretch()
        recording_layout.addLayout(capture_name_layout)
        
        # Кнопки управления
        buttons_layout = QHBoxLayout()
        
        self.start_button = QPushButton("Начать запись")
        self.start_button.clicked.connect(self.on_start_capture)
        self.start_button.setEnabled(False)
        buttons_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("Остановить запись")
        self.stop_button.clicked.connect(self.on_stop_capture)
        self.stop_button.setEnabled(False)
        buttons_layout.addWidget(self.stop_button)
        
        recording_layout.addLayout(buttons_layout)
        
        layout.addWidget(recording_group)
        layout.addStretch()
    
    def on_start_capture(self):
        """Обработчик нажатия кнопки начала записи"""
        self.start_capture_signal.emit()
    
    def on_stop_capture(self):
        """Обработчик нажатия кнопки остановки записи"""
        self.stop_capture_signal.emit()
    
    def update_connection_status(self, connected):
        """Обновление статуса подключения"""
        self.is_connected = connected
        self.connection_status.setText(
            config.STATUS_CONNECTED if connected else config.STATUS_DISCONNECTED
        )
        self.start_button.setEnabled(connected and not self.is_recording)
        self.stop_button.setEnabled(connected and self.is_recording)
    
    def update_recording_status(self, recording):
        """Обновление статуса записи"""
        self.is_recording = recording
        self.recording_status.setText(
            config.STATUS_RECORDING_ACTIVE if recording else config.STATUS_RECORDING_INACTIVE
        )
        self.start_button.setEnabled(self.is_connected and not recording)
        self.stop_button.setEnabled(self.is_connected and recording)
    
    def update_capture_name(self, name):
        """Обновление имени текущего захвата"""
        self.current_capture = name
        self.capture_name.setText(name if name else "-")
