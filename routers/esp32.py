from typing import Annotated, Optional
from fastapi import APIRouter, Depends, Path, Request, status, HTTPException
from pydantic import BaseModel, Field
from database import SessionLocal
from sqlalchemy.orm import Session
from models import SmartMeter, MeterReadings
from datetime import datetime


router = APIRouter(
    tags=['esp32'],
    prefix='/esp'
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class DataRequest(BaseModel):
    voltage: float = Field(default=None)
    current:float = Field(default=None)
    power:float = Field(default=None)
    energy: float = Field(default=None)
    time_stamp: datetime

    class Config:
        from_attributes = True


 
latest_data: Optional[SmartMeter]=None
db_dependency = Annotated[Session, Depends(get_db)]



async def get_latest_data():
    global latest_data
    if latest_data is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
    return DataRequest.from_orm(latest_data)


class ReadingRequest(BaseModel):
    voltage: float
    current: float
    power:float
    energy: float   


@router.post('/{device_id}', status_code=status.HTTP_201_CREATED)
async def send_data(request: Request,
                    db: db_dependency,
                    read: ReadingRequest,
                    device_id = Path(...)
                    ):
    meter_model = db.query(SmartMeter).filter(SmartMeter.access_id==device_id).first()
    
    if not meter_model:
        #add meter
        db_meter = SmartMeter(
            access_id = device_id
        )
        db.add(db_meter)
        db.flush()
        
        db_meter_reading = MeterReadings(
            meter_id = db_meter.id,
            voltage = read.voltage,
            current = read.current,
            power = read.power,
            energy = read.energy
        )

        db.add(db_meter_reading)
        db.commit()
    
    else:
        db_meter_reading = MeterReadings(
            meter_id = meter_model.id,
            voltage = read.voltage,
            current = read.current,
            power = read.power,
            energy = read.energy
        )

        db.add(db_meter_reading)
        db.commit()

    # Broadcast the new reading to connected websockets
    if hasattr(request.app.state, 'manager'):
        message = {
            "voltage": read.voltage,
            "current": read.current,
            "power": read.power,
            "energy": read.energy,
            "meter_id": device_id
        }
        await request.app.state.manager.broadcast(message, device_id)
