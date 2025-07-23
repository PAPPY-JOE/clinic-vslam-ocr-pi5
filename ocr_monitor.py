#!/usr/bin/env python3
import cv2
import numpy as np
import os
import time
import easyocr
from datetime import datetime
import logging
from collections import defaultdict
import struct

# Configuration
PIPE_PATH = "/tmp/frames.pipe"
POSE_PATH = "/tmp/latest_pose.txt"
LOG_DIR = "/home/jay/dev/ORB_SLAM3/Maps/OCR_Logs"
ERROR_LOG = "/home/jay/dev/ORB_SLAM3/Logs/ocr_errors.log"
KEYWORDS = ["RECEPTION", "LABORATORY", "PHARMACY", "WARD", "CLINIC"]
CONFIDENCE_THRESHOLD = 0.80  # Only log OCR results with confidence ≥ 0.80

def setup_logging():
    os.makedirs(LOG_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(ERROR_LOG), exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(ERROR_LOG),
            logging.StreamHandler()
        ]
    )

def process_image(frame):
    try:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        processed = cv2.bilateralFilter(gray, 11, 17, 17)
        return processed
    except Exception as e:
        logging.error(f"Image processing failed: {e}")
        return None

def read_pose():
    try:
        with open(POSE_PATH, 'r') as f:
            return f.read().strip()
    except Exception as e:
        logging.warning(f"Failed to read pose: {e}")
        return "unknown"

def read_exact(fd, size):
    data = bytearray()
    while len(data) < size:
        try:
            chunk = os.read(fd, size - len(data))
            if not chunk:
                return None
            data.extend(chunk)
        except BlockingIOError:
            time.sleep(0.005)
    return data

def main():
    setup_logging()
    logging.info("OCR Monitor starting...")

    last_detection_times = defaultdict(lambda: 0)
    COOLDOWN_SECONDS = 30

    while not os.path.exists(PIPE_PATH):
        time.sleep(0.5)

    try:
        pipe_fd = os.open(PIPE_PATH, os.O_RDONLY | os.O_NONBLOCK)
    except Exception as e:
        logging.error(f"Failed to open pipe: {e}")
        return

    frame_count = 0
    successful_reads = 0
    start_time = time.time()

    reader = easyocr.Reader(['en'], gpu=False)
    logging.info("Monitoring pipe for raw frames...")

    try:
        while True:
            header = read_exact(pipe_fd, 12)
            if not header or len(header) != 12:
                time.sleep(0.01)
                continue

            rows, cols, type_code = struct.unpack('III', header)

            if type_code == 16:  # CV_8UC3
                channels = 3
                dtype = np.uint8
            else:
                logging.warning(f"Unsupported frame type: {type_code}")
                continue

            frame_size = rows * cols * channels * np.dtype(dtype).itemsize
            frame_data = read_exact(pipe_fd, frame_size)
            if not frame_data or len(frame_data) != frame_size:
                logging.warning("Incomplete raw frame received")
                continue

            frame = np.frombuffer(frame_data, dtype=dtype).reshape((rows, cols, channels))

            frame_count += 1
            successful_reads += 1

            processed = process_image(frame)
            if processed is not None:
                results = reader.readtext(processed, detail=1)
                found_keywords = []

                for (bbox, text, conf) in results:
                    if conf >= CONFIDENCE_THRESHOLD:
                        clean_text = text.upper().strip()
                        for keyword in KEYWORDS:
                            if keyword in clean_text:
                                found_keywords.append((keyword, bbox, conf))

                                pts = np.array(bbox).astype(int)
                                cv2.polylines(frame, [pts], isClosed=True, color=(0, 255, 0), thickness=2)
                                x, y = pts[0]
                                cv2.putText(frame, f"{clean_text} ({int(conf * 100)}%)", (x, y - 10),
                                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                                break

                if found_keywords:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    pose = read_pose()
                    now = time.time()
                    new_keywords = []

                    for keyword, bbox, conf in found_keywords:
                        key = (keyword, pose)
                        if now - last_detection_times[key] >= COOLDOWN_SECONDS:
                            new_keywords.append((keyword, bbox, conf))
                            last_detection_times[key] = now

                    if not new_keywords:
                        logging.info("All keywords recently seen — skipping.")
                        continue

                    image_name = f"ocr_{timestamp}.jpg"
                    image_path = os.path.join(LOG_DIR, image_name)
                    cv2.imwrite(image_path, frame)
                    logging.info(f"Saved image to: {image_path}")

                    log_file = os.path.join(LOG_DIR, f"ocr_detections_{datetime.now().strftime('%Y%m%d')}.txt")
                    with open(log_file, 'a') as f:
                        f.write(f"== {timestamp} ==\n")
                        f.write(f"Pose: {pose}\n")
                        for keyword, bbox, conf in new_keywords:
                            f.write(f"Detected: {keyword}\n")
                            f.write(f"  Confidence: {conf:.2f}\n")
                            f.write(f"  BBox: {bbox}\n")
                            f.write(f"Saved Image: {image_name}\n\n")
                        f.write("\n")

                    for keyword, _, _ in new_keywords:
                        logging.info(f"Detected: {keyword}")

            if frame_count % 100 == 0:
                elapsed = time.time() - start_time
                fps = frame_count / elapsed
                success_rate = 100 * successful_reads / frame_count
                logging.info(f"Status: {frame_count} frames | {fps:.2f} FPS | Success rate: {success_rate:.1f}%")

    except KeyboardInterrupt:
        logging.info("Shutting down by user request")
    finally:
        os.close(pipe_fd)
        elapsed = time.time() - start_time
        fps = frame_count / elapsed
        success_rate = 100 * successful_reads / frame_count
        logging.info(f"Final stats: {frame_count} frames | {fps:.2f} FPS | Success rate: {success_rate:.1f}%")

if __name__ == "__main__":
    main()


# #!/usr/bin/env python3
# import cv2
# import numpy as np
# import os
# import time
# import easyocr
# from datetime import datetime
# import logging
# from collections import defaultdict

# # Configuration
# PIPE_PATH = "/tmp/frames.pipe"
# POSE_PATH = "/tmp/latest_pose.txt"
# LOG_DIR = "/home/jay/dev/ORB_SLAM3/Maps/OCR_Logs"
# ERROR_LOG = "/home/jay/dev/ORB_SLAM3/Logs/ocr_errors.log"
# KEYWORDS = ["RECEPTION", "LABORATORY", "PHARMACY", "WARD", "CLINIC"]
# CONFIDENCE_THRESHOLD = 0.80  # Only log OCR results with confidence ≥ 0.80

# # Configure logging
# def setup_logging():
#     os.makedirs(LOG_DIR, exist_ok=True)
#     os.makedirs(os.path.dirname(ERROR_LOG), exist_ok=True)

#     logging.basicConfig(
#         level=logging.INFO,
#         format='%(asctime)s - %(levelname)s - %(message)s',
#         handlers=[
#             logging.FileHandler(ERROR_LOG),
#             logging.StreamHandler()
#         ]
#     )

# def process_image(frame):
#     """Prepare frame for OCR (optimized for EasyOCR)"""
#     try:
#         gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#         processed = cv2.bilateralFilter(gray, 11, 17, 17)
#         return processed
#     except Exception as e:
#         logging.error(f"Image processing failed: {e}")
#         return None

# def read_pose():
#     """Read current pose from file"""
#     try:
#         with open(POSE_PATH, 'r') as f:
#             return f.read().strip()
#     except Exception as e:
#         logging.warning(f"Failed to read pose: {e}")
#         return "unknown"

# def main():
#     setup_logging()
#     logging.info("OCR Monitor starting...")

#     # Store last detection times: {(keyword, pose): timestamp}
#     last_detection_times = defaultdict(lambda: 0)
#     COOLDOWN_SECONDS = 30

#     while not os.path.exists(PIPE_PATH):
#         time.sleep(0.5)

#     try:
#         pipe_fd = os.open(PIPE_PATH, os.O_RDONLY | os.O_NONBLOCK)
#     except Exception as e:
#         logging.error(f"Failed to open pipe: {e}")
#         return

#     frame_count = 0
#     successful_reads = 0
#     start_time = time.time()

#     reader = easyocr.Reader(['en'], gpu=False)
#     logging.info("Monitoring pipe for frames...")

#     try:
#         while True:
#             try:
#                 size_data = os.read(pipe_fd, 4)
#                 if not size_data or len(size_data) != 4:
#                     time.sleep(0.01)
#                     continue

#                 size = int.from_bytes(size_data, byteorder='little')
#                 frame_data = bytearray()
#                 start_read = time.time()

#                 while len(frame_data) < size and (time.time() - start_read) < 1.0:
#                     chunk = os.read(pipe_fd, size - len(frame_data))
#                     if chunk:
#                         frame_data.extend(chunk)

#                 if len(frame_data) != size:
#                     logging.warning(f"Incomplete frame data ({len(frame_data)}/{size})")
#                     continue

#                 frame = cv2.imdecode(np.frombuffer(frame_data, dtype=np.uint8), cv2.IMREAD_COLOR)
#                 if frame is None:
#                     logging.warning("Failed to decode frame")
#                     continue

#                 frame_count += 1
#                 successful_reads += 1

#                 processed = process_image(frame)
#                 if processed is not None:
#                     results = reader.readtext(processed, detail=1)
#                     found_keywords = []

#                     for (bbox, text, conf) in results:
#                         if conf >= CONFIDENCE_THRESHOLD:
#                             clean_text = text.upper().strip()
#                             for keyword in KEYWORDS:
#                                 if keyword in clean_text:
#                                     found_keywords.append((keyword, bbox, conf))

#                                     # Draw bounding box
#                                     pts = np.array(bbox).astype(int)
#                                     cv2.polylines(frame, [pts], isClosed=True, color=(0, 255, 0), thickness=2)

#                                     # Label
#                                     x, y = pts[0]
#                                     cv2.putText(frame, f"{clean_text} ({int(conf * 100)}%)", (x, y - 10),
#                                                 cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
#                                     break

#                     if found_keywords:
#                         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#                         pose = read_pose()
#                         now = time.time()
#                         new_keywords = []

#                         # Filter out duplicates within cooldown window
#                         for keyword, bbox, conf in found_keywords:
#                             key = (keyword, pose)
#                             if now - last_detection_times[key] >= COOLDOWN_SECONDS:
#                                 new_keywords.append((keyword, bbox, conf))
#                                 last_detection_times[key] = now

#                         if not new_keywords:
#                             logging.info("All keywords recently seen — skipping.")
#                             continue  # Skip logging and image saving

#                         # Save image
#                         image_name = f"ocr_{timestamp}.jpg"
#                         image_path = os.path.join(LOG_DIR, image_name)
#                         cv2.imwrite(image_path, frame)
#                         logging.info(f"Saved image to: {image_path}")

#                         log_file = os.path.join(LOG_DIR, f"ocr_detections_{datetime.now().strftime('%Y%m%d')}.txt")
#                         with open(log_file, 'a') as f:
#                             f.write(f"== {timestamp} ==\n")
#                             f.write(f"Pose: {pose}\n")
#                             for keyword, bbox, conf in new_keywords:
#                                 f.write(f"Detected: {keyword}\n")
#                                 f.write(f"  Confidence: {conf:.2f}\n")
#                                 f.write(f"  BBox: {bbox}\n")
#                                 f.write(f"Saved Image: {image_name}\n\n")
#                             f.write("\n")

#                         for keyword, _, _ in new_keywords:
#                             logging.info(f"Detected: {keyword}")

#                 if frame_count % 100 == 0:
#                     elapsed = time.time() - start_time
#                     fps = frame_count / elapsed
#                     success_rate = 100 * successful_reads / frame_count
#                     logging.info(f"Status: {frame_count} frames | {fps:.2f} FPS | Success rate: {success_rate:.1f}%")

#             except BlockingIOError:
#                 time.sleep(0.005)
#             except Exception as e:
#                 logging.error(f"Processing error: {e}", exc_info=True)
#                 time.sleep(1)

#     except KeyboardInterrupt:
#         logging.info("Shutting down by user request")
#     finally:
#         os.close(pipe_fd)
#         elapsed = time.time() - start_time
#         fps = frame_count / elapsed
#         success_rate = 100 * successful_reads / frame_count
#         logging.info(f"Final stats: {frame_count} frames | {fps:.2f} FPS | Success rate: {success_rate:.1f}%")

# if __name__ == "__main__":
#     main()

