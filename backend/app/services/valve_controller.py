import threading
import time
from typing import Dict, Optional
from datetime import datetime

from app.config import get_settings

settings = get_settings()


class ValveController:
    def __init__(self):
        self._valves: Dict[str, Dict] = {}
        self._lock = threading.Lock()
        self._gpio_available = False
        self._gpio = None

        self._init_valves()
        self._init_gpio()

    def _init_valves(self) -> None:
        self._valves["VALVE-001"] = {
            "id": "VALVE-001",
            "name": "一号气动阀",
            "status": "closed",
            "conveyor_id": "CONV-001",
            "last_trigger": None,
            "trigger_count": 0
        }
        self._valves["VALVE-002"] = {
            "id": "VALVE-002",
            "name": "二号气动阀",
            "status": "closed",
            "conveyor_id": "CONV-002",
            "last_trigger": None,
            "trigger_count": 0
        }

    def _init_gpio(self) -> None:
        try:
            import RPi.GPIO as GPIO
            self._gpio = GPIO
            self._gpio.setmode(GPIO.BCM)
            self._gpio.setwarnings(False)
            self._gpio.setup(settings.VALVE_GPIO_PIN, GPIO.OUT)
            self._gpio.output(settings.VALVE_GPIO_PIN, GPIO.LOW)
            self._gpio_available = True
            print("GPIO 初始化成功，气动阀控制已启用")
        except ImportError:
            print("未检测到 RPi.GPIO 库，使用模拟气动阀模式")
            self._gpio_available = False
        except Exception as e:
            print(f"GPIO 初始化失败: {e}，使用模拟气动阀模式")
            self._gpio_available = False

    def trigger_valve(self, valve_id: str, duration: Optional[float] = None) -> Dict:
        if duration is None:
            duration = settings.VALVE_ACTIVE_DURATION

        with self._lock:
            if valve_id not in self._valves:
                return {
                    "success": False,
                    "valve_id": valve_id,
                    "action": "trigger",
                    "message": f"气动阀 {valve_id} 不存在"
                }

            valve = self._valves[valve_id]

            if valve["status"] == "open":
                return {
                    "success": True,
                    "valve_id": valve_id,
                    "action": "trigger",
                    "message": f"气动阀 {valve_id} 已处于开启状态"
                }

            if self._gpio_available:
                self._open_valve_hardware()
            else:
                print(f"[模拟] 气动阀 {valve_id} 已开启，持续 {duration} 秒")

            valve["status"] = "open"
            valve["last_trigger"] = datetime.now()
            valve["trigger_count"] += 1

            timer = threading.Timer(duration, self._auto_close_valve, args=[valve_id])
            timer.daemon = True
            timer.start()

            return {
                "success": True,
                "valve_id": valve_id,
                "action": "open",
                "duration": duration,
                "message": f"气动阀 {valve_id} 已开启，将在 {duration} 秒后自动关闭"
            }

    def open_valve(self, valve_id: str) -> Dict:
        with self._lock:
            if valve_id not in self._valves:
                return {
                    "success": False,
                    "valve_id": valve_id,
                    "action": "open",
                    "message": f"气动阀 {valve_id} 不存在"
                }

            valve = self._valves[valve_id]

            if self._gpio_available:
                self._open_valve_hardware()
            else:
                print(f"[模拟] 气动阀 {valve_id} 已手动开启")

            valve["status"] = "open"

            return {
                "success": True,
                "valve_id": valve_id,
                "action": "open",
                "message": f"气动阀 {valve_id} 已开启"
            }

    def close_valve(self, valve_id: str) -> Dict:
        with self._lock:
            if valve_id not in self._valves:
                return {
                    "success": False,
                    "valve_id": valve_id,
                    "action": "close",
                    "message": f"气动阀 {valve_id} 不存在"
                }

            valve = self._valves[valve_id]

            if self._gpio_available:
                self._close_valve_hardware()
            else:
                print(f"[模拟] 气动阀 {valve_id} 已关闭")

            valve["status"] = "closed"

            return {
                "success": True,
                "valve_id": valve_id,
                "action": "close",
                "message": f"气动阀 {valve_id} 已关闭"
            }

    def _auto_close_valve(self, valve_id: str) -> None:
        with self._lock:
            if valve_id in self._valves:
                valve = self._valves[valve_id]
                if self._gpio_available:
                    self._close_valve_hardware()
                else:
                    print(f"[模拟] 气动阀 {valve_id} 自动关闭")
                valve["status"] = "closed"

    def _open_valve_hardware(self) -> None:
        if self._gpio_available and self._gpio:
            self._gpio.output(settings.VALVE_GPIO_PIN, self._gpio.HIGH)

    def _close_valve_hardware(self) -> None:
        if self._gpio_available and self._gpio:
            self._gpio.output(settings.VALVE_GPIO_PIN, self._gpio.LOW)

    def get_valve_status(self, valve_id: str) -> Optional[Dict]:
        with self._lock:
            if valve_id in self._valves:
                valve = self._valves[valve_id].copy()
                valve["last_trigger"] = valve["last_trigger"].isoformat() if valve["last_trigger"] else None
                return valve
            return None

    def get_all_valves(self) -> Dict[str, Dict]:
        with self._lock:
            result = {}
            for vid, valve in self._valves.items():
                v = valve.copy()
                v["last_trigger"] = v["last_trigger"].isoformat() if v["last_trigger"] else None
                result[vid] = v
            return result

    def cleanup(self) -> None:
        if self._gpio_available and self._gpio:
            self._gpio.cleanup()
            print("GPIO 已清理")


_valve_controller: Optional[ValveController] = None


def get_valve_controller() -> ValveController:
    global _valve_controller
    if _valve_controller is None:
        _valve_controller = ValveController()
    return _valve_controller
