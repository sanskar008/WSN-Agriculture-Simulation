import sys
import csv
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QMessageBox)
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import Qt

class FieldReadingsWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FieldSense: Latest Field Readings")
        self.setFixedSize(400, 500)
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                                          stop:0 #e6f3e6, stop:1 #b3d9b3);
            }
        """)

        # Central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Header
        header_label = QLabel("Latest Field Conditions")
        header_label.setFont(QFont("Roboto", 18, QFont.Weight.Bold))
        header_label.setStyleSheet("""
            color: #2e7d32;
            padding: 10px;
            background: rgba(255, 255, 255, 0.7);
            border-radius: 8px;
            text-align: center;
        """)
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(header_label)

        # Data display layout
        self.data_labels = {}
        data_types = [
            ('Temperature', '🌡️', '°C'),
            ('Moisture', '💧', '%'),
            ('Humidity', '💨', '%'),
            ('Light', '☀️', 'µmol/m²/s'),
            ('Ph', '🧪', '')
        ]

        for data_type, icon, unit in data_types:
            row_layout = QHBoxLayout()
            row_layout.setSpacing(10)

            # Icon
            icon_label = QLabel(icon)
            icon_label.setFont(QFont("Roboto", 16))
            icon_label.setStyleSheet("padding: 5px;")
            row_layout.addWidget(icon_label)

            # Label and value
            label = QLabel(f"{data_type}:")
            label.setFont(QFont("Roboto", 14, QFont.Weight.Medium))
            label.setStyleSheet("color: #1a3c34; width: 100px;")
            row_layout.addWidget(label)

            value_label = QLabel("N/A")
            value_label.setFont(QFont("Roboto", 14))
            value_label.setStyleSheet("""
                color: #d81b60;
                background: rgba(255, 255, 255, 0.8);
                padding: 5px;
                border-radius: 5px;
                min-width: 80px;
            """)
            row_layout.addWidget(value_label)
            self.data_labels[data_type.lower()] = value_label

            # Unit
            unit_label = QLabel(unit)
            unit_label.setFont(QFont("Roboto", 12))
            unit_label.setStyleSheet("color: #1a3c34;")
            row_layout.addWidget(unit_label)

            row_layout.addStretch()
            main_layout.addLayout(row_layout)

        # Timestamp
        timestamp_layout = QHBoxLayout()
        timestamp_label = QLabel("Last Updated:")
        timestamp_label.setFont(QFont("Roboto", 12, QFont.Weight.Medium))
        timestamp_label.setStyleSheet("color: #1a3c34;")
        timestamp_layout.addWidget(timestamp_label)

        self.timestamp_value = QLabel("N/A")
        self.timestamp_value.setFont(QFont("Roboto", 12))
        self.timestamp_value.setStyleSheet("color: #d81b60;")
        timestamp_layout.addWidget(self.timestamp_value)
        timestamp_layout.addStretch()
        main_layout.addLayout(timestamp_layout)

        # Refresh button
        refresh_button = QPushButton("Refresh Data")
        refresh_button.setFont(QFont("Roboto", 14, QFont.Weight.Bold))
        refresh_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                                          stop:0 #4caf50, stop:1 #388e3c);
                color: white;
                padding: 10px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                                          stop:0 #66bb6a, stop:1 #4caf50);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                                          stop:0 #388e3c, stop:1 #2e7d32);
            }
        """)
        refresh_button.clicked.connect(self.load_csv_data)
        main_layout.addWidget(refresh_button)

        main_layout.addStretch()

        # Load initial data
        self.load_csv_data()

    def load_csv_data(self):
        try:
            with open('wsn_data.csv', 'r', newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                rows = list(reader)
                if not rows:
                    QMessageBox.warning(self, "No Data", "The CSV file is empty.")
                    return

                # Find the latest row based on timestamp
                latest_row = max(rows, key=lambda x: datetime.strptime(x['Timestamp'], "%Y-%m-%d %H:%M:%S"))

                # Update labels
                for data_type in ['temperature', 'moisture', 'humidity', 'light', 'ph']:
                    value = latest_row[data_type.capitalize()]
                    self.data_labels[data_type].setText(value if value != 'N/A' else 'N/A')

                # Update timestamp
                self.timestamp_value.setText(latest_row['Timestamp'])

        except FileNotFoundError:
            QMessageBox.critical(self, "Error", "wsn_data.csv not found in the current directory.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load CSV: {str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = FieldReadingsWindow()
    window.show()
    sys.exit(app.exec())