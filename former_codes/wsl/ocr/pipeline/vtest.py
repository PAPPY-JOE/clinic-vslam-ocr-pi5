import cv2
import re
import time
import torch
import matplotlib.pyplot as plt
from ultralytics import YOLO
import easyocr

# Load models
yolo_model = YOLO("yolov8n.pt")  # YOLOv8 for object detection
ocr_reader = easyocr.Reader(['en'], gpu=torch.cuda.is_available())  # Check GPU availability

# Confidence threshold for OCR
threshold = 0.5  # Adjust for accuracy

# Dynamic frame skipping
frame_skip = 15
last_time = time.time()
frame_count = 0

# Load video file
video_path = "./Photos/corridor.mov"
cap = cv2.VideoCapture(video_path)

# Function to filter text
def filter_text(text):
    """Cleans up detected text to remove unwanted characters."""
    filtered_text = re.sub(r'[^a-zA-Z0-9\s.,:;]', '', text)
    words = filtered_text.split()
    return ' '.join([word for word in words if len(word) > 1 or word.lower() in ['ai', 'iot', 'ml']]).title().strip()

# Flag to check if the plot is closed
plot_closed = False
def on_close(event):
    """Stops execution when the plot window is closed."""
    global plot_closed
    plot_closed = True
    plt.close()

plt.ion()  # Turn on interactive mode
fig = plt.figure()
fig.canvas.mpl_connect('close_event', on_close)  # Handle close event

while cap.isOpened() and not plot_closed:
    ret, frame = cap.read()
    if not ret:
        print("End of video")
        break
    
    frame_count += 1
    if frame_count % frame_skip != 0:
        continue  # Skip frames dynamically
    
    # Resize frame for faster processing
    frame = cv2.resize(frame, (640, 480))
    
    # Run YOLO object detection
    yolo_results = yolo_model(frame)
    annotated_frame = yolo_results[0].plot()
    
    # Reduce OCR image size for efficiency
    small_frame = cv2.resize(frame, (320, 240))
    ocr_results = ocr_reader.readtext(small_frame)
    
    seen_texts = set()  # Avoid duplicate detections
    for bbox, text, score in ocr_results:
        if score > threshold:
            text = filter_text(text)
            if not text or text in seen_texts:
                continue
            seen_texts.add(text)
            
            x1, y1 = map(int, bbox[0])
            x2, y2 = map(int, bbox[2])
            
            # Scale bounding box back to original size
            x1 = int(x1 * (640 / 320))
            y1 = int(y1 * (480 / 240))
            x2 = int(x2 * (640 / 320))
            y2 = int(y2 * (480 / 240))
            
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (255, 0, 0), 3)
            cv2.putText(
                annotated_frame, text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX,
                1, (255, 255, 255), 2, cv2.LINE_AA
            )
    
    # Adaptive frame skipping
    if time.time() - last_time > 0.1:
        frame_skip = max(5, frame_skip - 1)
    else:
        frame_skip = min(20, frame_skip + 1)
    last_time = time.time()
    
    # Display using Matplotlib
    plt.imshow(cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB))
    plt.title("OCR and Object Detection Pipeline for vSLAM")
    plt.pause(0.001)
    plt.clf()

cap.release()
plt.ioff()
plt.show()

# import cv2
# import re
# import subprocess
# import numpy as np
# import matplotlib.pyplot as plt
# from ultralytics import YOLO
# import easyocr
# import os

# # ORB-SLAM3 Path
# ORB_SLAM3_PATH = "/home/jfatoye22/dev/ORB_SLAM3/Examples/Monocular/mono_euroc"
# VOCABULARY_PATH = "/home/jfatoye22/dev/ORB_SLAM3/Vocabulary/ORBvoc.txt"
# CONFIG_PATH = "/home/jfatoye22/dev/ORB_SLAM3/Examples/Monocular/EuRoC.yaml"

# # Load models
# yolo_model = YOLO("yolov8n.pt")  # YOLOv8 model for object detection
# ocr_reader = easyocr.Reader(['en'], gpu=True)  # EasyOCR for text recognition

# # Confidence threshold for OCR
# threshold = 0.3  

# # Frame skipping (process every nth frame)
# frame_skip = 18  # Adjust for performance
# frame_count = 0

# # Load video file
# video_path = "./Photos/corridor.mov"  # Replace with your video file path
# cap = cv2.VideoCapture(video_path)

# # Create a directory to store extracted frames
# output_dir = "./slam_frames"
# os.makedirs(output_dir, exist_ok=True)

# # Function to filter text
# def filter_text(text):
#     """Cleans up detected text to remove unwanted characters."""
#     filtered_text = re.sub(r'[^a-zA-Z\s\.,\':;]', '', text)  # Keep letters, spaces, and some punctuation
#     filtered_text = ' '.join([word for word in filtered_text.split() if len(word) > 1])  # Remove short words
#     return filtered_text.title()  # Convert to title case

# plt.ion()  # Turn on interactive mode for real-time updates

# # Extract frames and create timestamps
# timestamps_file = os.path.join(output_dir, "timestamps.txt")
# with open(timestamps_file, "w") as f:
#     while cap.isOpened():
#         ret, frame = cap.read()
#         if not ret:
#             break

#         frame_count += 1
#         if frame_count % frame_skip != 0:
#             continue  # Skip frames to increase speed

#         # Save frame for ORB-SLAM3 processing
#         frame_filename = os.path.join(output_dir, f"frame_{frame_count:05d}.png")
#         cv2.imwrite(frame_filename, frame)

#         # Write timestamp (assuming 30 FPS video)
#         timestamp = frame_count / 30.0
#         f.write(f"{timestamp}\n")

#         # Resize frame for YOLO and OCR
#         frame = cv2.resize(frame, (640, 480))  # Adjust dimensions as needed

#         # Run YOLO object detection
#         yolo_results = yolo_model(frame)
#         annotated_frame = yolo_results[0].plot()  # Draw detections

#         # Reduce OCR image size before processing
#         small_frame = cv2.resize(frame, (320, 240))  # OCR processes a smaller version of the frame

#         # Run OCR on the smaller frame
#         ocr_results = ocr_reader.readtext(small_frame)

#         # Draw OCR bounding boxes
#         for bbox, text, score in ocr_results:
#             if score > threshold:
#                 x1, y1 = map(int, bbox[0])  # Top-left corner
#                 x2, y2 = map(int, bbox[2])  # Bottom-right corner

#                 # Scale bounding box back to original size
#                 x1 = int(x1 * (640 / 320))
#                 y1 = int(y1 * (480 / 240))
#                 x2 = int(x2 * (640 / 320))
#                 y2 = int(y2 * (480 / 240))

#                 # Clean detected text
#                 text = filter_text(text)

#                 if not text:
#                     continue  # Skip empty detections

#                 # Draw rectangle around detected text
#                 cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (255, 0, 0), 3)

#                 # Put text on frame
#                 cv2.putText(
#                     annotated_frame, text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX,
#                     1, (255, 255, 255), 2, cv2.LINE_AA
#                 )

#         # Display using Matplotlib instead of OpenCV
#         plt.imshow(cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB))
#         plt.title("OCR and Object Detection Pipeline for vSLAM")
#         plt.pause(0.001)  # Pause to allow real-time updates
#         plt.clf()  # Clear figure to prevent overlap

# cap.release()
# plt.ioff()  # Turn off interactive mode
# plt.show()

# # Run ORB-SLAM3 on the extracted frames
# slam_process = subprocess.run(
#     [ORB_SLAM3_PATH, VOCABULARY_PATH, CONFIG_PATH, output_dir, timestamps_file],
#     stdout=subprocess.PIPE,
#     stderr=subprocess.PIPE,
#     text=True
# )

# # Print ORB-SLAM3 output
# print("ORB-SLAM3 Output:")
# print(slam_process.stdout)
# print("ORB-SLAM3 Errors:")
# print(slam_process.stderr)