"""
Панель статуса устройств HyperDeck для главного окна.
"""

import logging
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QGroupBox, QGridLayout, QFrame)
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QColor, QPalette

from styles.app_styles import set_status_style

class HyperDeckStatusIndicator(QLabel):
    """Компактный индикатор статуса HyperDeck устройства"""
    def __init__(self, device_id, parent=None):
        super().__init__(parent)
        self.device_id = device_id
        self.setMinimumSize(20, 20)
        self.setMaximumSize(20, 20)
        self.is_connected = False
        self.is_recording = False
        self.update_display()
        
        # Добавляем тултип с информацией о статусе
        self.setToolTip(f"HyperDeck {device_id+1}: Не подключен")
    
    def update_display(self):
        """Обновить отображение статуса"""
        if self.is_connected:
            if self.is_recording:
                # Подключен и записывает - красный
                color = "#f44336"
                tooltip = f"HyperDeck {self.device_id+1}: Записывает"
            else:
                # Подключен, но не записывает - зеленый
                color = "#4caf50"
                tooltip = f"HyperDeck {self.device_id+1}: Подключен"
        else:
            # Не подключен - серый
            color = "#9e9e9e"
            tooltip = f"HyperDeck {self.device_id+1}: Не подключен"
            
        self.setStyleSheet(f"""
            QLabel {{
                border: 2px solid #666;
                border-radius: 10px;
                background-color: {color};
            }}
        """)
        self.setToolTip(tooltip)
    
    def set_connected(self, connected):
        """Установить статус подключения"""
        self.is_connected = connected
        if not connected:
            self.is_recording = False
        self.update_display()
    
    def set_recording(self, recording):
        """Установить статус записи"""
        self.is_recording = recording
        self.update_display()


class HyperDeckStatusPanel(QFrame):
    """Панель статуса устройств HyperDeck для главного окна"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger('ShogunOSC.HyperDeckStatusPanel')
        
        # Индикаторы для устройств
        self.device_indicators = []
        
        # Устанавливаем рамку
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setLineWidth(2)
        
        # Инициализация интерфейса
        self.init_ui()
        
        # Устанавливаем фиксированный размер, чтобы панель была хорошо видна
        self.setMinimumWidth(200)
        self.setMinimumHeight(50)
    
    def init_ui(self):
        """Инициализация интерфейса"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # Заголовок
        title = QLabel("<b>HyperDeck:</b>")
        layout.addWidget(title)
        
        # Создаем индикаторы для трех устройств
        indicators_layout = QHBoxLayout()
        indicators_layout.setSpacing(10)  # Увеличиваем расстояние между индикаторами
        
        for i in range(3):
            device_layout = QVBoxLayout()
            
            # Индикатор
            indicator = HyperDeckStatusIndicator(i)
            self.device_indicators.append(indicator)
            
            # Метка с номером устройства
            label = QLabel(f"{i+1}")
            label.setAlignment(Qt.AlignCenter)
            
            device_layout.addWidget(indicator, alignment=Qt.AlignCenter)
            device_layout.addWidget(label, alignment=Qt.AlignCenter)
            
            indicators_layout.addLayout(device_layout)
        
        layout.addLayout(indicators_layout)
    
    @pyqtSlot(int, bool)
    def update_device_status(self, device_id, connected):
        """Обновить статус подключения устройства"""
        if 0 <= device_id < len(self.device_indicators):
            self.device_indicators[device_id].set_connected(connected)
    
    @pyqtSlot(int, bool)
    def update_device_recording(self, device_id, is_recording):
        """Обновить статус записи устройства"""
        if 0 <= device_id < len(self.device_indicators):
            self.device_indicators[device_id].set_recording(is_recording)
