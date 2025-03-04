"""
Панель главного экрана приложения с отображением состояния всех компонентов.
"""

import logging
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QGroupBox, QGridLayout, QSplitter
)
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QIcon

import config
from gui.components.status_indicator import StatusIndicator
from gui.log_panel import LogPanel

class StatusWidget(QGroupBox):
    """Виджет статусов всех подключенных устройств"""
    
    def __init__(self, title):
        super().__init__(title)
        self.init_ui()
    
    def init_ui(self):
        layout = QGridLayout()
        layout.setSpacing(10)
        
        # Shogun Status
        self.shogun_indicator = StatusIndicator()
        self.shogun_info = QLabel("localhost")
        layout.addWidget(self.shogun_info, 0, 0)
        layout.addWidget(QLabel("Shogun:"), 0, 1)
        layout.addWidget(self.shogun_indicator, 0, 2)
        
        # OSC Server Status
        self.osc_indicator = StatusIndicator()
        self.osc_info = QLabel("")  # Will be set in update_info
        layout.addWidget(self.osc_info, 1, 0)
        layout.addWidget(QLabel("OSC Server:"), 1, 1)
        layout.addWidget(self.osc_indicator, 1, 2)
        
        # HyperDeck Status
        self.hyperdeck_indicators = []
        self.hyperdeck_infos = []
        for i in range(3):
            indicator = StatusIndicator()
            self.hyperdeck_indicators.append(indicator)
            info_label = QLabel("")  # Will be set in update_info
            self.hyperdeck_infos.append(info_label)
            layout.addWidget(info_label, i+2, 0)
            layout.addWidget(QLabel(f"HyperDeck {i+1}:"), i+2, 1)
            layout.addWidget(indicator, i+2, 2)
        
        self.setLayout(layout)
        
        # Initialize with default info
        self.update_info()
    
    def update_info(self):
        """Update connection info for all components"""
        import config
        
        # Update OSC info
        self.osc_info.setText(f"{config.DEFAULT_OSC_IP}:{config.DEFAULT_OSC_PORT}")
        
        # Update HyperDeck info from settings
        for i, info_label in enumerate(self.hyperdeck_infos):
            if i < len(config.HYPERDECK_DEVICES):
                device = config.HYPERDECK_DEVICES[i]
                if device.get('enabled', True):
                    info_label.setText(f"{device['ip']}:{device['port']}")
                else:
                    info_label.setText("Не активен")
            else:
                info_label.setText("Не настроен")

class RecordingControls(QGroupBox):
    """Панель управления записью"""
    
    # Сигналы для управления записью
    start_recording = pyqtSignal()
    stop_recording = pyqtSignal()
    
    def __init__(self):
        super().__init__("Recording Controls")
        self.init_ui()
    
    def init_ui(self):
        layout = QHBoxLayout()
        
        self.start_btn = QPushButton("Start Recording")
        try:
            self.start_btn.setIcon(QIcon.fromTheme("media-record"))
        except Exception as e:
            # Если иконка недоступна, продолжаем без неё
            pass
            
        self.stop_btn = QPushButton("Stop Recording")
        try:
            self.stop_btn.setIcon(QIcon.fromTheme("media-playback-stop"))
        except Exception as e:
            # Если иконка недоступна, продолжаем без неё
            pass
        
        layout.addWidget(self.start_btn)
        layout.addWidget(self.stop_btn)
        
        self.setLayout(layout)
        
        # Connect signals
        self.start_btn.clicked.connect(self.start_recording)
        self.stop_btn.clicked.connect(self.stop_recording)

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
        
        # Создаем панель статусов для информации о подключениях
        self.status_widget = StatusWidget("System Status")
        layout.addWidget(self.status_widget)
        
        # Создаем панель управления записью
        self.recording_controls = RecordingControls()
        layout.addWidget(self.recording_controls)
        
        # Подключаем сигналы от панели управления записью
        self.recording_controls.start_recording.connect(
            self.start_all_recording_signal)
        self.recording_controls.stop_recording.connect(
            self.stop_all_recording_signal)
    
    def update_status(self, component: str, status: bool):
        """Update status indicator for a specific component"""
        if component == "shogun":
            if hasattr(self.status_widget, 'shogun_indicator'):
                self.status_widget.shogun_indicator.set_status(status)
            if hasattr(self.status_panel, 'update_shogun_connection'):
                self.status_panel.update_shogun_connection(status)
        elif component == "osc":
            if hasattr(self.status_widget, 'osc_indicator'):
                self.status_widget.osc_indicator.set_status(status)
            if hasattr(self.status_panel, 'update_osc_status'):
                self.status_panel.update_osc_status(status)
        elif component.startswith("hyperdeck_"):
            try:
                index = int(component.split("_")[1]) - 1
                if hasattr(self.status_widget, 'hyperdeck_indicators') and 0 <= index < len(self.status_widget.hyperdeck_indicators):
                    self.status_widget.hyperdeck_indicators[index].set_status(status)
                if hasattr(self.status_panel, 'update_hyperdeck_connection') and 0 <= index < len(self.status_panel.hyperdeck_status):
                    self.status_panel.update_hyperdeck_connection(index, status)
            except (IndexError, ValueError) as e:
                # Логируем ошибку, но не прерываем выполнение
                self.logger.debug(f"Ошибка при обновлении статуса HyperDeck: {e}")
    
    def add_log_message(self, message: str, level: str = 'INFO'):
        """Add a colored message to the log panel"""
        if hasattr(self, 'log_panel') and hasattr(self.log_panel, 'add_log_message'):
            self.log_panel.add_log_message(message, level)