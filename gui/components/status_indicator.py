"""
Компонент индикатора статуса для отображения состояния различных устройств и сервисов.
"""

from PyQt5.QtWidgets import QLabel, QWidget, QHBoxLayout
from PyQt5.QtCore import Qt

class StatusIndicator(QWidget):
    """
    Универсальный индикатор статуса с меткой.
    
    Показывает цветной индикатор и текст состояния.
    Используется для наглядного отображения состояния подключения устройств
    и других параметров приложения.
    """
    
    # Константы для статусов
    STATUS_OK = "ok"
    STATUS_ERROR = "error"
    STATUS_WARNING = "warning"
    STATUS_INACTIVE = "inactive"
    STATUS_RECORDING = "recording"
    
    def __init__(self, label="Статус", parent=None):
        """
        Инициализация индикатора статуса.
        
        Args:
            label (str): Текст метки
            parent: Родительский виджет
        """
        super().__init__(parent)
        
        # Настройка макета
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # Индикатор (цветной кружок)
        self.indicator = QLabel()
        self.indicator.setMinimumSize(16, 16)
        self.indicator.setMaximumSize(16, 16)
        self.set_status(self.STATUS_INACTIVE)
        
        # Метка с текстом
        self.label = QLabel(label)
        
        # Текст статуса
        self.status_text = QLabel("Неизвестно")
        
        # Добавляем виджеты в макет
        layout.addWidget(self.indicator)
        layout.addWidget(self.label)
        layout.addWidget(self.status_text, 1)  # 1 = stretch factor
        
        self.setLayout(layout)
    
    def set_status(self, status, text=None):
        """
        Установка статуса индикатора.
        
        Args:
            status (str): Тип статуса (ok, error, warning, inactive, recording)
            text (str, optional): Текст статуса. Если None, используется стандартный текст.
        """
        # Определяем цвет и текст для статуса
        if status == self.STATUS_OK:
            color = "#4caf50"  # Зелёный
            default_text = "Работает"
        elif status == self.STATUS_ERROR:
            color = "#f44336"  # Красный
            default_text = "Ошибка"
        elif status == self.STATUS_WARNING:
            color = "#ff9800"  # Оранжевый
            default_text = "Предупреждение"
        elif status == self.STATUS_RECORDING:
            color = "#e91e63"  # Розовый
            default_text = "Запись"
        else:  # STATUS_INACTIVE
            color = "#9e9e9e"  # Серый
            default_text = "Не активен"
        
        # Обновляем стиль индикатора
        self.indicator.setStyleSheet(f"""
            QLabel {{
                border: 1px solid #666;
                border-radius: 8px;
                background-color: {color};
            }}
        """)
        
        # Обновляем текст статуса
        if text is not None:
            self.status_text.setText(text)
        else:
            self.status_text.setText(default_text)
