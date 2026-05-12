from flask import Flask, render_template, Response, jsonify
from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort

import cv2
import numpy as np
import time
import webbrowser

# =========================
# FLASK APP
# =========================
app = Flask(__name__)

# =========================
# LOAD YOLO MODEL
# =========================
model = YOLO("yolov8n.pt")

# =========================
# INITIALIZE TRACKER
# =========================
tracker = DeepSort(
    max_age=30
)

# =========================
# VIDEO SOURCE
# =========================
cap = cv2.VideoCapture("test.mp4")

print("Video Opened:", cap.isOpened())

# =========================
# VIDEO SETTINGS
# =========================
frame_width = 720
frame_height = 480

# =========================
# HEATMAP SETUP
# =========================
heatmap = np.zeros(
    (frame_height, frame_width),
    dtype=np.float32
)

# =========================
# ANALYTICS VARIABLES
# =========================
total_people = 0
threat_level = "LOW"
intrusion_count = 0
fight_count = 0
running_count = 0
event_log = []
track_positions = {}

# =========================
# GENERATE VIDEO FRAMES
# =========================
def generate_frames():

    global total_people
    global threat_level
    global heatmap
    global running_count
    global track_positions
    global event_log

    while True:

    try:

        success, frame = cap.read()

        if not success:

            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue

        if frame is None:
            continue

        # Resize frame
        frame = cv2.resize(frame, (720, 480))

        # YOLO Detection
        results = model(frame)

        detections = []

        people_count = 0

        for result in results:

            boxes = result.boxes

            for box in boxes:

                cls = int(box.cls[0])

                confidence = float(box.conf[0])

                # PERSON CLASS
                if cls == 0 and confidence > 0.4:

                    x1, y1, x2, y2 = map(
                        int,
                        box.xyxy[0]
                    )

                    detections.append(
                        ([x1, y1, x2 - x1, y2 - y1],
                         confidence,
                         'person')
                    )

                    people_count += 1

        total_people = people_count

        # Threat Level
        if total_people >= 8:
            threat_level = "HIGH"

        elif total_people >= 4:
            threat_level = "MEDIUM"

        else:
            threat_level = "LOW"

        # DeepSORT Tracking
        tracks = tracker.update_tracks(
            detections,
            frame=frame
        )

        for track in tracks:

            if not track.is_confirmed():
                continue

            track_id = track.track_id

            ltrb = track.to_ltrb()

            x1, y1, x2, y2 = map(int, ltrb)

            # Bounding Box
            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2
            )

            # ID Text
            cv2.putText(
                frame,
                f"ID {track_id}",
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2
            )

            center_x = int((x1 + x2) / 2)
            center_y = int((y1 + y2) / 2)

            # Heatmap Points
            cv2.circle(
                heatmap,
                (center_x, center_y),
                20,
                1,
                -1
            )

            # =========================
            # RUNNING DETECTION
            # =========================

            if track_id in track_positions:

                prev_x, prev_y = track_positions[track_id]

                distance = np.sqrt(
                    (center_x - prev_x) ** 2 +
                    (center_y - prev_y) ** 2
                )

                # RUNNING THRESHOLD
                if distance > 80:

                    current_time = time.strftime("%H:%M:%S")

                    alert_key = f"RUN_{track_id}"

                    if (
                        len(event_log) == 0
                        or event_log[-1] != alert_key
                    ):

                        running_count = min(
                            running_count + 1,
                            50
                        )

                        event_log.append(alert_key)

                        event_log.append(
                            f"[{current_time}] Running Detected - ID {track_id}"
                        )

                        if len(event_log) > 10:
                            event_log.pop(0)

                        # ALERT TEXT
                        cv2.putText(
                            frame,
                            "RUNNING DETECTED",
                            (x1, y1 - 40),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.8,
                            (0, 0, 255),
                            2
                        )

            # Store Previous Position
            track_positions[track_id] = (
                center_x,
                center_y
            )

        # Heatmap Decay
        heatmap *= 0.99

        # Blur Heatmap
        heatmap_blur = cv2.GaussianBlur(
            heatmap,
            (25, 25),
            0
        )

        # Normalize
        heatmap_norm = cv2.normalize(
            heatmap_blur,
            None,
            0,
            255,
            cv2.NORM_MINMAX
        ).astype(np.uint8)

        # Apply Color Map
        heatmap_color = cv2.applyColorMap(
            heatmap_norm,
            cv2.COLORMAP_JET
        )

        # Overlay Heatmap
        frame = cv2.addWeighted(
            frame,
            0.7,
            heatmap_color,
            0.3,
            0
        )

        # Dashboard Text
        cv2.putText(
            frame,
            "AI SURVEILLANCE SYSTEM",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 255, 255),
            2
        )

        cv2.putText(
            frame,
            f"People Count: {total_people}",
            (20, 90),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 255),
            2
        )

        # Threat Color
        threat_color = (0, 255, 0)

        if threat_level == "MEDIUM":
            threat_color = (0, 165, 255)

        elif threat_level == "HIGH":
            threat_color = (0, 0, 255)

        cv2.putText(
            frame,
            f"Threat Level: {threat_level}",
            (20, 140),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            threat_color,
            3
        )

        # Encode Frame
        ret, buffer = cv2.imencode(
            '.jpg',
            frame,
            [int(cv2.IMWRITE_JPEG_QUALITY), 80]
        )

        frame = buffer.tobytes()

        yield (
            b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n'
            + frame +
            b'\r\n'
        )

    except Exception as e:

        print("FRAME ERROR:", e)

         continue

# =========================
# HOME PAGE
# =========================
@app.route('/')
def index():

    return render_template(
        'index.html'
    )

# =========================
# VIDEO STREAM ROUTE
# =========================
@app.route('/video')
def video():

    return Response(
        generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )
# =========================
# LIVE ANALYTICS API
# =========================
@app.route('/api/stats')
def stats():

    return jsonify({

        "people": total_people,
        "threat": threat_level,
        "intrusions": intrusion_count,
        "fights": fight_count,
        "running": running_count

    })

# =========================
# LIVE ALERT API
# =========================
@app.route('/api/alerts')
def alerts():

    return jsonify(event_log)
# =========================
# RUN FLASK APP
# =========================
if __name__ == "__main__":

    webbrowser.open(
        "http://127.0.0.1:5000"
    )

    app.run(debug=False)