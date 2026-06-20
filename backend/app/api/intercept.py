from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from app.db.database import get_db
from app.models.schemas import (
    ValveControlRequest,
    ValveControlResponse,
    InterceptInfo,
    InterceptResponse
)
from app.models.models import InterceptRecord, Package
from app.services.intercept_service import get_intercept_service
from app.services.valve_controller import get_valve_controller

router = APIRouter(prefix="/intercept", tags=["拦截控制"])

intercept_service = get_intercept_service()
valve_controller = get_valve_controller()


@router.get("/active", response_model=List[InterceptInfo], summary="获取当前活跃拦截列表")
async def get_active_intercepts():
    return intercept_service.get_active_intercepts()


@router.get("/history", summary="获取拦截历史记录")
async def get_intercept_history(
    skip: int = 0,
    limit: int = 20,
    tracking_number: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(InterceptRecord)

    if tracking_number:
        query = query.filter(InterceptRecord.tracking_number.contains(tracking_number))

    total = query.count()
    records = query.order_by(InterceptRecord.trigger_time.desc()).offset(skip).limit(limit).all()

    return {
        "success": True,
        "total": total,
        "records": records
    }


@router.post("/check/{tracking_number}", response_model=InterceptResponse, summary="检查包裹是否需要拦截")
async def check_intercept(
    tracking_number: str,
    db: Session = Depends(get_db)
):
    return intercept_service.check_package_intercept(db, tracking_number)


@router.post("/handle/{tracking_number}", summary="处理拦截记录")
async def handle_intercept(
    tracking_number: str,
    handled_by: str = Query(..., description="处理人"),
    remark: Optional[str] = Query(None, description="处理备注"),
    db: Session = Depends(get_db)
):
    success = intercept_service.handle_intercept(
        db=db,
        tracking_number=tracking_number,
        handled_by=handled_by,
        remark=remark
    )

    if not success:
        raise HTTPException(status_code=404, detail="未找到待处理的拦截记录")

    return {
        "success": True,
        "message": f"包裹 {tracking_number} 拦截已处理"
    }


@router.post("/clear/{tracking_number}", summary="清除活跃拦截状态")
async def clear_active_intercept(tracking_number: str):
    success = intercept_service.clear_active_intercept(tracking_number)

    if not success:
        raise HTTPException(status_code=404, detail="未找到活跃拦截记录")

    return {
        "success": True,
        "message": f"包裹 {tracking_number} 活跃拦截已清除"
    }


@router.get("/valves", summary="获取所有气动阀状态")
async def get_all_valves():
    valves = valve_controller.get_all_valves()
    return {
        "success": True,
        "valves": list(valves.values())
    }


@router.get("/valves/{valve_id}", summary="获取单个气动阀状态")
async def get_valve_status(valve_id: str):
    status = valve_controller.get_valve_status(valve_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"气动阀 {valve_id} 不存在")
    return {
        "success": True,
        "valve": status
    }


@router.post("/valves/control", response_model=ValveControlResponse, summary="控制气动阀")
async def control_valve(request: ValveControlRequest):
    if request.action == "open":
        result = valve_controller.open_valve(request.valve_id)
    elif request.action == "close":
        result = valve_controller.close_valve(request.valve_id)
    elif request.action == "trigger":
        result = valve_controller.trigger_valve(request.valve_id, request.duration)
    else:
        raise HTTPException(status_code=400, detail="无效的操作，支持: open, close, trigger")

    return ValveControlResponse(
        success=result.get("success", False),
        valve_id=result.get("valve_id", request.valve_id),
        action=request.action,
        message=result.get("message", "")
    )


@router.post("/valves/{valve_id}/trigger", summary="触发气动阀（脉冲）")
async def trigger_valve(
    valve_id: str,
    duration: Optional[float] = Query(None, description="持续时间(秒)")
):
    result = valve_controller.trigger_valve(valve_id, duration)

    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("message", "触发失败"))

    return {
        "success": True,
        "valve_id": valve_id,
        "duration": duration,
        "message": result.get("message", "触发成功")
    }


@router.get("/packages/status/{tracking_number}", summary="查询包裹状态")
async def get_package_status(
    tracking_number: str,
    db: Session = Depends(get_db)
):
    package = db.query(Package).filter(Package.tracking_number == tracking_number).first()

    if not package:
        raise HTTPException(status_code=404, detail="未找到该包裹信息")

    is_intercepted = package.status in ["客户拦截", "疑似违禁品"]
    intercept_level = "三级拦截" if is_intercepted else None

    return {
        "success": True,
        "package": package,
        "is_intercepted": is_intercepted,
        "intercept_level": intercept_level
    }
