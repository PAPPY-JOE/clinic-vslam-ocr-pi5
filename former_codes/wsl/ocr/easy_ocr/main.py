import cv2 as cv
import easyocr
import matplotlib.pyplot as plt

# import matplotlib
# matplotlib.use('Agg')  # Use a backend that works in WSL
# import matplotlib.pyplot as plt


# Read image
image_path = './assets/text2.png'
img = cv.imread(image_path)

# Instance text detector
reader = easyocr.Reader(['en'], gpu=True)

# Detect text on image
text_ = reader.readtext(img)
threshold = 0.25

# Draw bbox and text
for t_, t in enumerate(text_):
    print(t)

    bbox, text, score = t

    if score > threshold:
        # Draw bounding box
        cv.rectangle(img, bbox[0], bbox[2], (255, 0, 0), 5)

        # Define the text to be written
        text_to_write = text  # Use the detected text or customize it

        # Define the position for the text (top-left corner of the bounding box)
        text_position = (bbox[0][0], bbox[0][1] - 10)  # Adjust y-coordinate to place text above the box

        # Get the size of the text
        font = cv.FONT_HERSHEY_COMPLEX
        font_scale = 1
        font_thickness = 2
        (text_width, text_height), _ = cv.getTextSize(text_to_write, font, font_scale, font_thickness)

        # Define the background rectangle coordinates
        background_top_left = (text_position[0], text_position[1] - text_height)
        background_bottom_right = (text_position[0] + text_width, text_position[1])

        # Fill the text background rectangle
        cv.rectangle(img, background_top_left, background_bottom_right, (255, 0, 0), -1)  # -1 fills the rectangle

        # Draw the text on top of the green background
        cv.putText(img, 
                   text_to_write, 
                   text_position, 
                   font, 
                   font_scale, 
                   (255, 255, 255),  # White text
                   font_thickness
                )

# Display the result
plt.imshow(cv.cvtColor(img, cv.COLOR_BGR2RGB))
plt.title(label="Detected Text", loc="center")
plt.show()