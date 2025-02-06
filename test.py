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

# Load color configurations from environment variables
load_dotenv()
cable12pins_str = os.getenv("CABLE12PINS")
cable12roi_str = os.getenv("CABLE12ROI")
cable16pins_str = os.getenv("CABLE16PINS")
cable16roi_str = os.getenv("CABLE16ROI")

CABLE12PINS = json.loads(cable12pins_str)
CABLE12ROI = json.loads(cable12roi_str)
CABLE16PINS = json.loads(cable16pins_str)
CABLE16ROI = json.loads(cable16roi_str)
TOLERANCE = int(os.getenv("TOLERANCE"))

# Global variable for the camera
cap = None
current_colors = CABLE12PINS
current_roi = CABLE12ROI
camera_running = False  # Track if the camera is running

# Function to get the dominant color in an ROI
def get_dominant_color(frame, roi):
    x, y, w, h = roi
    roi_frame = frame[y:y+h, x:x+w]  # Extract the ROI
    avg_color = np.mean(roi_frame, axis=(0, 1))  # Calculate the average color
    return avg_color

# Function to check if a color is detected in the ROI
def detect_color(frame, expected_color, roi):
    global TOLERANCE
    dominant_color = get_dominant_color(frame, roi)
    # Check if the dominant color is within a tolerance of the expected color
    lower_bound = np.array(expected_color) - TOLERANCE
    upper_bound = np.array(expected_color) + TOLERANCE
    return np.all((dominant_color >= lower_bound) & (dominant_color <= upper_bound))

# Function to update the camera feed and color detection
def update_frame():
    global cap, current_colors, current_roi, camera_running
    if camera_running and cap is not None and cap.isOpened():
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

            restart_app()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import configuration: {str(e)}")

# Function to restart the app after import
def restart_app():
    try:
        print("Restarting application...")
        subprocess.Popen(sys.executable)  # Start a new instance
        sys.exit()  # Close the current instance
    except Exception as e:
        print(f"Failed to restart: {e}")

# Function to run the color detector module in a separate thread
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
    global current_colors, color_labels, current_roi

    # Clear existing labels
    for label in color_labels:
        label.pack_forget()
    color_labels.clear()

    # Update the current colors
    if config == "12pins":
        current_colors = CABLE12PINS
        current_roi = CABLE12ROI
    elif config == "16pins":
        current_colors = CABLE16PINS
        current_roi = CABLE16ROI

    # Create new labels for the updated color list
    for color_name, _ in current_colors:
        label = tk.Label(color_frame, text=color_name, image=red_icon, compound=tk.LEFT, fg="red")
        label.pack(anchor=tk.W, pady=2)
        color_labels.append(label)

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
color_detection_menu.add_command(label="Detect Color 12", command=run_color_detector_12)
color_detection_menu.add_command(label="Detect Color 16", command=run_color_detector_16)

# Add Play and Stop buttons to the toolbar
toolbar.add_separator()
play_icon = ImageTk.PhotoImage(Image.open("play.png").resize((20, 20)))
stop_icon = ImageTk.PhotoImage(Image.open("stop.png").resize((20, 20)))

play_button = tk.Button(toolbar, image=play_icon, command=start_camera)
play_button.pack(side=tk.LEFT, padx=5, pady=5)

stop_button = tk.Button(toolbar, image=stop_icon, command=stop_camera, state=tk.DISABLED)
stop_button.pack(side=tk.LEFT, padx=5, pady=5)

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
color_labels = []
for pin_name, _ in CABLE12PINS:
    label = tk.Label(color_frame, text=pin_name, image=red_icon, compound=tk.LEFT, fg="red")
    label.pack(anchor=tk.W, pady=2)
    color_labels.append(label)

# Initialize camera
cap = cv2.VideoCapture(0)

# Start updating the frame
update_frame()

# Run the application
root.mainloop()

# Release the camera when the app is closed
if cap is not None:
    cap.release()