"""
Менеджер для управления несколькими устройствами HyperDeck.
Обеспечивает синхронизированную запись и управление состоянием устройств.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any
from PyQt5.QtCore import QObject, pyqtSignal

from .hyperdeck_client import HyperDeckClient


class HyperDeckManager(QObject):
    """Менеджер для управления несколькими устройствами HyperDeck"""
    
    # Сигналы для обновления UI
    devices_updated_signal = pyqtSignal(list)  # Список устройств с их состояниями
    recording_status_signal = pyqtSignal(bool)  # Общий статус записи (True если хотя бы одно устройство записывает)
    error_signal = pyqtSignal(str)  # Сообщение об ошибке
    
    def __init__(self):
        """Инициализация менеджера HyperDeck"""
        super().__init__()
        self.logger = logging.getLogger('ShogunOSC.HyperDeckManager')
        self.devices: Dict[int, HyperDeckClient] = {}
        self.recording = False
        self._loop = None
    
    def add_device(self, device_id: int, host: str, port: int = 9993) -> HyperDeckClient:
        """
        Добавление нового устройства HyperDeck
        
        Args:
            device_id: Уникальный идентификатор устройства
            host: IP-адрес устройства
            port: Порт для подключения (по умолчанию 9993)
            
        Returns:
            HyperDeckClient: Созданный клиент устройства
        """
        if device_id in self.devices:
            self.logger.warning(f"Устройство с ID {device_id} уже существует, будет заменено")
            # Отключаем существующее устройство
            asyncio.create_task(self.devices[device_id].disconnect())
        
        # Создаем новый клиент
        device = HyperDeckClient(device_id, host, port)
        
        # Подключаем сигналы устройства
        device.connection_signal.connect(self._on_device_connection_changed)
        device.recording_signal.connect(self._on_device_recording_changed)
        device.error_signal.connect(self._on_device_error)
        
        # Добавляем устройство в словарь
        self.devices[device_id] = device
        
        # Уведомляем об обновлении списка устройств
        self._update_devices_list()
        
        return device
    
    def remove_device(self, device_id: int) -> None:
        """
        Удаление устройства HyperDeck
        
        Args:
            device_id: Идентификатор устройства для удаления
        """
        if device_id in self.devices:
            # Отключаем устройство
            asyncio.create_task(self.devices[device_id].disconnect())
            # Удаляем из словаря
            del self.devices[device_id]
            # Уведомляем об обновлении списка устройств
            self._update_devices_list()
    
    async def connect_all(self) -> bool:
        """
        Подключение ко всем устройствам
        
        Returns:
            bool: True если все устройства подключены успешно, иначе False
        """
        if not self.devices:
            self.logger.warning("Нет добавленных устройств HyperDeck")
            return False
        
        self._loop = asyncio.get_event_loop()
        
        # Запускаем подключение для всех устройств параллельно
        tasks = [device.connect() for device in self.devices.values()]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Проверяем результаты
        success = all(isinstance(result, bool) and result for result in results)
        
        if success:
            self.logger.info("Все устройства HyperDeck подключены успешно")
        else:
            self.logger.error("Не удалось подключить все устройства HyperDeck")
            
            # Логируем ошибки для каждого устройства
            for device_id, result in zip(self.devices.keys(), results):
                if isinstance(result, Exception):
                    self.logger.error(f"Ошибка подключения устройства {device_id}: {result}")
                elif not result:
                    self.logger.error(f"Не удалось подключить устройство {device_id}")
        
        return success
    
    async def disconnect_all(self) -> None:
        """Отключение от всех устройств"""
        if not self.devices:
            return
        
        # Запускаем отключение для всех устройств параллельно
        tasks = [device.disconnect() for device in self.devices.values()]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        self.logger.info("Все устройства HyperDeck отключены")
    
    async def start_recording(self, name: Optional[str] = None) -> bool:
        """
        Запуск записи на всех устройствах
        
        Args:
            name: Базовое имя для записи (к нему будет добавлен ID устройства)
            
        Returns:
            bool: True если запись успешно запущена на всех устройствах, иначе False
        """
        if not self.devices:
            self.logger.warning("Нет добавленных устройств HyperDeck для записи")
            return False
        
        # Формируем имена для каждого устройства
        device_names = {}
        for device_id in self.devices:
            if name:
                device_names[device_id] = f"{name}_deck{device_id}"
            else:
                device_names[device_id] = None
        
        # Запускаем запись на всех устройствах параллельно
        tasks = [device.record(device_names.get(device_id)) 
                for device_id, device in self.devices.items()]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Проверяем результаты
        success = all(isinstance(result, bool) and result for result in results)
        
        if success:
            self.logger.info("Запись начата на всех устройствах HyperDeck")
            self.recording = True
            self.recording_status_signal.emit(True)
        else:
            # Если не удалось запустить запись на всех устройствах, останавливаем те, где она запущена
            self.logger.error("Не удалось запустить запись на всех устройствах HyperDeck")
            
            # Логируем ошибки для каждого устройства
            for device_id, result in zip(self.devices.keys(), results):
                if isinstance(result, Exception):
                    self.logger.error(f"Ошибка запуска записи на устройстве {device_id}: {result}")
                    self.error_signal.emit(f"Ошибка запуска записи на HyperDeck {device_id}: {result}")
                elif not result:
                    self.logger.error(f"Не удалось запустить запись на устройстве {device_id}")
                    self.error_signal.emit(f"Не удалось запустить запись на HyperDeck {device_id}")
            
            # Останавливаем запись на всех устройствах
            await self.stop_recording()
        
        return success
    
    async def stop_recording(self) -> bool:
        """
        Остановка записи на всех устройствах
        
        Returns:
            bool: True если запись успешно остановлена на всех устройствах, иначе False
        """
        if not self.devices:
            return False
        
        # Запускаем остановку записи на всех устройствах параллельно
        tasks = [device.stop() for device in self.devices.values()]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Проверяем результаты
        success = all(isinstance(result, bool) and result for result in results)
        
        if success:
            self.logger.info("Запись остановлена на всех устройствах HyperDeck")
        else:
            self.logger.error("Не удалось остановить запись на всех устройствах HyperDeck")
            
            # Логируем ошибки для каждого устройства
            for device_id, result in zip(self.devices.keys(), results):
                if isinstance(result, Exception):
                    self.logger.error(f"Ошибка остановки записи на устройстве {device_id}: {result}")
                    self.error_signal.emit(f"Ошибка остановки записи на HyperDeck {device_id}: {result}")
                elif not result:
                    self.logger.error(f"Не удалось остановить запись на устройстве {device_id}")
                    self.error_signal.emit(f"Не удалось остановить запись на HyperDeck {device_id}")
        
        # В любом случае считаем, что запись остановлена
        self.recording = False
        self.recording_status_signal.emit(False)
        
        return success
    
    async def update_all_status(self) -> Dict[int, Dict[str, str]]:
        """
        Обновление статуса всех устройств
        
        Returns:
            Dict[int, Dict[str, str]]: Словарь с ID устройств и их статусами
        """
        if not self.devices:
            return {}
        
        # Запускаем обновление статуса на всех устройствах параллельно
        tasks = [(device_id, device.update_status()) 
                for device_id, device in self.devices.items()]
        
        results = {}
        for device_id, task in tasks:
            try:
                status = await task
                results[device_id] = status
            except Exception as e:
                self.logger.error(f"Ошибка обновления статуса устройства {device_id}: {e}")
                results[device_id] = {}
        
        return results
    
    async def update_all_clips(self) -> Dict[int, List[Dict[str, str]]]:
        """
        Обновление списка клипов всех устройств
        
        Returns:
            Dict[int, List[Dict[str, str]]]: Словарь с ID устройств и их клипами
        """
        if not self.devices:
            return {}
        
        # Запускаем обновление клипов на всех устройствах параллельно
        tasks = [(device_id, device.update_clips()) 
                for device_id, device in self.devices.items()]
        
        results = {}
        for device_id, task in tasks:
            try:
                clips = await task
                results[device_id] = clips
            except Exception as e:
                self.logger.error(f"Ошибка обновления клипов устройства {device_id}: {e}")
                results[device_id] = []
        
        return results
    
    def _update_devices_list(self) -> None:
        """Обновление списка устройств и отправка сигнала"""
        devices_info = []
        
        for device_id, device in self.devices.items():
            devices_info.append({
                'id': device_id,
                'host': device.host,
                'port': device.port,
                'connected': device.connected,
                'recording': device.recording,
                'status': device.status.get('status', 'unknown')
            })
        
        self.devices_updated_signal.emit(devices_info)
    
    def _on_device_connection_changed(self, device_id: int, connected: bool) -> None:
        """
        Обработчик изменения статуса подключения устройства
        
        Args:
            device_id: ID устройства
            connected: Статус подключения
        """
        self.logger.info(f"HyperDeck {device_id}: {'Подключен' if connected else 'Отключен'}")
        self._update_devices_list()
    
    def _on_device_recording_changed(self, device_id: int, recording: bool) -> None:
        """
        Обработчик изменения статуса записи устройства
        
        Args:
            device_id: ID устройства
            recording: Статус записи
        """
        self.logger.info(f"HyperDeck {device_id}: {'Запись' if recording else 'Остановка записи'}")
        
        # Обновляем общий статус записи
        any_recording = any(device.recording for device in self.devices.values())
        if any_recording != self.recording:
            self.recording = any_recording
            self.recording_status_signal.emit(any_recording)
        
        self._update_devices_list()
    
    def _on_device_error(self, device_id: int, error_message: str) -> None:
        """
        Обработчик ошибок устройства
        
        Args:
            device_id: ID устройства
            error_message: Сообщение об ошибке
        """
        self.logger.error(f"HyperDeck {device_id}: {error_message}")
        self.error_signal.emit(f"HyperDeck {device_id}: {error_message}")
