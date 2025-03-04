"""
Модуль для работы с OSC-сервером.
Обеспечивает прием и отправку OSC-сообщений.
"""

import logging
import threading
import time
from typing import Dict, Any, Optional, Callable, Tuple, List

from pythonosc import dispatcher, osc_server, udp_client
from pythonosc.osc_message_builder import OscMessageBuilder

import config


def format_osc_message(address: str, value: Any) -> str:
    """
    Форматирует OSC-сообщение для отображения в логах
    
    Args:
        address: Адрес OSC-сообщения
        value: Значение сообщения
        
    Returns:
        str: Отформатированное сообщение
    """
    if isinstance(value, (list, tuple)):
        value_str = ", ".join(str(v) for v in value)
    else:
        value_str = str(value)
    
    return f"{address} {value_str}"


class OSCServer:
    """Класс для работы с OSC-сервером"""
    
    def __init__(self, ip: str, port: int):
        """
        Инициализация OSC-сервера
        
        Args:
            ip: IP-адрес для прослушивания
            port: Порт для прослушивания
        """
        self.logger = logging.getLogger('ShogunOSC.OSCServer')
        self.ip = ip
        self.port = port
        self.broadcast_ip = config.DEFAULT_OSC_BROADCAST_IP
        self.broadcast_port = config.DEFAULT_OSC_BROADCAST_PORT
        
        # Создаем диспетчер OSC
        self.dispatcher = dispatcher.Dispatcher()
        
        # Регистрируем обработчики по умолчанию
        self.dispatcher.set_default_handler(self._default_handler)
        
        # Сервер и клиент
        self.server = None
        self.client = None
        self.server_thread = None
        
        # Кеш клиентов для отправки сообщений
        self._clients_cache = {}
        
        # Флаг работы сервера
        self.running = False
        
        # Список зарегистрированных обработчиков
        self.handlers = {}
        
        # Сигнал об изменении статуса сервера
        self.status_callback = None
    
    def register_handler(self, address: str, handler: Callable) -> None:
        """
        Регистрация обработчика OSC-сообщений
        
        Args:
            address: Адрес OSC-сообщения
            handler: Функция-обработчик
        """
        self.dispatcher.map(address, handler)
        self.handlers[address] = handler
        self.logger.debug(f"Зарегистрирован обработчик для {address}")
    
    def set_status_callback(self, callback: Callable[[bool], None]) -> None:
        """
        Установка функции обратного вызова для уведомления об изменении статуса сервера
        
        Args:
            callback: Функция обратного вызова, принимающая булево значение (True - запущен, False - остановлен)
        """
        self.status_callback = callback
    
    def start(self) -> bool:
        """
        Запуск OSC-сервера
        
        Returns:
            bool: True если сервер успешно запущен, иначе False
        """
        if self.running:
            self.logger.warning("OSC-сервер уже запущен")
            return True
        
        try:
            # Создаем сервер
            self.server = osc_server.ThreadingOSCUDPServer(
                (self.ip, self.port), self.dispatcher)
            
            # Запускаем сервер в отдельном потоке
            self.server_thread = threading.Thread(
                target=self.server.serve_forever, daemon=True)
            self.server_thread.start()
            
            self.running = True
            self.logger.info(f"OSC-сервер запущен на {self.ip}:{self.port}")
            
            # Уведомляем о запуске сервера
            if self.status_callback:
                self.status_callback(True)
                
            return True
        except Exception as e:
            self.logger.error(f"Ошибка запуска OSC-сервера: {e}")
            
            # Уведомляем об ошибке запуска
            if self.status_callback:
                self.status_callback(False)
                
            return False
    
    def stop(self) -> None:
        """Остановка OSC-сервера"""
        if not self.running:
            return
        
        try:
            # Останавливаем сервер
            if self.server:
                self.server.shutdown()
                self.server.server_close()
            
            # Ждем завершения потока
            if self.server_thread:
                self.server_thread.join(timeout=1.0)
            
            self.running = False
            self.logger.info("OSC-сервер остановлен")
            
            # Уведомляем об остановке сервера
            if self.status_callback:
                self.status_callback(False)
                
        except Exception as e:
            self.logger.error(f"Ошибка остановки OSC-сервера: {e}")
    
    def restart(self) -> bool:
        """
        Перезапуск OSC-сервера
        
        Returns:
            bool: True если сервер успешно перезапущен, иначе False
        """
        self.logger.info("Перезапуск OSC-сервера...")
        
        # Останавливаем сервер если он запущен
        if self.running:
            self.stop()
            
            # Небольшая пауза для корректного завершения предыдущего сервера
            time.sleep(0.5)
        
        # Запускаем сервер заново
        return self.start()
    
    def send_message(self, address: str, value: Any = None) -> bool:
        """
        Отправка OSC-сообщения
        
        Args:
            address: Адрес OSC-сообщения
            value: Значение сообщения (опционально)
            
        Returns:
            bool: True если сообщение успешно отправлено, иначе False
        """
        try:
            # Получаем или создаем клиента для отправки
            client = self._get_client(self.broadcast_ip, self.broadcast_port)
            
            # Отправляем сообщение
            if value is not None:
                client.send_message(address, value)
            else:
                client.send_message(address, "")
            
            self.logger.debug(f"Отправлено OSC-сообщение: {format_osc_message(address, value)}")
            return True
        except Exception as e:
            self.logger.error(f"Ошибка отправки OSC-сообщения: {e}")
            return False
    
    def set_broadcast_settings(self, ip: str, port: int) -> None:
        """
        Установка настроек широковещательной рассылки
        
        Args:
            ip: IP-адрес для отправки
            port: Порт для отправки
        """
        self.broadcast_ip = ip
        self.broadcast_port = port
        
        # Очищаем кеш клиентов при изменении настроек
        self._clients_cache = {}
    
    def get_registered_handlers(self) -> List[str]:
        """
        Получение списка зарегистрированных обработчиков
        
        Returns:
            List[str]: Список адресов OSC-сообщений
        """
        return list(self.handlers.keys()) + [
            config.OSC_START_RECORDING,
            config.OSC_STOP_RECORDING,
            config.OSC_CAPTURE_NAME_CHANGED,
            config.OSC_CAPTURE_ERROR,
            config.OSC_HYPERDECK_START_RECORDING,
            config.OSC_HYPERDECK_STOP_RECORDING,
            config.OSC_HYPERDECK_STATUS,
            config.OSC_HYPERDECK_ERROR,
            config.OSC_HYPERDECK_CONNECTED,
            config.OSC_START_ALL_RECORDING,
            config.OSC_STOP_ALL_RECORDING
        ]
    
    def is_running(self) -> bool:
        """
        Проверка активности сервера
        
        Returns:
            bool: True если сервер запущен, иначе False
        """
        return self.running
    
    def _get_client(self, ip: str, port: int) -> udp_client.SimpleUDPClient:
        """
        Получение клиента для отправки OSC-сообщений
        
        Args:
            ip: IP-адрес для отправки
            port: Порт для отправки
            
        Returns:
            SimpleUDPClient: Клиент для отправки OSC-сообщений
        """
        # Проверяем наличие клиента в кеше
        client_key = f"{ip}:{port}"
        if client_key not in self._clients_cache:
            self._clients_cache[client_key] = udp_client.SimpleUDPClient(ip, port)
        
        return self._clients_cache[client_key]
    
    def _default_handler(self, address: str, *args) -> None:
        """
        Обработчик по умолчанию для OSC-сообщений
        
        Args:
            address: Адрес OSC-сообщения
            *args: Аргументы сообщения
        """
        self.logger.debug(f"Получено OSC-сообщение: {format_osc_message(address, args)}")