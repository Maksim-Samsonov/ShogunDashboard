"""
Единая панель настроек для всего оборудования и сервисов приложения.
"""

import logging
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QGroupBox, QLineEdit, QSpinBox, QCheckBox, QTextEdit,
    QTabWidget, QFormLayout, QGridLayout, QTableWidget, 
    QTableWidgetItem, QHeaderView, QAbstractItemView
)
from PyQt5.QtCore import Qt, pyqtSignal

import config
from gui.components.status_indicator import StatusIndicator

class OSCSettingsPanel(QGroupBox):
    """Панель настроек OSC-сервера"""
    
    # Сигналы
    osc_settings_changed = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__("OSC Сервер", parent)
        self.logger = logging.getLogger('ShogunOSC.OSCSettingsPanel')
        
        # Инициализация интерфейса
        self.init_ui()
        
        # Загрузка настроек
        self.load_settings()
    
    def init_ui(self):
        """Инициализация интерфейса панели OSC"""
        layout = QVBoxLayout(self)
        
        # Блок статуса сервера
        status_layout = QHBoxLayout()
        self.status_indicator = StatusIndicator("Статус сервера:")
        self.restart_button = QPushButton("Перезапустить сервер")
        status_layout.addWidget(self.status_indicator, 1)
        status_layout.addWidget(self.restart_button)
        layout.addLayout(status_layout)
        
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
        self.osc_enabled.stateChanged.connect(self.on_settings_changed)
    
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
        self.broadcast_ip.setText(config.app_settings.get("osc_broadcast_ip", config.DEFAULT_OSC_BROADCAST_IP))
        self.broadcast_port.setValue(config.app_settings.get("osc_broadcast_port", config.DEFAULT_OSC_BROADCAST_PORT))
        self.osc_enabled.setChecked(config.app_settings.get("osc_enabled", True))
    
    def on_settings_changed(self):
        """Обработка изменения настроек OSC-сервера"""
        settings = {
            "osc_ip": self.osc_ip.text(),
            "osc_port": self.osc_port.value(),
            "osc_broadcast_ip": self.broadcast_ip.text(),
            "osc_broadcast_port": self.broadcast_port.value(),
            "osc_enabled": self.osc_enabled.isChecked()
        }
        self.osc_settings_changed.emit(settings)
    
    def update_server_status(self, running):
        """Обновление индикатора статуса сервера"""
        if running:
            self.status_indicator.set_status(StatusIndicator.STATUS_OK, "Работает")
        else:
            self.status_indicator.set_status(StatusIndicator.STATUS_ERROR, "Остановлен")


class HyperDeckSettingsPanel(QGroupBox):
    """Настройки устройств HyperDeck"""
    
    # Сигналы
    hyperdeck_settings_changed = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__("Настройки HyperDeck", parent)
        self.logger = logging.getLogger('ShogunOSC.HyperDeckSettingsPanel')
        
        # Инициализация интерфейса
        self.init_ui()
        
        # Загрузка настроек
        self.load_settings()
    
    def init_ui(self):
        """Инициализация интерфейса панели HyperDeck"""
        layout = QVBoxLayout(self)
        
        # Включение/отключение HyperDeck
        self.hyperdeck_enabled = QCheckBox("Включить поддержку HyperDeck")
        self.hyperdeck_enabled.setChecked(config.HYPERDECK_ENABLED)
        layout.addWidget(self.hyperdeck_enabled)
        
        # Синхронизация с Shogun
        self.sync_with_shogun = QCheckBox("Синхронизировать запись с Shogun")
        self.sync_with_shogun.setChecked(config.HYPERDECK_SYNC_WITH_SHOGUN)
        layout.addWidget(self.sync_with_shogun)
        
        # Таблица с настройками устройств
        self.devices_table = QTableWidget()
        self.devices_table.setColumnCount(4)
        self.devices_table.setHorizontalHeaderLabels(["ID", "IP адрес", "Порт", "Включено"])
        
        # Настройка таблицы
        self.devices_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.devices_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.devices_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.devices_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        # Заполняем таблицу устройствами
        self.update_devices_table()
        
        layout.addWidget(self.devices_table)
        
        # Подключение сигналов
        self.hyperdeck_enabled.stateChanged.connect(self.on_settings_changed)
        self.sync_with_shogun.stateChanged.connect(self.on_settings_changed)
        self.devices_table.itemChanged.connect(self.on_device_changed)
    
    def update_devices_table(self):
        """Обновление таблицы устройств"""
        self.devices_table.setRowCount(len(config.HYPERDECK_DEVICES))
        
        for i, device in enumerate(config.HYPERDECK_DEVICES):
            # ID устройства
            id_item = QTableWidgetItem(str(device['id']))
            id_item.setFlags(id_item.flags() & ~Qt.ItemIsEditable)  # Делаем неизменяемым
            self.devices_table.setItem(i, 0, id_item)
            
            # IP адрес
            ip_item = QTableWidgetItem(device['ip'])
            self.devices_table.setItem(i, 1, ip_item)
            
            # Порт
            port_item = QTableWidgetItem(str(device['port']))
            self.devices_table.setItem(i, 2, port_item)
            
            # Включено
            enabled_item = QTableWidgetItem()
            enabled_item.setFlags(enabled_item.flags() | Qt.ItemIsUserCheckable)
            enabled_item.setCheckState(Qt.Checked if device['enabled'] else Qt.Unchecked)
            self.devices_table.setItem(i, 3, enabled_item)
    
    def load_settings(self):
        """Загрузка настроек HyperDeck"""
        self.hyperdeck_enabled.setChecked(config.HYPERDECK_ENABLED)
        self.sync_with_shogun.setChecked(config.HYPERDECK_SYNC_WITH_SHOGUN)
        self.update_devices_table()
    
    def on_settings_changed(self):
        """Обработка изменения настроек HyperDeck"""
        settings = {
            "hyperdeck_enabled": self.hyperdeck_enabled.isChecked(),
            "hyperdeck_sync_with_shogun": self.sync_with_shogun.isChecked()
        }
        self.hyperdeck_settings_changed.emit(settings)
    
    def on_device_changed(self, item):
        """Обработка изменения настроек устройства HyperDeck"""
        if self.devices_table.currentRow() >= 0 and self.devices_table.currentRow() < len(config.HYPERDECK_DEVICES):
            row = self.devices_table.currentRow()
            
            # Получаем текущие настройки устройства
            device = config.HYPERDECK_DEVICES[row].copy()
            
            # Обновляем нужные поля
            if item.column() == 1:  # IP адрес
                device['ip'] = item.text()
            elif item.column() == 2:  # Порт
                try:
                    device['port'] = int(item.text())
                except ValueError:
                    # Если некорректный порт, восстанавливаем старое значение
                    self.devices_table.blockSignals(True)
                    item.setText(str(device['port']))
                    self.devices_table.blockSignals(False)
            elif item.column() == 3:  # Включено
                device['enabled'] = (item.checkState() == Qt.Checked)
            
            # Обновляем настройки устройства
            config.HYPERDECK_DEVICES[row] = device
            
            # Отправляем сигнал об изменении настроек
            settings = {
                "hyperdeck_devices": config.HYPERDECK_DEVICES
            }
            self.hyperdeck_settings_changed.emit(settings)


class ShogunSettingsPanel(QGroupBox):
    """Настройки Shogun Live"""
    
    # Сигналы
    shogun_settings_changed = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__("Настройки Shogun Live", parent)
        self.logger = logging.getLogger('ShogunOSC.ShogunSettingsPanel')
        
        # Инициализация интерфейса
        self.init_ui()
    
    def init_ui(self):
        """Инициализация интерфейса панели Shogun"""
        layout = QFormLayout(self)
        
        # Время попыток переподключения
        layout.addRow(QLabel("<b>Настройки подключения</b>"))
        
        layout.addRow(QLabel("Максимальное количество попыток:"), 
                      QLabel(str(config.MAX_RECONNECT_ATTEMPTS)))
        
        layout.addRow(QLabel("Начальная задержка (сек):"), 
                      QLabel(str(config.BASE_RECONNECT_DELAY)))
        
        layout.addRow(QLabel("Максимальная задержка (сек):"), 
                      QLabel(str(config.MAX_RECONNECT_DELAY)))
        
        # Дополнительные настройки
        layout.addRow(QLabel("<b>Дополнительные настройки</b>"))
        
        # Здесь можно добавить дополнительные настройки для Shogun Live


class SettingsPanel(QWidget):
    """
    Панель с объединёнными настройками для всех компонентов системы.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger('ShogunOSC.SettingsPanel')
        self.init_ui()
    
    def init_ui(self):
        """Инициализация интерфейса панели настроек"""
        layout = QVBoxLayout(self)
        
        # Панель с вкладками для разных групп настроек
        tabs = QTabWidget()
        
        # Вкладка настроек Shogun
        self.shogun_settings = ShogunSettingsPanel()
        tabs.addTab(self.shogun_settings, "Shogun Live")
        
        # Вкладка настроек HyperDeck
        self.hyperdeck_settings = HyperDeckSettingsPanel()
        tabs.addTab(self.hyperdeck_settings, "HyperDeck")
        
        # Вкладка настроек OSC
        self.osc_settings = OSCSettingsPanel()
        tabs.addTab(self.osc_settings, "OSC Сервер")
        
        # Вкладка общих настроек
        general_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)
        
        # Переключатель темной темы
        self.dark_mode = QCheckBox("Использовать тёмную тему")
        self.dark_mode.setChecked(config.DARK_MODE)
        general_layout.addWidget(self.dark_mode)
        
        general_layout.addStretch()
        tabs.addTab(general_tab, "Общие")
        
        layout.addWidget(tabs)
        
        # Кнопки в нижней части
        buttons_layout = QHBoxLayout()
        
        self.apply_button = QPushButton("Применить")
        self.reset_button = QPushButton("Сбросить")
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.reset_button)
        buttons_layout.addWidget(self.apply_button)
        
        layout.addLayout(buttons_layout)
