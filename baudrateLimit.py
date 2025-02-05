import tkinter as tk
from tkinter import ttk
from tkinter.messagebox import showerror

# Constants
COMMON_BAUD_RATES = [9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600]
VARIABLE_SIZE_BYTES = 4  # Size of one variable in bytes

# Global variables for sliders and labels
variables_slider = []
frequencies_entry = []
variable_value_labels = []
frequency_value_labels = []

# Function to calculate total bandwidth usage
def calculate_bandwidth(baudrate, variables, frequencies, overhead_per_variable, overhead_per_speed):
    total_bytes_per_second = 0
    for i in range(len(frequencies)):  # Loop through the variable number of frequencies
        variables_at_speed = variables[i]
        frequency = frequencies[i]
        overhead = overhead_per_speed + (overhead_per_variable * variables_at_speed)
        total_bytes_per_second += (variables_at_speed * VARIABLE_SIZE_BYTES + overhead) * frequency
    total_bits_per_second = total_bytes_per_second * 8
    bandwidth_percentage = (total_bits_per_second / baudrate) * 100
    return bandwidth_percentage, total_bits_per_second

# Update function for progress bar and status
def update_status():
    try:
        baudrate = int(baudrate_var.get())
        variables = [variables_slider[i].get() for i in range(number_of_different_frequencies)]
        frequencies = [int(frequencies_entry[i].get()) for i in range(number_of_different_frequencies)]
        overhead_per_variable = int(overhead_variable_entry.get())
        overhead_per_speed = int(overhead_speed_entry.get())

        bandwidth_percentage, total_bits_per_second = calculate_bandwidth(
            baudrate, variables, frequencies, overhead_per_variable, overhead_per_speed
        )

        # Update progress bar
        progress_bar["value"] = min(bandwidth_percentage, 100)

        # Update label
        if bandwidth_percentage > 100:
            status_label["text"] = (
                f"Bandwidth exceeded! ({bandwidth_percentage:.2f}%)\n"
                f"Total bps: {total_bits_per_second}"
            )
            status_label["foreground"] = "red"
        else:
            status_label["text"] = (
                f"Bandwidth usage: {bandwidth_percentage:.2f}%\n"
                f"Total bps: {total_bits_per_second}"
            )
            status_label["foreground"] = "green"
    except ValueError:
        showerror("Invalid Input", "Please enter valid numeric values.")

# Function to validate numeric input
def validate_input(P):
    return P.isdigit() or P == ""  # Only digits or empty string are allowed

# Function to update the value labels for sliders
def update_slider_values(i):
    variable_value_labels[i].config(text=f"n_var: {int(variables_slider[i].get())}")
    frequency_value_labels[i].config(text=f" Hz")

# Function to update sliders based on the number of frequencies
def update_frequency_sliders():
    global number_of_different_frequencies, variables_slider, frequencies_entry, variable_value_labels, frequency_value_labels
    try:
        number_of_different_frequencies = int(number_of_frequencies_entry.get())
        if number_of_different_frequencies < 1:
            showerror("Invalid Input", "Number of frequencies must be at least 1.")
            return

        # Clear previous sliders and labels
        for widget in sliders_frame.winfo_children():
            widget.grid_forget()

        variables_slider.clear()
        frequencies_entry.clear()
        variable_value_labels.clear()
        frequency_value_labels.clear()

        # Create sliders and labels for the new number of frequencies
        for i in range(number_of_different_frequencies):
            ttk.Label(sliders_frame, text=f"Speed {i + 1}:").grid(row=i, column=0, padx=5, pady=5)

            # Frequency Entry Box (Textbox)
            freq_entry = ttk.Entry(sliders_frame)
            freq_entry.insert(0, "1000")  # Default frequency value
            freq_entry.grid(row=i, column=1, padx=5, pady=5)
            frequencies_entry.append(freq_entry)
            freq_label = ttk.Label(sliders_frame, text=f" Hz")
            freq_label.grid(row=i, column=2)
            frequency_value_labels.append(freq_label)

            # Variables Slider (still using a scale here, since it's mentioned for "n_var")
            var_slider = ttk.Scale(sliders_frame, from_=0, to=100, orient="horizontal", length=200)
            var_slider.set(10)
            var_slider.grid(row=i, column=3, padx=5, pady=5)
            variables_slider.append(var_slider)
            var_label = ttk.Label(sliders_frame, text=f"n_var: {int(var_slider.get())}")
            var_label.grid(row=i, column=4)
            variable_value_labels.append(var_label)

            # Update function for each slider
            var_slider.config(command=lambda e, i=i: update_slider_values(i))
            freq_entry.bind("<KeyRelease>", lambda e, i=i: update_slider_values(i))  # Bind text change to update

    except ValueError:
        showerror("Invalid Input", "Please enter a valid number of frequencies.")

# GUI setup
root = tk.Tk()
root.title("Baud Rate Bandwidth Assessment")

# Baudrate Dropdown
baudrate_var = tk.StringVar(value=str(COMMON_BAUD_RATES[0]))
baudrate_label = ttk.Label(root, text="Baud Rate:")
baudrate_label.grid(row=0, column=0, padx=5, pady=5)
baudrate_dropdown = ttk.Combobox(root, textvariable=baudrate_var, values=COMMON_BAUD_RATES, state="readonly")
baudrate_dropdown.grid(row=0, column=1, padx=5, pady=5)

# Number of Frequencies Input and Update Button
number_of_frequencies_label = ttk.Label(root, text="Number of Frequencies:")
number_of_frequencies_label.grid(row=1, column=0, padx=5, pady=5)

number_of_frequencies_entry = ttk.Entry(root)
number_of_frequencies_entry.grid(row=1, column=1, padx=5, pady=5)
number_of_frequencies_entry.insert(0, "3")  # Default value of 3 frequencies

update_button = ttk.Button(root, text="Update Frequencies", command=update_frequency_sliders)
update_button.grid(row=1, column=2, padx=5, pady=5)

# Frame for sliders and labels
sliders_frame = ttk.Frame(root)
sliders_frame.grid(row=2, column=0, columnspan=3, padx=5, pady=5)

# Overhead per Variable Entry
overhead_variable_label = ttk.Label(root, text="Overhead per Variable:")
overhead_variable_label.grid(row=3, column=0, padx=5, pady=5)
overhead_variable_entry = ttk.Entry(root, validate="key", validatecommand=(root.register(validate_input), "%P"))
overhead_variable_entry.grid(row=3, column=1, padx=5, pady=5)
overhead_variable_entry.insert(0, "0")

# Overhead per Speed Entry
overhead_speed_label = ttk.Label(root, text="Overhead per Speed:")
overhead_speed_label.grid(row=3, column=2, padx=5, pady=5)
overhead_speed_entry = ttk.Entry(root, validate="key", validatecommand=(root.register(validate_input), "%P"))
overhead_speed_entry.grid(row=3, column=3, padx=5, pady=5)
overhead_speed_entry.insert(0, "0")

# Progress Bar
progress_bar = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate")
progress_bar.grid(row=4, column=0, columnspan=3, padx=10, pady=10)

# Status Label
status_label = ttk.Label(root, text="Bandwidth usage: 0%", font=("Arial", 12))
status_label.grid(row=5, column=0, columnspan=5, padx=10, pady=10)

# Update Button
update_button = ttk.Button(root, text="Update", command=update_status)
update_button.grid(row=6, column=0, columnspan=5, pady=10)

# Initialize with default 3 frequencies
number_of_different_frequencies = 3
update_frequency_sliders()

root.mainloop()
