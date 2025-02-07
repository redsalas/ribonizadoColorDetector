import os
import dotenv
import json
import tkinter as tk
from tkinter import ttk, colorchooser, messagebox

# Load environment variables
dotenv.load_dotenv()


class SettingsForm(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Propiedades")
        self.geometry("600x400")  # Increased width for color picker

        # Load settings
        self.tolerance, self.pin12data, self.pin16data = self.load_settings()

        # Tolerance Field
        tk.Label(self, text="Tolerancia:").pack()
        self.tolerance_var = tk.IntVar(value=self.tolerance)
        tk.Entry(self, textvariable=self.tolerance_var).pack()

        # Pin Selection Combo Box
        tk.Label(self, text="Selecciona tipo de cable:").pack()
        self.pin_option_var = tk.StringVar(value="12-Pin")
        self.pin_combobox = ttk.Combobox(self, textvariable=self.pin_option_var,
                                         values=["12-Pin", "16-Pin"])
        self.pin_combobox.pack()
        self.pin_combobox.bind("<<ComboboxSelected>>", self.update_pin_fields)

        # Frame for Pin Fields
        self.pin_frame = tk.Frame(self)
        self.pin_frame.pack()

        # Save Button
        self.save_button = tk.Button(self, text="Guardar Propiedades", command=self.save_settings)
        self.save_button.pack()

        # Status Label
        self.status_label = tk.Label(self, text="", fg="red")
        self.status_label.pack()

        # Initialize fields
        self.update_pin_fields()

    def load_settings(self):
        # Load settings from .env file
        tolerance = int(os.getenv("TOLERANCE", "0"))
        pin12data = json.loads(os.getenv("CABLE12PINS", "[]"))
        pin16data = json.loads(os.getenv("CABLE16PINS", "[]"))
        return tolerance, pin12data, pin16data

    def save_settings(self):
        # Save settings to .env file
        tolerance = self.tolerance_var.get()
        pin_data = []

        for entry, color in zip(self.pin_entries, self.pin_colors):
            pin_name = entry.get()
            pin_color = color["rgb"]
            pin_data.append([pin_name, pin_color])

        pin_data_str = json.dumps(pin_data)

        if self.pin_option_var.get() == "12-Pin":
            dotenv.set_key(".env", "CABLE12PINS", pin_data_str)
        else:
            dotenv.set_key(".env", "CABLE16PINS", pin_data_str)

        dotenv.set_key(".env", "TOLERANCE", str(tolerance))
        self.status_label.config(text="Cambios guardados exitosamente!", fg="green")

    def update_pin_fields(self, *args):
        # Update the number of fields dynamically based on selection
        for widget in self.pin_frame.winfo_children():
            widget.destroy()

        pin_count = 12 if self.pin_option_var.get() == "12-Pin" else 16
        pin_data = self.pin12data if pin_count == 12 else self.pin16data

        self.pin_entries = []
        self.pin_colors = []

        for i in range(pin_count):
            row, col = divmod(i, 2)  # Arrange fields in two columns
            label = tk.Label(self.pin_frame, text=f"Pin {i + 1}:")
            label.grid(row=row, column=col * 3, padx=5, pady=2)

            entry = tk.Entry(self.pin_frame)
            entry.insert(0, pin_data[i][0] if i < len(pin_data) else "")
            entry.grid(row=row, column=col * 3 + 1, padx=5, pady=2)
            self.pin_entries.append(entry)

            color_button = tk.Button(self.pin_frame, text="Pin Color",
                                     command=lambda idx=i: self.pick_color(idx))
            color_button.grid(row=row, column=col * 3 + 2, padx=5, pady=2)

            default_color = pin_data[i][1] if i < len(pin_data) else [255, 255, 255]
            self.pin_colors.append({"button": color_button, "rgb": default_color})
            color_button.config(bg=self.rgb_to_hex(default_color))

    def pick_color(self, idx):
        # Open a color picker and update the button color
        color_code = colorchooser.askcolor(title="Choose Color")[0]
        if color_code:
            rgb_color = [int(c) for c in color_code]
            self.pin_colors[idx]["rgb"] = rgb_color
            self.pin_colors[idx]["button"].config(bg=self.rgb_to_hex(rgb_color))

    @staticmethod
    def rgb_to_hex(rgb):
        # Convert an RGB tuple to a hex color string
        return "#%02x%02x%02x" % tuple(rgb)

# Open the settings form in a new window from another part of the application
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    settings_window = SettingsForm(root)
    settings_window.mainloop()