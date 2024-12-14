from flask import Flask, Response, render_template_string
import cv2
import pickle
import cvzone
import numpy as np
from pymongo import MongoClient
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)

# MongoDB setup
client = MongoClient("mongodb+srv://sujal1234:sujal123456@cluster0.l6lil.mongodb.net/")
db = client["CarPlateDB"]
collection = db["ParkingStatus"]

# Video feed
cap = cv2.VideoCapture('carPark.mp4')

# Load parking positions
with open('CarParkPos', 'rb') as f:
    posList = pickle.load(f)

# Parking space dimensions
width, height = 107, 48

# Total parking spaces
TOTAL_SPACES = 69

def checkParkingSpace(imgPro, img):
    """Check parking spaces and display status."""
    spaceCounter = 0
    vip_slots = []  # List to store VIP slot numbers
    common_slots = []  # List to store Common slot numbers

    for index, pos in enumerate(posList):
        x, y = pos
        imgCrop = imgPro[y:y + height, x:x + width]
        count = cv2.countNonZero(imgCrop)

        if count < 900:
            color = (0, 255, 0)
            thickness = 5
            if index < 10:
                vip_slots.append(index + 1)
            else:
                common_slots.append(index + 1)
            spaceCounter += 1
        else:
            color = (0, 0, 255)
            thickness = 2

        # Draw the rectangle and display the slot number
        cv2.rectangle(img, pos, (pos[0] + width, pos[1] + height), color, thickness)
        cvzone.putTextRect(img, f"{index + 1}", (x + 5, y + 20), scale=1,
                           thickness=2, offset=0, colorR=color)

    # Display free slots and count
    free_slots_text = f"VIP Slots: {', '.join(map(str, vip_slots))}, Common Slots: {', '.join(map(str, common_slots))}" if spaceCounter else "No Free Slots"
    cvzone.putTextRect(img, f'Free: {spaceCounter}/{TOTAL_SPACES}', (100, 50), scale=3,
                       thickness=5, offset=20, colorR=(0, 200, 0))  # Green background
    cvzone.putTextRect(img, free_slots_text, (100, 100), scale=1,
                       thickness=2, offset=10, colorR=(0, 200, 0), colorT=(255, 255, 255))  # Green bg, white text

    # Update MongoDB with VIP and Common slots and count
    update_mongodb_realtime(vip_slots, common_slots, spaceCounter)

def update_mongodb_realtime(vip_slots, common_slots, free_count):
    """Update MongoDB with VIP and Common slots along with free count."""
    update = {
        "$set": {
            "timestamp": datetime.now(),
            "free_count": free_count,
            "total_spaces": TOTAL_SPACES,
            "vip_slots": vip_slots,
            "common_slots": common_slots
        }
    }
    collection.update_one({}, update, upsert=True)

def generate_frames():
    """Generate video frames for Flask app."""
    while True:
        if cap.get(cv2.CAP_PROP_POS_FRAMES) == cap.get(cv2.CAP_PROP_FRAME_COUNT):
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

        success, frame = cap.read()
        if not success:
            break

        # Process the frame
        imgGray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        imgBlur = cv2.GaussianBlur(imgGray, (3, 3), 1)
        imgThreshold = cv2.adaptiveThreshold(
            imgBlur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 25, 16
        )
        imgMedian = cv2.medianBlur(imgThreshold, 5)
        kernel = np.ones((3, 3), np.uint8)
        imgDilate = cv2.dilate(imgMedian, kernel, iterations=1)

        # Call parking space detection
        checkParkingSpace(imgDilate, frame)

        # Encode the frame to bytes
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    """Route to stream video."""
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index():
    """Home route."""
    return render_template_string("<h1>Parking Detection</h1><img src='/video_feed' style='width:900px; height:auto;'>")

if __name__ == "__main__":
    app.run(debug=True)
