track_positions = {}
if track_id in track_positions:
    px, py = track_positions[track_id]
    dist = ((cx-px)**2 + (cy-py)**2)**0.5

    if dist > 80:
        cv2.putText(frame,"RUNNING",(x1,y1-50),
                    cv2.FONT_HERSHEY_SIMPLEX,0.7,(0,0,255),2)

track_positions[track_id] = (cx,cy)
