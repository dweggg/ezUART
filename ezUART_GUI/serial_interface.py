import serial
import serial.tools.list_ports
import struct

class SerialInterface:
    def __init__(self):
        self.serial_port = None
        self.buffer = bytearray()  # Buffer to accumulate incoming bytes

    def list_ports(self):
        """List available USB-to-UART ports."""
        ports = [port.device for port in serial.tools.list_ports.comports()]
        usb_ports = [port for port in ports if "ttyUSB" in port or "ttyACM" in port]
        return usb_ports

    def connect(self, port, baudrate):
        """Connect to the specified serial port."""
        self.serial_port = serial.Serial(port, baudrate, timeout=1)

    def disconnect(self):
        """Disconnect from the serial port."""
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
            self.serial_port = None

    def is_connected(self):
        """Check if connected to the serial port."""
        return self.serial_port is not None and self.serial_port.is_open

    def read(self):
        """Read data directly from the serial port and decode packets in real time."""
        try:
            while self.is_connected():
                # Read one byte at a time
                byte = self.serial_port.read(1)
                if not byte:
                    continue  # No data read, try again

                # Look for start of frame (SOF)
                if byte == b'\xAA':
                    packet = byte  # Start new packet

                    # Read until end of frame (EOF)
                    while True:
                        next_byte = self.serial_port.read(1)
                        if not next_byte:
                            continue  # Continue waiting for more data

                        packet += next_byte

                        # Check for end of frame (EOF)
                        if next_byte == b'\x55':
                            # Process packet now
                            result = self.decode_packet(packet.hex())
                            return result

        except serial.SerialException as e:
            self.disconnect()
            return f"Serial exception occurred: {e}"
        except Exception as e:
            return f"An error occurred: {e}"

    def write(self, data):
        """Write data to the serial port."""
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.write(data)

    def decode_packet(self, hex_data):
        """Decode the received hex packet and extract variable ID and data."""
        packet = bytes.fromhex(hex_data)

        # Validate packet start and end
        if packet[0] != 0xAA or packet[-1] != 0x55:
            return "Invalid packet: does not start with 0xAA or end with 0x55."

        # Payload size is in bytes (1 byte)
        payload_size = packet[1]
        expected_length = payload_size + 2  # Payload size + start (1 byte) + end (1 byte)

        # Check if the packet length matches the expected length
        if len(packet) < expected_length:
            return f"Invalid packet length: expected {expected_length}, got {len(packet)}."

        index = 2  # Start after the payload size byte
        decoded_message = ""  # Initialize the decoded message string

        # Process packet based on new protocol
        while index < expected_length - 1:  # Avoid the last byte (EOF)
            if index >= len(packet):
                break

            var_id = packet[index]  # Get the variable ID
            index += 1

            # Decode data based on variable ID
            if var_id == 1 or var_id == 2 :  # Data ID specified in your example
                # Expecting a float value next
                data_value = struct.unpack('<f', packet[index:index + 4])[0]  # Little-endian float
                index += 4
                decoded_message += f"ID: {var_id} | Type: float | Value: {data_value:.6f}\n"
            else:
                decoded_message += f"ID: {var_id} | Type: Unknown | Value: N/A\n"

        return decoded_message
