from typing import List
from fastapi import FastAPI, WebSocket, Depends
from fastapi.concurrency import asynccontextmanager
import models
from routers import esp32
from database import engine, SessionLocal
from sqlalchemy.orm import Session

class ConnectionManager:
    def __init__(self):
        # Store connections in a dictionary: meter_id -> List[WebSocket]
        self.active_connections: dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, meter_id: str):
        await websocket.accept()
        if meter_id not in self.active_connections:
            self.active_connections[meter_id] = []
        self.active_connections[meter_id].append(websocket)
        
    def disconnect(self, websocket: WebSocket, meter_id: str):
        if meter_id in self.active_connections:
            if websocket in self.active_connections[meter_id]:
                self.active_connections[meter_id].remove(websocket)
            if not self.active_connections[meter_id]:
                del self.active_connections[meter_id]
        
    async def broadcast(self, message: dict, meter_id: str):
        if meter_id in self.active_connections:
            for connection in self.active_connections[meter_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    # If sending fails, we assume the client disconnected
                    pass
            
manager =ConnectionManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    
app = FastAPI(lifespan=lifespan)

# Store manager in app state so routers can access it
app.state.manager = manager

models.Base.metadata.create_all(bind=engine)

app.include_router(esp32.router)

@app.websocket("/ws/{meter_id}")
async def websocket_endpoint(websocket: WebSocket, meter_id: str):
    await manager.connect(websocket, meter_id)
    
    # Optional: Send the latest data immediately upon connection
    db = SessionLocal()
    try:
        # Find the internal ID for this access_id/meter_id
        meter = db.query(models.SmartMeter).filter(models.SmartMeter.access_id == meter_id).first()
        if meter:
            # Fetch latest reading. Note: MeterReadings.meter_id seems to store the internal int ID
            latest = db.query(models.MeterReadings).filter(models.MeterReadings.meter_id == str(meter.id)).order_by(models.MeterReadings.id.desc()).first()
            if latest:
                await websocket.send_json({
                    "voltage": latest.voltage,
                    "current": latest.current,
                    "power": latest.power,
                    "energy": latest.energy,
                    "meter_id": meter_id
                })
    except Exception as e:
        print(f"Error fetching initial data: {e}")
    finally:
        db.close()

    try:
        while True:
            await websocket.receive_text()
    except Exception:
        manager.disconnect(websocket, meter_id)
