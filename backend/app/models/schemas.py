from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field


class PackageBase(BaseModel):
    tracking_number: str
    destination_city: Optional[str] = None
    status: str = "正常"
    sender: Optional[str] = None
    receiver: Optional[str] = None
    weight: Optional[int] = None


class PackageCreate(PackageBase):
    pass


class Package(PackageBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class HeatmapRegion(BaseModel):
    x: float = Field(..., description="区域左上角 x 比例 (0-1)")
    y: float = Field(..., description="区域左上角 y 比例 (0-1)")
    w: float = Field(..., description="区域宽度比例 (0-1)")
    h: float = Field(..., description="区域高度比例 (0-1)")
    confidence: float = Field(..., description="该区域最差置信度")
    issue_type: str = Field(..., description="问题类型: unclear / damaged")
    issue_label: str = Field(..., description="问题中文标签")


class HeatmapStats(BaseModel):
    avg_confidence: float
    problem_region_count: int
    problem_ratio: float
    timesteps: int


class HeatmapData(BaseModel):
    enabled: bool = False
    grid: List[List[float]] = Field(default_factory=list, description="2D 问题分数网格 (rows x cols, 0-1)")
    grid_rows: int = 0
    grid_cols: int = 0
    regions: List[HeatmapRegion] = Field(default_factory=list)
    stats: Optional[HeatmapStats] = None
    image_size: Optional[dict] = None


class ScanResult(BaseModel):
    tracking_number: str
    destination_city: str
    confidence: float
    processing_time: float
    heatmap: Optional[HeatmapData] = None


class ScanRecordBase(BaseModel):
    tracking_number: str
    destination_city: Optional[str] = None
    conveyor_id: Optional[str] = None
    is_intercepted: bool = False
    intercept_level: Optional[str] = None
    intercept_reason: Optional[str] = None
    recognition_confidence: Optional[int] = None


class ScanRecordCreate(ScanRecordBase):
    pass


class ScanRecord(ScanRecordBase):
    id: int
    scan_time: datetime

    class Config:
        from_attributes = True


class InterceptInfo(BaseModel):
    tracking_number: str
    intercept_level: str
    intercept_reason: str
    package_status: str
    destination_city: Optional[str] = None


class InterceptResponse(BaseModel):
    intercepted: bool
    intercept_level: Optional[str] = None
    intercept_reason: Optional[str] = None
    valve_triggered: bool = False
    package_info: Optional[Package] = None


class ValveControlRequest(BaseModel):
    valve_id: str
    action: str = Field(..., description="open 或 close")
    duration: Optional[float] = None


class ValveControlResponse(BaseModel):
    success: bool
    valve_id: str
    action: str
    message: str


class ConveyorBeltBase(BaseModel):
    belt_id: str
    name: str
    status: str = "运行中"
    speed: int = 60
    camera_id: Optional[str] = None
    valve_id: Optional[str] = None


class ConveyorBelt(ConveyorBeltBase):
    id: int

    class Config:
        from_attributes = True
