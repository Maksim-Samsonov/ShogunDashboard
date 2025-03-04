"""
Панель статуса состояния Shogun Live и настроек OSC.
"""

import asyncio
import logging
import threading
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QPushButton, QGroupBox, QGridLayout,
                            QLineEdit, QSpinBox, QCheckBox, QTextEdit)
from PyQt5.QtCore import Qt, pyqtSignal

import config
from styles.app_styles import set_status_style

class ShogunPanel(QGroupBox):
    """Панель информации о состоянии Shogun Live и кнопок управления"""
    def __init__(self, shogun_worker):
        super().__init__("Shogun Live")
        self.logger = logging.getLogger('ShogunOSC')
        self.shogun_worker = shogun_worker
        self.init_ui()
        self.connect_signals()
    
    def init_ui(self):
        """Инициализация интерфейса панели Shogun"""
        layout = QGridLayout()
        
        # Информация о состоянии
        layout.addWidget(QLabel("Статус:"), 0, 0)
        self.status_label = QLabel(config.STATUS_DISCONNECTED)
        set_status_style(self.status_label, "disconnected")
        layout.addWidget(self.status_label, 0, 1)
        
        layout.addWidget(QLabel("Запись:"), 1, 0)
        self.recording_label = QLabel(config.STATUS_RECORDING_INACTIVE)
        self.recording_label.setStyleSheet("color: gray;")
        layout.addWidget(self.recording_label, 1, 1)
        
        layout.addWidget(QLabel("Текущий тейк:"), 2, 0)
        self.take_label = QLabel("Нет данных")
        layout.addWidget(self.take_label, 2, 1)
        
        # Добавляем поле для отображения имени захвата
        layout.addWidget(QLabel("Имя захвата:"), 3, 0)
        self.capture_name_label = QLabel("Нет данных")
        layout.addWidget(self.capture_name_label, 3, 1)
        
        # Кнопки управления
        button_layout = QHBoxLayout()
        
        self.connect_button = QPushButton("Подключиться")
        self.connect_button.clicked.connect(self.reconnect_shogun)
        button_layout.addWidget(self.connect_button)
        
        self.start_button = QPushButton("Начать запись")
        self.start_button.clicked.connect(self.start_recording)
        self.start_button.setEnabled(False)
        button_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("Остановить запись")
        self.stop_button.clicked.connect(self.stop_recording)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)
        
        layout.addLayout(button_layout, 4, 0, 1, 2)
        self.setLayout(layout)
    
    def connect_signals(self):
        """Подключение сигналов от Shogun Worker"""
        self.shogun_worker.connection_signal.connect(self.update_connection_status)
        self.shogun_worker.recording_signal.connect(self.update_recording_status)
        self.shogun_worker.take_name_signal.connect(self.update_take_name)
        self.shogun_worker.capture_name_changed_signal.connect(self.update_capture_name)
    
    def update_connection_status(self, connected):
        """Обновление отображения статуса подключения"""
        if connected:
            self.status_label.setText(config.STATUS_CONNECTED)
            set_status_style(self.status_label, "connected")
            self.start_button.setEnabled(True)
            self.connect_button.setEnabled(False)
        else:
            self.status_label.setText(config.STATUS_DISCONNECTED)
            set_status_style(self.status_label, "disconnected")
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(False)
            self.connect_button.setEnabled(True)
    
    def update_recording_status(self, is_recording):
        """Обновление отображения статуса записи"""
        if is_recording:
            self.recording_label.setText(config.STATUS_RECORDING_ACTIVE)
            set_status_style(self.recording_label, "recording")
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
        else:
            self.recording_label.setText(config.STATUS_RECORDING_INACTIVE)
            set_status_style(self.recording_label, "")
            self.start_button.setEnabled(self.shogun_worker.connected)
            self.stop_button.setEnabled(False)
    
    def update_take_name(self, name):
        """Обновление имени текущего тейка"""
        self.take_label.setText(name)
    
    def update_capture_name(self, name):
        """Обновление имени захвата"""
        self.capture_name_label.setText(name)
    
    def reconnect_shogun(self):
        """Запуск переподключения к Shogun Live"""
        threading.Thread(target=self._run_reconnect).start()
    
    def _run_reconnect(self):
        """Выполнение переподключения в отдельном потоке"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(self.shogun_worker.reconnect_shogun())
            if result:
                self.logger.info("Переподключение выполнено успешно")
            else:
                self.logger.error("Не удалось переподключиться")
        finally:
            loop.close()
    
    def start_recording(self):
        """Запуск записи"""
        threading.Thread(target=self._run_start_recording).start()
    
    def _run_start_recording(self):
        """Запуск записи в отдельном потоке"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.shogun_worker.startcapture())
        finally:
            loop.close()
    
    def stop_recording(self):
        """Остановка записи"""
        threading.Thread(target=self._run_stop_recording).start()
    
    def _run_stop_recording(self):
        """Остановка записи в отдельном потоке"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.shogun_worker.stopcapture())
        finally:
            loop.close()

class OSCPanel(QGroupBox):
    """Панель настроек и статуса OSC-сервера"""
    
    # Сигналы
    osc_settings_changed = pyqtSignal(dict)  # Сигнал изменения настроек OSC
    
    def __init__(self, parent=None):
        super().__init__("OSC Сервер", parent)
        self.logger = logging.getLogger('ShogunOSC')
        
        # Инициализация интерфейса
        self.init_ui()
        
        # Загрузка настроек
        self.load_settings()
    
    def init_ui(self):
        """Инициализация интерфейса панели OSC"""
        layout = QVBoxLayout(self)
        
        # Настройки OSC-сервера
        settings_group = QGroupBox("Настройки сервера")
        settings_layout = QGridLayout(settings_group)
        
        # IP-адрес
        settings_layout.addWidget(QLabel("IP-адрес:"), 0, 0)
        self.osc_ip = QLineEdit(config.DEFAULT_OSC_IP)
        settings_layout.addWidget(self.osc_ip, 0, 1)
        
        # Порт
        settings_layout.addWidget(QLabel("Порт:"), 1, 0)
        self.osc_port = QSpinBox()
        self.osc_port.setRange(1024, 65535)
        self.osc_port.setValue(config.DEFAULT_OSC_PORT)
        settings_layout.addWidget(self.osc_port, 1, 1)
        
        # Чекбокс включения/выключения
        self.osc_enabled = QCheckBox("Включить OSC-сервер")
        self.osc_enabled.setChecked(config.app_settings.get("osc_enabled", True))
        settings_layout.addWidget(self.osc_enabled, 2, 0, 1, 2)
        
        layout.addWidget(settings_group)
        
        # Настройки широковещательной рассылки
        broadcast_group = QGroupBox("Настройки рассылки")
        broadcast_layout = QGridLayout(broadcast_group)
        
        # IP-адрес для рассылки
        broadcast_layout.addWidget(QLabel("IP-адрес:"), 0, 0)
        self.broadcast_ip = QLineEdit(config.DEFAULT_OSC_BROADCAST_IP)
        broadcast_layout.addWidget(self.broadcast_ip, 0, 1)
        
        # Порт для рассылки
        broadcast_layout.addWidget(QLabel("Порт:"), 1, 0)
        self.broadcast_port = QSpinBox()
        self.broadcast_port.setRange(1024, 65535)
        self.broadcast_port.setValue(config.DEFAULT_OSC_BROADCAST_PORT)
        broadcast_layout.addWidget(self.broadcast_port, 1, 1)
        
        layout.addWidget(broadcast_group)
        
        # Список доступных команд
        commands_group = QGroupBox("Доступные команды")
        commands_layout = QVBoxLayout(commands_group)
        
        self.commands_list = QTextEdit()
        self.commands_list.setReadOnly(True)
        self.commands_list.setMaximumHeight(150)
        
        # Заполняем список команд
        self.update_commands_list()
        
        commands_layout.addWidget(self.commands_list)
        layout.addWidget(commands_group)
        
        # Подключаем сигналы
        self.osc_ip.textChanged.connect(self.on_settings_changed)
        self.osc_port.valueChanged.connect(self.on_settings_changed)
        self.broadcast_ip.textChanged.connect(self.on_settings_changed)
        self.broadcast_port.valueChanged.connect(self.on_settings_changed)
    
    def update_commands_list(self):
        """Обновление списка доступных OSC-команд"""
        commands = [
            f"<b>{config.OSC_START_RECORDING}</b> - Начать запись в Shogun Live",
            f"<b>{config.OSC_STOP_RECORDING}</b> - Остановить запись в Shogun Live",
            f"<b>{config.OSC_CAPTURE_NAME_CHANGED}</b> - Уведомление об изменении имени захвата",
            f"<b>{config.OSC_CAPTURE_ERROR}</b> - Уведомление об ошибке захвата",
            f"<b>{config.OSC_HYPERDECK_START_RECORDING}</b> - Начать запись на HyperDeck",
            f"<b>{config.OSC_HYPERDECK_STOP_RECORDING}</b> - Остановить запись на HyperDeck",
            f"<b>{config.OSC_HYPERDECK_STATUS}</b> - Статус HyperDeck устройств",
            f"<b>{config.OSC_HYPERDECK_ERROR}</b> - Уведомление об ошибке HyperDeck",
            f"<b>{config.OSC_HYPERDECK_CONNECTED}</b> - Уведомление о подключении HyperDeck",
            f"<b>{config.OSC_START_ALL_RECORDING}</b> - Начать запись на всех устройствах",
            f"<b>{config.OSC_STOP_ALL_RECORDING}</b> - Остановить запись на всех устройствах"
        ]
        
        self.commands_list.setHtml("<br>".join(commands))
    
    def load_settings(self):
        """Загрузка настроек OSC-сервера"""
        self.osc_ip.setText(config.app_settings.get("osc_ip", config.DEFAULT_OSC_IP))
        self.osc_port.setValue(config.app_settings.get("osc_port", config.DEFAULT_OSC_PORT))
        self.broadcast_ip.setText(config.app_settings.get("broadcast_ip", config.DEFAULT_OSC_BROADCAST_IP))
        self.broadcast_port.setValue(config.app_settings.get("broadcast_port", config.DEFAULT_OSC_BROADCAST_PORT))
        self.osc_enabled.setChecked(config.app_settings.get("osc_enabled", True))
    
    def on_settings_changed(self):
        """Обработка изменения настроек OSC-сервера"""
        settings = {
            "osc_ip": self.osc_ip.text(),
            "osc_port": self.osc_port.value(),
            "broadcast_ip": self.broadcast_ip.text(),
            "broadcast_port": self.broadcast_port.value(),
            "osc_enabled": self.osc_enabled.isChecked()
        }
        self.osc_settings_changed.emit(settings)

class StatusPanel(QWidget):
    """Составная панель статуса и настроек"""
    def __init__(self, shogun_worker):
        super().__init__()
        self.init_ui(shogun_worker)
    
    def init_ui(self, shogun_worker):
        """Инициализация составной панели"""
        layout = QHBoxLayout()
        
        # Создаем панели
        self.shogun_panel = ShogunPanel(shogun_worker)
        self.osc_panel = OSCPanel()
        
        # Добавляем панели с разным весом
        layout.addWidget(self.shogun_panel, 3)  # Больший вес для панели Shogun
        layout.addWidget(self.osc_panel, 2)
        
        self.setLayout(layout)