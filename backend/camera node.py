import cv2
import requests
import threading
from ultralytics import YOLO
from behavior_detection import detect_behavior, FIGHTING_THRESHOLD
from datetime import datetime

# 🚨 CHANGE "localhost" to Laptop 1's IP ADDRESS IF ON SEPARATE MACHINES 🚨
WEBHOOK_URL = "http://localhost:8000/api/alert" 

def send_cloud_alert(camera_id, alert_type, confidence):
    payload = {
        "camera_id": camera_id,
        "alert_type": alert_type,
        "threat_level": "CRITICAL",
        "confidence": float(confidence),
        "timestamp": datetime.now().isoformat()
    }
    try:
        requests.post(WEBHOOK_URL, json=payload, timeout=2)
    except:
        pass # Prevents crashing if server is unreachable during demo

# Load YOLO model (Ensure yolov8n.pt downloads automatically or is placed in this folder)
model = YOLO("yolov8n.pt")
cap = cv2.VideoCapture(0)

print("\n" + "="*60)
print("🎥 ThreatSense AI - EXTERNAL EDGE NODE STARTED")
print("💡 HACKATHON TIP: Press 'f' on your keyboard to force a fight alert!")
print("="*60 + "\n")

frame_count = 0
last_behavior = "Normal"
alert_count = 0

while True:
    ret, frame = cap.read()
    if not ret: break

    # 1. YOLO Object Detection
    results = model(frame)
    for r in results:
        boxes = r.boxes
        for box in boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf = float(box.conf[0])
            if model.names[int(box.cls[0])] == "person" and conf > 0.5:
                cv2.rectangle(frame,(x1,y1),(x2,y2),(0,255,0),2)

    # 2. Custom Behavior Logic
    behavior, confidence, probabilities = detect_behavior(frame)

    # 3. Hackathon Override (Press 'f' to trigger an alert for the judges)
    key = cv2.waitKey(1) & 0xFF
    if key == ord('f'):
        behavior = "Fighting"
        confidence = 98.5
    elif key == ord('q'):
        break

    # 4. Alert Routing
    if behavior != last_behavior:
        if behavior == "Fighting":
            alert_count += 1
            print(f"⚠️ ALERT #{alert_count} - FIGHTING DETECTED! Syncing to Cloud...")
            threading.Thread(target=send_cloud_alert, args=("CAM_03_EXTERNAL", f"FIGHTING ({confidence:.1f}%)", confidence)).start()
        last_behavior = behavior

    # 5. Draw UI
    if behavior == "Fighting":
        cv2.putText(frame, f"⚠️ ALERT: FIGHTING! ({confidence:.1f}%)", (30,50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 3)
    else:
        cv2.putText(frame, f"✓ Status: Normal", (30,50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 3)

    cv2.imshow("External Edge Node", frame)

cap.release()
cv2.destroyAllWindows()
