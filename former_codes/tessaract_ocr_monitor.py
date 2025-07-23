#!/usr/bin/env python3
import cv2 # works but is too poor, switching to easy_ocr
import numpy as np
import os
import time
import pytesseract
from datetime import datetime
import logging

# Configuration
PIPE_PATH = "/tmp/frames.pipe"
POSE_PATH = "/tmp/latest_pose.txt"
LOG_DIR = "/home/jay/dev/ORB_SLAM3/Maps/OCR_Logs"
ERROR_LOG = "/home/jay/dev/ORB_SLAM3/Logs/ocr_errors.log"
KEYWORDS = ["Reception", "Laboratory", "Pharmacy", "Ward", "Clinic"]
TESSERACT_CONFIG = r'--oem 1 --psm 6'  # LSTM OCR engine, assume uniform block of text

# Configure logging
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
    """Process frame for OCR with optimized operations"""
    try:
        # Convert to grayscale and apply adaptive thresholding
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        thresh = cv2.adaptiveThreshold(
            gray, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 11, 2
        )
        
        # Optional: Add denoising
        # thresh = cv2.fastNlMeansDenoising(thresh, h=10)
        
        return thresh
    except Exception as e:
        logging.error(f"Image processing failed: {e}")
        return None

def read_pose():
    """Read current pose from file"""
    try:
        with open(POSE_PATH, 'r') as f:
            return f.read().strip()
    except Exception as e:
        logging.warning(f"Failed to read pose: {e}")
        return "unknown"

def main():
    setup_logging()
    logging.info("OCR Monitor starting...")
    
    # Wait for pipe to be created
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
    
    logging.info("Monitoring pipe for frames...")
    
    try:
        while True:
            try:
                # Read frame size (4 bytes)
                size_data = os.read(pipe_fd, 4)
                if not size_data:
                    time.sleep(0.01)
                    continue
                
                if len(size_data) != 4:
                    logging.warning("Incomplete size data received")
                    continue
                
                size = int.from_bytes(size_data, byteorder='little')
                frame_data = bytearray()
                
                # Read frame data with timeout
                start_read = time.time()
                while len(frame_data) < size and (time.time() - start_read) < 0.5:
                    chunk = os.read(pipe_fd, size - len(frame_data))
                    if chunk:
                        frame_data.extend(chunk)
                
                if len(frame_data) != size:
                    logging.warning(f"Incomplete frame data ({len(frame_data)}/{size} bytes)")
                    continue
                
                # Process frame
                frame = cv2.imdecode(np.frombuffer(frame_data, dtype=np.uint8), cv2.IMREAD_COLOR)
                if frame is None:
                    logging.warning("Failed to decode frame")
                    continue
                
                frame_count += 1
                successful_reads += 1
                
                # Process image and run OCR
                processed = process_image(frame)
                if processed is not None:
                    text = pytesseract.image_to_string(processed, config=TESSERACT_CONFIG).strip()
                    
                    # Check for keywords
                    if any(keyword.lower() in text.lower() for keyword in KEYWORDS):
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        pose = read_pose()
                        
                        log_entry = (
                            f"== {timestamp} ==\n"
                            f"Detected Text: {text}\n"
                            f"Pose: {pose}\n\n"
                        )
                        
                        # Save to log file
                        log_file = os.path.join(LOG_DIR, f"ocr_detections_{datetime.now().strftime('%Y%m%d')}.txt")
                        with open(log_file, 'a') as f:
                            f.write(log_entry)
                        
                        logging.info(f"Detected text: {text[:50]}...")  # Log first 50 chars
                
                # Periodic status report
                if frame_count % 100 == 0:
                    elapsed = time.time() - start_time
                    logging.info(
                        f"Status: {frame_count} frames, "
                        f"{frame_count/elapsed:.2f} FPS, "
                        f"Success rate: {100*successful_reads/frame_count:.1f}%"
                    )
                
            except BlockingIOError:
                time.sleep(0.005)  # Short sleep when no data available
            except Exception as e:
                logging.error(f"Processing error: {e}", exc_info=True)
                time.sleep(1)  # Recover after error
    
    except KeyboardInterrupt:
        logging.info("Shutting down by user request")
    finally:
        os.close(pipe_fd)
        elapsed = time.time() - start_time
        logging.info(
            f"Final stats: {frame_count} frames processed, "
            f"{frame_count/elapsed:.2f} FPS, "
            f"Success rate: {100*successful_reads/frame_count:.1f}%"
        )

if __name__ == "__main__":
    pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"
    main()