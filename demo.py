import sys
import random
import math
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, 
                            QDialog, QTextEdit, QDialogButtonBox, QLabel)
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QImage, QBrush
from PyQt6.QtCore import Qt, QTimer

# Sensor Node class
class SensorNode:
    def __init__(self, id, x, y, data_type, battery=100.0, sensing_range=10.0, comm_range=50.0):
        self.id = id
        self.x = x
        self.y = y
        self.battery = battery
        self.sensing_range = sensing_range
        self.comm_range = comm_range
        self.active = True
        self.data_type = data_type  # 'moisture', 'temperature', 'humidity', 'light', 'ph'
        self.data = {self.data_type: 0.0}
        self.energy_per_sense = 0.05
        self.energy_per_transmit = 0.1

    def sense_environment(self):
        if not self.active or self.battery <= 0:
            self.active = False
            return None
        # Generate data based on assigned type
        if self.data_type == 'moisture':
            self.data['moisture'] = random.uniform(20, 80)
        elif self.data_type == 'temperature':
            self.data['temperature'] = random.uniform(15, 35)
        elif self.data_type == 'humidity':
            self.data['humidity'] = random.uniform(20, 80)
        elif self.data_type == 'light':
            self.data['light'] = random.uniform(100, 1000)
        elif self.data_type == 'ph':
            self.data['ph'] = random.uniform(5.5, 7.5)
        self.battery -= self.energy_per_sense
        if self.battery <= 0:
            self.active = False
        return self.data

    def transmit_data(self, base_station):
        if not self.active or self.battery <= 0:
            self.active = False
            return False
        distance = math.sqrt((self.x - base_station.x)**2 + (self.y - base_station.y)**2)
        if distance <= self.comm_range:
            self.battery -= self.energy_per_transmit * (distance / self.comm_range)
            if self.battery <= 0:
                self.active = False
            return True
        return False

# Base Station class
class BaseStation:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.collected_data = []

    def receive_data(self, node_id, data):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.collected_data.append({
            'node_id': node_id,
            'timestamp': timestamp,
            'data': data
        })

# Field Canvas for visualizing nodes, base station, transmissions, and data
class FieldCanvas(QWidget):
    def __init__(self, nodes, base_station, field_size):
        super().__init__()
        self.nodes = nodes
        self.base_station = base_station
        self.field_width, self.field_height = field_size
        self.transmissions = []  # List of (node_x, node_y, opacity) for active transmissions
        self.data_labels = []  # List of (node_x, node_y, text) for data display
        self.setFixedSize(500, 500)
        # Load background image
        self.background_image = QImage("field2.jpg")
        # Timer to clear transmissions and data labels
        self.clear_timer = QTimer()
        self.clear_timer.timeout.connect(self.clear_transmissions_and_labels)
        # Timer for pulsing effect
        self.pulse_timer = QTimer()
        self.pulse_timer.timeout.connect(self.update_pulse)
        self.pulse_opacity = 255  # Initial opacity for pulsing

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw background image, scaled to canvas size
        if not self.background_image.isNull():
            painter.drawImage(self.rect(), self.background_image.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            painter.fillRect(self.rect(), QColor(0, 128, 0))  # Fallback green background

        # Scale coordinates to fit canvas
        scale_x = self.width() / self.field_width
        scale_y = self.height() / self.field_height

        # Draw transmission lines
        for node_x, node_y, opacity in self.transmissions:
            painter.setPen(QPen(QColor(0, 255, 0, opacity), 4, Qt.PenStyle.SolidLine))
            start_x = node_x * scale_x
            start_y = node_y * scale_y
            end_x = self.base_station.x * scale_x
            end_y = self.base_station.y * scale_y
            painter.drawLine(int(start_x), int(start_y), int(end_x), int(end_y))

        # Draw base station (blue square)
        painter.setPen(QPen(Qt.GlobalColor.black, 2))
        painter.setBrush(QColor(0, 0, 255))
        bs_x = self.base_station.x * scale_x
        bs_y = self.base_station.y * scale_y
        painter.drawRect(int(bs_x - 10), int(bs_y - 10), 20, 20)

        # Draw nodes
        for node in self.nodes:
            x = node.x * scale_x
            y = node.y * scale_y
            if node.active and node.battery > 0:
                painter.setBrush(QColor(255, 255, 0))  # Yellow for active
            else:
                painter.setBrush(QColor(255, 0, 0))  # Red for dead
            painter.drawEllipse(int(x - 5), int(y - 5), 10, 10)

        # Draw data labels to the right of nodes
        painter.setFont(QFont("Arial", 8))
        for x, y, text in self.data_labels:
            label_x = x * scale_x + 15  # Position tightly to the right of node
            label_y = y * scale_y - 20  # Align vertically with node, slightly above center
            # Draw semi-transparent background for text
            text_rect = painter.boundingRect(int(label_x), int(label_y - 30), 80, 50, Qt.TextFlag.TextWordWrap, text)
            painter.setBrush(QBrush(QColor(0, 0, 0, 150)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(text_rect.adjusted(-3, -3, 3, 3))  # Compact background
            # Draw text
            painter.setPen(QPen(QColor(255, 255, 255)))
            painter.drawText(text_rect, Qt.TextFlag.TextWordWrap, text)

        painter.end()

    def add_transmission_and_data(self, node_x, node_y, node_id, data, battery, data_type):
        # Add transmission line with initial opacity
        self.transmissions.append((node_x, node_y, 255))
        # Add data label
        value = list(data.values())[0]
        unit = '%' if data_type in ['moisture', 'humidity'] else 'µmol/m²/s' if data_type == 'light' else '°C' if data_type == 'temperature' else ''
        text = (
            f"ID: {node_id}\n"
            f"{data_type.capitalize()}: {value:.1f}{unit}\n"
            f"B: {battery:.1f}%"
        )
        self.data_labels.append((node_x, node_y, text))
        self.update()
        # Start timers
        self.clear_timer.start(1000)  # Clear after 1 second
        self.pulse_timer.start(100)   # Pulse every 100ms

    def update_pulse(self):
        # Update opacity for pulsing effect
        self.pulse_opacity = 255 if self.pulse_opacity < 100 else self.pulse_opacity - 50
        self.transmissions = [(x, y, self.pulse_opacity) for x, y, _ in self.transmissions]
        self.update()

    def clear_transmissions_and_labels(self):
        self.transmissions = []
        self.data_labels = []
        self.pulse_opacity = 255
        self.update()
        self.clear_timer.stop()
        self.pulse_timer.stop()

# Main Window for the WSN Simulator
class WSNMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WSN Agriculture Simulator")
        self.setFixedSize(600, 600)

        # Initialize simulator
        self.field_size = (100, 100)
        self.nodes = []
        self.base_station = BaseStation(self.field_size[0] / 2, self.field_size[1] / 2)
        self.setup_nodes()
        self.cycle = 0
        self.max_cycles = 5

        # GUI setup
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Canvas
        self.canvas = FieldCanvas(self.nodes, self.base_station, self.field_size)
        layout.addWidget(self.canvas)

        # Start button
        self.start_button = QPushButton("Start Simulation")
        self.start_button.clicked.connect(self.start_simulation)
        self.start_button.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px; font-size: 16px;")
        layout.addWidget(self.start_button)

        # Status label
        self.status_label = QLabel("Click 'Start Simulation' to begin")
        self.status_label.setStyleSheet("font-size: 14px; padding: 10px;")
        layout.addWidget(self.status_label)

        # Timer for simulation cycles
        self.timer = QTimer()
        self.timer.timeout.connect(self.run_cycle)

    def setup_nodes(self):
        # Fixed 5 nodes in a star topology around base station at (50, 50)
        radius = 20  # Distance from base station
        num_nodes = 5
        node_configs = [
            {'id': 0, 'data_type': 'moisture'},   # Soil Moisture
            {'id': 1, 'data_type': 'temperature'}, # Temperature
            {'id': 2, 'data_type': 'humidity'},   # Humidity
            {'id': 3, 'data_type': 'light'},      # Light Intensity
            {'id': 4, 'data_type': 'ph'},         # Soil pH
        ]
        for i, config in enumerate(node_configs):
            # Calculate position in a circular pattern
            angle = 2 * math.pi * i / num_nodes  # Evenly spaced angles
            x = 50 + radius * math.cos(angle)
            y = 50 + radius * math.sin(angle)
            node = SensorNode(
                id=config['id'],
                x=x,
                y=y,
                data_type=config['data_type'],
                comm_range=50.0  # Ensure all nodes are within range
            )
            self.nodes.append(node)

    def start_simulation(self):
        self.start_button.setEnabled(False)
        self.status_label.setText("Simulation Running...")
        self.cycle = 0
        self.timer.start(2000)  # Run every 2 seconds

    def run_cycle(self):
        self.cycle += 1
        if self.cycle > self.max_cycles:
            self.timer.stop()
            self.start_button.setEnabled(True)
            self.status_label.setText("Simulation Completed")
            self.show_summary()
            return

        active_nodes = 0
        self.status_label.setText(f"Cycle {self.cycle}/{self.max_cycles}")
        
        for node in self.nodes:
            if not node.active:
                continue
            # Sense environment
            data = node.sense_environment()
            if data:
                active_nodes += 1
                if node.transmit_data(self.base_station):
                    self.base_station.receive_data(node.id, data)
                    # Show transmission and data on canvas
                    self.canvas.add_transmission_and_data(node.x, node.y, node.id, data, node.battery, node.data_type)
                else:
                    self.status_label.setText(f"Node {node.id} failed to transmit")
        
        # Update canvas
        self.canvas.update()
        
        if active_nodes == 0:
            self.timer.stop()
            self.start_button.setEnabled(True)
            self.status_label.setText("All nodes depleted")
            self.show_summary()

    def show_summary(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Simulation Summary")
        dialog.setFixedSize(400, 300)
        layout = QVBoxLayout()

        text = QTextEdit()
        text.setReadOnly(True)
        text.setStyleSheet("background-color: #f0f0f0; font-size: 14px; padding: 10px;")
        summary_text = (
            f"Total Data Points Collected: {len(self.base_station.collected_data)}\n"
            f"Dead Nodes: {sum(1 for node in self.nodes if not node.active)}/{len(self.nodes)}\n\n"
            "Last 5 Data Points:\n"
        )
        for data in self.base_station.collected_data[-5:]:
            data_type = list(data['data'].keys())[0]
            value = list(data['data'].values())[0]
            unit = '%' if data_type in ['moisture', 'humidity'] else 'µmol/m²/s' if data_type == 'light' else '°C' if data_type == 'temperature' else ''
            summary_text += (
                f"Node {data['node_id']} at {data['timestamp']}:\n"
                f"  {data_type.capitalize()}: {value:.1f}{unit}\n"
            )
        text.setText(summary_text)
        layout.addWidget(text)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(dialog.accept)
        layout.addWidget(buttons)

        dialog.setLayout(layout)
        dialog.exec()

# Run the application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WSNMainWindow()
    window.show()
    sys.exit(app.exec())