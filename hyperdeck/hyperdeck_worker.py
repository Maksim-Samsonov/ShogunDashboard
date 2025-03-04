"""
Рабочий поток для управления устройствами HyperDeck.
"""

import logging
import time
import asyncio
from typing import Dict, List, Optional, Any
from PyQt5.QtCore import QThread, pyqtSignal

from .hyperdeck_client import HyperDeckClient
import config

class HyperDeckWorker(QThread):
    """Рабочий поток для управления устройствами HyperDeck"""
    
    # Сигналы для обновления интерфейса
    device_status_signal = pyqtSignal(int, bool)  # device_id, connected
    device_recording_signal = pyqtSignal(int, bool)  # device_id, is_recording
    error_signal = pyqtSignal(str)  # error_message
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger('ShogunOSC.HyperDeckWorker')
        self.running = True
        self.devices: Dict[int, HyperDeckClient] = {}  # device_id -> client
        self.loop = None
        self._last_check_time = 0
        self._check_interval = 1.0  # Интервал проверки в секундах
        self._error_count = 0
        self._max_error_count = 5
    
    def run(self):
        """Основной метод потока"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        # Основной цикл мониторинга
        while self.running:
            try:
                current_time = time.time()
                
                # Проверяем состояние устройств с адаптивным интервалом
                if current_time - self._last_check_time >= self._check_interval:
                    self._last_check_time = current_time
                    
                    # Проверяем каждое устройство
                    for device_id, client in list(self.devices.items()):
                        try:
                            # Проверяем соединение
                            connected = self.loop.run_until_complete(client.check_connection())
                            self.device_status_signal.emit(device_id, connected)
                            
                            if connected:
                                # Проверяем статус записи
                                is_recording = self.loop.run_until_complete(client.is_recording())
                                self.device_recording_signal.emit(device_id, is_recording)
                                
                                # Сбрасываем счетчик ошибок при успешной проверке
                                self._error_count = 0
                            else:
                                # Если соединение потеряно, удаляем устройство
                                del self.devices[device_id]
                                self.logger.warning(f"Соединение с HyperDeck {device_id} потеряно")
                                
                        except Exception as e:
                            self.logger.error(f"Ошибка при проверке HyperDeck {device_id}: {e}")
                            self._error_count += 1
                            
                            # Если слишком много ошибок, увеличиваем интервал проверки
                            if self._error_count >= self._max_error_count:
                                self._check_interval = min(5.0, self._check_interval * 1.5)
                                self.logger.warning(f"Увеличен интервал проверки до {self._check_interval}с")
                
                # Небольшая пауза для снижения нагрузки
                time.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"Ошибка в основном цикле HyperDeckWorker: {e}")
                self.error_signal.emit(str(e))
    
    def connect_devices(self, devices):
        """
        Подключение к устройствам HyperDeck
        
        Args:
            devices: Список кортежей (device_id, ip)
        """
        for device_id, ip in devices:
            try:
                # Создаем нового клиента
                client = HyperDeckClient(device_id, ip)
                
                # Подключаемся асинхронно
                success = self.loop.run_until_complete(client.connect())
                
                if success:
                    self.devices[device_id] = client
                    self.device_status_signal.emit(device_id, True)
                    self.logger.info(f"Подключено к HyperDeck {device_id} ({ip})")
                else:
                    self.error_signal.emit(f"Не удалось подключиться к HyperDeck {device_id} ({ip})")
                    
            except Exception as e:
                error_msg = f"Ошибка при подключении к HyperDeck {device_id} ({ip}): {e}"
                self.logger.error(error_msg)
                self.error_signal.emit(error_msg)
    
    def disconnect_devices(self, device_ids):
        """
        Отключение от устройств HyperDeck
        
        Args:
            device_ids: Список ID устройств для отключения
        """
        for device_id in device_ids:
            try:
                if device_id in self.devices:
                    client = self.devices[device_id]
                    # Отключаемся асинхронно
                    self.loop.run_until_complete(client.disconnect())
                    del self.devices[device_id]
                    self.device_status_signal.emit(device_id, False)
                    self.logger.info(f"Отключено от HyperDeck {device_id}")
                    
            except Exception as e:
                error_msg = f"Ошибка при отключении от HyperDeck {device_id}: {e}"
                self.logger.error(error_msg)
                self.error_signal.emit(error_msg)
    
    def start_recording(self, device_ids=None):
        """
        Запуск записи на устройствах HyperDeck
        
        Args:
            device_ids: Список ID устройств для начала записи. Если None, то на всех устройствах.
        """
        # Если device_ids не указаны, используем все подключенные устройства
        if device_ids is None:
            device_ids = list(self.devices.keys())
            
        for device_id in device_ids:
            try:
                if device_id in self.devices:
                    client = self.devices[device_id]
                    # Запускаем запись асинхронно
                    success = self.loop.run_until_complete(client.start_recording())
                    if success:
                        self.device_recording_signal.emit(device_id, True)
                        self.logger.info(f"Запись начата на HyperDeck {device_id}")
                    else:
                        self.error_signal.emit(f"Не удалось начать запись на HyperDeck {device_id}")
                        
            except Exception as e:
                error_msg = f"Ошибка при запуске записи на HyperDeck {device_id}: {e}"
                self.logger.error(error_msg)
                self.error_signal.emit(error_msg)
    
    def stop_recording(self, device_ids=None):
        """
        Остановка записи на устройствах HyperDeck
        
        Args:
            device_ids: Список ID устройств для остановки записи. Если None, то на всех устройствах.
        """
        # Если device_ids не указаны, используем все подключенные устройства
        if device_ids is None:
            device_ids = list(self.devices.keys())
            
        for device_id in device_ids:
            try:
                if device_id in self.devices:
                    client = self.devices[device_id]
                    # Останавливаем запись асинхронно
                    success = self.loop.run_until_complete(client.stop_recording())
                    if success:
                        self.device_recording_signal.emit(device_id, False)
                        self.logger.info(f"Запись остановлена на HyperDeck {device_id}")
                    else:
                        self.error_signal.emit(f"Не удалось остановить запись на HyperDeck {device_id}")
                        
            except Exception as e:
                error_msg = f"Ошибка при остановке записи на HyperDeck {device_id}: {e}"
                self.logger.error(error_msg)
                self.error_signal.emit(error_msg)
    
    def has_devices(self) -> bool:
        """
        Проверяет, есть ли доступные устройства HyperDeck
        
        Returns:
            bool: True если есть хотя бы одно доступное устройство, иначе False
        """
        return len(self.devices) > 0
    
    def update_devices(self, device_list: List[Dict[str, Any]]) -> None:
        """
        Обновление списка устройств из конфигурации
        
        Args:
            device_list: Список настроек устройств из конфигурации
        """
        self.logger.info(f"Обновление списка устройств HyperDeck: {len(device_list)} устройств")
        
        # Получаем список ID текущих устройств
        current_device_ids = set(self.devices.keys())
        
        # Создаем список новых устройств
        new_devices = []
        for i, device_config in enumerate(device_list):
            device_id = device_config.get('id', i + 1)
            ip = device_config.get('ip', '')
            port = device_config.get('port', 9993)
            enabled = device_config.get('enabled', True)
            
            # Пропускаем отключенные устройства
            if not enabled:
                continue
                
            # Если у нас нет IP, пропускаем
            if not ip:
                continue
                
            # Добавляем устройство в список
            new_devices.append((device_id, ip, port))
            
            # Если устройство уже подключено, удаляем его из списка текущих
            if device_id in current_device_ids:
                current_device_ids.remove(device_id)
        
        # Отключаем устройства, которых нет в новой конфигурации
        self.disconnect_devices(current_device_ids)
        
        # Подключаем новые устройства
        for device_id, ip, port in new_devices:
            # Если устройство уже подключено, проверяем параметры
            if device_id in self.devices:
                client = self.devices[device_id]
                # Если параметры изменились, переподключаем
                if client.host != ip or client.port != port:
                    self.logger.info(f"Переподключение HyperDeck {device_id} ({ip}:{port})")
                    self.disconnect_devices([device_id])
                    self.connect_devices([(device_id, ip)])
            else:
                # Подключаем новое устройство
                self.connect_devices([(device_id, ip)])
    
    def stop(self):
        """Остановка рабочего потока"""
        self.running = False
        
        # Отключаем все устройства
        for device_id in list(self.devices.keys()):
            try:
                client = self.devices[device_id]
                self.loop.run_until_complete(client.disconnect())
            except Exception as e:
                self.logger.error(f"Ошибка при отключении HyperDeck {device_id}: {e}")
        
        self.devices.clear()
        self.wait()  # Ждем завершения потока