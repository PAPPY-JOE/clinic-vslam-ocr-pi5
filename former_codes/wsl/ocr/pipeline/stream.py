import cv2
import socket
import struct
import pickle
import re
from ultralytics import YOLO
import easyocr

# Load models
yolo_model = YOLO("yolov8n.pt")  # YOLOv8 model for object detection
ocr_reader = easyocr.Reader(['en'], gpu=True)  # EasyOCR for text recognition

# Connect to Windows Server
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(("172.19.80.1", 8485))  # Replace with your Windows IP

data = b""
# payload_size = struct.calcsize("L")
payload_size = struct.calcsize("Q")

# Confidence threshold for OCR
threshold = 0.3  

# Function to filter text
def filter_text(text):
    """Cleans up detected text to remove unwanted characters."""
    filtered_text = re.sub(r'[^a-zA-Z\s\.,\':;]', '', text)  # Keep letters, spaces, and some punctuation
    filtered_text = ' '.join([word for word in filtered_text.split() if len(word) > 1])  # Remove short words
    return filtered_text.title()  # Convert to title case

while True:
    # Receive frame size
    while len(data) < payload_size:
        packet = client_socket.recv(4096)
        if not packet:
            print("Connection closed by server")
            break
        data += packet
        print(f"Received {len(packet)} bytes, total {len(data)}/{payload_size}")

    # Extract frame size correctly
    packed_msg_size = data[:payload_size]
    data = data[payload_size:]
    msg_size = struct.unpack("Q", packed_msg_size)[0]  # Use "Q" instead of "L"

    print(f"Expected frame size: {msg_size} bytes")  # Debug output

    # Receive frame data
    while len(data) < msg_size:
        data += client_socket.recv(4096)
    
    frame_data = data[:msg_size]
    data = data[msg_size:]

    # Deserialize frame
    frame = pickle.loads(frame_data)

    # Run YOLO object detection
    yolo_results = yolo_model(frame)
    annotated_frame = yolo_results[0].plot()  # Draw detections

    # Run OCR on the frame
    ocr_results = ocr_reader.readtext(frame)

    # Draw OCR bounding boxes
    for bbox, text, score in ocr_results:
        if score > threshold:
            x1, y1 = map(int, bbox[0])  # Top-left corner
            x2, y2 = map(int, bbox[2])  # Bottom-right corner

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

    # Show final processed frame
    cv2.imshow("Live Object Detection & OCR", annotated_frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

client_socket.close()
cv2.destroyAllWindows()


# import cv2
# import socket
# import struct
# import pickle

# # Connect to Windows Server
# client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# client_socket.connect(("172.19.80.1", 8485))  # Replace with your Windows IP

# data = b""
# payload_size = struct.calcsize("L")

# while True:
#     while len(data) < payload_size:
#         data += client_socket.recv(4096)

#     packed_msg_size = data[:payload_size]
#     data = data[payload_size:]
#     msg_size = struct.unpack("L", packed_msg_size)[0]

#     while len(data) < msg_size:
#         data += client_socket.recv(4096)

#     frame_data = data[:msg_size]
#     data = data[msg_size:]

#     frame = pickle.loads(frame_data)
#     cv2.imshow("WSL Camera Feed", frame)

#     if cv2.waitKey(1) & 0xFF == ord("q"):
#         break

# client_socket.close()
# cv2.destroyAllWindows()
