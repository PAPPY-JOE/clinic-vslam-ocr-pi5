import cv2
import re
import matplotlib.pyplot as plt
# import numpy as np
from ultralytics import YOLO
import easyocr
import ORB_SLAM3.System as ORB

# Load ORB-SLAM3 system
orb_slam = ORB.System("ORB_SLAM3/Vocabulary/ORBvoc.txt", "ORB_SLAM3/Calibration/camera.yaml", ORB.SENSOR_MONOCULAR)
orb_slam.initialize()

# Load models
yolo_model = YOLO("yolov8n.pt")  # YOLOv8 model for object detection
ocr_reader = easyocr.Reader(['en'], gpu=True)  # EasyOCR for text recognition

# Confidence threshold for OCR
threshold = 0.3  
frame_skip = 18  # Process every nth frame for performance
frame_count = 0

# Load video file
video_path = "./Photos/corridor.mov"  # Replace with your video file path
cap = cv2.VideoCapture(video_path)

# Function to filter text
def filter_text(text):
    """Cleans up detected text to remove unwanted characters."""
    filtered_text = re.sub(r'[^a-zA-Z\s\.,\':;]', '', text)  # Keep letters, spaces, and some punctuation
    filtered_text = ' '.join([word for word in filtered_text.split() if len(word) > 1])  # Remove short words
    return filtered_text.title()  # Convert to title case

plt.ion()  # Turn on interactive mode for real-time updates

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("End of video")
        plt.close()
        break

    frame_count += 1
    if frame_count % frame_skip != 0:
        continue  # Skip frames to increase speed

    # Resize frame to improve processing speed
    frame = cv2.resize(frame, (640, 480))  # Adjust dimensions as needed

    # Run ORB-SLAM3 (pose estimation)
    pose = orb_slam.track_monocular(frame, frame_count / 30.0)

    # Run YOLO object detection
    yolo_results = yolo_model(frame)
    annotated_frame = yolo_results[0].plot()  # Draw detections

    # Reduce OCR image size before processing
    small_frame = cv2.resize(frame, (320, 240))  # OCR processes a smaller version of the frame

    # Run OCR on the smaller frame
    ocr_results = ocr_reader.readtext(small_frame)

    # Draw OCR bounding boxes
    for bbox, text, score in ocr_results:
        if score > threshold:
            x1, y1 = map(int, bbox[0])  # Top-left corner
            x2, y2 = map(int, bbox[2])  # Bottom-right corner

            # Scale bounding box back to original size
            x1 = int(x1 * (640 / 320))
            y1 = int(y1 * (480 / 240))
            x2 = int(x2 * (640 / 320))
            y2 = int(y2 * (480 / 240))

            # Clean detected text
            text = filter_text(text)

            if not text:
                continue  # Skip empty detections

            # Draw rectangle around detected text
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (255, 0, 0), 3)

            # Put text on frame
            cv2.putText(
                annotated_frame, text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX,
                1, (255, 255, 255), 2, cv2.LINE_AA
            )

    # Display pose estimation
    print(f"Pose Estimate: {pose}")

    # Display using Matplotlib instead of OpenCV
    plt.imshow(cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB))
    plt.title("ORB-SLAM3, YOLO, and OCR Pipeline")
    plt.pause(0.001)  # Pause to allow real-time updates
    plt.clf()  # Clear figure to prevent overlap

cap.release()
orb_slam.shutdown()  # Shutdown ORB-SLAM3
plt.ioff()  # Turn off interactive mode
plt.show()
