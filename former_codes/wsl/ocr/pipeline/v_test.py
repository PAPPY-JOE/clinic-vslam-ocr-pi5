import sys
sys.path.append("/home/jfatoye22/dev/ORB_SLAM3/lib")
sys.path.append("/home/jfatoye22/dev/ORB_SLAM3/python")

import cv2
import re
import matplotlib.pyplot as plt
import numpy as np
import easyocr
from ultralytics import YOLO
import ORB_SLAM3.System as SLAM3  # Import ORB-SLAM3 Python bindings

# --- Load models ---
yolo_model = YOLO("yolov8n.pt")  # YOLOv8 model for object detection
ocr_reader = easyocr.Reader(['en'], gpu=True)  # EasyOCR for text recognition

# --- ORB-SLAM3 Setup ---
voc_path = "/home/jfatoye22/dev/ORB_SLAM3/Vocabulary/ORBvoc.txt"  # ORB-SLAM3 vocabulary
slam_config = "/home/jfatoye22/dev/ORB_SLAM3/Examples/Monocular/EuRoC.yaml"  # ORB-SLAM3 config file
slam_system = SLAM3(voc_path, slam_config, SLAM3.MONOCULAR)
slam_system.Initialize()

# --- Parameters ---
threshold = 0.3  # Confidence threshold for OCR
frame_skip = 18  # Process every nth frame for efficiency
frame_count = 0

# --- Load Video ---
video_path = "./Photos/corridor.mov"  # Replace with your video file path
cap = cv2.VideoCapture(video_path)

# --- Filter Text Function ---
def filter_text(text):
    """Cleans up detected text to remove unwanted characters."""
    filtered_text = re.sub(r'[^a-zA-Z\s\.,\':;]', '', text)  # Keep letters, spaces, and punctuation
    filtered_text = ' '.join([word for word in filtered_text.split() if len(word) > 1])  # Remove short words
    return filtered_text.title()  # Convert to title case

plt.ion()  # Interactive mode for real-time updates

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("End of video")
        plt.close()
        break

    frame_count += 1
    if frame_count % frame_skip != 0:
        continue  # Skip frames to improve speed

    # Resize frame
    frame = cv2.resize(frame, (640, 480))

    # --- Run ORB-SLAM3 ---
    pose = slam_system.TrackMonocular(frame, frame_count)
    
    # Check if ORB-SLAM3 is tracking
    if pose is not None:
        print(f"Frame {frame_count}: SLAM Pose Estimated")
    else:
        print(f"Frame {frame_count}: SLAM Tracking Lost")

    # --- Run YOLO object detection ---
    yolo_results = yolo_model(frame)
    annotated_frame = yolo_results[0].plot()

    # --- OCR (Text Detection) ---
    small_frame = cv2.resize(frame, (320, 240))  # Reduce image size for OCR
    ocr_results = ocr_reader.readtext(small_frame)

    # Draw OCR bounding boxes
    for bbox, text, score in ocr_results:
        if score > threshold:
            x1, y1 = map(int, bbox[0])
            x2, y2 = map(int, bbox[2])

            # Scale bounding box back to original size
            x1, x2 = int(x1 * (640 / 320)), int(x2 * (640 / 320))
            y1, y2 = int(y1 * (480 / 240)), int(y2 * (480 / 240))

            text = filter_text(text)

            if not text:
                continue  # Skip empty detections

            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (255, 0, 0), 3)
            cv2.putText(annotated_frame, text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

    # --- Display Results ---
    plt.imshow(cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB))
    plt.title(f"SLAM + Object Detection + OCR (Frame {frame_count})")
    plt.pause(0.001)
    plt.clf()

cap.release()
slam_system.Shutdown()  # Properly close ORB-SLAM3
plt.ioff()
plt.show()


# import cv2
# import torch
# import time
# import subprocess
# import os
# import re
# import easyocr
# import matplotlib.pyplot as plt
# from ultralytics import YOLO

# # Define paths
# ORB_SLAM3_PATH = "/home/jfatoye22/dev/ORB_SLAM3/Examples/Monocular/mono_euroc"
# VOCABULARY_PATH = "/home/jfatoye22/dev/ORB_SLAM3/Vocabulary/ORBvoc.txt"
# CONFIG_PATH = "/home/jfatoye22/dev/ORB_SLAM3/Examples/Monocular/EuRoC.yaml"
# VIDEO_PATH = "/home/jfatoye22/dev/project/video.mp4"

# # Ensure ORB-SLAM3 is executable
# os.chmod(ORB_SLAM3_PATH, 0o755)

# # Start ORB-SLAM3
# slam_process = subprocess.Popen(
#     [ORB_SLAM3_PATH, VOCABULARY_PATH, CONFIG_PATH],
#     stdout=subprocess.PIPE,
#     stderr=subprocess.PIPE,
#     text=True
# )

# # Wait for SLAM to initialize
# time.sleep(3)
# if slam_process.poll() is not None:
#     print("⚠️ ORB-SLAM3 failed to start! Check the error logs.")
#     stderr_output, _ = slam_process.communicate()
#     print(stderr_output)
#     exit(1)

# # Load YOLO model
# yolo_model = YOLO("yolov8n.pt")

# # Initialize OCR
# reader = easyocr.Reader(["en"])

# # Open video file
# cap = cv2.VideoCapture(VIDEO_PATH)
# if not cap.isOpened():
#     print(f"❌ Error: Could not open video file {VIDEO_PATH}")
#     exit(1)

# frame_count = 0

# while cap.isOpened():
#     ret, frame = cap.read()
#     if not ret:
#         break

#     frame_count += 1
#     print(f"Processing frame {frame_count}")

#     # Resize frame for OCR
#     small_frame = cv2.resize(frame, (320, 240))

#     # YOLO Object Detection
#     yolo_results = yolo_model(frame)

#     # OCR Text Detection
#     ocr_results = reader.readtext(small_frame)

#     # Calculate scaling factors
#     scale_x = frame.shape[1] / small_frame.shape[1]
#     scale_y = frame.shape[0] / small_frame.shape[0]

#     # Draw YOLO results
#     for result in yolo_results:
#         if hasattr(result, 'boxes'):
#             for box in result.boxes:
#                 x1, y1, x2, y2 = map(int, box.xyxy[0])
#                 confidence = box.conf[0].item()
#                 label = result.names[int(box.cls[0])]

#                 if confidence > 0.5:
#                     cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
#                     cv2.putText(frame, f"{label} {confidence:.2f}", (x1, y1 - 10),
#                                 cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

#     # Draw OCR results
#     for bbox, text, score in ocr_results:
#         if score > 0.5:
#             x1, y1 = map(int, bbox[0])  # Top-left corner
#             x2, y2 = map(int, bbox[2])  # Bottom-right corner

#             # Scale coordinates
#             x1 = int(x1 * scale_x)
#             y1 = int(y1 * scale_y)
#             x2 = int(x2 * scale_x)
#             y2 = int(y2 * scale_y)

#             # Clean detected text
#             text = re.sub(r'[^a-zA-Z0-9\s\.,\':;]', '', text).strip()
#             if len(text) > 1:
#                 cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
#                 cv2.putText(frame, text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

#     # Show processed frame
#     cv2.imshow("ORB-SLAM3 + YOLO + OCR", frame)

#     # Plot results
#     plt.imshow(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
#     plt.axis("off")
#     plt.pause(0.001)
#     plt.clf()

#     # Exit loop if 'q' is pressed
#     if cv2.waitKey(1) & 0xFF == ord("q"):
#         break

# cap.release()
# cv2.destroyAllWindows()

# # Stop ORB-SLAM3 process
# slam_process.terminate()
