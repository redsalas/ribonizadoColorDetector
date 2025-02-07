import cv2
import tkinter as tk
import sys
from tkinter import ttk
from PIL import Image, ImageTk
import numpy as np
import threading
import os
import json
from dotenv import load_dotenv
import shutil
import subprocess
from tkinter import filedialog, messagebox

from settings import SettingsForm

# Global variables
cap = None
current_colors = []
current_roi = []
CABLE12PINS = []
CABLE12ROI = []
CABLE16PINS = []
CABLE16ROI = []
color_labels = []
camera_running = True
TOLERANCE = 10  # Default tolerance in case .env is not loaded properly


def reload_configuration():
    # Reloads configuration from .env and updates global variables.
    global current_colors, current_roi, TOLERANCE, CABLE12PINS, CABLE12ROI, CABLE16PINS, CABLE16ROI

    # Reload environment variables
    load_dotenv(override=True)

    # Read from .env
    cable12pins_str = os.getenv("CABLE12PINS", "[]")
    cable12roi_str = os.getenv("CABLE12ROI", "[]")
    cable16pins_str = os.getenv("CABLE16PINS", "[]")
    cable16roi_str = os.getenv("CABLE16ROI", "[]")
    TOLERANCE = int(os.getenv("TOLERANCE", "10"))  # Default to 10 if not found

    # Convert JSON strings to Python lists
    CABLE12PINS = json.loads(cable12pins_str)
    CABLE12ROI = json.loads(cable12roi_str)
    CABLE16PINS = json.loads(cable16pins_str)
    CABLE16ROI = json.loads(cable16roi_str)

    print("Configuration reloaded successfully!")

    # Update the UI with new color labels
    update_color_list("12pins")  # Default to 12-pin mode after reloading

# Function to get the dominant color in an ROI
def get_dominant_color(frame, roi):
    x, y, w, h = roi
    roi_frame = frame[y:y+h, x:x+w]  # Extract the ROI
    avg_color = np.mean(roi_frame, axis=(0, 1)).astype(np.uint8)  # Calculate the average color
    return avg_color  # Returns [B, G, R]


# Function to check if a color is within tolerance range
def detect_color(frame, expected_color, roi):
    global TOLERANCE
    dominant_color = get_dominant_color(frame, roi)
    print("expected color: ", expected_color)
    print("dominant_color: ", dominant_color)

    # Convert to NumPy arrays for easier computation
    dominant_color = np.array(dominant_color, dtype=np.int16)
    expected_color = np.array(expected_color, dtype=np.int16)

    # Compute absolute difference per channel (B, G, R)
    diff = np.abs(dominant_color - expected_color)

    # Check if all channels are within tolerance range
    return np.all(diff <= TOLERANCE)

# Function to update the camera feed and color detection
def update_frame():
    global cap, current_colors, current_roi
    if cap is not None and cap.isOpened():
        ret, frame = cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (640, 480))
            img = ImageTk.PhotoImage(image=Image.fromarray(frame))
            camera_label.config(image=img)
            camera_label.image = img

            # Detect colors in each ROI and compare with expected colors
            all_green = True  # Assume all pins are green initially
            for i, (pin_name, expected_color) in enumerate(current_colors):
                if i < len(current_roi):  # Ensure we don't exceed the number of ROIs
                    roi = current_roi[i][1]  # Get the ROI for this pin
                    if detect_color(frame, expected_color, roi):
                        color_labels[i].config(image=green_icon, fg="green")
                    else:
                        color_labels[i].config(image=red_icon, fg="red")
                        all_green = False  # At least one pin is not green

                    # Draw the ROI on the frame for visualization
                    x, y, w, h = roi
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    cv2.putText(frame, pin_name, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

            # Update the result label based on whether all pins are green
            if all_green:
                result_label.config(text="Result: OK", fg="green")
            else:
                result_label.config(text="Result: NOT OK", fg="red")

    if camera_running:
        camera_label.after(10, update_frame)

# Function to handle properties option (placeholder)
def show_properties():
    settings_window = SettingsForm(root)

# Function to export the .env file properties
def export_env_file():
    # Exports the .env file as properties.env to a user-specified location.
    source_file = ".env"  # The original .env file
    destination_path = filedialog.asksaveasfilename(
        defaultextension=".env",
        filetypes=[("Environment File", "*.env")],
        initialfile="properties.env",
        title="Save .env File As"
    )

    if destination_path:  # Check if the user selected a location
        shutil.copy(source_file, destination_path)
        print(f".env file exported successfully to {destination_path}")

# Function to import a .env file properties
def import_env_file():
    # Imports a new .env file, overwrites the current .env file, and reloads the app.
    file_path = filedialog.askopenfilename(
        filetypes=[("Environment File", "*.env")],
        title="Select an .env File to Import"
    )

    if file_path:  # If the user selected a file
        try:
            shutil.copy(file_path, ".env")  # Overwrite the current .env file
            messagebox.showinfo("Success", "Configuration imported successfully. Restart the application to see the new configuration.")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to import configuration: {str(e)}")

# Function to run the color or ROI detector module in a separate thread
def run_roi_detector_12():
    global cap

    # Release the camera in the main application
    if cap is not None:
        cap.release()
        cap = None

    # Start the color detector in a separate thread
    def target():
        import roi_detector_12pin  # Import the color detector module
        roi_detector_12pin  # Call the main function of the color detector module

        # Reinitialize the camera in the main application after the detector is closed
        global cap
        if cap is None:
            cap = cv2.VideoCapture(0)

    detector_thread = threading.Thread(target=target)
    detector_thread.daemon = True  # Daemonize the thread so it exits when the main program exits
    detector_thread.start()

def run_roi_detector_16():
    global cap

    # Release the camera in the main application
    if cap is not None:
        cap.release()
        cap = None

    # Start the color detector in a separate thread
    def target():
        import roi_detector_16pin  # Import the color detector module
        roi_detector_16pin  # Call the main function of the color detector module

        # Reinitialize the camera in the main application after the detector is closed
        global cap
        if cap is None:
            cap = cv2.VideoCapture(0)

    detector_thread = threading.Thread(target=target)
    detector_thread.daemon = True  # Daemonize the thread so it exits when the main program exits
    detector_thread.start()

def run_color_detector_12():
    global cap

    # Release the camera in the main application
    if cap is not None:
        cap.release()
        cap = None

    # Start the color detector in a separate thread
    def target():
        import color_detector_12pin  # Import the color detector module
        color_detector_12pin  # Call the main function of the color detector module

        # Reinitialize the camera in the main application after the detector is closed
        global cap
        if cap is None:
            cap = cv2.VideoCapture(0)

    detector_thread = threading.Thread(target=target)
    detector_thread.daemon = True  # Daemonize the thread so it exits when the main program exits
    detector_thread.start()

def run_color_detector_16():
    global cap

    # Release the camera in the main application
    if cap is not None:
        cap.release()
        cap = None

    # Start the color detector in a separate thread
    def target():
        import color_detector_16pin  # Import the color detector module
        color_detector_16pin  # Call the main function of the color detector module

        # Reinitialize the camera in the main application after the detector is closed
        global cap
        if cap is None:
            cap = cv2.VideoCapture(0)

    detector_thread = threading.Thread(target=target)
    detector_thread.daemon = True  # Daemonize the thread so it exits when the main program exits
    detector_thread.start()

# Function to update the color list based on the selected configuration
def update_color_list(config):
    global current_colors, current_roi, color_labels

    # Clear existing labels
    for label in color_labels:
        label.destroy()  # Properly remove old labels
    color_labels.clear()  # Empty the list

    # Update the current colors based on selection
    if config == "12pins":
        current_colors = CABLE12PINS
        current_roi = CABLE12ROI
    elif config == "16pins":
        current_colors = CABLE16PINS
        current_roi = CABLE16ROI

    # Create new labels for the updated color list
    for pin_name, _ in current_colors:
        label = tk.Label(color_frame, text=pin_name, image=red_icon, compound=tk.LEFT, fg="red")
        label.pack(anchor=tk.W, pady=2)
        color_labels.append(label)

# Function to start the camera
def start_camera():
    global cap, camera_running
    if not camera_running:
        cap = cv2.VideoCapture(0)
        camera_running = True
        play_button.config(state=tk.DISABLED)
        stop_button.config(state=tk.NORMAL)
        update_frame()

# Function to stop the camera
def stop_camera():
    global cap, camera_running
    if camera_running:
        cap.release()
        camera_running = False
        play_button.config(state=tk.NORMAL)
        stop_button.config(state=tk.DISABLED)
        camera_label.config(image=None)  # Clear the camera feed

# Initialize the main window
root = tk.Tk()
root.title("Color Detection App")

# Toolbar
toolbar = tk.Menu(root)
root.config(menu=toolbar)

# Properties menu
properties_menu = tk.Menu(toolbar, tearoff=0)
toolbar.add_cascade(label="Properties", menu=properties_menu)
properties_menu.add_command(label="Settings", command=show_properties)
properties_menu.add_command(label="Export Settings", command=export_env_file)
properties_menu.add_command(label="Import .env", command=import_env_file)

# Configuration menu
config_menu = tk.Menu(toolbar, tearoff=0)
toolbar.add_cascade(label="Configuration", menu=config_menu)
config_menu.add_command(label="12-Pin Cable", command=lambda: update_color_list("12pins"))
config_menu.add_command(label="16-Pin Cable", command=lambda: update_color_list("16pins"))

# Color detection menu
color_detection_menu = tk.Menu(toolbar, tearoff=0)
toolbar.add_cascade(label="Color Configuration", menu=color_detection_menu)
color_detection_menu.add_command(label="Detect ROI 12-Pin", command=run_roi_detector_12)
color_detection_menu.add_command(label="Detect ROI 16-Pin", command=run_roi_detector_16)
color_detection_menu.add_command(label="Detect Color 12-Pin", command=run_color_detector_12)
color_detection_menu.add_command(label="Detect Color 16-Pin", command=run_color_detector_16)

# Create a toolbar frame (instead of tk.Menu)
toolbar_frame = tk.Frame(root)
toolbar_frame.pack(fill=tk.X, padx=5, pady=5)

# Add Play and Stop buttons to the toolbar
play_icon = ImageTk.PhotoImage(Image.open("play.png").resize((20, 20)))
stop_icon = ImageTk.PhotoImage(Image.open("stop.png").resize((20, 20)))
reload_icon = ImageTk.PhotoImage(Image.open("reload.png").resize((20, 20)))

# Create Play Button
play_button = tk.Button(toolbar_frame, image=play_icon, command=start_camera, borderwidth=0)
play_button.pack(side=tk.LEFT, padx=5)

# Create Stop Button
stop_button = tk.Button(toolbar_frame, image=stop_icon, command=stop_camera, borderwidth=0)
stop_button.pack(side=tk.LEFT, padx=5)

# Create Reload Button
reload_button = tk.Button(toolbar_frame, image=reload_icon, command=reload_configuration, borderwidth=0)
reload_button.pack(side=tk.LEFT, padx=5)

# Camera feed section
camera_frame = tk.Frame(root, width=640, height=480)
camera_frame.pack(side=tk.LEFT, padx=10, pady=10)

camera_label = tk.Label(camera_frame)
camera_label.pack()

# Color list section
color_frame = tk.Frame(root, width=200, height=480)
color_frame.pack(side=tk.RIGHT, padx=10, pady=10)

# Add a result label above the pins
result_label = tk.Label(color_frame, text="Result: ", font=("Arial", 12, "bold"))
result_label.pack(anchor=tk.W, pady=10)

# Load icons
green_icon = ImageTk.PhotoImage(Image.open("green_icon.png").resize((20, 20)))
red_icon = ImageTk.PhotoImage(Image.open("red_icon.png").resize((20, 20)))

# Initialize color labels
reload_configuration()
'''
color_labels = []
for pin_name, _ in CABLE12PINS:
    label = tk.Label(color_frame, text=pin_name, image=red_icon, compound=tk.LEFT, fg="red")
    label.pack(anchor=tk.W, pady=2)
    color_labels.append(label)
'''

# Initialize camera
cap = cv2.VideoCapture(0)

# Start updating the frame
update_frame()

# Run the application
root.mainloop()

# Release the camera when the app is closed
if cap is not None:
    cap.release()