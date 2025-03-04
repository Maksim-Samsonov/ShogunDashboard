"""
Модуль для взаимодействия с устройствами Blackmagic HyperDeck.
Обеспечивает подключение, управление записью и получение информации о клипах.
"""

import asyncio
import logging
from typing import Optional, List, Dict, Any, Tuple, Callable
from PyQt5.QtCore import QObject, pyqtSignal


class HyperDeckClient(QObject):
    """Клиент для взаимодействия с устройствами Blackmagic HyperDeck"""
    
    # Сигналы для обновления UI
    connection_signal = pyqtSignal(int, bool)  # (device_id, connected)
    status_signal = pyqtSignal(int, str)       # (device_id, status)
    recording_signal = pyqtSignal(int, bool)   # (device_id, is_recording)
    clips_updated_signal = pyqtSignal(int, list)  # (device_id, clips)
    error_signal = pyqtSignal(int, str)        # (device_id, error_message)
    
    def __init__(self, device_id: int, host: str, port: int = 9993):
        """
        Инициализация клиента HyperDeck
        
        Args:
            device_id: Уникальный идентификатор устройства
            host: IP-адрес устройства
            port: Порт для подключения (по умолчанию 9993)
        """
        super().__init__()
        self.logger = logging.getLogger('ShogunOSC.HyperDeck')
        self.device_id = device_id
        self.host = host
        self.port = port
        self.clips = []
        self.status = {}
        self.connected = False
        self.recording = False
        
        # Внутренние переменные для работы с соединением
        self._transport = None
        self._protocol = None
        self._response_future = None
        self._loop = None
        self._polling_task = None
        self._connection_task = None
        self._stopping = False
    
    async def connect(self) -> bool:
        """
        Подключение к устройству HyperDeck
        
        Returns:
            bool: True если подключение успешно, иначе False
        """
        if self._transport:
            self.logger.debug(f"HyperDeck {self.device_id}: Уже подключен к {self.host}:{self.port}")
            return True
            
        self.logger.info(f"HyperDeck {self.device_id}: Подключение к {self.host}:{self.port}...")
        
        try:
            self._loop = asyncio.get_event_loop()
            reader, writer = await asyncio.open_connection(
                host=self.host, 
                port=self.port
            )
            self._transport = (reader, writer)
            
            # Ожидаем приветственное сообщение от устройства
            welcome = await self._receive()
            if not welcome or not welcome[0].startswith('500'):
                self.logger.error(f"HyperDeck {self.device_id}: Некорректное приветствие: {welcome}")
                await self._close_connection()
                self.connection_signal.emit(self.device_id, False)
                return False
                
            self.logger.info(f"HyperDeck {self.device_id}: Подключение установлено")
            
            # Настраиваем уведомления
            await self.enable_notifications()
            
            # Запускаем задачу для периодического опроса состояния
            self._polling_task = asyncio.create_task(self._poll_state())
            
            # Обновляем информацию о клипах
            await self.update_clips()
            
            self.connected = True
            self.connection_signal.emit(self.device_id, True)
            return True
            
        except Exception as e:
            self.logger.error(f"HyperDeck {self.device_id}: Ошибка подключения: {e}")
            self.error_signal.emit(self.device_id, f"Ошибка подключения: {e}")
            await self._close_connection()
            self.connection_signal.emit(self.device_id, False)
            return False
    
    async def disconnect(self) -> None:
        """Отключение от устройства HyperDeck"""
        self.logger.info(f"HyperDeck {self.device_id}: Отключение...")
        self._stopping = True
        
        # Останавливаем задачу опроса состояния
        if self._polling_task:
            self._polling_task.cancel()
            try:
                await self._polling_task
            except asyncio.CancelledError:
                pass
            self._polling_task = None
        
        await self._close_connection()
        self.connected = False
        self.connection_signal.emit(self.device_id, False)
        self._stopping = False
    
    async def record(self, name: Optional[str] = None) -> bool:
        """
        Запуск записи на устройстве HyperDeck
        
        Args:
            name: Имя для записи (опционально)
            
        Returns:
            bool: True если запись успешно запущена, иначе False
        """
        if not self._transport:
            self.logger.error(f"HyperDeck {self.device_id}: Попытка записи без подключения")
            return False
        
        command = 'record'
        if name:
            command = f'record: name: {name}'
        
        response = await self._send_command(command)
        success = response and not response.get('error', True)
        
        if success:
            self.logger.info(f"HyperDeck {self.device_id}: Запись начата{' с именем ' + name if name else ''}")
            self.recording = True
            self.recording_signal.emit(self.device_id, True)
        else:
            error_msg = "Неизвестная ошибка"
            if response and 'lines' in response and len(response['lines']) > 0:
                error_msg = response['lines'][0]
            self.logger.error(f"HyperDeck {self.device_id}: Ошибка запуска записи: {error_msg}")
            self.error_signal.emit(self.device_id, f"Ошибка запуска записи: {error_msg}")
        
        return success
    
    async def stop(self) -> bool:
        """
        Остановка записи на устройстве HyperDeck
        
        Returns:
            bool: True если запись успешно остановлена, иначе False
        """
        if not self._transport:
            self.logger.error(f"HyperDeck {self.device_id}: Попытка остановки без подключения")
            return False
        
        response = await self._send_command('stop')
        success = response and not response.get('error', True)
        
        if success:
            self.logger.info(f"HyperDeck {self.device_id}: Запись остановлена")
            self.recording = False
            self.recording_signal.emit(self.device_id, False)
        else:
            error_msg = "Неизвестная ошибка"
            if response and 'lines' in response and len(response['lines']) > 0:
                error_msg = response['lines'][0]
            self.logger.error(f"HyperDeck {self.device_id}: Ошибка остановки записи: {error_msg}")
            self.error_signal.emit(self.device_id, f"Ошибка остановки записи: {error_msg}")
        
        return success
    
    async def update_clips(self) -> List[Dict[str, str]]:
        """
        Обновление списка клипов с устройства
        
        Returns:
            List[Dict[str, str]]: Список клипов
        """
        if not self._transport:
            self.logger.error(f"HyperDeck {self.device_id}: Попытка получения клипов без подключения")
            return []
        
        response = await self._send_command('clips get')
        
        # Очищаем кеш клипов в любом случае
        self.clips = []
        
        if response and response.get('code') == 205:
            # Пропускаем первые две строки (код и количество клипов)
            clip_info = response['lines'][2:]
            
            for info in clip_info:
                fields = info.split(' ')
                
                # Каждая строка содержит: индекс клипа, имя, таймкод начала и длительность
                clip = {
                    'id': fields[0],
                    'name': ' '.join(fields[1: len(fields) - 2]),
                    'timecode': fields[-2],
                    'duration': fields[-1],
                }
                
                self.clips.append(clip)
            
            self.logger.debug(f"HyperDeck {self.device_id}: Получено {len(self.clips)} клипов")
            self.clips_updated_signal.emit(self.device_id, self.clips)
        else:
            self.logger.warning(f"HyperDeck {self.device_id}: Не удалось получить список клипов")
        
        return self.clips
    
    async def update_status(self) -> Dict[str, str]:
        """
        Обновление статуса устройства
        
        Returns:
            Dict[str, str]: Словарь с параметрами статуса
        """
        if not self._transport:
            return {}
        
        response = await self._send_command('transport info')
        
        self.status = {}
        
        if response and response.get('code') == 208:
            transport_info = response['lines'][1:]
            
            # Каждая строка после первой содержит отдельный параметр статуса
            for line in transport_info:
                try:
                    (name, value) = line.split(': ', 1)
                    self.status[name] = value
                except ValueError:
                    continue
            
            # Проверяем статус записи
            is_recording = self.status.get('status', '').lower() == 'record'
            if is_recording != self.recording:
                self.recording = is_recording
                self.recording_signal.emit(self.device_id, is_recording)
            
            # Отправляем сигнал с текущим статусом
            status_text = self.status.get('status', 'unknown')
            self.status_signal.emit(self.device_id, status_text)
        
        return self.status
    
    async def enable_notifications(self, slot: bool = True, remote: bool = True, config: bool = True) -> bool:
        """
        Включение уведомлений от устройства
        
        Args:
            slot: Уведомления о слотах
            remote: Уведомления о дистанционном управлении
            config: Уведомления о конфигурации
            
        Returns:
            bool: True если уведомления включены успешно, иначе False
        """
        command = f'notify:\nslot: {str(slot).lower()}\nremote: {str(remote).lower()}\nconfiguration: {str(config).lower()}\n\n'
        response = await self._send_command(command)
        return response and not response.get('error', True)
    
    async def _send_command(self, command: str) -> Dict[str, Any]:
        """
        Отправка команды на устройство
        
        Args:
            command: Текст команды
            
        Returns:
            Dict[str, Any]: Ответ от устройства
        """
        if not self._transport:
            return {'error': True, 'code': 0, 'lines': ['Not connected']}
        
        # Ждем завершения предыдущей команды
        if self._response_future:
            try:
                await self._response_future
            except Exception:
                pass
        
        # Создаем Future для получения ответа
        self._response_future = asyncio.Future()
        
        # Отправляем команду
        await self._send(command)
        
        try:
            # Ждем ответа с таймаутом
            response = await asyncio.wait_for(self._response_future, timeout=5.0)
            self._response_future = None
            return response
        except asyncio.TimeoutError:
            self.logger.error(f"HyperDeck {self.device_id}: Таймаут ожидания ответа на команду: {command}")
            self._response_future = None
            return {'error': True, 'code': 0, 'lines': ['Timeout']}
        except Exception as e:
            self.logger.error(f"HyperDeck {self.device_id}: Ошибка при отправке команды: {e}")
            self._response_future = None
            return {'error': True, 'code': 0, 'lines': [str(e)]}
    
    async def _poll_state(self) -> None:
        """Периодический опрос состояния устройства"""
        while not self._stopping:
            try:
                if self._transport:
                    await self.update_status()
            except Exception as e:
                if not self._stopping:
                    self.logger.error(f"HyperDeck {self.device_id}: Ошибка при опросе состояния: {e}")
                    # Пробуем переподключиться при ошибке
                    await self._close_connection()
                    self.connected = False
                    self.connection_signal.emit(self.device_id, False)
                    
                    # Небольшая задержка перед повторным подключением
                    await asyncio.sleep(5)
                    
                    if not self._stopping:
                        self._connection_task = asyncio.create_task(self.connect())
            
            # Ждем перед следующим опросом
            await asyncio.sleep(1)
    
    async def _send(self, data: str) -> None:
        """
        Отправка данных на устройство
        
        Args:
            data: Данные для отправки
        """
        if not self._transport:
            return
        
        self.logger.debug(f"HyperDeck {self.device_id}: Отправка: {data}")
        
        data += '\r\n'
        self._transport[1].write(data.encode('utf-8'))
        await self._transport[1].drain()
    
    async def _receive(self) -> List[str]:
        """
        Получение данных от устройства
        
        Returns:
            List[str]: Список строк ответа
        """
        if not self._transport:
            return []
        
        async def _read_line() -> str:
            try:
                line = await self._transport[0].readline()
                return line.decode('utf-8').rstrip()
            except Exception as e:
                self.logger.error(f"HyperDeck {self.device_id}: Ошибка чтения: {e}")
                return ""
        
        lines = []
        
        # Получаем первую строку ответа
        first_line = await _read_line()
        if not first_line:
            return []
            
        lines.append(first_line)
        
        # Многострочные ответы заканчиваются двоеточием в первой строке
        if first_line.endswith(':'):
            while True:
                line = await _read_line()
                if not line:
                    break
                
                lines.append(line)
        
        self.logger.debug(f"HyperDeck {self.device_id}: Получено: {lines}")
        
        # Обрабатываем ответ если есть ожидающий future
        if lines and self._response_future and not self._response_future.done():
            try:
                # Код ответа - первое число в первой строке
                response_code = int(lines[0].split(' ', 1)[0])
                
                # Определяем тип ответа
                is_error = response_code >= 100 and response_code < 200
                is_async = response_code >= 500 and response_code < 600
                
                # Для асинхронных уведомлений не сигнализируем о завершении команды
                if not is_async:
                    response = {
                        'error': is_error,
                        'code': response_code,
                        'lines': lines,
                    }
                    
                    self._response_future.set_result(response)
            except Exception as e:
                self.logger.error(f"HyperDeck {self.device_id}: Ошибка обработки ответа: {e}")
                if not self._response_future.done():
                    self._response_future.set_exception(e)
        
        return lines
    
    async def _close_connection(self) -> None:
        """Закрытие соединения с устройством"""
        if self._transport:
            try:
                self._transport[1].close()
                await self._transport[1].wait_closed()
            except Exception as e:
                self.logger.error(f"HyperDeck {self.device_id}: Ошибка при закрытии соединения: {e}")
            finally:
                self._transport = None
