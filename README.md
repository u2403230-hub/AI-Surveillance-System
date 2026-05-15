#  AI Surveillance System – Suspicious Behaviour Detection

An intelligent real-time surveillance system built using **Computer Vision and Deep Learning** to detect, track, and analyze human activities such as **intrusion and abnormal movement (running)**, with a live dashboard, alerts, and report generation.

---

##  Overview

This project simulates a real-world **AI-powered surveillance system** that processes video input to:

* Detect people in real-time
* Track individuals across frames
* Identify suspicious activities
* Generate alerts and logs
* Provide analytics through a web dashboard

The system integrates **YOLOv8, DeepSORT, OpenCV, and Flask** into a complete end-to-end solution.

---

##  Key Features

###  1. Real-Time Person Detection

* Uses **YOLOv8** for fast and accurate detection
* Detects only humans with confidence filtering

---

###  2. Multi-Object Tracking

* Uses **DeepSORT**
* Assigns unique IDs to each person
* Tracks movement across frames

---

###  3. Intrusion Detection

* Defines a **restricted zone**
* Detects when a person enters the zone
* Triggers:

  * Alerts
  * Screenshot capture
  * Event logging

---

###  4. Running Detection

* Calculates movement speed using frame-to-frame distance
* Detects abnormal fast motion
* Flags it as suspicious behavior

---

###  5. Alert System

* **Sound alerts** (real-time beep)
* **Event logs** with timestamps
* **WhatsApp alert integration** (optional)
* Includes:

  * Person ID
  * Location
  * Time

---

###  6. Heatmap Analysis

* Visualizes crowd movement patterns
* Highlights frequently visited areas
* Updates dynamically

---

###  7. Live Analytics Dashboard

* Built using **Flask + HTML + JavaScript**
* Displays:

  * Live video stream
  * People count
  * Threat level
  * Intrusion count
  * Running count

---

###  8. Graph Analytics

* Time-based data visualization using **Chart.js**
* Tracks:

  * People count over time
  * Intrusion events
  * Running events

---

###  9. Evidence Capture

* Automatically saves screenshots on detection
* Stored in `evidence/screenshots/`

---

###  10. PDF Report Generation

* Generates downloadable report using **ReportLab**
* Includes:

  * Summary statistics
  * Event logs
  * Graphs
  * Evidence images

---

##  Technologies Used

| Technology  | Purpose              |
| ----------- | -------------------- |
| Python      | Core programming     |
| YOLOv8      | Object detection     |
| DeepSORT    | Object tracking      |
| OpenCV      | Video processing     |
| Flask       | Backend + API        |
| HTML/CSS/JS | Frontend UI          |
| Chart.js    | Graph visualization  |
| NumPy       | Numerical operations |
| ReportLab   | PDF generation       |

---

##  Project Structure

```
AI-Surveillance-System/
│
├── app.py
├── yolov8n.pt
├── test.mp4
│
├── templates/
│   └── index.html
│
├── static/
│   └── script.js
│
├── evidence/
│   └── screenshots/
│
├── README.md
```

---

##  How to Run

### 1️ Clone the repository

```
git clone https://github.com/your-username/AI-Surveillance-System.git
cd AI-Surveillance-System
```

---

### 2️ Install dependencies

```
pip install ultralytics opencv-python flask numpy reportlab deep-sort-realtime pywhatkit
```

---

### 3️ Run the application

```
python app.py
```

---

### 4️ Open in browser

```
http://127.0.0.1:5000
```

---

##  System Workflow

1. Video is read frame-by-frame using OpenCV
2. YOLO detects people in each frame
3. DeepSORT assigns unique IDs and tracks movement
4. System analyzes:

   * Entry into restricted zones
   * Movement speed (running detection)
5. Alerts are triggered if suspicious behavior is detected
6. Data is sent to the Flask UI for live visualization
7. Heatmap and analytics are updated continuously
8. Reports can be generated and downloaded

---

##  Real-World Applications

*  Campus security
*  Office surveillance
*  Retail monitoring
*  Public places (stations, airports)
*  Industrial safety

---

## Limitations

* Depends on camera angle and video quality
* WhatsApp alerts depend on internet and browser session
* Running detection is based on simple motion threshold
* No facial recognition (can be added)

---

##  Future Improvements

* Real-time cloud alert system (Twilio, Firebase)
* Face recognition integration
* Multi-camera support
* Database storage for logs
* Advanced behavior detection (fight detection)
* Mobile app integration

---

##  Learning Outcomes

Through this project, I learned:

* Computer Vision (object detection & tracking)
* Real-time video processing
* AI model integration into applications
* Backend development using Flask
* Frontend dashboard design
* Event detection logic and alert systems
* Debugging and system optimization

---

##  Author

Developed as part of an internship project on **AI Surveillance and Suspicious Behaviour Detection**.

---

##  Conclusion

This project demonstrates how AI can be applied to build **intelligent surveillance systems** that enhance safety through automation, real-time monitoring, and actionable insights.

---
