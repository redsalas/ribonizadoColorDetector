import cv2
import numpy as np
from dotenv import load_dotenv, set_key
import os
import json

# Load environment variables from .env file
load_dotenv()
pin16names = json.loads(os.getenv("PIN16NAMES", "[]"))

# Global variables
clicked_points = []  # Stores clicked points
detected_colors = []  # Stores detected colors
rois = []  # Stores ROIs
num_pins = 16  # Default to 12 pins
current_pin = 0  # Tracks the current pin being configured

# Define the header height (adjust based on your text size)
HEADER_HEIGHT = 40  # Adjust this value based on the text size

# Mouse callback function to get the clicked point and define the ROI
def get_clicked_point(event, x, y, flags, param):
    global clicked_points, detected_colors, rois, current_pin
    if event == cv2.EVENT_LBUTTONDOWN and current_pin < num_pins:
        adjusted_y = y - HEADER_HEIGHT  # Adjust for header height

        if adjusted_y < 0:  # Prevent out-of-frame issues
            return

        clicked_points.append((x, adjusted_y))

        # Define the ROI as a 80*20 area around the clicked point
        roi = (x - 40, adjusted_y - 10, 80, 20)  # Adjusted ROI
        rois.append(roi)

        # Get the color of the clicked pixel
        detected_color = frame[adjusted_y, x].tolist()
        detected_colors.append(detected_color)

        print(f"Pin {current_pin + 1}: Detected Color (BGR): {detected_color}, ROI: {roi}")

        current_pin += 1

        # If all pins are configured, save results
        if current_pin == num_pins:
            print("All pins configured. Saving results...")
            save_results_to_env()
            display_results()

# Function to save the results to the .env file
def save_results_to_env():
    global detected_colors, rois, pin16names
    # Prepare the CABLE16PINS variable
    cable_pins = [[pin16names[i], color] for i, color in enumerate(detected_colors)]
    # Prepare the CABLE16ROI variable
    cable_rois = [[pin16names[i], roi] for i, roi in enumerate(rois)]
    # Write the variables to the .env file using double quotes
    set_key(".env", "CABLE16PINS", json.dumps(cable_pins))
    set_key(".env", "CABLE16ROI", json.dumps(cable_rois))
    print("Results saved to .env file.")

# Function to display all ROIs and RGB values on the screen
def display_results():
    global frame
    ''' 
    # Display at the end
    for i, (roi, color) in enumerate(zip(rois, detected_colors)):
        x, y, w, h = roi
        # Draw the ROI on the frame
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        # Display the RGB values
        color_text = f"Pin {i + 1}: BGR: {color}"
        cv2.putText(frame, color_text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    '''

# Initialize the camera
cap = cv2.VideoCapture(0)

# Create a named window and set the mouse callback
cv2.namedWindow("Lectura de Video - Configurar")
cv2.setMouseCallback("Lectura de Video - Configurar", get_clicked_point)

print("Click on the Lectura de Video - Configurar to define ROIs for each pin. Press 'q' to quit.")

while True:
    # Capture frame-by-frame
    ret, frame = cap.read()
    if not ret:
        break

    # Define the header height
    header_height = 40
    frame_width = frame.shape[1]

    # Create a black header (same width as the frame)
    header = np.zeros((header_height, frame_width, 3), dtype=np.uint8)

    # Set legend text
    if current_pin < num_pins:
        legend_text = f"Pin {current_pin + 1}, click para guardar el color"
    else:
        legend_text = "Pines configurados. Presione 'q' para salir."

    # Calculate text position
    text_size = cv2.getTextSize(legend_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
    text_x = (frame_width - text_size[0]) // 2  # Center the text horizontally
    text_y = header_height - 10  # Adjust vertical position within the header

    # Display text on the black header
    cv2.putText(header, legend_text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    # Stack the header on top of the camera frame
    combined_frame = np.vstack((header, frame))

    # Display the ROI for each pin as it is clicked
    for i, roi in enumerate(rois):
        x, y, w, h = roi
        y += header_height  # Adjust for the header
        cv2.rectangle(combined_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        pin_text = f"Pin {i + 1}"
        cv2.putText(combined_frame, pin_text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    # If all pins are configured, display the results
    if current_pin == num_pins:
        display_results()

    # Show the new frame with the header
    cv2.imshow("Lectura de Video - Configurar", combined_frame)

    # Check if the window is closed
    if cv2.getWindowProperty("Lectura de Video - Configurar", cv2.WND_PROP_VISIBLE) < 1:
        break

    # Break the loop if 'q' or 'Q' is pressed
    if cv2.waitKey(1) & 0xFF in [ord('q'), ord('Q')]:
        break

# Release the camera and close the window
cap.release()
cv2.destroyAllWindows()