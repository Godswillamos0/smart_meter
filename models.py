from database import Base
from sqlalchemy import Column, Integer, String, Float, DateTime

class SmartMeter(Base):
    __tablename__ = 'smart_meter'
    
    id=Column(Integer, primary_key=True, index=True)
    access_id = Column(String, unique=True, nullable=False)
    
    
class MeterReadings(Base): 
    __tablename__ = 'meter_readings'
    
    id=Column(Integer, primary_key=True, index=True)
    meter_id = Column(String, nullable=False)
    voltage = Column(String)
    current = Column(String)
    power = Column(String)
    energy = Column(String)