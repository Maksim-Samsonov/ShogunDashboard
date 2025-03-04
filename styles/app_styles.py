"""
Модуль для управления стилями приложения.
Содержит стили для светлой и тёмной темы.
"""

from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt

# Определения базовых цветов для тем
LIGHT_THEME_COLORS = {
    'window': '#f0f0f0',
    'window_text': '#000000',
    'base': '#ffffff',
    'alternate_base': '#f7f7f7',
    'text': '#000000',
    'button': '#e0e0e0',
    'button_text': '#000000',
    'bright_text': '#ffffff',
    'highlight': '#308cc6',
    'highlight_text': '#ffffff',
    'link': '#2a82da',
    'mid': '#d0d0d0',
    'dark': '#a0a0a0',
    'shadow': '#505050',
    
    # Дополнительные цвета для компонентов
    'success': '#4caf50',
    'error': '#f44336',
    'warning': '#ff9800',
    'info': '#2196f3'
}

DARK_THEME_COLORS = {
    'window': '#2b2b2b',
    'window_text': '#ffffff',
    'base': '#373737',
    'alternate_base': '#323232',
    'text': '#ffffff',
    'button': '#4a4a4a',
    'button_text': '#ffffff',
    'bright_text': '#ffffff',
    'highlight': '#2a82da',
    'highlight_text': '#ffffff',
    'link': '#56a0d6',
    'mid': '#3c3c3c',
    'dark': '#2e2e2e',
    'shadow': '#1e1e1e',
    
    # Дополнительные цвета для компонентов
    'success': '#66bb6a',
    'error': '#e57373',
    'warning': '#ffb74d',
    'info': '#64b5f6'
}

def get_palette(dark_mode=False):
    """
    Создает QPalette для указанной темы
    
    Args:
        dark_mode (bool): True для тёмной темы, False для светлой
    
    Returns:
        QPalette: Палитра цветов для приложения
    """
    colors = DARK_THEME_COLORS if dark_mode else LIGHT_THEME_COLORS
    palette = QPalette()
    
    palette.setColor(QPalette.Window, QColor(colors['window']))
    palette.setColor(QPalette.WindowText, QColor(colors['window_text']))
    palette.setColor(QPalette.Base, QColor(colors['base']))
    palette.setColor(QPalette.AlternateBase, QColor(colors['alternate_base']))
    palette.setColor(QPalette.Text, QColor(colors['text']))
    palette.setColor(QPalette.Button, QColor(colors['button']))
    palette.setColor(QPalette.ButtonText, QColor(colors['button_text']))
    palette.setColor(QPalette.BrightText, QColor(colors['bright_text']))
    palette.setColor(QPalette.Highlight, QColor(colors['highlight']))
    palette.setColor(QPalette.HighlightedText, QColor(colors['highlight_text']))
    palette.setColor(QPalette.Link, QColor(colors['link']))
    
    # Установка цветов для 3D-эффектов
    palette.setColor(QPalette.Light, QColor(colors['base']))
    palette.setColor(QPalette.Midlight, QColor(colors['mid']))
    palette.setColor(QPalette.Mid, QColor(colors['mid']))
    palette.setColor(QPalette.Dark, QColor(colors['dark']))
    palette.setColor(QPalette.Shadow, QColor(colors['shadow']))
    
    return palette

def get_stylesheet(dark_mode=False):
    """
    Возвращает таблицу стилей для приложения
    
    Args:
        dark_mode (bool): True для тёмной темы, False для светлой
    
    Returns:
        str: Таблица стилей CSS
    """
    colors = DARK_THEME_COLORS if dark_mode else LIGHT_THEME_COLORS
    
    return f"""
    /* Стилизация QGroupBox */
    QGroupBox {{
        border: 1px solid {colors['mid']};
        border-radius: 5px;
        margin-top: 1ex;
        font-weight: bold;
    }}
    
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top center;
        padding: 0 5px;
    }}
    
    /* Стилизация QPushButton */
    QPushButton {{
        background-color: {colors['button']};
        color: {colors['button_text']};
        border: 1px solid {colors['mid']};
        border-radius: 4px;
        padding: 5px 15px;
        min-width: 80px;
    }}
    
    QPushButton:hover {{
        background-color: {colors['highlight']};
        color: {colors['highlight_text']};
    }}
    
    QPushButton:pressed {{
        background-color: {colors['dark']};
    }}
    
    QPushButton:disabled {{
        background-color: {colors['dark']};
        color: {colors['mid']};
    }}
    
    /* Стилизация для статусных индикаторов */
    QLabel[status="connected"] {{
        color: {colors['success']};
        font-weight: bold;
    }}
    
    QLabel[status="disconnected"] {{
        color: {colors['error']};
        font-weight: bold;
    }}
    
    QLabel[status="recording"] {{
        color: {colors['success']};
        font-weight: bold;
    }}
    
    /* Стилизация для QTextEdit (логи) */
    QTextEdit {{
        background-color: {colors['base']};
        color: {colors['text']};
        border: 1px solid {colors['mid']};
        border-radius: 4px;
    }}
    
    /* Настройка для QStatusBar */
    QStatusBar {{
        background-color: {colors['window']};
        color: {colors['window_text']};
        border-top: 1px solid {colors['mid']};
    }}
    
    /* QSpinBox и QLineEdit */
    QSpinBox, QLineEdit {{
        background-color: {colors['base']};
        color: {colors['text']};
        border: 1px solid {colors['mid']};
        border-radius: 4px;
        padding: 2px 4px;
    }}
    
    QSpinBox:disabled, QLineEdit:disabled {{
        background-color: {colors['alternate_base']};
        color: {colors['mid']};
    }}
    
    /* QCheckBox */
    QCheckBox {{
        spacing: 5px;
    }}
    
    QCheckBox::indicator {{
        width: 15px;
        height: 15px;
        border: 1px solid {colors['mid']};
        border-radius: 3px;
    }}
    
    QCheckBox::indicator:checked {{
        background-color: {colors['highlight']};
    }}
    
    QCheckBox::indicator:hover {{
        border: 1px solid {colors['highlight']};
    }}
    """

def set_status_style(label, status):
    """
    Устанавливает атрибут status для лейбла для стилизации
    
    Args:
        label (QLabel): Метка для установки стиля
        status (str): Статус ('connected', 'disconnected', 'recording')
    """
    label.setProperty("status", status)
    label.style().unpolish(label)
    label.style().polish(label)