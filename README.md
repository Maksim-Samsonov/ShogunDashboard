# Shogun OSC GUI

GUI-приложение для управления Vicon Shogun Live через OSC-протокол.

## Возможности

- Подключение к Shogun Live API
- Автоматическое обнаружение запущенного Shogun Live
- OSC-сервер для приема команд дистанционного управления
- Управление записью в Shogun Live
- Светлая и тёмная темы оформления

## Требования

- Python 3.6+
- Vicon Shogun Live (установлен и запущен на локальном компьютере)
- Библиотеки:
  - PyQt5
  - vicon-core-api
  - shogun-live-api
  - python-osc
  - psutil

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/username/shogun-osc-gui.git
cd shogun-osc-gui
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

## Использование

Запустите приложение:
```bash
python main.py
```

### OSC-команды

Приложение принимает следующие OSC-команды:

- `/RecordStartShogunLive` - начать запись в Shogun Live
- `/RecordStopShogunLive` - остановить запись в Shogun Live

## Структура проекта

```
shogun_osc/
├── main.py                     # Точка входа в программу
├── config.py                   # Конфигурационные параметры
├── logger/
│   ├── __init__.py
│   └── custom_logger.py        # Настройка логирования
├── shogun/
│   ├── __init__.py
│   └── shogun_client.py        # Взаимодействие с Shogun Live
├── osc/
│   ├── __init__.py
│   └── osc_server.py           # OSC-сервер и обработчики сообщений
├── styles/
│   ├── __init__.py
│   └── app_styles.py           # Стили приложения (темы)
└── gui/
    ├── __init__.py
    ├── main_window.py          # Главное окно приложения
    ├── status_panel.py         # Панель информации о состоянии
    └── log_panel.py            # Панель для отображения логов
```

## Настройка

Настройки приложения хранятся в каталоге `~/.shogun_osc/settings.json` и включают:

- `dark_mode`: использование тёмной темы (true/false)
- `osc_ip`: IP-адрес для OSC-сервера
- `osc_port`: порт для OSC-сервера
- `osc_enabled`: включение/отключение OSC-сервера при запуске

## Лицензия

MIT