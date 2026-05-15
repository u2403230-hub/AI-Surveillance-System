from flask import Flask, render_template, Response, jsonify, request, send_file
from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort

import cv2
import numpy as np
import time
import webbrowser
import threading
import base64
import os
import winsound   # (Windows only)
import pywhatkit 

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet

# =========================
# FLASK APP
# =========================
app = Flask(__name__)

# =========================
# LOAD MODEL + VIDEO
# =========================
model = YOLO("yolov8n.pt")
cap = cv2.VideoCapture("test.mp4")

print("Video Opened:", cap.isOpened())

tracker = DeepSort(max_age=30)

# =========================
# FRAME SIZE
# =========================
frame_width = 720
frame_height = 480

# =========================
# HEATMAP
# =========================
heatmap = np.zeros((frame_height, frame_width), dtype=np.float32)

# =========================
# GLOBAL VARIABLES
# =========================
total_people = 0
threat_level = "LOW"
intrusion_count = 0
running_count = 0
fight_count = 0

people_history = []
running_history = []
intrusion_history = []
time_history = []

event_log = []
track_positions = {}
alert_cooldown = {}


whatsapp_alerted_ids = set()

# =========================
# EMAIL SIMULATION
# =========================
def send_email():
    current_time = time.strftime("%H:%M:%S")
    message = f"[{current_time}] 📧 Email Alert Sent (Simulated)"
    print(message)
    event_log.append(message)

# =========================
# FRAME GENERATOR
# =========================
def generate_frames():

    global total_people, threat_level, heatmap
    global running_count, intrusion_count
    global track_positions, event_log

    while True:

        try:
            success, frame = cap.read()

            if not success:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue

            frame = cv2.resize(frame, (frame_width, frame_height))

            # =========================
            # RESTRICTED ZONE
            # =========================
            zone_x1, zone_y1 = 250, 150
            zone_x2, zone_y2 = 500, 400

            cv2.rectangle(frame, (zone_x1, zone_y1), (zone_x2, zone_y2), (0,0,255), 2)

            # =========================
            # YOLO DETECTION
            # =========================
            results = model(frame)

            detections = []
            people_count = 0

            for result in results:
                for box in result.boxes:
                    cls = int(box.cls[0])
                    conf = float(box.conf[0])

                    if cls == 0 and conf > 0.4:
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        detections.append(([x1, y1, x2-x1, y2-y1], conf, 'person'))
                        people_count += 1

            total_people = people_count

            # =========================
            # GRAPH DATA
            # =========================
            current_time = time.strftime("%H:%M:%S")
            people_history.append(total_people)
            running_history.append(running_count)
            intrusion_history.append(intrusion_count)
            time_history.append(current_time)

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
            # TRACKING
            # =========================
            tracks = tracker.update_tracks(detections, frame=frame)

            for track in tracks:
        
                if not track.is_confirmed():
                    continue

                track_id = track.track_id
                x1, y1, x2, y2 = map(int, track.to_ltrb())

                cv2.rectangle(frame, (x1,y1), (x2,y2), (0,255,0), 2)
                cv2.putText(frame, f"ID {track_id}", (x1,y1-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)

                cx = int((x1+x2)/2)
                cy = int((y1+y2)/2)

                cv2.circle(heatmap, (cx,cy), 20, 1, -1)

                # =========================
                # RUNNING DETECTION + SCREENSHOT
                # =========================
                if track_id in track_positions:
                    px, py = track_positions[track_id]

                    dist = np.sqrt((cx-px)**2 + (cy-py)**2)

                    if dist > 80:

                     if track_id not in alert_cooldown:

                        winsound.Beep(1000, 500)

                         # 📱 WHATSAPP ALERT
                        pywhatkit.sendwhatmsg_instantly(
                           "+91 8590723110",
                          f"🚨 Running detected! ID: {track_id}",
                         wait_time=10
        )

                        running_count += 1
                        alert_cooldown[track_id] = time.time()

                        winsound.Beep(1000, 500)  # 🔊 SOUND ALERT

                        running_count += 1
                        alert_cooldown[track_id] = time.time()

                        t = time.strftime("%Y%m%d_%H%M%S")
                        filename = f"evidence/screenshots/running_ID{track_id}_{t}.jpg"
                        cv2.imwrite(filename, frame)

                        event_log.append(f"[{time.strftime('%H:%M:%S')}] Running - ID {track_id}")

                        running_count += 1
                        alert_cooldown[track_id] = time.time()

                        t = time.strftime("%Y%m%d_%H%M%S")
                        filename = f"evidence/screenshots/running_ID{track_id}_{t}.jpg"
                        cv2.imwrite(filename, frame)

                        event_log.append(f"[{time.strftime('%H:%M:%S')}] Running - ID {track_id}")

                        cv2.putText(frame, "RUNNING", (x1,y1-40),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,255), 2)

                # =========================
                # INTRUSION + SCREENSHOT
                # =========================
                global whatsapp_sent

                if zone_x1 < cx < zone_x2 and zone_y1 < cy < zone_y2:

                   if track_id not in alert_cooldown:

                     winsound.Beep(1500, 700)

                     # 📱 WHATSAPP ALERT (PASTE HERE)
                     if track_id not in whatsapp_alerted_ids:

                       current_time = time.strftime("%H:%M:%S")

                       pywhatkit.sendwhatmsg_instantly(
                        "+91 8590723110",
                        f"🚨 Intrusion detected!\n"
                        f"ID: {track_id}\n"
                          f"Location: Main Gate, College Campus\n"
                           f"Time: {current_time}",
                          wait_time=10
                    )

                     whatsapp_alerted_ids.add(track_id)

                intrusion_count += 1
                alert_cooldown[track_id] = time.time()

                t = time.strftime("%Y%m%d_%H%M%S")
                filename = f"evidence/screenshots/intrusion_ID{track_id}_{t}.jpg"
                cv2.imwrite(filename, frame)

                event_log.append(f"[{time.strftime('%H:%M:%S')}] Intrusion - ID {track_id}")

                
                cv2.rectangle(frame,(x1,y1),(x2,y2),(0,0,255),3)
                     
                    

                track_positions[track_id] = (cx,cy)

            # =========================
            # HEATMAP
            # =========================
            heatmap *= 0.99
            heat_blur = cv2.GaussianBlur(heatmap,(25,25),0)
            heat_norm = cv2.normalize(heat_blur,None,0,255,cv2.NORM_MINMAX).astype(np.uint8)
            heat_color = cv2.applyColorMap(heat_norm, cv2.COLORMAP_JET)
            frame = cv2.addWeighted(frame,0.7,heat_color,0.3,0)

            # =========================
            # TEXT
            # =========================
            cv2.putText(frame, f"People: {total_people}", (20,80),
                        cv2.FONT_HERSHEY_SIMPLEX,1,(0,255,255),2)

            # =========================
            # STREAM
            # =========================
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()

            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

        except Exception as e:
            print("FRAME ERROR:", e)
            continue

# =========================
# ROUTES
# =========================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video')
def video():
    return Response(generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/stats')
def stats():
    return jsonify({
        "people": total_people,
        "threat": threat_level,
        "intrusions": intrusion_count,
        "running": running_count,
        "fights":fight_count
    })

@app.route('/api/alerts')
def alerts():
    return jsonify(event_log[-10:])

@app.route('/api/graph')
def graph():
    return jsonify({
        "time": time_history,
        "people": people_history,
        "running": running_history,
        "intrusion": intrusion_history
    })

@app.route('/save_graph', methods=['POST'])
def save_graph():
    data = request.json['image']
    img = base64.b64decode(data.split(",")[1])
    with open("graph.png", "wb") as f:
        f.write(img)
    return "OK"

# =========================
# PDF REPORT
# =========================
@app.route('/download_report')
def download_report():

    file_path = "analytics_report.pdf"
    doc = SimpleDocTemplate(file_path)
    styles = getSampleStyleSheet()
    content = []

    content.append(Paragraph("AI Surveillance Report", styles['Title']))
    content.append(Spacer(1,20))

    content.append(Paragraph(f"People: {total_people}", styles['Normal']))
    content.append(Paragraph(f"Running: {running_count}", styles['Normal']))
    content.append(Paragraph(f"Intrusions: {intrusion_count}", styles['Normal']))

    content.append(Spacer(1,20))

    for e in event_log[-10:]:
        content.append(Paragraph(e, styles['Normal']))

    # Graph
    if os.path.exists("graph.png"):
        content.append(Spacer(1,20))
        content.append(Image("graph.png", width=400, height=200))

    doc.build(content)

    send_email()

    return send_file(file_path, as_attachment=True)

# =========================
# AUTO OPEN
# =========================
def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000")

if __name__ == '__main__':
    threading.Timer(1, open_browser).start()
    app.run(debug=False)
