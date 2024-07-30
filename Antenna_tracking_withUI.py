import sys
import cv2
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QFileDialog, QLabel, QMessageBox
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
import time
from datetime import datetime

from ultralytics import YOLO

import snap7
from snap7.util import *

#PLC Interface 
class output(object):
	bool=1
	int=2
	real=3
	word=4
	dword=5
	
class S71200():
    def __init__(self,ip,debug=False):
        self.debug = debug
        self.plc = snap7.client.Client()
        self.plc.connect(ip,0,1)
        self.ip = ip
    def getMem(self,mem,returnByte=False):
        area=Areas.MK 
        length=1
        out=None
        bit=0
        start=0
        if(mem[0].lower()=='m'):
            area=Areas.MK 
        if(mem[0].lower()=='q'):
            area= Areas.PA 
        if(mem[0].lower()=='i'):
            area=Areas.PE 
        if(mem[1].lower()=='x'): 
            length=1
            out=output().bool
            start = int(mem.split('.')[0][2:])
        if(mem[1].lower()=='b'): 
            length=1
            out=output().int
            start = int(mem[2:])
        if(mem[1].lower()=='w'):
            length=2
            out=output().int
            start = int(mem[2:])
            
        if(mem[1].lower()=='d'):
            out=output().dword
            length=4
            start = int(mem.split('.')[0][2:])
        if('freal' in mem.lower()): 
            length=4
            start=int(mem.lower().replace('freal',''))
            out=output().real
        if(output().bool==out):
            bit = int(mem.split('.')[1])
        if(self.debug):
            print (mem[0].lower(),bit)
        self.plc.read_area(area,0,start,length)
        mbyte=self.plc.read_area(area,0,start,length)
        if(returnByte):
            return mbyte
        elif(output().bool==out):
            return get_bool(mbyte,0,bit)
        elif(output().int==out):
            return get_int(mbyte,start)
        elif(output().real==out):
            return get_real(mbyte,0)
        elif(output().dword==out):
            return get_dword(mbyte,0)
        elif(output().word==out):
            return get_int(mbyte,start)
    def writeMem(self,mem,value):
        data=self.getMem(mem,True)
        area=Areas.MK 
        length=1
    
        out=None
        bit=0
        start=0
        if(mem[0].lower()=='m'):
            area= Areas.MK 
        if(mem[0].lower()=='q'):
            area=Areas.PA 
        if(mem[0].lower()=='i'):
            area=Areas.PE 
        if(mem[1].lower()=='x'): 
            length=1
            out=output().bool
            start = int(mem.split('.')[0][2:])
            bit = int(mem.split('.')[1])
            set_bool(data,0,bit,int(value))
        if(mem[1].lower()=='b'): 
            length=1
            out=output().int
            start = int(mem[2:])
            set_int(data,0,value)
        if(mem[1].lower()=='d'):
            out=output().dword
            length=4
            start = int(mem.split('.')[0][2:])
            set_dword(data,0,value)
        if('freal' in mem.lower()): 
            length=4
            start=int(mem.lower().replace('freal',''))
            set_real(data,0,value)
        return self.plc.write_area(area,0,start,data)
        
plc = S71200('192.168.0.1')

# Define video processing thread
class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(QImage)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.run_flag = True
        self.video_source = None
        self.model = YOLO("newdrone.pt")
        self.tracked_drones = []  # List to hold tracked drones
        self.trackers = []  # List to hold trackers for each drone
        self.current_drone_index = 0  # Index to keep track of current drone being tracked
        self.Vid= None

    def __del__(self):
        if self.Vid:
            self.Vid.release()
    def run(self):
        if self.video_source is not None:
            cap = cv2.VideoCapture(self.video_source)
            frame_width1 = int(cap.get(3))
            frame_height1 = int(cap.get(4))
            size = (frame_width1,frame_height1)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.video_filename = f"VideoSave_{timestamp}.avi"
            self.Vid = cv2.VideoWriter(self.video_filename,
                          cv2.VideoWriter_fourcc(*'MJPG'),
                          10, size)
               
         
            if not cap.isOpened():
                self.emit_error_signal("Error: Could not open video source.")
                return
            while self.run_flag:
                ret, frame = cap.read()
                if ret:
                    if len(self.tracked_drones) == 0:
                        results = self.model(frame)
                        boxes = results[0].boxes.xyxy.cpu().numpy().astype(int)
                        for box in boxes:
                            x1, y1, x2, y2 = box[:4]
                            self.tracked_drones.append((x1, y1, x2-x1, y2-y1))
                            tracker = cv2.TrackerCSRT_create()
                            tracker.init(frame, (x1, y1, x2-x1, y2-y1))
                            self.trackers.append(tracker)
                    else:
                        success, box = self.trackers[self.current_drone_index].update(frame)
                        if success:
                            x, y, w, h = map(int, box)
                            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                            label = f"Tracked Drone {self.current_drone_index + 1}"
                            cv2.putText(frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                    
                        if x+w/2>frame_width1/2:
                            plc.writeMem('mx800.'+str(3),False)
                            plc.writeMem('mx800.'+str(2),True)
                        else:
                            plc.writeMem('mx800.'+str(2),False)
                            plc.writeMem('mx800.'+str(3),True)

                        if y+h/2>frame_height1/2:
                            plc.writeMem('mx800.'+str(1),False)
                            plc.writeMem('mx800.'+str(0),True)
                        else:
                            plc.writeMem('mx800.'+str(0),False)
                            plc.writeMem('mx800.'+str(1),True)

                    # Resize frame for display
                    resized_frame = cv2.resize(frame, (640, 480))

                    
            

                    # Convert frame to QImage format
                    rgb_image = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)
                    h, w, ch = rgb_image.shape
                    bytes_per_line = ch * w
                    convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
                    p = convert_to_Qt_format.scaled(800, 600, Qt.KeepAspectRatio)
                    self.change_pixmap_signal.emit(p)

                    self.Vid.write(frame)
                
                
            plc.writeMem('mx800.'+str(0),False)
            plc.writeMem('mx800.'+str(1),False)
            plc.writeMem('mx800.'+str(2),False)
            plc.writeMem('mx800.'+str(3),False)
            plc.plc.disconnect()
            cap.release()
            

    def stop(self):
        self.run_flag = False
        self.wait()

    def switch_drone(self):
        if self.tracked_drones:
            self.current_drone_index = (self.current_drone_index + 1) % len(self.tracked_drones)

    def emit_error_signal(self, message):
        self.change_pixmap_signal.emit(QImage())  # Clear the image
        QMessageBox.warning(None, "Error", message)

# Define main application window
class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Drone Tracker")
        self.setGeometry(400, 400, 800, 600)  # Increased window size

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Add logo
        self.logo_label = QLabel(self)
        self.load_logo()
        layout.addWidget(self.logo_label)

        self.video_label = QLabel(self)
        layout.addWidget(self.video_label)

        # Increase button size and font size
        button_style = """
        QPushButton {
            font-size: 18px;
            padding: 10px;
            min-width: 200px;
            min-height: 50px;
        }
        """

        self.select_button = QPushButton("Select Video", self)
        self.select_button.clicked.connect(self.select_video)
        self.select_button.setStyleSheet(button_style)
        layout.addWidget(self.select_button)

        self.start_button = QPushButton("Start Processing", self)
        self.start_button.clicked.connect(self.start_processing)
        self.start_button.setStyleSheet(button_style)
        layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop Processing", self)
        self.stop_button.clicked.connect(self.stop_processing)
        self.stop_button.setStyleSheet(button_style)
        layout.addWidget(self.stop_button)

        # Add camera connection option
        self.camera_button = QPushButton("Connect to Camera", self)
        self.camera_button.clicked.connect(self.connect_to_camera)
        self.camera_button.setStyleSheet(button_style)
        layout.addWidget(self.camera_button)

        self.thread = None
        self.video_path = None

    def load_logo(self):
        logo_path = r"C:\Users\BARC-1\Desktop\bhabha"  # Replace with your logo path
        logo_pixmap = QPixmap(logo_path)
        scaled_logo = logo_pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.logo_label.setPixmap(scaled_logo)
        self.logo_label.setAlignment(Qt.AlignCenter)

    def select_video(self):
        self.video_path, _ = QFileDialog.getOpenFileName(self, "Select Video", "", "Video Files (*.mp4 *.avi)")
        if self.video_path:
            self.select_button.setText(f"Selected: {self.video_path.split('/')[-1]}")

    def start_processing(self):
        if self.video_path:
            self.thread = VideoThread()
            self.thread.video_source = self.video_path
            self.thread.change_pixmap_signal.connect(self.update_image)
            self.thread.start()
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
        else:
            QMessageBox.warning(self, "Warning", "Please select a video file first.")

    def stop_processing(self):
        if self.thread:
            self.thread.stop()
            self.thread = None
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            
            cv2.destroyAllWindows()
            

    def update_image(self, image):
        self.video_label.setPixmap(QPixmap.fromImage(image))

    def closeEvent(self, event):
        if self.thread:
            self.thread.stop()
        event.accept()

    def connect_to_camera(self):
        self.thread = VideoThread()
        self.thread.video_source = 0  # Camera index 0 for default camera
       # self.thread.video_source ="rtsp://admin:@192.168.0.6/1" #camera ip address
        self.thread.change_pixmap_signal.connect(self.update_image)
        self.thread.start()
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_S:
            if self.thread and len(self.thread.tracked_drones) > 1:
                self.thread.switch_drone()

# Main execution point
if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = App()
    ex.show()
    sys.exit(app.exec_())