class HardwareConfig:
    def __init__(self):
        self.supported_hardware = {
            'STM32': {
                'baud_rates': [9600, 115200],
                'data_types': ['int', 'float', 'string']
            }
            # Add more hardware configurations as needed
        }

    def get_supported_hardware(self):
        return self.supported_hardware

    # Additional methods to manage hardware configurations can be added here.
