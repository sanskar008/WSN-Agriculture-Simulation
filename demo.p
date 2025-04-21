import sys
import random
import math
import csv
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, 
                            QDialog, QTextEdit, QDialogButtonBox, QLabel)
from PyQt6.QtGui import (QPainter, QColor, QPen, QFont, QImage, QBrush, QRadialGradient, 
                        QLinearGradient, QPainterPath, QPolygonF)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QPointF, QRectF

# Sensor Node class with LPWAN and adaptive duty cycle
class SensorNode:
    def __init__(self, id, x, y, data_type, battery=100.0, sensing_range=10.0, comm_range=1000.0):
        self.id = id
        self.x = x
        self.y = y
        self.battery = battery
        self.sensing_range = sensing_range
        self.comm_range = comm_range  # Increased for LPWAN
        self.active = True
        self.data_type = data_type
        self.data = {self.data_type: 0.0}
        self.energy_per_sense = 0.02  # Reduced for LPWAN
        self.energy_per_transmit = 0.05  # Reduced for LPWAN
        self.duty_cycle = 1.0  # Percentage of time active (1.0 = always active)
        self.sleep_time = 0  # Cycles to sleep
        self.last_value = None  # For data criticality
        self.critical_thresholds = {
            'moisture': (30, 70),  # Critical if <30% or >70%
            'temperature': (20, 30),  # Critical if <20°C or >30°C
            'humidity': (30, 70),  # Critical if <30% or >70%
            'light': (200, 800),  # Critical if <200 or >800 µmol/m²/s
            'ph': (6.0, 7.0)  # Critical if <6.0 or >7.0
        }

    def update_duty_cycle(self):
        # Adjust duty cycle based on battery and data criticality
        if self.battery <= 0:
            self.active = False
            self.duty_cycle = 0.0
            return
        # Battery-based adjustment
        if self.battery < 20:
            self.duty_cycle = 0.2  # Low battery: sense/transmit less often
        elif self.battery < 50:
            self.duty_cycle = 0.5
        else:
            self.duty_cycle = 1.0
        # Data criticality adjustment
        if self.last_value is not None:
            low, high = self.critical_thresholds[self.data_type]
            if self.last_value < low or self.last_value > high:
                self.duty_cycle = min(self.duty_cycle * 2, 1.0)  # Increase frequency for critical data

    def sense_environment(self):
        if not self.active or self.battery <= 0 or self.sleep_time > 0:
            self.active = False if self.battery <= 0 else self.active
            self.sleep_time -= 1 if self.sleep_time > 0 else 0
            return None
        if random.random() > self.duty_cycle:
            self.sleep_time = 1  # Skip this cycle
            return None
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
        self.last_value = list(self.data.values())[0]
        self.battery -= self.energy_per_sense
        self.update_duty_cycle()
        if self.battery <= 0:
            self.active = False
        return self.data

    def transmit_data(self, base_station):
        if not self.active or self.battery <= 0 or self.sleep_time > 0:
            self.active = False if self.battery <= 0 else self.active
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

    def receive_data(self, node_id, data, duty_cycle):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.colibrated_data.append({
            'node_id': node_id,
            'timestamp': timestamp,
            'data': data,
            'duty_cycle': duty_cycle
        })

# Field Canvas for visualizing nodes, base station, transmissions, and data
class FieldCanvas(QWidget):
    def __init__(self, nodes, base_station, field_size):
        super().__init__()
        self.nodes = nodes
        self.base_station = base_station
        self.field_width, self.field_height = field_size
        self.transmissions = []
        self.data_labels = []
        self.setFixedSize(500, 500)
        self.background_image = QImage("field2.png")
        self._node_opacity = 0
        self.fade_anim = QPropertyAnimation(self, b"node_opacity")
        self.fade_anim.setDuration(1000)
        self.fade_anim.setStartValue(0)
        self.fade_anim.setEndValue(255)
        self.fade_anim.start()
        self.base_pulse = 0
        self.pulse_timer = QTimer()
        self.pulse_timer.timeout.connect(self.update_base_pulse)
        self.pulse_timer.start(50)
        self.clear_timer = QTimer()
        self.clear_timer.timeout.connect(self.clear_transmissions_and_labels)

    def set_node_opacity(self, opacity):
        self._node_opacity = opacity
        self.update()

    def get_node_opacity(self):
        return self._node_opacity

    node_opacity = property(get_node_opacity, set_node_opacity)

    def update_base_pulse(self):
        self.base_pulse = (self.base_pulse + 5) % 360
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw background
        if not self.background_image.isNull():
            painter.drawImage(self.rect(), self.background_image.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            gradient = QRadialGradient(250, 250, 250)
            gradient.setColorAt(0, QColor(0, 100, 0))
            gradient.setColorAt(1, QColor(0, 50, 0))
            painter.fillRect(self.rect(), gradient)
        vignette = QRadialGradient(250, 250, 300)
        vignette.setColorAt(0, QColor(0, 0, 0, 0))
        vignette.setColorAt(1, QColor(0, 0, 0, 100))
        painter.fillRect(self.rect(), vignette)

        scale_x = self.width() / self.field_width
        scale_y = self.height() / self.field_height

        # Draw transmission lines
        for node_x, node_y, opacity in self.transmissions:
            start_x = node_x * scale_x
            start_y = node_y * scale_y
            end_x = self.base_station.x * scale_x
            end_y = self.base_station.y * scale_y
            gradient = QLinearGradient(start_x, start_y, end_x, end_y)
            gradient.setColorAt(0, QColor(0, 255, 0, opacity))
            gradient.setColorAt(1, QColor(0, 255, 255, opacity))
            painter.setPen(QPen(QBrush(gradient), 3, Qt.PenStyle.DashLine))
            painter.drawLine(int(start_x), int(start_y), int(end_x), int(end_y))

        # Draw base station
        bs_x = self.base_station.x * scale_x
        bs_y = self.base_station.y * scale_y
        hexagon = QPolygonF()
        for i in range(6):
            angle = 2 * math.pi * i / 6 + self.base_pulse / 180 * math.pi
            x = bs_x + 12 * math.cos(angle)
            y = bs_y + 12 * math.sin(angle)
            hexagon.append(QPointF(x, y))
        gradient = QRadialGradient(bs_x, bs_y, 15)
        gradient.setColorAt(0, QColor(0, 200, 255))
        gradient.setColorAt(1, QColor(0, 100, 200))
        painter.setBrush(gradient)
        painter.setPen(QPen(QColor(0, 255, 255, 200), 2))
        painter.drawPolygon(hexagon)
        glow = QRadialGradient(bs_x, bs_y, 20)
        glow.setColorAt(0, QColor(0, 255, 255, 100))
        glow.setColorAt(1, QColor(0, 255, 255, 0))
        painter.setBrush(glow)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(bs_x, bs_y), 20, 20)

        # Draw nodes
        for node in self.nodes:
            x = node.x * scale_x
            y = node.y * scale_y
            colors = {
                'moisture': (0, 150, 255),
                'temperature': (255, 100, 0),
                'humidity': (0, 200, 0),
                'light': (255, 255, 0),
                'ph': (200, 0, 200)
            }
            color = colors[node.data_type] if node.active and node.battery > 0 and node.sleep_time == 0 else (100, 100, 100)
            gradient = QRadialGradient(x, y, 8)
            gradient.setColorAt(0, QColor(*color, self._node_opacity))
            gradient.setColorAt(1, QColor(*color, int(self._node_opacity * 0.5)))
            painter.setBrush(gradient)
            painter.setPen(QPen(QColor(255, 255, 255, self._node_opacity), 1))
            painter.drawEllipse(QPointF(x, y), 8, 8)
            shadow = QRadialGradient(x + 2, y + 2, 10)
            shadow.setColorAt(0, QColor(0, 0, 0, 50))
            shadow.setColorAt(1, QColor(0, 0, 0, 0))
            painter.setBrush(shadow)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPointF(x + 2, y + 2), 10, 10)

        # Draw data labels
        painter.setFont(QFont("Roboto", 9, QFont.Weight.Bold))
        for x, y, text, opacity in self.data_labels:
            label_x = x * scale_x + 15
            label_y = y * scale_y - 30
            path = QPainterPath()
            rect = QRectF(label_x - 5, label_y - 35, 120, 70)
            path.addRoundedRect(rect, 10, 10)
            painter.setBrush(QBrush(QColor(255, 255, 255, 80)))
            painter.setPen(QPen(QColor(255, 255, 255, 150), 1))
            painter.drawPath(path)
            painter.setPen(QPen(QColor(255, 255, 255, opacity)))
            painter.drawText(rect.adjusted(8, 8, -8, -8), Qt.TextFlag.TextWordWrap, text)

        painter.end()

    def add_transmission_and_data(self, node_x, node_y, node_id, data, battery, data_type, duty_cycle):
        self.transmissions.append((node_x, node_y, 255))
        value = list(data.values())[0]
        unit = '%' if data_type in ['moisture', 'humidity'] else 'µmol/m²/s' if data_type == 'light' else '°C' if data_type == 'temperature' else ''
        icons = {
            'moisture': '💧 ',
            'temperature': '🌡️ ',
            'humidity': '💨 ',
            'light': '☀️ ',
            'ph': '🧪 '
        }
        text = (
            f"ID: {node_id}\n"
            f"{icons[data_type]}{data_type.capitalize()}: {value:.1f}{unit}\n"
            f"🔋 Battery: {battery:.1f}%\n"
            f"🔄 Duty Cycle: {duty_cycle*100:.0f}%"
        )
        self.data_labels.append((node_x, node_y, text, 255))
        self.update()
        self.clear_timer.start(1000)

    def clear_transmissions_and_labels(self):
        self.transmissions = []
        self.data_labels = []
        self.update()
        self.clear_timer.stop()

# Main Window for the WSN Simulator
class WSNMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WSN Agriculture Simulator with LPWAN")
        self.setFixedSize(600, 600)
        self.setStyleSheet("background-color: #1a1a1a;")

        self.field_size = (100, 100)
        self.nodes = []
        self.base_station = BaseStation(self.field_size[0] / 2, self.field_size[1] / 2)
        self.setup_nodes()
        self.cycle = 0
        self.max_cycles = 5

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)

        self.canvas = FieldCanvas(self.nodes, self.base_station, self.field_size)
        self.canvas.setStyleSheet("border-radius: 10px; overflow: hidden;")
        layout.addWidget(self.canvas)

        self.start_button = QPushButton("Start Simulation")
        self.start_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #00b4db, stop:1 #0083b0);
                color: white;
                font-family: Roboto;
                font-size: 16px;
                font-weight: bold;
                padding: 12px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #00d4fb, stop:1 #00a3d0);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0083b0, stop:1 #005370);
            }
        """)
        self.start_button.clicked.connect(self.start_simulation)
        layout.addWidget(self.start_button)

        self.status_label = QLabel("Click 'Start Simulation' to begin")
        self.status_label.setStyleSheet("""
            color: #ffffff;
            font-family: Roboto;
            font-size: 14px;
            padding: 10px;
            background: rgba(0, 0, 0, 50);
            border-radius: 5px;
            text-shadow: 0 0 5px rgba(0, 255, 255, 0.5);
        """)
        layout.addWidget(self.status_label)

        self.timer = QTimer()
        self.timer.timeout.connect(self.run_cycle)

    def setup_nodes(self):
        radius = 20
        num_nodes = 5
        node_configs = [
            {'id': 0, 'data_type': 'moisture'},
            {'id': 1, 'data_type': 'temperature'},
            {'id': 2, 'data_type': 'humidity'},
            {'id': 3, 'data_type': 'light'},
            {'id': 4, 'data_type': 'ph'},
        ]
        for i, config in enumerate(node_configs):
            angle = 2 * math.pi * i / num_nodes
            x = 50 + radius * math.cos(angle)
            y = 50 + radius * math.sin(angle)
            node = SensorNode(
                id=config['id'],
                x=x,
                y=y,
                data_type=config['data_type'],
                comm_range=1000.0  # LPWAN range
            )
            self.nodes.append(node)

    def start_simulation(self):
        self.start_button.setEnabled(False)
        self.status_label.setText("Simulation Running...")
        self.cycle = 0
        self.timer.start(2000)

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
            data = node.sense_environment()
            if data:
                active_nodes += 1
                if node.transmit_data(self.base_station):
                    self.base_station.receive_data(node.id, data, node.duty_cycle)
                    self.canvas.add_transmission_and_data(node.x, node.y, node.id, data, node.battery, node.data_type, node.duty_cycle)
                else:
                    self.status_label.setText(f"Node {node.id} failed to transmit")
        
        self.canvas.update()
        
        if active_nodes == 0:
            self.timer.stop()
            self.start_button.setEnabled(True)
            self.status_label.setText("All nodes depleted")
            self.show_summary()

    def show_summary(self):
        with open('wsn_data.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['NodeID', 'Timestamp', 'DataType', 'Value', 'Unit', 'DutyCycle'])
            for data in self.base_station.collected_data:
                data_type = list(data['data'].keys())[0]
                value = list(data['data'].values())[0]
                unit = '%' if data_type in ['moisture', 'humidity'] else 'µmol/m²/s' if data_type == 'light' else '°C' if data_type == 'temperature' else ''
                writer.writerow([data['node_id'], data['timestamp'], data_type.capitalize(), f"{value:.1f}", unit, f"{data['duty_cycle']*100:.0f}%"])

        dialog = QDialog(self)
        dialog.setWindowTitle("Simulation Summary")
        dialog.setFixedSize(400, 300)
        dialog.setStyleSheet("""
            background-color: #2a2a2a;
            color: #ffffff;
            font-family: Roboto;
            border-radius: 10px;
        """)
        layout = QVBoxLayout()

        text = QTextEdit()
        text.setReadOnly(True)
        text.setStyleSheet("""
            background-color: #3a3a3a;
            color: #ffffff;
            font-size: 14px;
            padding: 10px;
            border-radius: 5px;
            border: none;
        """)
        summary_text = (
            f"Total Data Points Collected: {len(self.base_station.collected_data)}\n"
            f"Dead Nodes: {sum(1 for node in self.nodes if not node.active)}/{len(self.nodes)}\n"
            f"Data saved to 'wsn_data.csv'\n\n"
            "Last 5 Data Points:\n"
        )
        for data in self.base_station.collected_data[-5:]:
            data_type = list(data['data'].keys())[0]
            value = list(data['data'].values())[0]
            unit = '%' if data_type in ['moisture', 'humidity'] else 'µmol/m²/s' if data_type == 'light' else '°C' if data_type == 'temperature' else ''
            summary_text += (
                f"Node {data['node_id']} at {data['timestamp']}:\n"
                f"  {data_type.capitalize()}: {value:.1f}{unit}\n"
                f"  Duty Cycle: {data['duty_cycle']*100:.0f}%\n"
            )
        text.setText(summary_text)
        layout.addWidget(text)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #00b4db, stop:1 #0083b0);
                color: white;
                font-family: Roboto;
                font-size: 14px;
                padding: 8px;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #00d4fb, stop:1 #00a3d0);
            }
        """)
        buttons.accepted.connect(dialog        layout.addWidget(buttons)

        dialog.setLayout(layout)
        dialog.exec()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = WSNMainWindow()
    window.show()
    sys.exit(app.exec())