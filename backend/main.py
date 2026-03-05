from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import json
from datetime import datetime

app = FastAPI(title="ThreatSense OS Backend")

# Allow web and edge nodes to communicate
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize SQLite Database (Immutable Ledger)
def init_db():
    conn = sqlite3.connect("threatsense.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS security_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            camera_id TEXT,
            alert_type TEXT,
            threat_level TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# WEBSOCKET ROUTE (For the HTML Web Dashboard)
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

manager = ConnectionManager()

@app.websocket("/ws/stream")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            
            conn = sqlite3.connect("threatsense.db")
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO security_alerts (camera_id, alert_type, threat_level, timestamp) VALUES (?, ?, ?, ?)",
                (payload.get("camera_id"), payload.get("alert_type"), payload.get("threat_level"), datetime.now().isoformat())
            )
            conn.commit()
            conn.close()
            print(f"🌐 [WEB AI ALERT] {payload.get('camera_id')} - {payload.get('alert_type')}")
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# REST API ROUTE (For the Python YOLO Camera)
class AlertPayload(BaseModel):
    camera_id: str
    alert_type: str
    threat_level: str
    confidence: float
    timestamp: str

@app.post("/api/alert")
async def receive_edge_alert(payload: AlertPayload):
    conn = sqlite3.connect("threatsense.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO security_alerts (camera_id, alert_type, threat_level, timestamp) VALUES (?, ?, ?, ?)",
        (payload.camera_id, payload.alert_type, payload.threat_level, payload.timestamp)
    )
    conn.commit()
    conn.close()
    
    print(f"🚨 [YOLO EDGE ALERT] {payload.camera_id} detected {payload.alert_type}!")
    return {"status": "success"}
