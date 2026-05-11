from ultralytics import YOLO
import cv2
from deep_sort_realtime.deepsort_tracker import DeepSort
import time
import os
import pygame

# =========================
# LOAD YOLO MODEL
# =========================
model = YOLO("yolov8n.pt")

# =========================
# INITIALIZE TRACKER
# =========================
tracker = DeepSort(max_age=30)

# =========================
# INITIALIZE ALARM SYSTEM
# =========================
try:
    pygame.mixer.init()
    pygame.mixer.music.load("alarm.wav")
    sound_enabled = True
except:
    print("Alarm sound could not be loaded")
    sound_enabled = False

# =========================
# OPEN VIDEO
# =========================
cap = cv2.VideoCapture("test.mp4")

# =========================
# CREATE FOLDERS
# =========================
os.makedirs("evidence/screenshots", exist_ok=True)

# =========================
# STORE PREVIOUS POSITIONS
# =========================
previous_positions = {}

# =========================
# EVENT HISTORY
# =========================
event_history = []

# =========================
# ALERT COOLDOWN
# =========================
last_running_alert_time = 0
last_intrusion_alert_time = 0

alert_cooldown = 5  # seconds

# =========================
# RESTRICTED ZONE
# =========================
zone_x1 = 300
zone_y1 = 100
zone_x2 = 600
zone_y2 = 400

# =========================
# MAIN LOOP
# =========================
while True:

    # READ FRAME
    ret, frame = cap.read()

    if not ret:
        break

    # =========================
    # RUN YOLO DETECTION
    # =========================
    results = model(frame)

    detections = []

    # =========================
    # PROCESS DETECTIONS
    # =========================
    for r in results:

        boxes = r.boxes

        for box in boxes:

            cls = int(box.cls[0])

            # PERSON CLASS ONLY
            if cls == 0:

                x1, y1, x2, y2 = box.xyxy[0]

                conf = float(box.conf[0])

                detections.append(
                    (
                        [int(x1), int(y1),
                         int(x2 - x1),
                         int(y2 - y1)],
                        conf,
                        "person"
                    )
                )

    # =========================
    # UPDATE TRACKER
    # =========================
    tracks = tracker.update_tracks(detections, frame=frame)

    # =========================
    # DRAW RESTRICTED AREA
    # =========================
    cv2.rectangle(frame,
                  (zone_x1, zone_y1),
                  (zone_x2, zone_y2),
                  (255, 0, 0),
                  3)

    cv2.putText(frame,
                "RESTRICTED AREA",
                (zone_x1, zone_y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 0, 0),
                2)

    # =========================
    # PROCESS TRACKS
    # =========================
    for track in tracks:

        if not track.is_confirmed():
            continue

        track_id = track.track_id

        ltrb = track.to_ltrb()

        x1, y1, x2, y2 = map(int, ltrb)

        # =========================
        # DRAW PERSON BOX
        # =========================
        cv2.rectangle(frame,
                      (x1, y1),
                      (x2, y2),
                      (0, 255, 0),
                      2)

        # =========================
        # SHOW TRACK ID
        # =========================
        cv2.putText(frame,
                    f"ID: {track_id}",
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2)

        # =========================
        # CENTER POINT
        # =========================
        center_x = int((x1 + x2) / 2)
        center_y = int((y1 + y2) / 2)

        # DRAW CENTER POINT
        cv2.circle(frame,
                   (center_x, center_y),
                   5,
                   (0, 0, 255),
                   -1)

        # ====================================================
        # INTRUSION DETECTION
        # ====================================================
        if (zone_x1 < center_x < zone_x2 and
            zone_y1 < center_y < zone_y2):

            current_time_seconds = time.time()

            # ALERT COOLDOWN
            if current_time_seconds - last_intrusion_alert_time > alert_cooldown:

                last_intrusion_alert_time = current_time_seconds

                # PLAY ALARM
                if sound_enabled:
                  if not pygame.mixer.music.get_busy():
                    pygame.mixer.music.play()   

                # WARNING ON MAIN SCREEN
                cv2.putText(frame,
                            "INTRUSION DETECTED!",
                            (50, 100),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            1,
                            (0, 0, 255),
                            3)

                # CREATE ALERT POPUP
                intrusion_alert = frame.copy()

                # CURRENT TIME
                current_time = time.strftime("%Y-%m-%d %H:%M:%S")

                # ALERT TEXTS
                cv2.putText(intrusion_alert,
                            "ALERT: Restricted Area Intrusion",
                            (50, 100),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            1,
                            (0, 0, 255),
                            3)

                cv2.putText(intrusion_alert,
                            f"Track ID: {track_id}",
                            (50, 150),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.8,
                            (255, 255, 255),
                            2)

                cv2.putText(intrusion_alert,
                            f"Time: {current_time}",
                            (50, 200),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.8,
                            (255, 255, 255),
                            2)

                cv2.putText(intrusion_alert,
                            "Action: Security Team Dispatched",
                            (50, 250),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.8,
                            (255, 255, 255),
                            2)

                # SAVE SCREENSHOT
                current_timestamp = time.strftime("%Y%m%d_%H%M%S")

                intrusion_screenshot = (
                    f"evidence/screenshots/"
                    f"intrusion_ID{track_id}_{current_timestamp}.jpg"
                )

                cv2.imwrite(intrusion_screenshot, frame)

                # SAVE EVENT LOG
                log_message = (
                    f"[{current_time}] "
                    f"ALERT: Intrusion Detected | "
                    f"Track ID: {track_id} | "
                    f"Action: Security Team Dispatched\n"
                )

                with open("event_log.txt", "a") as log_file:
                    log_file.write(log_message)

                # STORE EVENT HISTORY
                event_history.append({
                    "time": current_time,
                    "event": "Intrusion Detected",
                    "track_id": track_id
                })

                # SHOW POPUP WINDOW
                cv2.imshow("INTRUSION ALERT", intrusion_alert)

        # ====================================================
        # RUNNING DETECTION
        # ====================================================
        if track_id in previous_positions:

            prev_x, prev_y = previous_positions[track_id]

            distance = ((center_x - prev_x) ** 2 +
                        (center_y - prev_y) ** 2) ** 0.5

            # RUNNING THRESHOLD
            if distance > 40:

                current_time_seconds = time.time()

                # ALERT COOLDOWN
                if current_time_seconds - last_running_alert_time > alert_cooldown:

                    last_running_alert_time = current_time_seconds

                    # PLAY ALARM
                    if not pygame.mixer.music.get_busy():
                        pygame.mixer.music.play()

                    # WARNING ON MAIN SCREEN
                    cv2.putText(frame,
                                "RUNNING DETECTED!",
                                (50, 50),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                1,
                                (0, 0, 255),
                                3)

                    # CREATE ALERT WINDOW
                    alert_frame = frame.copy()

                    # CURRENT TIME
                    current_time = time.strftime("%Y-%m-%d %H:%M:%S")

                    # ALERT TEXTS
                    cv2.putText(alert_frame,
                                "ALERT: Suspicious Running Detected",
                                (50, 100),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                1,
                                (0, 0, 255),
                                3)

                    cv2.putText(alert_frame,
                                f"Track ID: {track_id}",
                                (50, 150),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.8,
                                (255, 255, 255),
                                2)

                    cv2.putText(alert_frame,
                                f"Time: {current_time}",
                                (50, 200),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.8,
                                (255, 255, 255),
                                2)

                    cv2.putText(alert_frame,
                                "Action: Security Alert Triggered",
                                (50, 250),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.8,
                                (255, 255, 255),
                                2)

                    # SAVE SCREENSHOT
                    current_timestamp = time.strftime("%Y%m%d_%H%M%S")

                    screenshot_name = (
                        f"evidence/screenshots/"
                        f"running_alert_ID{track_id}_{current_timestamp}.jpg"
                    )

                    cv2.imwrite(screenshot_name, frame)

                    # SAVE EVENT LOG
                    log_message = (
                        f"[{current_time}] "
                        f"ALERT: Running Detected | "
                        f"Track ID: {track_id} | "
                        f"Action: Security Alert Triggered\n"
                    )

                    with open("event_log.txt", "a") as log_file:
                        log_file.write(log_message)

                    # STORE EVENT HISTORY
                    event_history.append({
                        "time": current_time,
                        "event": "Running Detected",
                        "track_id": track_id
                    })

                    # SHOW ALERT WINDOW
                    cv2.imshow("RUNNING ALERT", alert_frame)

        # =========================
        # UPDATE POSITION
        # =========================
        previous_positions[track_id] = (
            center_x,
            center_y
        )

    # =========================
    # SHOW MAIN WINDOW
    # =========================
    cv2.imshow("AI Surveillance System", frame)

    # =========================
    # EXIT KEY
    # =========================
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# =========================
# RELEASE EVERYTHING
# =========================
cap.release()
cv2.destroyAllWindows()