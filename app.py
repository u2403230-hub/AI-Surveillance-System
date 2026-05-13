from flask import Flask, render_template, Response, jsonify
from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort
from flask import request

import cv2
import numpy as np
import time
import webbrowser
import threading
import base64


# =========================
# FLASK APP
# =========================
app = Flask(__name__)

# =========================
# LOAD YOLO MODEL
# =========================
model = YOLO("yolov8n.pt")

# =========================
# LOAD VIDEO
# =========================
cap = cv2.VideoCapture("test.mp4")

print("Video Opened:", cap.isOpened())

# =========================
# DEEPSORT TRACKER
# =========================
tracker = DeepSort(max_age=30)

# =========================
# FRAME SIZE
# =========================
frame_width = 720
frame_height = 480

# =========================
# HEATMAP
# =========================
heatmap = np.zeros(
    (frame_height, frame_width),
    dtype=np.float32
)

# =========================
# LIVE ANALYTICS
# =========================
total_people = 0
threat_level = "LOW"
intrusion_count = 0
fight_count = 0
running_count = 0
 # =========================
 # ANALYTICS HISTORY
 # =========================
people_history = []
running_history = []
intrusion_history = []
time_history = []

# =========================
# ALERT SYSTEM
# =========================
event_log = []

# =========================
# TRACK POSITIONS
# =========================
track_positions = {}

# =========================
# FRAME GENERATOR
# =========================
def generate_frames():

    global total_people
    global threat_level
    global heatmap
    global running_count
    global track_positions
    global event_log
    global intrusion_count
   

    while True:

        try:

            success, frame = cap.read()

            # Restart video when finished
            if not success:

                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue

            # Safety check
            if frame is None:
                continue

            # Resize frame
            frame = cv2.resize(
                frame,
                (frame_width, frame_height)
            )
            # =========================
            # RESTRICTED ZONE
            # =========================

            zone_x1 = 250
            zone_y1 = 150

            zone_x2 = 500
            zone_y2 = 400

            cv2.rectangle(
                frame,
                (zone_x1, zone_y1),
                (zone_x2, zone_y2),
                (0, 0, 255),
                 2
            )

            cv2.putText(
                frame,
                "RESTRICTED ZONE",
                (zone_x1, zone_y1 - 10),
                 cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2
            )

            # =========================
            # YOLO DETECTION
            # =========================
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
                            (
                                [x1, y1, x2 - x1, y2 - y1],
                                confidence,
                                'person'
                            )
                        )

                        people_count += 1

            total_people = people_count

            current_time = time.strftime("%H:%M:%S")

            people_history.append(total_people)
            running_history.append(running_count)
            intrusion_history.append(intrusion_count)
            time_history.append(current_time)

            # Keep only last 20 points (for clean graph)
            if len(people_history) > 20:
             people_history.pop(0)
             running_history.pop(0)
             intrusion_history.pop(0)
             time_history.pop(0)

            # =========================
            # THREAT LEVEL
            # =========================
            if total_people >= 8:

                threat_level = "HIGH"

            elif total_people >= 4:

                threat_level = "MEDIUM"

            else:

                threat_level = "LOW"

            # =========================
            # CROWD ALERT
            # =========================
            current_time = time.strftime("%H:%M:%S")

            if total_people >= 5:

                crowd_alert = (
                    f"[{current_time}] Crowd Activity Detected"
                )

                if crowd_alert not in event_log:

                    event_log.append(crowd_alert)

                    if len(event_log) > 10:
                        event_log.pop(0)

            # =========================
            # TRACKING
            # =========================
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

                # =========================
                # DRAW BOUNDING BOX
                # =========================
                cv2.rectangle(
                    frame,
                    (x1, y1),
                    (x2, y2),
                    (0, 255, 0),
                    2
                )

                # =========================
                # TRACK ID
                # =========================
                cv2.putText(
                    frame,
                    f"ID {track_id}",
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2
                )

                # =========================
                # CENTER POINT
                # =========================
                center_x = int((x1 + x2) / 2)
                center_y = int((y1 + y2) / 2)

                # =========================
                # HEATMAP
                # =========================
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
                # =========================
                # INTRUSION DETECTION
                # =========================

                if (

                     center_x > zone_x1 and
                     center_x < zone_x2 and
                     center_y > zone_y1 and
                     center_y < zone_y2

):

                  intrusion_count += 1

                  current_time = time.strftime("%H:%M:%S")

                  intrusion_alert = (
                    f"[{current_time}] Intrusion Detected - ID {track_id}"
    )

                  if intrusion_alert not in event_log:

                   event_log.append(intrusion_alert)

                   if len(event_log) > 10:
                     event_log.pop(0)

                # RED WARNING BOX
                cv2.rectangle(
                  frame,
                  (x1, y1),
                  (x2, y2),
                  (0, 0, 255),
                   3
    )

                cv2.putText(
                   frame,
                   "INTRUSION ALERT",
                   (x1, y1 - 60),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                   (0, 0, 255),
                    2
    )
                # =========================
                # SAVE POSITION
                # =========================
                track_positions[track_id] = (
                    center_x,
                    center_y
                )

            # =========================
            # HEATMAP DECAY
            # =========================
            heatmap *= 0.99

            # =========================
            # HEATMAP BLUR
            # =========================
            heatmap_blur = cv2.GaussianBlur(
                heatmap,
                (25, 25),
                0
            )

            # =========================
            # NORMALIZE HEATMAP
            # =========================
            heatmap_norm = cv2.normalize(
                heatmap_blur,
                None,
                0,
                255,
                cv2.NORM_MINMAX
            ).astype(np.uint8)

            # =========================
            # APPLY COLORMAP
            # =========================
            heatmap_color = cv2.applyColorMap(
                heatmap_norm,
                cv2.COLORMAP_JET
            )

            # =========================
            # OVERLAY HEATMAP
            # =========================
            frame = cv2.addWeighted(
                frame,
                0.7,
                heatmap_color,
                0.3,
                0
            )

            # =========================
            # DASHBOARD TITLE
            # =========================
            cv2.putText(
                frame,
                "AI SURVEILLANCE SYSTEM",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (255, 255, 255),
                2
            )

            # =========================
            # PEOPLE COUNT
            # =========================
            cv2.putText(
                frame,
                f"People Count: {total_people}",
                (20, 90),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 255),
                2
            )

            # =========================
            # THREAT COLOR
            # =========================
            threat_color = (0, 255, 0)

            if threat_level == "MEDIUM":

                threat_color = (0, 165, 255)

            elif threat_level == "HIGH":

                threat_color = (0, 0, 255)

            # =========================
            # THREAT TEXT
            # =========================
            cv2.putText(
                frame,
                f"Threat Level: {threat_level}",
                (20, 140),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                threat_color,
                3
            )

            # =========================
            # ENCODE FRAME
            # =========================
            ret, buffer = cv2.imencode(
                '.jpg',
                frame,
                [int(cv2.IMWRITE_JPEG_QUALITY), 80]
            )

            frame = buffer.tobytes()

            # =========================
            # STREAM FRAME
            # =========================
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

    return render_template('index.html')

# =========================
# VIDEO STREAM
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
# LIVE ALERTS API
# =========================
@app.route('/api/alerts')
def alerts():

    cleaned_alerts = [

        alert for alert in event_log

        if not alert.startswith("RUN_")
    ]

    return jsonify(cleaned_alerts)
# =========================
# ANALYTICS GRAPH API
# =========================
@app.route('/api/graph')
def graph_data():

    return jsonify({
        "time": time_history,
        "people": people_history,
        "running": running_history,
        "intrusion": intrusion_history
    })
@app.route('/save_graph', methods=['POST'])
def save_graph():

    data = request.json['image']

    image_data = data.split(",")[1]

    with open("graph.png", "wb") as f:
        f.write(base64.b64decode(image_data))

    return "OK"
# =========================
# PDF REPORT GENERATION
# =========================
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from flask import send_file
import os

@app.route('/download_report')
def download_report():
    from reportlab.platypus import Image

    file_path = "analytics_report.pdf"

    doc = SimpleDocTemplate(file_path)
    styles = getSampleStyleSheet()

    content = []

    # Title
    content.append(Paragraph("AI Surveillance Report", styles['Title']))
    content.append(Spacer(1, 20))

    # Summary
    content.append(Paragraph(f"Total People Detected: {total_people}", styles['Normal']))
    content.append(Paragraph(f"Running Events: {running_count}", styles['Normal']))
    content.append(Paragraph(f"Intrusions: {intrusion_count}", styles['Normal']))
    content.append(Paragraph(f"Threat Level: {threat_level}", styles['Normal']))

    content.append(Spacer(1, 20))

    # Event Logs
    content.append(Paragraph("Event Logs:", styles['Heading2']))
    content.append(Spacer(1, 10))

    for event in event_log[-10:]:
        content.append(Paragraph(event, styles['Normal']))
        content.append(Spacer(1, 5))
    # Add Graph Image
    if os.path.exists("graph.png"):

      content.append(Spacer(1, 20))
      content.append(Paragraph("Analytics Graph:", styles['Heading2']))
      content.append(Spacer(1, 10))

      content.append(Image("graph.png", width=400, height=200))
    # Build PDF
    doc.build(content)

    # Simulated Email Notification
    event_log.append("📧 Email Alert Sent (Simulated)")

    return send_file(file_path, as_attachment=True)


    # Add Screenshots
    content.append(Spacer(1, 20))
    content.append(Paragraph("Captured Evidence:", styles['Heading2']))

    screenshot_folder = "evidence/screenshots"

    if os.path.exists(screenshot_folder):

      images = os.listdir(screenshot_folder)[-3:]  # last 3 images

      for img in images:

        path = os.path.join(screenshot_folder, img)

        content.append(Spacer(1, 10))
        content.append(Image(path, width=300, height=200))
    current_time = time.strftime("%Y-%m-%d %H:%M:%S")

    content.append(Paragraph(f"Report Generated At: {current_time}", styles['Normal']))    

# =========================
# AUTO OPEN BROWSER
# =========================
def open_browser():

    webbrowser.open_new(
        "http://127.0.0.1:5000"
    )

# =========================
# MAIN
# =========================
if __name__ == '__main__':

    threading.Timer(
        1,
        open_browser
    ).start()

    app.run(debug=False)