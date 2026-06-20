from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.sql import func

from app.db.database import Base


class Package(Base):
    __tablename__ = "packages"

    id = Column(Integer, primary_key=True, index=True)
    tracking_number = Column(String(50), unique=True, index=True, nullable=False)
    destination_city = Column(String(100))
    status = Column(String(50), default="正常", index=True)
    sender = Column(String(100))
    receiver = Column(String(100))
    weight = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class ScanRecord(Base):
    __tablename__ = "scan_records"

    id = Column(Integer, primary_key=True, index=True)
    tracking_number = Column(String(50), index=True)
    destination_city = Column(String(100))
    scan_time = Column(DateTime(timezone=True), server_default=func.now())
    conveyor_id = Column(String(50))
    is_intercepted = Column(Boolean, default=False)
    intercept_level = Column(String(20))
    intercept_reason = Column(String(200))
    image_path = Column(String(500))
    recognition_confidence = Column(Integer)


class InterceptRecord(Base):
    __tablename__ = "intercept_records"

    id = Column(Integer, primary_key=True, index=True)
    tracking_number = Column(String(50), index=True)
    intercept_level = Column(String(20), nullable=False)
    intercept_reason = Column(String(200))
    valve_triggered = Column(Boolean, default=False)
    trigger_time = Column(DateTime(timezone=True), server_default=func.now())
    handled = Column(Boolean, default=False)
    handled_by = Column(String(50))
    handled_at = Column(DateTime(timezone=True))
    remark = Column(Text)


class ConveyorBelt(Base):
    __tablename__ = "conveyor_belts"

    id = Column(Integer, primary_key=True, index=True)
    belt_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100))
    status = Column(String(20), default="运行中")
    speed = Column(Integer, default=60)
    camera_id = Column(String(50))
    valve_id = Column(String(50))
