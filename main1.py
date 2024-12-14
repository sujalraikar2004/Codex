import cv2
import pandas as pd
from ultralytics import YOLO
import cvzone
import numpy as np
import pytesseract
import pyttsx3
import pyautogui
from datetime import datetime
from pymongo import MongoClient

# Set the Tesseract-OCR path
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# MongoDB connection setup
client = MongoClient("mongodb+srv://sujal1234:sujal123456@cluster0.l6lil.mongodb.net/")  # Replace with your MongoDB connection string if using MongoDB Atlas
db = client["CarPlateDB"]  # Database name
collection = db["CarPlateData"]  # Collection name
registered_cars_collection = db["car"]  # Collection with registered car details

# Initialize Text-to-Speech Engine
engine = pyttsx3.init()
engine.setProperty('rate', 150)  # Adjust speaking speed
engine.setProperty('volume', 1.0)  # Max volume

# Load YOLO model
model = YOLO('best.pt')

def speak_message(message):
    """Speak the provided message."""
    engine.say(message)
    engine.runAndWait()

# Mouse callback for debugging
def RGB(event, x, y, flags, param):
    if event == cv2.EVENT_MOUSEMOVE:
        point = [x, y]
        print(point)

cv2.namedWindow('RGB')
cv2.setMouseCallback('RGB', RGB)

# Load the video
cap = cv2.VideoCapture('mycarplate.mp4')

# Adjust video speed
fps = cap.get(cv2.CAP_PROP_FPS)
frame_delay = int((1 / fps) * 1000 * 4)  # 0.25x speed

# Load class names
with open("coco1.txt", "r") as my_file:
    class_list = my_file.read().splitlines()

# Define the area of interest
area = [(27, 417), (16, 456), (1015, 451), (992, 417)]

# Variables to manage detections
count = 0
processed_numbers = set()

# Main loop
while True:
    ret, frame = cap.read()
    count += 1

    if count % 3 != 0:
        continue

    if not ret:
        break

    # Resize the frame
    frame = cv2.resize(frame, (1020, 500))

    # Run YOLO model
    results = model.predict(frame)
    a = results[0].boxes.data.cpu().numpy()  # Move tensor to CPU and convert to NumPy
    px = pd.DataFrame(a).astype("float")

    # Process detected boxes
    for index, row in px.iterrows():
        x1 = int(row[0])
        y1 = int(row[1])
        x2 = int(row[2])
        y2 = int(row[3])

        d = int(row[5])
        c = class_list[d]
        cx = int((x1 + x2) / 2)
        cy = int((y1 + y2) / 2)

        result = cv2.pointPolygonTest(np.array(area, np.int32), (cx, cy), False)

        if result >= 0:
            crop = frame[y1:y2, x1:x2]
            gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
            gray = cv2.bilateralFilter(gray, 10, 20, 20)

            text = pytesseract.image_to_string(gray).strip()
            text = text.replace('(', '').replace(')', '').replace(',', '').replace(']', '').replace(" ","").replace("U","J").replace("O","Q")

            if text not in processed_numbers:
                processed_numbers.add(text)
                current_datetime = datetime.now()
                date_str = current_datetime.strftime("%Y-%m-%d")
                time_str = current_datetime.strftime("%H:%M:%S")

                # Check if car is registered
                registered_car = registered_cars_collection.find_one({"numberplate": text})
                if registered_car:
                    message = f"Car {text} is registered. Let it go."
                    print(message)
                    speak_message(message)
                else:
                    message = f"Car {text} is not registered. Do not let it go."
                    print(message)
                    speak_message(message)
                    pyautogui.alert(text=message, title="Unregistered Vehicle Alert", button="OK")

                # Save detected car data to MongoDB
                document = {
                    "NumberPlate": text,
                    "Date": date_str,
                    "Time": time_str
                }
                collection.insert_one(document)

                # Draw rectangle and display crop
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 1)
                cv2.imshow('crop', crop)

    # Draw the area of interest
    cv2.polylines(frame, [np.array(area, np.int32)], True, (255, 0, 0), 2)
    cv2.imshow("RGB", frame)

    if cv2.waitKey(frame_delay) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
