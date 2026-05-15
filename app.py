import winsound, time, os

if dist > 80:
    winsound.Beep(1000,500)

    filename = f"screenshot_{track_id}_{int(time.time())}.jpg"
    cv2.imwrite(filename, frame)
