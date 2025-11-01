import numpy as np
from ultralytics import YOLO
import cv2
import cvzone
import math
import time
from sort import *

# Open video file or webcam
cap = cv2.VideoCapture("./video/Video.mp4")  # For Webcam, you can uncomment the lines below and set the webcam parameters
# cap.set(3, 1280)
# cap.set(4, 720)
# cap = cv2.VideoCapture("Video3.mp4")  # For Video

# Load YOLO model
model = YOLO("../Yolo-Weights/yolov8l.pt")

# Class names for YOLO
classNames = ["person", "bicycle", "car", "motorbike", "aeroplane", "bus", "train", "truck", "boat",
              "traffic light", "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat",
              "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "backpack", "umbrella",
              "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard", "sports ball", "kite", "baseball bat",
              "baseball glove", "skateboard", "surfboard", "tennis racket", "bottle", "wine glass", "cup",
              "fork", "knife", "spoon", "bowl", "banana", "apple", "sandwich", "orange", "broccoli",
              "carrot", "hot dog", "pizza", "donut", "cake", "chair", "sofa", "pottedplant", "bed",
              "diningtable", "toilet", "tvmonitor", "laptop", "mouse", "remote", "keyboard", "cell phone",
              "microwave", "oven", "toaster", "sink", "refrigerator", "book", "clock", "vase", "scissors",
              "teddy bear", "hair drier", "toothbrush"]

# Initialize previous and current time for FPS calculation
prev_frame_time = 0
new_frame_time = 0

# Load mask
mask = cv2.imread("Masks/mask.png")

# Initialize SORT tracker
tracker = Sort(max_age=20, min_hits=3, iou_threshold=0.3)
totalCount = []
Count = 0

# Define start and end points for counting
start = [450, 347, 620, 347]
end = [300, 447, 600, 447]

while True:
    new_frame_time = time.time()
    success, img = cap.read()

    if not success:
        break

    # Resize mask to match video frame size
    mask_resized = cv2.resize(mask, (img.shape[1], img.shape[0]))
    imgRegion = cv2.bitwise_and(img, mask_resized)

    imgGraphics = cv2.imread("assets/graphics.png", cv2.IMREAD_UNCHANGED)
    cvzone.overlayPNG(img, imgGraphics, (0, 0))
    results = model(imgRegion, stream=True)

    detections = np.empty((0, 5))
    for r in results:
        boxes = r.boxes
        for box in boxes:
            x1, y1, x2, y2 = box.xyxy[0]
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            w, h = x2 - x1, y2 - y1

            conf = math.ceil((box.conf[0] * 100)) / 100
            cls = int(box.cls[0])
            currentClass = classNames[cls]

            if (currentClass in ["car", "truck", "bus", "motorbike"] and conf > 0.3):
                cvzone.cornerRect(img, (x1, y1, w, h), l=9)
                currentArray = np.array([x1, y1, x2, y2, conf])
                detections = np.vstack((detections, currentArray))

    resultsTracker = tracker.update(detections)
    cv2.line(img, (start[0], start[1]), (start[2], start[3]), (255, 0, 0), 5)
    cv2.line(img, (end[0], end[1]), (end[2], end[3]), (255, 0, 0), 5)

    for result in resultsTracker:
        x1, y1, x2, y2, Id = result
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
        w, h = x2 - x1, y2 - y1
        cvzone.cornerRect(img, (x1, y1, w, h), l=9, rt=2, colorR=(0, 0, 255))  # Red rect
        cvzone.putTextRect(img, f'{int(Id)}', (max(0, x1), max(35, y1)), scale=2, thickness=3, offset=10)
        cx, cy = x1 + w // 2, y1 + h // 2
        cv2.circle(img, (cx, cy), 5, (0, 0, 255), cv2.FILLED)

        if start[0] < cx < start[2] and start[1] - 15 < cy < start[1] + 15:
            if totalCount.count(Id) == 0:
                totalCount.append(Id)
                Count += 1
                cv2.line(img, (start[0], start[1]), (start[2], start[3]), (0, 255, 0), 5)

        if end[0] < cx < end[2] and end[1] - 15 < cy < end[1] + 15:
            if totalCount.count(Id) != 0:
                totalCount.remove(Id)
                Count -= 1
                cv2.line(img, (end[0], end[1]), (end[2], end[3]), (255, 0, 0), 5)

    cv2.putText(img, str(Count), (255, 100), cv2.FONT_HERSHEY_PLAIN, 5, (50, 50, 255), 8)

    # Calculate FPS and control frame rate
    fps = 1 / (new_frame_time - prev_frame_time)
    prev_frame_time = new_frame_time
    print(f"FPS: {fps:.2f}")

    # Display the frame
    cv2.imshow("Image", img)

    # Introduce delay to achieve ~30 FPS
    if cv2.waitKey(int(1000 / 30)) & 0xFF == ord('q'):
        break

# Release resources
cap.release()
cv2.destroyAllWindows()
