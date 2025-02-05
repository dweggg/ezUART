import csv
import os

class Database:
    BAUD_RATES = {
        'slow': 115200,
        'fast': 115200,
        'very fast': 115200
    }

    def __init__(self, filename='variables.csv'):
        self.filename = filename
        self.variables = []
        self.load_variables()

    def add_variable(self, variable_name, baud_rate_name, data_type):
        # Ensure unique variable names
        if any(var[0] == variable_name for var in self.variables):
            print(f"Variable '{variable_name}' already exists.")
            return
        baud_rate = self.BAUD_RATES.get(baud_rate_name)
        if baud_rate is None:
            print(f"Invalid baud rate name: {baud_rate_name}")
            return
        self.variables.append((variable_name, baud_rate, data_type))

    def get_variables(self):
        return self.variables

    def save_variables(self):
        with open(self.filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['id', 'baud_rate', 'type'])  # Header row
            for var in self.variables:
                writer.writerow(var)

    def load_variables(self):
        if os.path.exists(self.filename):
            with open(self.filename, mode='r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    variable_name = row['id']
                    baud_rate = int(row['baud_rate'])
                    data_type = row['type']
                    self.variables.append((variable_name, baud_rate, data_type))

    # Additional methods to handle database operations can be added here.
