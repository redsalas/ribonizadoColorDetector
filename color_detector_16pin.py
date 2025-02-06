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

# Mouse callback function to get the clicked point and define the ROI
def get_clicked_point(event, x, y, flags, param):
    global clicked_points, detected_colors, rois, current_pin
    if event == cv2.EVENT_LBUTTONDOWN and current_pin < num_pins:
        clicked_points.append((x, y))
        # Define the ROI as a 30*65 area around the clicked point
        roi = (x - 25, y - 25, 30, 65)  # (x, y, width, height)
        rois.append(roi)
        # Get the color of the clicked pixel
        detected_color = frame[y, x].tolist()
        detected_colors.append(detected_color)
        print(f"Pin {current_pin + 1}: Detected Color (BGR): {detected_color}, ROI: {roi}")
        current_pin += 1

        # If all pins are configured, save the results to .env and display them
        if current_pin == num_pins:
            print("All pins configured. Saving results to .env file...")
            save_results_to_env()
            display_results()

# Function to save the results to the .env file
def save_results_to_env():
    global detected_colors, rois, pin16names
    # Prepare the CABLE12PINS variable
    cable_pins = [[pin16names[i], color] for i, color in enumerate(detected_colors)]
    # Prepare the CABLE12ROI variable
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
cv2.namedWindow("Camera Feed")
cv2.setMouseCallback("Camera Feed", get_clicked_point)

print("Click on the camera feed to define ROIs for each pin. Press 'q' to quit.")

while True:
    # Capture frame-by-frame
    ret, frame = cap.read()
    if not ret:
        break

    # Add the legend at the top of the frame with a black background
    if current_pin < num_pins:
        legend_text = f"Setting Pin {current_pin + 1}, click in the selected area to store the area and color."
    else:
        legend_text = "All pins configured. Press 'q' to quit."
    text_size = cv2.getTextSize(legend_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
    text_x = (frame.shape[1] - text_size[0]) // 2  # Center the text horizontally
    # Draw a black rectangle as the background for the text
    cv2.rectangle(frame, (text_x - 5, 10), (text_x + text_size[0] + 5, 10 + text_size[1] + 10), (0, 0, 0), -1)
    # Display the text
    cv2.putText(frame, legend_text, (text_x, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    # Display the ROI for each pin as it is clicked
    for i, roi in enumerate(rois):
        x, y, w, h = roi
        # Draw the ROI on the frame
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        # Display the pin number
        pin_text = f"Pin {i + 1}"
        cv2.putText(frame, pin_text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    # If all pins are configured, display the results
    if current_pin == num_pins:
        display_results()

    # Display the frame
    cv2.imshow("Camera Feed", frame)

    # Check if the window is closed
    if cv2.getWindowProperty("Camera Feed", cv2.WND_PROP_VISIBLE) < 1:
        break

    # Break the loop if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the camera and close the window
cap.release()
cv2.destroyAllWindows()