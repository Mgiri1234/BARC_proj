# Drone Tracker Application

## Overview
This Python application is a drone tracking system using YOLO (You Only Look Once) for object detection and OpenCV for video processing. It includes a graphical user interface (GUI) built with PyQt5. The application connects to a Siemens S7-1200 PLC to control and monitor the drone tracking process.

## Features
- Load and process video files to detect and track drones.
- Real-time tracking using a connected camera.
- PLC (Programmable Logic Controller) interface for controlling actuators based on drone positions.
- Graphical user interface for easy interaction.
- Ability to switch between tracked drones using the keyboard.

## Requirements
- Python 3.x
- OpenCV
- PyQt5
- YOLO (from the ultralytics package)
- snap7

## Installation
1. Install the required packages:
    ```bash
    pip install opencv-python-headless PyQt5 ultralytics snap7
    ```

2. Ensure you have the necessary YOLO model file (`newdrone.pt`) in the same directory as your script.

3. Update the PLC IP address and video logo path in the script as needed.

## How to Use
1. **Run the Application**: Execute the script to start the application.
    ```bash
    python your_script.py
    ```

2. **Select Video**: Click the "Select Video" button to choose a video file for processing.

3. **Start Processing**: Click the "Start Processing" button to begin video processing and drone tracking.

4. **Stop Processing**: Click the "Stop Processing" button to stop the video processing.

5. **Connect to Camera**: Click the "Connect to Camera" button to use a real-time camera feed for drone tracking.

6. **Switch Drones**: Press the 'S' key to switch between tracked drones when multiple drones are detected.

## Classes and Functions

### PLC Interface

#### `class output(object)`
Defines data types for PLC memory areas.

#### `class S71200()`
Handles connection and communication with the Siemens S7-1200 PLC.
- `__init__(self, ip, debug=False)`: Initializes the PLC connection.
- `getMem(self, mem, returnByte=False)`: Reads a memory location from the PLC.
- `writeMem(self, mem, value)`: Writes a value to a memory location on the PLC.

### Video Processing

#### `class VideoThread(QThread)`
Handles video processing and drone tracking in a separate thread.
- `run(self)`: Processes the video frame by frame, detecting and tracking drones.
- `stop(self)`: Stops the video processing.
- `switch_drone(self)`: Switches between tracked drones.
- `emit_error_signal(self, message)`: Emits an error signal to the GUI.

### Main Application Window

#### `class App(QMainWindow)`
Defines the main application window and its functionalities.
- `load_logo(self)`: Loads and displays the application logo.
- `select_video(self)`: Opens a file dialog to select a video file.
- `start_processing(self)`: Starts video processing.
- `stop_processing(self)`: Stops video processing.
- `update_image(self, image)`: Updates the displayed video frame in the GUI.
- `closeEvent(self, event)`: Handles application close event.
- `connect_to_camera(self)`: Connects to a real-time camera feed.
- `keyPressEvent(self, event)`: Handles key press events for switching drones.

### Main Execution Point
The main script initializes the application and starts the PyQt5 event loop.
```python
if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = App()
    ex.show()
    sys.exit(app.exec_())
```

## Notes
- Ensure the PLC is correctly configured and connected to the network.
- Adjust the camera IP address and logo path according to your setup.
- The application currently supports video files in `.mp4` and `.avi` formats.
