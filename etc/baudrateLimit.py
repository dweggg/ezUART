from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QComboBox, QLineEdit, QPushButton,
    QSlider, QVBoxLayout, QHBoxLayout, QGridLayout, QProgressBar, QMessageBox
)
from PyQt6.QtCore import Qt
import sys

# Constants
COMMON_BAUD_RATES = [9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600]
VARIABLE_SIZE_BYTES = 4  # Size of one variable in bytes


class BandwidthApp(QWidget):
    def __init__(self):
        super().__init__()

        self.variables_slider = []
        self.frequencies_entry = []
        self.variable_value_labels = []
        self.frequency_value_labels = []

        self.number_of_different_frequencies = 3

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Baud Rate Bandwidth Assessment")

        layout = QVBoxLayout()

        # Baud Rate Dropdown
        baud_layout = QHBoxLayout()
        baud_layout.addWidget(QLabel("Baud Rate:"))
        self.baudrate_combo = QComboBox()
        self.baudrate_combo.addItems([str(rate) for rate in COMMON_BAUD_RATES])
        baud_layout.addWidget(self.baudrate_combo)
        layout.addLayout(baud_layout)

        # Number of Frequencies
        freq_layout = QHBoxLayout()
        freq_layout.addWidget(QLabel("Number of Frequencies:"))
        self.num_freq_entry = QLineEdit("3")
        freq_layout.addWidget(self.num_freq_entry)
        self.update_freq_button = QPushButton("Update Frequencies")
        self.update_freq_button.clicked.connect(self.update_frequency_sliders)
        freq_layout.addWidget(self.update_freq_button)
        layout.addLayout(freq_layout)

        # Sliders Frame
        self.sliders_layout = QGridLayout()
        layout.addLayout(self.sliders_layout)

        # Overhead Inputs
        overhead_layout = QHBoxLayout()
        self.overhead_var_entry = QLineEdit("0")
        self.overhead_speed_entry = QLineEdit("0")
        overhead_layout.addWidget(QLabel("Overhead per Variable:"))
        overhead_layout.addWidget(self.overhead_var_entry)
        overhead_layout.addWidget(QLabel("Overhead per Speed:"))
        overhead_layout.addWidget(self.overhead_speed_entry)
        layout.addLayout(overhead_layout)

        # Progress Bar
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        # Status Label
        self.status_label = QLabel("Bandwidth usage: 0%")
        layout.addWidget(self.status_label)

        # Update Button
        self.update_button = QPushButton("Update")
        self.update_button.clicked.connect(self.update_status)
        layout.addWidget(self.update_button)

        self.setLayout(layout)
        self.update_frequency_sliders()  # Initialize with 3

    def update_slider_values(self, index):
        self.variable_value_labels[index].setText(f"n_var: {self.variables_slider[index].value()}")
        self.frequency_value_labels[index].setText("Hz")

    def update_frequency_sliders(self):
        try:
            num_freqs = int(self.num_freq_entry.text())
            if num_freqs < 1:
                QMessageBox.critical(self, "Invalid Input", "Number of frequencies must be at least 1.")
                return

            self.number_of_different_frequencies = num_freqs

            # Clear layout
            while self.sliders_layout.count():
                child = self.sliders_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

            self.variables_slider.clear()
            self.frequencies_entry.clear()
            self.variable_value_labels.clear()
            self.frequency_value_labels.clear()

            for i in range(num_freqs):
                self.sliders_layout.addWidget(QLabel(f"Speed {i+1}:"), i, 0)

                freq_entry = QLineEdit("1000")
                self.frequencies_entry.append(freq_entry)
                self.sliders_layout.addWidget(freq_entry, i, 1)

                freq_label = QLabel("Hz")
                self.frequency_value_labels.append(freq_label)
                self.sliders_layout.addWidget(freq_label, i, 2)

                var_slider = QSlider(Qt.Orientation.Horizontal)
                var_slider.setMinimum(0)
                var_slider.setMaximum(100)
                var_slider.setValue(10)
                var_slider.setSingleStep(1)
                var_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
                var_slider.valueChanged.connect(lambda _, j=i: self.update_slider_values(j))
                self.variables_slider.append(var_slider)
                self.sliders_layout.addWidget(var_slider, i, 3)

                var_label = QLabel(f"n_var: {var_slider.value()}")
                self.variable_value_labels.append(var_label)
                self.sliders_layout.addWidget(var_label, i, 4)

        except ValueError:
            QMessageBox.critical(self, "Invalid Input", "Please enter a valid number of frequencies.")

    def calculate_bandwidth(self, baudrate, variables, frequencies, overhead_per_variable, overhead_per_speed):
        total_bytes_per_second = 0
        for i in range(len(frequencies)):
            variables_at_speed = variables[i]
            frequency = frequencies[i]
            overhead = overhead_per_speed + (overhead_per_variable * variables_at_speed)
            total_bytes_per_second += (variables_at_speed * VARIABLE_SIZE_BYTES + overhead) * frequency
        total_bits_per_second = total_bytes_per_second * 8
        bandwidth_percentage = (total_bits_per_second / baudrate) * 100
        return bandwidth_percentage, total_bits_per_second

    def update_status(self):
        try:
            baudrate = int(self.baudrate_combo.currentText())
            variables = [slider.value() for slider in self.variables_slider]
            frequencies = [int(entry.text()) for entry in self.frequencies_entry]
            overhead_var = int(self.overhead_var_entry.text())
            overhead_speed = int(self.overhead_speed_entry.text())

            percent, total_bps = self.calculate_bandwidth(
                baudrate, variables, frequencies, overhead_var, overhead_speed
            )

            self.progress_bar.setValue(min(int(percent), 100))

            if percent > 100:
                self.status_label.setText(
                    f"<span style='color:red;'>Bandwidth exceeded! ({percent:.2f}%)<br>Total bps: {total_bps}</span>"
                )
            else:
                self.status_label.setText(
                    f"<span style='color:green;'>Bandwidth usage: {percent:.2f}%<br>Total bps: {total_bps}</span>"
                )

        except ValueError:
            QMessageBox.critical(self, "Invalid Input", "Please enter valid numeric values.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BandwidthApp()
    window.resize(600, 400)
    window.show()
    sys.exit(app.exec())
