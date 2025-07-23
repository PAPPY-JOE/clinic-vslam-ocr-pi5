import cv2 as cv
import easyocr

# import matplotlib
# matplotlib.use('Agg')  # Use the 'Agg' backend 

import matplotlib.pyplot as plt
# plt.switch_backend('TkAgg')  # Try 'Qt5Agg' if TkAgg doesn't work
# plt.switch_backend('Qt5Agg')  # Try 'Qt5Agg' if TkAgg doesn't work

# Read image
image_path = './assets/text_test2.png'
img = cv.imread(image_path)

# Validate if the image was loaded correctly
if img is None:
    raise FileNotFoundError(f"Error: Could not read image at {image_path}")

# Initialize EasyOCR text detector
reader = easyocr.Reader(['en'], gpu=True)

# Detect text on image
text_results = reader.readtext(img)
threshold = 0.25

# Process detected text
for bbox, text, score in text_results:
    if score > threshold:
        # Get bounding box coordinates
        x1, y1 = map(int, bbox[0])  # Top-left
        x2, y2 = map(int, bbox[2])  # Bottom-right

        # Draw bounding box around text
        cv.rectangle(img, (x1, y1), (x2, y2), (255, 0, 0), 3)

        # Prepare text for display
        text_position = (x1, y1 - 10)  # Slightly above the box
        font = cv.FONT_HERSHEY_SIMPLEX
        font_scale = 1
        font_thickness = 2

        # Get text size to create background rectangle
        (text_width, text_height), _ = cv.getTextSize(text, font, font_scale, font_thickness)
        background_top_left = (x1, y1 - text_height - 10)
        background_bottom_right = (x1 + text_width, y1)

        # Draw filled background rectangle
        cv.rectangle(img, background_top_left, background_bottom_right, (255, 0, 0), -1)

        # Put the detected text on the image
        cv.putText(img, text, text_position, font, font_scale, (255, 255, 255), font_thickness)

# Save output image for verification
output_path = "output_detected.png"
cv.imwrite(output_path, img)
print(f"🔹 Output saved as {output_path}")

# Display using Matplotlib (works in WSL)
plt.figure(figsize=(10, 6))
plt.imshow(cv.cvtColor(img, cv.COLOR_BGR2RGB))
plt.axis("off")
plt.title("Detected Text with Bounding Boxes")

# Ensure Matplotlib displays the image
plt.show()
plt.savefig("detected_output.png")
plt.pause(5)  # Keep the figure open for 5 seconds before closing
plt.close()  # Close the plot after 5 seconds
