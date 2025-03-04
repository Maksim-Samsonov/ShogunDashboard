"""
Unified settings panel for managing all device configurations and application settings.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
                           QLabel, QPushButton, QLineEdit, QGroupBox, 
                           QFormLayout, QSpinBox, QComboBox, QCheckBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon

class DeviceDiscovery(QWidget):
    device_found = pyqtSignal(str, str)  # ip, device_type
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Manual IP input
        ip_group = QGroupBox("Manual IP Input")
        ip_layout = QHBoxLayout()
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("Enter IP address")
        self.add_ip_btn = QPushButton("Add Device")
        ip_layout.addWidget(self.ip_input)
        ip_layout.addWidget(self.add_ip_btn)
        ip_group.setLayout(ip_layout)
        
        # Auto discovery
        scan_group = QGroupBox("Network Scan")
        scan_layout = QVBoxLayout()
        self.scan_btn = QPushButton("Scan Network")
        self.scan_status = QLabel("Ready")
        scan_layout.addWidget(self.scan_btn)
        scan_layout.addWidget(self.scan_status)
        scan_group.setLayout(scan_layout)
        
        layout.addWidget(ip_group)
        layout.addWidget(scan_group)
        layout.addStretch()
        
        self.setLayout(layout)
        
        # Connect signals
        self.scan_btn.clicked.connect(self.start_network_scan)
        self.add_ip_btn.clicked.connect(self.add_manual_ip)
    
    def start_network_scan(self):
        self.scan_status.setText("Scanning...")
        # Network scanning logic will be implemented here
    
    def add_manual_ip(self):
        ip = self.ip_input.text()
        if ip:
            self.device_found.emit(ip, "unknown")

class SettingsPanel(QWidget):
    settings_changed = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Create tabs for different settings categories
        tabs = QTabWidget()
        
        # OSC Settings
        osc_tab = QWidget()
        osc_layout = QVBoxLayout()
        
        # Server settings
        server_group = QGroupBox("OSC Server Settings")
        server_form = QFormLayout()
        
        self.osc_listen_ip = QLineEdit()
        self.osc_listen_port = QSpinBox()
        self.osc_listen_port.setRange(1024, 65535)
        
        self.osc_broadcast_ip = QLineEdit()
        self.osc_broadcast_port = QSpinBox()
        self.osc_broadcast_port.setRange(1024, 65535)
        
        server_form.addRow("Listen IP:", self.osc_listen_ip)
        server_form.addRow("Listen Port:", self.osc_listen_port)
        server_form.addRow("Broadcast IP:", self.osc_broadcast_ip)
        server_form.addRow("Broadcast Port:", self.osc_broadcast_port)
        
        server_group.setLayout(server_form)
        osc_layout.addWidget(server_group)
        
        # OSC Commands
        commands_group = QGroupBox("OSC Commands")
        commands_form = QFormLayout()
        
        commands = [
            ("Start All Recording", "Start All Recording"),
            ("Stop All Recording", "Stop All Recording"),
            ("Start Shogun Recording", "Start Shogun Recording"),
            ("Stop Shogun Recording", "Stop Shogun Recording"),
            ("Start HyperDeck Recording", "Start HyperDeck Recording"),
            ("Stop HyperDeck Recording", "Stop HyperDeck Recording")
        ]
        
        for label, command in commands:
            commands_form.addRow(f"{label}:", QLabel(command))
        
        commands_group.setLayout(commands_form)
        osc_layout.addWidget(commands_group)
        
        # Server control
        control_group = QGroupBox("Server Control")
        control_layout = QHBoxLayout()
        self.restart_osc_btn = QPushButton("Restart OSC Server")
        control_layout.addWidget(self.restart_osc_btn)
        control_group.setLayout(control_layout)
        osc_layout.addWidget(control_group)
        
        osc_tab.setLayout(osc_layout)
        
        # HyperDeck Settings
        hyperdeck_tab = QWidget()
        hyperdeck_layout = QVBoxLayout()
        
        # Enable/Disable HyperDeck support
        self.hyperdeck_enabled = QCheckBox("Enable HyperDeck Support")
        hyperdeck_layout.addWidget(self.hyperdeck_enabled)
        
        # HyperDeck devices
        devices_group = QGroupBox("HyperDeck Devices")
        devices_layout = QVBoxLayout()
        
        self.hyperdeck_devices = []
        for i in range(3):
            device_group = QGroupBox(f"HyperDeck {i+1}")
            device_form = QFormLayout()
            
            enabled = QCheckBox("Enabled")
            ip = QLineEdit()
            port = QSpinBox()
            port.setRange(1, 65535)
            
            device_form.addRow("", enabled)
            device_form.addRow("IP:", ip)
            device_form.addRow("Port:", port)
            
            device_group.setLayout(device_form)
            devices_layout.addWidget(device_group)
            
            self.hyperdeck_devices.append({
                'enabled': enabled,
                'ip': ip,
                'port': port
            })
        
        devices_group.setLayout(devices_layout)
        hyperdeck_layout.addWidget(devices_group)
        
        # Sync settings
        sync_group = QGroupBox("Recording Sync")
        sync_layout = QVBoxLayout()
        self.sync_with_shogun = QCheckBox("Sync recording with Shogun")
        sync_layout.addWidget(self.sync_with_shogun)
        sync_group.setLayout(sync_layout)
        hyperdeck_layout.addWidget(sync_group)
        
        hyperdeck_tab.setLayout(hyperdeck_layout)
        
        # Add all tabs
        tabs.addTab(osc_tab, "OSC Server")
        tabs.addTab(hyperdeck_tab, "HyperDeck")
        
        layout.addWidget(tabs)
        
        # Save/Apply buttons
        button_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save Settings")
        self.apply_btn = QPushButton("Apply")
        
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.apply_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Connect signals
        self.save_btn.clicked.connect(self.save_settings)
        self.apply_btn.clicked.connect(self.apply_settings)
        self.restart_osc_btn.clicked.connect(self.restart_osc_server)
    
    def load_settings(self):
        """Load settings from config"""
        # OSC Settings
        self.osc_listen_ip.setText("127.0.0.1")
        self.osc_listen_port.setValue(8000)
        self.osc_broadcast_ip.setText("127.0.0.1")
        self.osc_broadcast_port.setValue(8000)
        
        # HyperDeck Settings
        self.hyperdeck_enabled.setChecked(True)
        self.sync_with_shogun.setChecked(True)
        
        for i, device in enumerate([{'enabled': True, 'ip': '10.0.0.51', 'port': 9999}, {'enabled': True, 'ip': '10.0.0.52', 'port': 9999}, {'enabled': True, 'ip': '10.0.0.53', 'port': 9999}]):
            if i < len(self.hyperdeck_devices):
                self.hyperdeck_devices[i]['enabled'].setChecked(device['enabled'])
                self.hyperdeck_devices[i]['ip'].setText(device['ip'])
                self.hyperdeck_devices[i]['port'].setValue(device['port'])
    
    def get_current_settings(self):
        """Get current settings as dictionary"""
        settings = {
            'osc_ip': self.osc_listen_ip.text(),
            'osc_port': self.osc_listen_port.value(),
            'osc_broadcast_ip': self.osc_broadcast_ip.text(),
            'osc_broadcast_port': self.osc_broadcast_port.value(),
            'hyperdeck_enabled': self.hyperdeck_enabled.isChecked(),
            'hyperdeck_sync_with_shogun': self.sync_with_shogun.isChecked(),
            'hyperdeck_devices': []
        }
        
        for device in self.hyperdeck_devices:
            settings['hyperdeck_devices'].append({
                'enabled': device['enabled'].isChecked(),
                'ip': device['ip'].text(),
                'port': device['port'].value()
            })
        
        return settings
    
    def save_settings(self):
        """Save settings and emit signal"""
        settings = self.get_current_settings()
        self.settings_changed.emit(settings)
    
    def apply_settings(self):
        """Apply settings without saving"""
        settings = self.get_current_settings()
        self.settings_changed.emit(settings)
    
    def restart_osc_server(self):
        """Signal to restart the OSC server"""
        settings = self.get_current_settings()
        settings['restart_osc'] = True
        self.settings_changed.emit(settings)
