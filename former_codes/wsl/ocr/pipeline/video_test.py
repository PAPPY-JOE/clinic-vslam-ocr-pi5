import cv2
import re
import matplotlib.pyplot as plt
from ultralytics import YOLO
import easyocr

# Load models
yolo_model = YOLO("yolov8n.pt")  # YOLOv8 model for object detection
ocr_reader = easyocr.Reader(['en'], gpu=True)  # EasyOCR for text recognition

# Confidence threshold for OCR
threshold = 0.5  # Increased for better accuracy

# Frame skipping (dynamic adjustment for performance)
frame_skip = 15  # Adjust as needed
frame_count = 0

# Load video file
video_path = "./Photos/corridor.mov"  # Replace with your video file path
cap = cv2.VideoCapture(video_path)

# Function to filter text
def filter_text(text):
    """Cleans up detected text to remove unwanted characters."""
    filtered_text = re.sub(r'[^a-zA-Z0-9\s.,:;]', '', text)  # Keep alphanumeric and punctuation
    filtered_text = ' '.join([word for word in filtered_text.split() if len(word) > 1])  # Remove short words
    return filtered_text.title().strip()  # Convert to title case

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
        continue  # Skip frames to increase speed

    # Resize frame for faster processing
    frame = cv2.resize(frame, (640, 480))  

    # Run YOLO object detection
    yolo_results = yolo_model(frame)
    annotated_frame = yolo_results[0].plot()  # Draw detections

    # Reduce OCR image size before processing
    small_frame = cv2.resize(frame, (320, 240))  # OCR processes a smaller version of the frame

    # Run OCR on the smaller frame
    ocr_results = ocr_reader.readtext(small_frame)

    # Draw OCR bounding boxes
    seen_texts = set()  # Avoid duplicate detections
    for bbox, text, score in ocr_results:
        if score > threshold:
            text = filter_text(text)
            if not text or text in seen_texts:
                continue  # Skip empty or duplicate detections
            seen_texts.add(text)

            x1, y1 = map(int, bbox[0])  # Top-left corner
            x2, y2 = map(int, bbox[2])  # Bottom-right corner

            # Scale bounding box back to original size
            x1 = int(x1 * (640 / 320))
            y1 = int(y1 * (480 / 240))
            x2 = int(x2 * (640 / 320))
            y2 = int(y2 * (480 / 240))

            # Draw rectangle around detected text
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (255, 0, 0), 3)
            
            # Put text on frame
            cv2.putText(
                annotated_frame, text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX,
                1, (255, 255, 255), 2, cv2.LINE_AA
            )

    # Display using Matplotlib
    plt.imshow(cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB))
    plt.title("OCR and Object Detection Pipeline for vSLAM")
    plt.pause(0.001)  # Pause for real-time updates
    plt.clf()  # Clear figure to prevent overlap

cap.release()
plt.ioff()  # Turn off interactive mode
plt.show()

# import cv2
# import re
# import matplotlib.pyplot as plt
# from ultralytics import YOLO
# import easyocr

# # Load models
# yolo_model = YOLO("yolov8n.pt")  # YOLOv8 model for object detection
# ocr_reader = easyocr.Reader(['en'], gpu=True)  # EasyOCR for text recognition

# # Confidence threshold for OCR
# threshold = 0.3  

# # Frame skipping (process every nth frame)
# frame_skip = 18  # Adjust this for performance
# # frame_skip = 20  # Adjust this for performance
# frame_count = 0

# # Load video file
# video_path = "./Photos/corridor.mov"  # Replace with your video file path
# cap = cv2.VideoCapture(video_path)

# # Function to filter text
# def filter_text(text):
#     """Cleans up detected text to remove unwanted characters."""
#     filtered_text = re.sub(r'[^a-zA-Z\s\.,\':;]', '', text)  # Keep letters, spaces, and some punctuation
#     filtered_text = ' '.join([word for word in filtered_text.split() if len(word) > 1])  # Remove short words
#     return filtered_text.title()  # Convert to title case

# plt.ion()  # Turn on interactive mode for real-time updates

# while cap.isOpened():
#     ret, frame = cap.read()
#     if not ret:
#         print("End of video")
#         plt.close()
#         break
    
#     frame_count += 1
#     if frame_count % frame_skip != 0:
#         continue  # Skip frames to increase speed

#     # Resize frame to improve processing speed
#     frame = cv2.resize(frame, (640, 480))  # Adjust dimensions as needed

#     # Run YOLO object detection
#     yolo_results = yolo_model(frame)
#     annotated_frame = yolo_results[0].plot()  # Draw detections

#     # Reduce OCR image size before processing
#     small_frame = cv2.resize(frame, (320, 240))  # OCR processes a smaller version of the frame

#     # Run OCR on the smaller frame
#     ocr_results = ocr_reader.readtext(small_frame)

#     # Draw OCR bounding boxes
#     for bbox, text, score in ocr_results:
#         if score > threshold:
#             x1, y1 = map(int, bbox[0])  # Top-left corner
#             x2, y2 = map(int, bbox[2])  # Bottom-right corner

#             # Scale bounding box back to original size
#             x1 = int(x1 * (640 / 320))
#             y1 = int(y1 * (480 / 240))
#             x2 = int(x2 * (640 / 320))
#             y2 = int(y2 * (480 / 240))

#             # Clean detected text
#             text = filter_text(text)

#             if not text:
#                 continue  # Skip empty detections

#             # Draw rectangle around detected text
#             cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (255, 0, 0), 3)

#             # Put text on frame
#             cv2.putText(
#                 annotated_frame, text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX,
#                 1, (255, 255, 255), 2, cv2.LINE_AA
#             )

#     # Display using Matplotlib instead of OpenCV
#     plt.imshow(cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB))
#     plt.title("OCR and Object Detection Pipeline for vSLAM")
#     plt.pause(0.001)  # Pause to allow real-time updates
#     plt.clf()  # Clear figure to prevent overlap

# cap.release()
# plt.ioff()  # Turn off interactive mode
# plt.show()