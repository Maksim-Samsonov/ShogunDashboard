"""
Main dashboard panel displaying system status and controls.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                           QLabel, QPushButton, QGroupBox, QTextEdit)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QPainter, QIcon
import logging
import config

class StatusIndicator(QWidget):
    def __init__(self, size=16):
        super().__init__()
        self.size = size
        self.status = False
        self.setFixedSize(size, size)
    
    def set_status(self, status: bool):
        self.status = status
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        color = QColor("#2ecc71") if self.status else QColor("#e74c3c")
        painter.setBrush(color)
        painter.setPen(Qt.NoPen)
        
        painter.drawEllipse(0, 0, self.size, self.size)

class SystemStatusWidget(QGroupBox):
    def __init__(self, title):
        super().__init__(title)
        self.init_ui()
    
    def init_ui(self):
        layout = QGridLayout()
        layout.setSpacing(10)
        
        # Shogun Status
        self.shogun_indicator = StatusIndicator()
        self.shogun_info = QLabel("localhost")
        layout.addWidget(self.shogun_info, 0, 0)
        layout.addWidget(QLabel("Shogun:"), 0, 1)
        layout.addWidget(self.shogun_indicator, 0, 2)
        
        # OSC Server Status
        self.osc_indicator = StatusIndicator()
        self.osc_info = QLabel("")  # Will be set in update_info
        layout.addWidget(self.osc_info, 1, 0)
        layout.addWidget(QLabel("OSC Server:"), 1, 1)
        layout.addWidget(self.osc_indicator, 1, 2)
        
        # HyperDeck Status
        self.hyperdeck_indicators = []
        self.hyperdeck_infos = []
        for i in range(3):
            indicator = StatusIndicator()
            self.hyperdeck_indicators.append(indicator)
            info_label = QLabel("")  # Will be set in update_info
            self.hyperdeck_infos.append(info_label)
            layout.addWidget(info_label, i+2, 0)
            layout.addWidget(QLabel(f"HyperDeck {i+1}:"), i+2, 1)
            layout.addWidget(indicator, i+2, 2)
        
        self.setLayout(layout)
        
        # Initialize with default info
        self.update_info()
    
    def update_info(self):
        """Update connection info for all components"""
        import config
        
        # Update OSC info
        self.osc_info.setText(f"{config.DEFAULT_OSC_IP}:{config.DEFAULT_OSC_PORT}")
        
        # Update HyperDeck info from settings
        for i, info_label in enumerate(self.hyperdeck_infos):
            if i < len(config.HYPERDECK_DEVICES):
                device = config.HYPERDECK_DEVICES[i]
                info_label.setText(f"{device['ip']}:{device['port']}")
            else:
                info_label.setText("Not configured")

class RecordingControls(QGroupBox):
    start_recording = pyqtSignal()
    stop_recording = pyqtSignal()
    
    def __init__(self):
        super().__init__("Recording Controls")
        self.init_ui()
    
    def init_ui(self):
        layout = QHBoxLayout()
        
        self.start_btn = QPushButton("Start Recording")
        self.start_btn.setIcon(QIcon.fromTheme("media-record"))
        self.stop_btn = QPushButton("Stop Recording")
        self.stop_btn.setIcon(QIcon.fromTheme("media-playback-stop"))
        
        layout.addWidget(self.start_btn)
        layout.addWidget(self.stop_btn)
        
        self.setLayout(layout)
        
        # Connect signals
        self.start_btn.clicked.connect(self.start_recording)
        self.stop_btn.clicked.connect(self.stop_recording)

class DashboardPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
        # Configure logging
        self.logger = logging.getLogger('ShogunOSC')
        self.logger.setLevel(logging.INFO)
        
        # Add handler for the text widget
        self.log_handler = ColoredLogHandler(self)
        self.log_handler.setFormatter(logging.Formatter(config.LOG_FORMAT))
        self.logger.addHandler(self.log_handler)
    
    def write(self, message):
        """StreamHandler write method for logging"""
        if message.strip():  # Only add non-empty messages
            self.add_log_message(message.strip())
    
    def flush(self):
        """StreamHandler flush method for logging"""
        pass
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # System Status
        self.status_widget = SystemStatusWidget("System Status")
        layout.addWidget(self.status_widget)
        
        # Recording Controls
        self.recording_controls = RecordingControls()
        layout.addWidget(self.recording_controls)
        
        # Real-time Logs
        log_group = QGroupBox("System Logs")
        log_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        
        layout.addWidget(log_group)
        
        self.setLayout(layout)
    
    def update_status(self, component: str, status: bool):
        """Update status indicator for a specific component"""
        if component == "shogun":
            self.status_widget.shogun_indicator.set_status(status)
        elif component == "osc":
            self.status_widget.osc_indicator.set_status(status)
        elif component.startswith("hyperdeck"):
            try:
                index = int(component.split("_")[1]) - 1
                self.status_widget.hyperdeck_indicators[index].set_status(status)
            except (IndexError, ValueError):
                pass
    
    def add_log_message(self, message: str, level: str = 'INFO'):
        """Add a colored message to the log panel"""
        color = {
            'DEBUG': '#808080',    # Gray
            'INFO': '#000000',     # Black
            'WARNING': '#FFA500',  # Orange
            'ERROR': '#FF0000',    # Red
            'CRITICAL': '#8B0000'  # Dark Red
        }.get(level, '#000000')
        
        self.log_text.append(f'<span style="color: {color};">{message}</span>')
        # Auto-scroll to bottom
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )

class ColoredLogHandler(logging.StreamHandler):
    def emit(self, record):
        msg = self.format(record)
        self.stream.add_log_message(msg, record.levelname)
