"""
Файл с конфигурационными параметрами и проверкой зависимостей.
"""

import os
import json
import logging
import sys
from typing import Dict, Any, Optional
from PyQt5.QtCore import QSettings

# Пути к директориям
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESOURCES_DIR = os.path.join(BASE_DIR, "resources")
CONFIG_DIR = os.path.expanduser("~/.shogun_osc")
CONFIG_FILE = os.path.join(CONFIG_DIR, "settings.json")

# Создаем директории если не существуют
for directory in [RESOURCES_DIR, CONFIG_DIR]:
    if not os.path.exists(directory):
        try:
            os.makedirs(directory)
        except OSError as e:
            print(f"Ошибка при создании директории {directory}: {e}")
            sys.exit(1)

# Настройки приложения по умолчанию
DEFAULT_SETTINGS = {
    "dark_mode": False,
    "osc_ip": "0.0.0.0",
    "osc_port": 5555,
    "osc_enabled": True,
    "osc_broadcast_port": 9000,  # Порт для отправки OSC-сообщений
    "osc_broadcast_ip": "255.255.255.255",  # IP для отправки OSC-сообщений (широковещательный)
    # Настройки HyperDeck устройств
    "hyperdeck_enabled": True,  # Включение поддержки HyperDeck
    "hyperdeck_devices": [
        {"id": 1, "ip": "10.0.0.51", "port": 9993, "enabled": True},
        {"id": 2, "ip": "10.0.0.52", "port": 9993, "enabled": True},
        {"id": 3, "ip": "10.0.0.53", "port": 9993, "enabled": True}
    ],
    "hyperdeck_sync_with_shogun": True  # Синхронизировать запись с Shogun
}

print("DEFAULT_SETTINGS['hyperdeck_enabled'] =", DEFAULT_SETTINGS['hyperdeck_enabled'])

# Менеджер настроек
settings = QSettings("ShogunOSC", "ShogunOSCApp")

def load_settings() -> Dict[str, Any]:
    """
    Загрузка настроек приложения
    
    Returns:
        Dict[str, Any]: Словарь с настройками приложения
    """
    settings_dict = DEFAULT_SETTINGS.copy()
    
    try:
        # Пробуем загрузить настройки из QSettings
        for key in DEFAULT_SETTINGS.keys():
            if settings.contains(key):
                value = settings.value(key)
                # Преобразуем строковые значения 'true'/'false' в булевы
                if isinstance(value, str) and value.lower() in ['true', 'false']:
                    value = value.lower() == 'true'
                # Преобразуем числовые значения из строк в числа
                elif key in ['osc_port', 'osc_broadcast_port'] and isinstance(value, str) and value.isdigit():
                    value = int(value)
                # Обработка списка устройств HyperDeck
                elif key == 'hyperdeck_devices' and isinstance(value, str):
                    try:
                        value = json.loads(value)
                    except json.JSONDecodeError:
                        value = DEFAULT_SETTINGS[key]
                settings_dict[key] = value
                
                # Отладочный вывод для hyperdeck_enabled
                if key == 'hyperdeck_enabled':
                    print(f"LOADED hyperdeck_enabled from settings: {value}, type: {type(value)}")
    except Exception as e:
        logging.getLogger('ShogunOSC').error(f"Ошибка при загрузке настроек: {e}")
        # В случае ошибки используем настройки по умолчанию
        settings_dict = DEFAULT_SETTINGS.copy()
    
    print(f"FINAL settings_dict['hyperdeck_enabled'] = {settings_dict.get('hyperdeck_enabled')}")
    return settings_dict

def save_settings(settings_dict: Dict[str, Any]) -> None:
    """
    Сохранение настроек приложения
    
    Args:
        settings_dict: Словарь с настройками для сохранения
    """
    try:
        # Очищаем все старые настройки
        settings.clear()
        
        # Сохраняем новые настройки
        for key, value in settings_dict.items():
            # Преобразуем список устройств HyperDeck в JSON-строку
            if key == 'hyperdeck_devices':
                value = json.dumps(value)
            settings.setValue(key, value)
        
        # Принудительно синхронизируем с диском
        settings.sync()
        
        logging.getLogger('ShogunOSC').info("Настройки успешно сохранены")
    except Exception as e:
        logging.getLogger('ShogunOSC').error(f"Ошибка при сохранении настроек: {e}")

# Загружаем настройки
app_settings = load_settings()

# Флаг темной темы
DARK_MODE = app_settings.get('dark_mode', False)

# Настройки OSC-сервера
DEFAULT_OSC_IP = app_settings.get('osc_ip', '0.0.0.0')
DEFAULT_OSC_PORT = app_settings.get('osc_port', 5555)
DEFAULT_OSC_BROADCAST_IP = app_settings.get('osc_broadcast_ip', '255.255.255.255')
DEFAULT_OSC_BROADCAST_PORT = app_settings.get('osc_broadcast_port', 9000)

# Настройки HyperDeck
HYPERDECK_ENABLED = app_settings.get('hyperdeck_enabled', True)
print(f"FINAL HYPERDECK_ENABLED = {HYPERDECK_ENABLED}, type: {type(HYPERDECK_ENABLED)}")
HYPERDECK_SYNC_WITH_SHOGUN = app_settings.get('hyperdeck_sync_with_shogun', True)
HYPERDECK_DEVICES = app_settings.get("hyperdeck_devices", DEFAULT_SETTINGS["hyperdeck_devices"])

# Проверка зависимостей
IMPORT_SUCCESS = True
IMPORT_ERROR = ""

try:
    # Библиотеки для Shogun Live
    from vicon_core_api import Client
    from shogun_live_api import CaptureServices
    
    # Библиотеки для OSC
    from pythonosc import dispatcher, osc_server
except ImportError as e:
    IMPORT_SUCCESS = False
    IMPORT_ERROR = str(e)

# OSC-адреса для управления Shogun Live
OSC_START_RECORDING = "/RecordStartShogunLive"
OSC_STOP_RECORDING = "/RecordStopShogunLive"
OSC_CAPTURE_NAME_CHANGED = "/ShogunLiveCaptureName"  # Новый адрес для уведомления об изменении имени захвата
OSC_CAPTURE_ERROR = "/ShogunCaptureError"  # Адрес для уведомления об ошибках захвата

# OSC-адреса для управления HyperDeck
OSC_HYPERDECK_START_RECORDING = "/RecordStartHyperDeck"
OSC_HYPERDECK_STOP_RECORDING = "/RecordStopHyperDeck"
OSC_HYPERDECK_STATUS = "/HyperDeckStatus"
OSC_HYPERDECK_ERROR = "/HyperDeckError"
OSC_HYPERDECK_CONNECTED = "/HyperDeckConnected"

# OSC-адреса для синхронизированного управления
OSC_START_ALL_RECORDING = "/RecordStartAll"
OSC_STOP_ALL_RECORDING = "/RecordStopAll"

# Настройки логирования
LOG_FORMAT = '%(asctime)s [%(levelname)s] %(message)s'
LOG_MAX_LINES = 1000

# Настройки для проверки соединения с Shogun Live
MAX_RECONNECT_ATTEMPTS = 10
BASE_RECONNECT_DELAY = 1
MAX_RECONNECT_DELAY = 15

# Названия статусов для понятного отображения
STATUS_CONNECTED = "Подключено"
STATUS_DISCONNECTED = "Отключено"
STATUS_RECORDING_ACTIVE = "Активна"
STATUS_RECORDING_INACTIVE = "Не активна"

# Версия приложения
APP_VERSION = "1.0.1"

def get_app_version() -> str:
    """
    Возвращает текущую версию приложения
    
    Returns:
        str: Версия приложения
    """
    return APP_VERSION