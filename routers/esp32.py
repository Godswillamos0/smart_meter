from typing import Annotated, Optional
from fastapi import APIRouter, Depends, Path, Request, status, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from database import SessionLocal
from sqlalchemy.orm import Session
from models import SmartMeter, MeterReadings
from datetime import datetime
import csv
import io


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


@router.post('/upload_csv', status_code=status.HTTP_201_CREATED)
async def upload_csv(db: db_dependency, file: UploadFile = File(...)):
    content = await file.read()
    decoded_content = content.decode('utf-8')
    csv_reader = csv.reader(io.StringIO(decoded_content))
    rows = list(csv_reader)

    if not rows:
        raise HTTPException(status_code=400, detail="Empty file")

    # Cache existing meters to minimize DB queries
    meters = db.query(SmartMeter).all()
    meter_map = {m.access_id: m for m in meters}

    # Skip header if it looks like one
    start_index = 0
    if rows[0] and rows[0][0] in ('id', 'meter_access_id'):
        start_index = 1

    for i in range(start_index, len(rows)):
        row = rows[i]
        if not row: continue

        try:
            # Support both download_csv format (6 cols) and direct format (5 cols)
            # download_csv: id, meter_access_id, voltage, current, power, energy
            if len(row) >= 6:
                access_id = row[1]
                vals = row[2:6]
            # direct: meter_access_id, voltage, current, power, energy
            elif len(row) >= 5:
                access_id = row[0]
                vals = row[1:5]
            else:
                continue

            voltage, current, power, energy = map(float, vals)
        except ValueError:
            continue

        meter = meter_map.get(access_id)
        if not meter:
            meter = SmartMeter(access_id=access_id)
            db.add(meter)
            db.flush() # Flush to generate ID for the new meter
            meter_map[access_id] = meter

        reading = MeterReadings(
            meter_id=meter.id,
            voltage=voltage,
            current=current,
            power=power,
            energy=energy
        )
        db.add(reading)

    db.commit()
    return {"message": "Successfully uploaded CSV data"}


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


@router.get('/download_csv')
async def download_data_from_db(db: db_dependency):
    meters = db.query(SmartMeter).all()
    meter_map = {str(m.id): m.access_id for m in meters}
    
    readings = db.query(MeterReadings).all()
    
    def iter_csv():
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow(['id', 'meter_access_id', 'voltage', 'current', 'power', 'energy'])
        yield output.getvalue()
        output.seek(0)
        output.truncate(0)
        
        for reading in readings:
            meter_access_id = meter_map.get(reading.meter_id, "Unknown")
            writer.writerow([reading.id, meter_access_id, reading.voltage, reading.current, reading.power, reading.energy])
            yield output.getvalue()
            output.seek(0)
            output.truncate(0)
            
    response = StreamingResponse(iter_csv(), media_type='text/csv')
    response.headers["Content-Disposition"] = "attachment; filename=all_meter_data.csv"
    return response
