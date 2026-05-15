zone_x1, zone_y1, zone_x2, zone_y2 = 200,100,500,400
cx = (x1+x2)//2
cy = (y1+y2)//2

if zone_x1 < cx < zone_x2 and zone_y1 < cy < zone_y2:
    cv2.putText(frame,"INTRUSION",(x1,y1-30),
                cv2.FONT_HERSHEY_SIMPLEX,0.7,(0,0,255),2)

cv2.rectangle(frame,(zone_x1,zone_y1),(zone_x2,zone_y2),(0,0,255),2)
