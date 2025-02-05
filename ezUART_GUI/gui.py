from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import pyqtSignal
import pyqtgraph as pg
import qdarktheme  # Import the theme
from serial_interface import SerialInterface
from database import Database
import threading
import struct

class ezUARTApp(QtWidgets.QMainWindow):
    data_received_signal = pyqtSignal(str)  # Signal to emit received decoded data

    def __init__(self):
        super().__init__()
        self.setWindowTitle("ezUART - Serial Port GUI")
        self.setGeometry(100, 100, 1000, 600)
        qdarktheme.setup_theme()

        # Connect the data_received_signal to the slot to update the GUI
        self.data_received_signal.connect(self.update_serial_text_area)

        # Main widget and layout
        main_widget = QtWidgets.QWidget()
        self.setCentralWidget(main_widget)
        layout = QtWidgets.QVBoxLayout()
        main_widget.setLayout(layout)

        # Tab widget
        self.tabs = QtWidgets.QTabWidget()
        layout.addWidget(self.tabs)

        # Serial Interface and Database Editor tabs
        self.serial_tab = QtWidgets.QWidget()
        self.database_tab = QtWidgets.QWidget()
        self.tabs.addTab(self.serial_tab, "Serial Interface")
        self.tabs.addTab(self.database_tab, "Database Editor")

        # Initialize Serial Interface
        self.serial_interface = SerialInterface()
        self.init_serial_interface()

        # Initialize Database Editor
        self.database = Database()

        # Plotting related data
        self.plot_data_id1 = [0] * 100  # Store data for ID 1
        self.plot_data_id2 = [0] * 100  # Store data for ID 2

    def init_serial_interface(self):
        serial_layout = QtWidgets.QVBoxLayout(self.serial_tab)

        # Serial Port Settings
        port_frame = QtWidgets.QGroupBox("Serial Port Settings")
        serial_layout.addWidget(port_frame)
        port_layout = QtWidgets.QFormLayout(port_frame)

        self.port_combobox = QtWidgets.QComboBox()
        self.port_combobox.addItems(self.serial_interface.list_ports())
        self.baud_combobox = QtWidgets.QComboBox()
        self.baud_combobox.addItems(["slow", "fast", "very fast"])  # Updated baud rate options

        port_layout.addRow("Select Port:", self.port_combobox)
        port_layout.addRow("Baud Rate:", self.baud_combobox)

        # Connect button
        self.connect_button = QtWidgets.QPushButton("Connect")
        self.connect_button.clicked.connect(self.connect_serial)
        serial_layout.addWidget(self.connect_button)

        # Serial data display
        self.serial_text_area = QtWidgets.QTextEdit()
        self.serial_text_area.setReadOnly(True)
        serial_layout.addWidget(self.serial_text_area)

        # Send data
        self.send_entry = QtWidgets.QLineEdit()
        self.send_button = QtWidgets.QPushButton("Send")
        self.send_button.clicked.connect(self.send_data)
        serial_layout.addWidget(self.send_entry)
        serial_layout.addWidget(self.send_button)

        # Status Bar
        self.status_bar = QtWidgets.QLabel("Status: Disconnected")
        serial_layout.addWidget(self.status_bar)

        # Plot widget for live data
        self.plot_widget = pg.GraphicsLayoutWidget()
        self.plot_widget.setBackground('black')
        self.plot = self.plot_widget.addPlot(title="Real-Time Plot")
        self.curve_id1 = self.plot.plot(pen='y')  # Yellow for ID 1
        self.curve_id2 = self.plot.plot(pen='c')  # Cyan for ID 2
        self.plot.showGrid(x=True, y=True)
        self.plot.setLabel('left', 'Value')
        self.plot.setLabel('bottom', 'Time')
        serial_layout.addWidget(self.plot_widget)

        # Set up data for plotting
        self.plot_timer = QtCore.QTimer()
        self.plot_timer.timeout.connect(self.update_plot)
        self.plot_timer.start(100)

    def connect_serial(self):
        if self.serial_interface.is_connected():
            self.serial_interface.disconnect()
            self.connect_button.setText("Connect")
            self.status_bar.setText("Status: Disconnected")
        else:
            port = self.port_combobox.currentText()
            baudrate_name = self.baud_combobox.currentText()
            baudrate = Database.BAUD_RATES[baudrate_name]
            self.serial_interface.connect(port, baudrate)
            self.connect_button.setText("Disconnect")
            self.status_bar.setText(f"Status: Connected to {port} at {baudrate} baud")
            threading.Thread(target=self.read_serial, daemon=True).start()

    def read_serial(self):
        while self.serial_interface.is_connected():
            data = self.serial_interface.read()
            if data:
                self.data_received_signal.emit(data)  # Emit the decoded message

    def update_serial_text_area(self, text):
        """Update the serial text area in the main GUI thread."""
        self.serial_text_area.append(text)
        self.serial_text_area.moveCursor(QtGui.QTextCursor.End)
        
        # Attempt to extract value for plotting
        self.extract_and_plot_value(text)

    def extract_and_plot_value(self, decoded_message):
        """Extract values from the decoded message and update plot data for both IDs."""
        try:
            lines = decoded_message.strip().split("\n")
            for line in lines:
                if "ID: 1" in line:  # Check for ID 1
                    value_str = line.split("|")[-1].split(":")[-1].strip()
                    value = float(value_str)
                    self.update_plot_data(value, id=1)  # Update plot for ID 1
                elif "ID: 2" in line:  # Check for ID 2
                    value_str = line.split("|")[-1].split(":")[-1].strip()
                    value = float(value_str)
                    self.update_plot_data(value, id=2)  # Update plot for ID 2
        except (ValueError, IndexError) as e:
            print(f"Error extracting value: {e}")

    def update_plot_data(self, value, id):
        """Update the data for plotting, for a specific ID."""
        if id == 1:
            self.plot_data_id1.append(value)
            if len(self.plot_data_id1) > 100:
                self.plot_data_id1.pop(0)  # Keep the last 100 data points for ID 1
        elif id == 2:
            self.plot_data_id2.append(value)
            if len(self.plot_data_id2) > 100:
                self.plot_data_id2.pop(0)  # Keep the last 100 data points for ID 2

    def send_data(self):
        if self.serial_interface.is_connected():
            data = self.send_entry.text()
            self.serial_interface.write(data.encode('utf-8'))
            self.serial_text_area.append(f"Sent: {data}")
            self.send_entry.clear()

    def update_plot(self):
        """Update the plot with the latest data from both IDs."""
        if self.plot_data_id1:
            self.curve_id1.setData(self.plot_data_id1)  # Update the plot with data for ID 1
        if self.plot_data_id2:
            self.curve_id2.setData(self.plot_data_id2)  # Update the plot with data for ID 2
