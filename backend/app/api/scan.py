from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Form, Request
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session
from typing import Optional
import os
import uuid
import time
import asyncio
from datetime import datetime

from app.db.database import get_db
from app.models.schemas import ScanRecord
from app.models.models import ScanRecord as ScanRecordModel
from app.services.ocr_service import get_ocr_service
from app.services.intercept_service import get_intercept_service
from app.config import get_settings

settings = get_settings()
router = APIRouter(prefix="/scan", tags=["扫描识别"])

ocr_service = get_ocr_service()
intercept_service = get_intercept_service()

REQUEST_TIMEOUT = 45.0


def _save_image_sync(image_bytes: bytes, ext: str) -> str:
    upload_dir = "./uploads"
    os.makedirs(upload_dir, exist_ok=True)
    filename = f"{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:8]}{ext}"
    filepath = os.path.join(upload_dir, filename)
    with open(filepath, "wb") as f:
        f.write(image_bytes)
    return filepath


def _validate_and_get_ext(filename: Optional[str], file_bytes: bytes) -> str:
    if len(file_bytes) > settings.MAX_IMAGE_SIZE:
        raise HTTPException(status_code=400, detail="图片大小超过限制")

    if filename:
        allowed_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的图片格式，支持格式: {', '.join(allowed_extensions)}"
            )
        return file_ext

    return ".jpg"


@router.post("/waybill", response_model=dict, summary="扫描面单图片并识别")
async def scan_waybill(
    request: Request,
    image: UploadFile = File(..., description="面单图片文件"),
    conveyor_id: Optional[str] = Form("CONV-001", description="传送带ID"),
    db: Session = Depends(get_db),
):
    if not image.filename:
        raise HTTPException(status_code=400, detail="请上传图片文件")

    try:
        image_bytes = await asyncio.wait_for(image.read(), timeout=REQUEST_TIMEOUT)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=408, detail="图片上传超时")

    file_ext = _validate_and_get_ext(image.filename, image_bytes)

    try:
        ocr_result = await asyncio.wait_for(
            ocr_service.recognize_waybill(image_bytes),
            timeout=REQUEST_TIMEOUT,
        )
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="OCR识别超时，请重试")

    try:
        image_path = await run_in_threadpool(_save_image_sync, image_bytes, file_ext)
    except Exception as e:
        print(f"[scan.py] 保存图片失败: {e}")
        image_path = ""

    intercept_result = await run_in_threadpool(
        intercept_service.check_package_intercept,
        db,
        ocr_result["tracking_number"],
        ocr_result["destination_city"],
    )

    try:
        scan_record = ScanRecordModel(
            tracking_number=ocr_result["tracking_number"],
            destination_city=ocr_result["destination_city"],
            conveyor_id=conveyor_id,
            is_intercepted=intercept_result.intercepted,
            intercept_level=intercept_result.intercept_level,
            intercept_reason=intercept_result.intercept_reason,
            image_path=image_path,
            recognition_confidence=int(ocr_result["confidence"] * 100),
        )
        db.add(scan_record)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[scan.py] 保存扫描记录失败: {e}")

    elapsed_ms = None
    if hasattr(request.state, "start_time"):
        elapsed_ms = int((time.time() - request.state.start_time) * 1000)

    return {
        "success": True,
        "ocr_result": ocr_result,
        "intercept_result": intercept_result,
        "image_path": image_path,
        "scan_time": datetime.now().isoformat(),
        "server_processing_time_ms": elapsed_ms,
    }


@router.post("/waybill/base64", response_model=dict, summary="通过Base64图片扫描面单")
async def scan_waybill_base64(
    request: Request,
    image_data: dict,
    conveyor_id: Optional[str] = "CONV-001",
    db: Session = Depends(get_db),
):
    import base64

    try:
        image_base64 = image_data.get("image", "")
        if not image_base64:
            raise HTTPException(status_code=400, detail="图片数据不能为空")

        if "," in image_base64:
            image_base64 = image_base64.split(",")[1]

        try:
            image_bytes = base64.b64decode(image_base64)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"图片解码失败: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"图片处理失败: {str(e)}")

    file_ext = _validate_and_get_ext(None, image_bytes)

    try:
        ocr_result = await asyncio.wait_for(
            ocr_service.recognize_waybill(image_bytes),
            timeout=REQUEST_TIMEOUT,
        )
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="OCR识别超时，请重试")

    try:
        image_path = await run_in_threadpool(_save_image_sync, image_bytes, file_ext)
    except Exception as e:
        print(f"[scan.py] 保存图片失败: {e}")
        image_path = ""

    intercept_result = await run_in_threadpool(
        intercept_service.check_package_intercept,
        db,
        ocr_result["tracking_number"],
        ocr_result["destination_city"],
    )

    try:
        scan_record = ScanRecordModel(
            tracking_number=ocr_result["tracking_number"],
            destination_city=ocr_result["destination_city"],
            conveyor_id=conveyor_id,
            is_intercepted=intercept_result.intercepted,
            intercept_level=intercept_result.intercept_level,
            intercept_reason=intercept_result.intercept_reason,
            image_path=image_path,
            recognition_confidence=int(ocr_result["confidence"] * 100),
        )
        db.add(scan_record)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[scan.py] 保存扫描记录失败: {e}")

    elapsed_ms = None
    if hasattr(request.state, "start_time"):
        elapsed_ms = int((time.time() - request.state.start_time) * 1000)

    return {
        "success": True,
        "ocr_result": ocr_result,
        "intercept_result": intercept_result,
        "image_path": image_path,
        "scan_time": datetime.now().isoformat(),
        "server_processing_time_ms": elapsed_ms,
    }


@router.get("/records", summary="获取扫描记录列表")
async def get_scan_records(
    skip: int = 0,
    limit: int = 50,
    tracking_number: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(ScanRecordModel)

    if tracking_number:
        query = query.filter(ScanRecordModel.tracking_number.contains(tracking_number))

    total = query.count()
    records = query.order_by(ScanRecordModel.scan_time.desc()).offset(skip).limit(limit).all()

    return {
        "success": True,
        "total": total,
        "records": records,
    }


@router.get("/records/{record_id}", response_model=ScanRecord, summary="获取单条扫描记录")
async def get_scan_record(
    record_id: int,
    db: Session = Depends(get_db),
):
    record = db.query(ScanRecordModel).filter(ScanRecordModel.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="扫描记录不存在")
    return record


@router.get("/performance", summary="获取OCR服务性能统计")
async def get_ocr_performance():
    return {
        "success": True,
        "stats": ocr_service.get_performance_stats(),
    }
