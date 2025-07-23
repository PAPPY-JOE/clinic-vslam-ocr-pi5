import cv2
import pytesseract

img = cv2.imread('.././assets/text2.png')
text = pytesseract.image_to_string(img)
print(text)

# import cv2
# import pytesseract
# import time
# import json
# from datetime import datetime

# video = cv2.VideoCapture(0)  # Or use your camera feed
# frame_interval = 5  # seconds
# last_time = time.time()

# while True:
#     ret, frame = video.read()
#     if not ret:
#         break

#     now = time.time()
#     if now - last_time >= frame_interval:
#         last_time = now
#         gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#         text = pytesseract.image_to_string(gray)

#         if text.strip():
#             print("Detected text:", text.strip())

#             # TODO: Replace with actual pose from ORB_SLAM3
#             dummy_pose = {
#                 "timestamp": datetime.now().isoformat(),
#                 "text": text.strip(),
#                 "pose": [0.1, 0.2, 0.3]  # Replace with (x, y, z)
#             }

#             with open("text_landmarks.jsonl", "a") as f:
#                 f.write(json.dumps(dummy_pose) + "\n")

#     cv2.imshow("Live Feed", frame)
#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         break

# video.release()
# cv2.destroyAllWindows()

# # import cv2 as cv
# # import pytesseract

# # # Load image
# # image_path = '../easy_ocr/assets/text2.png'
# # image = cv.imread(image_path)  

# # # Preprocessing: Convert to grayscale and apply thresholding
# # gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
# # thresh = cv.threshold(gray, 150, 255, cv.THRESH_BINARY_INV)[1]

# # # Perform OCR
# # text = pytesseract.image_to_string(thresh, config='--psm 6')
# # print("Detected Room Label:", text)

# # # Display results
# # cv.imshow("Processed Image", thresh)
# # cv.waitKey(0)
# # cv.destroyAllWindows()
