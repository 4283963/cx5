import time
import threading
from typing import Optional, Dict, List
from datetime import datetime

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.models import Package, InterceptRecord
from app.models.schemas import InterceptResponse, InterceptInfo
from app.services.valve_controller import get_valve_controller

settings = get_settings()


class InterceptService:
    def __init__(self):
        self.valve_controller = get_valve_controller()
        self._active_intercepts: Dict[str, Dict] = {}
        self._intercept_history: List[Dict] = []
        self._lock = threading.Lock()

    def check_package_intercept(
        self,
        db: Session,
        tracking_number: str,
        destination_city: Optional[str] = None
    ) -> InterceptResponse:
        package = db.query(Package).filter(
            Package.tracking_number == tracking_number
        ).first()

        if not package:
            return InterceptResponse(
                intercepted=False,
                package_info=None
            )

        is_intercepted = package.status in settings.INTERCEPT_LEVEL_THREE

        if not is_intercepted:
            return InterceptResponse(
                intercepted=False,
                package_info=package
            )

        intercept_level = self._determine_intercept_level(package.status)
        intercept_reason = self._get_intercept_reason(package.status)

        valve_triggered = self._trigger_valve(package.tracking_number, intercept_level)

        self._record_intercept(
            db,
            tracking_number=tracking_number,
            intercept_level=intercept_level,
            intercept_reason=intercept_reason,
            valve_triggered=valve_triggered
        )

        with self._lock:
            intercept_data = {
                "tracking_number": tracking_number,
                "intercept_level": intercept_level,
                "intercept_reason": intercept_reason,
                "package_status": package.status,
                "destination_city": package.destination_city or destination_city,
                "trigger_time": datetime.now().isoformat(),
                "valve_triggered": valve_triggered,
                "package": package
            }
            self._active_intercepts[tracking_number] = intercept_data
            self._intercept_history.append(intercept_data)
            if len(self._intercept_history) > 100:
                self._intercept_history.pop(0)

        return InterceptResponse(
            intercepted=True,
            intercept_level=intercept_level,
            intercept_reason=intercept_reason,
            valve_triggered=valve_triggered,
            package_info=package
        )

    def _determine_intercept_level(self, package_status: str) -> str:
        level_mapping = {
            "客户拦截": "三级拦截",
            "疑似违禁品": "三级拦截",
            "地址异常": "二级拦截",
            "超时未取": "一级拦截",
        }
        return level_mapping.get(package_status, "三级拦截")

    def _get_intercept_reason(self, package_status: str) -> str:
        reason_mapping = {
            "客户拦截": "客户申请拦截此包裹",
            "疑似违禁品": "安检系统检测到疑似违禁物品",
            "地址异常": "收件地址信息异常",
            "超时未取": "包裹超时未取件",
        }
        return reason_mapping.get(package_status, "未知原因")

    def _trigger_valve(self, tracking_number: str, intercept_level: str) -> bool:
        try:
            result = self.valve_controller.trigger_valve(
                valve_id="VALVE-001",
                duration=settings.VALVE_ACTIVE_DURATION
            )
            return result.get("success", False)
        except Exception as e:
            print(f"触发气动阀失败: {e}")
            return False

    def _record_intercept(
        self,
        db: Session,
        tracking_number: str,
        intercept_level: str,
        intercept_reason: str,
        valve_triggered: bool
    ) -> None:
        try:
            record = InterceptRecord(
                tracking_number=tracking_number,
                intercept_level=intercept_level,
                intercept_reason=intercept_reason,
                valve_triggered=valve_triggered
            )
            db.add(record)
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"记录拦截信息失败: {e}")

    def get_active_intercepts(self) -> List[InterceptInfo]:
        with self._lock:
            result = []
            for data in self._active_intercepts.values():
                result.append(InterceptInfo(
                    tracking_number=data["tracking_number"],
                    intercept_level=data["intercept_level"],
                    intercept_reason=data["intercept_reason"],
                    package_status=data["package_status"],
                    destination_city=data.get("destination_city")
                ))
            return result

    def get_intercept_history(self, limit: int = 20) -> List[Dict]:
        with self._lock:
            return self._intercept_history[-limit:]

    def clear_active_intercept(self, tracking_number: str) -> bool:
        with self._lock:
            if tracking_number in self._active_intercepts:
                del self._active_intercepts[tracking_number]
                return True
            return False

    def handle_intercept(
        self,
        db: Session,
        tracking_number: str,
        handled_by: str,
        remark: Optional[str] = None
    ) -> bool:
        try:
            records = db.query(InterceptRecord).filter(
                InterceptRecord.tracking_number == tracking_number,
                InterceptRecord.handled == False
            ).all()

            for record in records:
                record.handled = True
                record.handled_by = handled_by
                record.handled_at = datetime.now()
                record.remark = remark

            db.commit()

            self.clear_active_intercept(tracking_number)
            return True
        except Exception as e:
            db.rollback()
            print(f"处理拦截记录失败: {e}")
            return False


_intercept_service: Optional[InterceptService] = None


def get_intercept_service() -> InterceptService:
    global _intercept_service
    if _intercept_service is None:
        _intercept_service = InterceptService()
    return _intercept_service
