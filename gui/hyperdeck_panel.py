"""
Панель управления устройствами HyperDeck.
"""

import logging
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QGroupBox, QLineEdit, QFormLayout)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QColor

import config

class StatusIndicator(QLabel):
    """Индикатор статуса подключения"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(16, 16)
        self.setMaximumSize(16, 16)
        self.setStyleSheet("""
            QLabel {
                border: 1px solid #666;
                border-radius: 8px;
                background-color: #f44336;
            }
        """)
    
    def set_status(self, connected):
        """Установить статус подключения"""
        color = "#4caf50" if connected else "#f44336"
        self.setStyleSheet(f"""
            QLabel {{
                border: 1px solid #666;
                border-radius: 8px;
                background-color: {color};
            }}
        """)

class HyperDeckDeviceWidget(QGroupBox):
    """Виджет для управления одним устройством HyperDeck"""
    
    def __init__(self, device_id, parent=None):
        super().__init__(f"HyperDeck {device_id + 1}", parent)
        self.device_id = device_id
        self.init_ui()
    
    def init_ui(self):
        """Инициализация интерфейса"""
        layout = QFormLayout(self)
        
        # IP адрес
        ip_layout = QHBoxLayout()
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("192.168.1.100")
        self.status_indicator = StatusIndicator()
        ip_layout.addWidget(self.ip_input)
        ip_layout.addWidget(self.status_indicator)
        layout.addRow("IP адрес:", ip_layout)
        
        # Статус записи
        self.recording_status = QLabel("Не записывает")
        layout.addRow("Статус:", self.recording_status)
        
        # Кнопки управления
        buttons_layout = QHBoxLayout()
        self.connect_button = QPushButton("Подключить")
        self.record_button = QPushButton("Начать запись")
        self.record_button.setEnabled(False)
        buttons_layout.addWidget(self.connect_button)
        buttons_layout.addWidget(self.record_button)
        layout.addRow("", buttons_layout)
    
    def update_status(self, connected):
        """Обновить статус подключения"""
        self.status_indicator.set_status(connected)
        self.connect_button.setText("Отключить" if connected else "Подключить")
        self.record_button.setEnabled(connected)
    
    def update_recording(self, is_recording):
        """Обновить статус записи"""
        self.recording_status.setText("Записывает" if is_recording else "Не записывает")
        self.record_button.setText("Остановить запись" if is_recording else "Начать запись")

class HyperDeckPanel(QWidget):
    """Панель управления устройствами HyperDeck"""
    
    # Сигналы для взаимодействия с основным окном
    connect_signal = pyqtSignal(list)  # [(device_id, ip), ...]
    disconnect_signal = pyqtSignal(list)  # [device_id, ...]
    start_recording_signal = pyqtSignal(list)  # [device_id, ...]
    stop_recording_signal = pyqtSignal(list)  # [device_id, ...]
    
    def __init__(self, parent=None):
        """Инициализация панели HyperDeck"""
        super().__init__(parent)
        self.logger = logging.getLogger('ShogunOSC.HyperDeckPanel')
        
        # Состояние устройств
        self.devices = []
        self.connected = False
        self.recording = False
        
        # Инициализация интерфейса
        self.init_ui()
        
        # Таймер для обновления статуса
        self.status_timer = None  # QTimer(self)
        # self.status_timer.timeout.connect(self.update_status_display)
        # self.status_timer.start(1000)  # Обновление каждую секунду
    
    def init_ui(self):
        """Инициализация элементов интерфейса"""
        main_layout = QVBoxLayout(self)
        
        # Заголовок панели
        header_layout = QHBoxLayout()
        header_label = QLabel("HyperDeck устройства")
        header_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        header_layout.addWidget(header_label)
        
        # Чекбокс для включения/выключения поддержки HyperDeck
        self.enable_checkbox = None  # QCheckBox("Включить HyperDeck")
        # self.enable_checkbox.setChecked(config.HYPERDECK_ENABLED)
        # self.enable_checkbox.toggled.connect(self.on_enable_toggled)
        # header_layout.addWidget(self.enable_checkbox, 0, Qt.AlignRight)
        
        main_layout.addLayout(header_layout)
        
        # Группа настроек устройств
        devices_group = QGroupBox("Настройка устройств")
        devices_layout = QVBoxLayout(devices_group)
        
        # Создаем виджеты для каждого устройства
        for i in range(3):  # Три устройства
            device = HyperDeckDeviceWidget(i)
            device.connect_button.clicked.connect(lambda checked, d=i: self.on_connect_clicked(d))
            device.record_button.clicked.connect(lambda checked, d=i: self.on_record_clicked(d))
            self.devices.append(device)
            devices_layout.addWidget(device)
        
        # Кнопки группового управления
        group_buttons = QHBoxLayout()
        
        self.connect_all_button = QPushButton("Подключить все")
        self.connect_all_button.clicked.connect(self.on_connect_all_clicked)
        group_buttons.addWidget(self.connect_all_button)
        
        self.record_all_button = QPushButton("Начать запись на всех")
        self.record_all_button.setEnabled(False)
        self.record_all_button.clicked.connect(self.on_record_all_clicked)
        group_buttons.addWidget(self.record_all_button)
        
        devices_layout.addLayout(group_buttons)
        
        main_layout.addWidget(devices_group)
        
        # Установка состояния элементов в зависимости от настроек
        self.update_ui_state()
        
        # Растягивающийся элемент в конце
        main_layout.addStretch()
    
    def update_ui_state(self):
        """Обновление состояния элементов интерфейса"""
        enabled = self.enable_checkbox.isChecked() if self.enable_checkbox else True
        
        # Активация/деактивация элементов управления
        for device in self.devices:
            device.setEnabled(enabled)
        
        # Кнопки группового управления
        self.connect_all_button.setEnabled(enabled)
        self.record_all_button.setEnabled(enabled)
    
    def on_connect_clicked(self, device_id):
        """Обработчик нажатия кнопки подключения"""
        device = self.devices[device_id]
        ip = device.ip_input.text().strip()
        
        if not ip:
            self.logger.warning(f"IP адрес для HyperDeck {device_id + 1} не указан")
            return
        
        if device.connect_button.text() == "Подключить":
            self.connect_signal.emit([(device_id, ip)])
        else:
            self.disconnect_signal.emit([device_id])
    
    def on_record_clicked(self, device_id):
        """Обработчик нажатия кнопки записи"""
        device = self.devices[device_id]
        if device.record_button.text() == "Начать запись":
            self.start_recording_signal.emit([device_id])
        else:
            self.stop_recording_signal.emit([device_id])
    
    def on_connect_all_clicked(self):
        """Обработчик нажатия кнопки подключения всех устройств"""
        if self.connect_all_button.text() == "Подключить все":
            # Собираем все указанные IP
            devices = []
            for i, device in enumerate(self.devices):
                ip = device.ip_input.text().strip()
                if ip:
                    devices.append((i, ip))
            if devices:
                self.connect_signal.emit(devices)
        else:
            # Отключаем все подключенные устройства
            disconnected = []
            for i, device in enumerate(self.devices):
                if device.connect_button.text() == "Отключить":
                    disconnected.append(i)
            if disconnected:
                self.disconnect_signal.emit(disconnected)
    
    def on_record_all_clicked(self):
        """Обработчик нажатия кнопки записи на всех устройствах"""
        if self.record_all_button.text() == "Начать запись на всех":
            # Начинаем запись на всех подключенных устройствах
            devices = []
            for i, device in enumerate(self.devices):
                if device.record_button.isEnabled():
                    devices.append(i)
            if devices:
                self.start_recording_signal.emit(devices)
        else:
            # Останавливаем запись на всех записывающих устройствах
            devices = []
            for i, device in enumerate(self.devices):
                if device.record_button.text() == "Остановить запись":
                    devices.append(i)
            if devices:
                self.stop_recording_signal.emit(devices)
    
    def update_device_status(self, device_id, connected):
        """Обновить статус подключения устройства"""
        if 0 <= device_id < len(self.devices):
            self.devices[device_id].update_status(connected)
            
            # Обновляем состояние кнопки "Подключить все"
            all_connected = all(d.connect_button.text() == "Отключить" 
                              for d in self.devices if d.ip_input.text().strip())
            self.connect_all_button.setText("Отключить все" if all_connected else "Подключить все")
            
            # Обновляем доступность кнопки "Начать запись на всех"
            any_connected = any(d.record_button.isEnabled() for d in self.devices)
            self.record_all_button.setEnabled(any_connected)
    
    def update_device_recording(self, device_id, is_recording):
        """Обновить статус записи устройства"""
        if 0 <= device_id < len(self.devices):
            self.devices[device_id].update_recording(is_recording)
            
            # Обновляем текст кнопки "Начать запись на всех"
            any_recording = any(d.record_button.text() == "Остановить запись" 
                              for d in self.devices if d.record_button.isEnabled())
            self.record_all_button.setText("Остановить запись на всех" if any_recording 
                                         else "Начать запись на всех")
    
    def update_status_display(self):
        """Обновление отображения статуса записи"""
        pass
    
    @pyqtSlot(bool)
    def on_enable_toggled(self, checked):
        """Обработчик включения/выключения поддержки HyperDeck"""
        pass
    
    @pyqtSlot(bool)
    def on_sync_toggled(self, checked):
        """Обработчик включения/выключения синхронизации с Shogun"""
        pass
    
    @pyqtSlot()
    def on_disconnect_clicked(self):
        """Обработчик нажатия кнопки отключения"""
        pass
    
    @pyqtSlot()
    def on_start_recording_clicked(self):
        """Обработчик нажатия кнопки начала записи"""
        pass
    
    @pyqtSlot()
    def on_stop_recording_clicked(self):
        """Обработчик нажатия кнопки остановки записи"""
        pass
    
    @pyqtSlot(list)
    def on_devices_updated(self, devices_info):
        """
        Обработчик обновления информации об устройствах
        
        Args:
            devices_info: Список словарей с информацией об устройствах
        """
        pass
    
    @pyqtSlot(bool)
    def on_recording_status_changed(self, recording):
        """
        Обработчик изменения статуса записи
        
        Args:
            recording: True если запись активна, иначе False
        """
        pass
    
    @pyqtSlot(str)
    def on_error(self, error_message):
        """
        Обработчик ошибок HyperDeck
        
        Args:
            error_message: Сообщение об ошибке
        """
        pass
