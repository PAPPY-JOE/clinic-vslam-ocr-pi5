import cv2
import pytesseract
import time

# Optional: Resize frame to improve speed or accuracy
RESIZE_WIDTH = 640

# Initialize webcam (use 0 or /dev/videoX)
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("❌ ERROR: Could not open webcam.")
    exit()

print("📸 OCR is running. Press 'q' to quit.\n")

while True:
    ret, frame = cap.read()
    if not ret:
        print("❌ Failed to grab frame.")
        break

    # Resize for consistent processing
    h, w = frame.shape[:2]
    scale = RESIZE_WIDTH / w
    frame_resized = cv2.resize(frame, (RESIZE_WIDTH, int(h * scale)))

    # Convert to grayscale for better OCR results
    gray = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2GRAY)

    # Run OCR
    text = pytesseract.image_to_string(gray)

    # Print cleaned-up result
    cleaned = text.strip()
    if cleaned:
        print(f"[{time.strftime('%H:%M:%S')}] 📝 Detected text:\n{cleaned}\n")

    # Show frame
    cv2.imshow("Live OCR (press 'q' to quit)", frame_resized)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Cleanup
cap.release()
cv2.destroyAllWindows()
