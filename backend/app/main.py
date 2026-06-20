import time
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.config import get_settings
from app.api import scan, intercept
from app.db.database import engine, Base
from app.db.init_db import init_database
from app.services.ocr_service import get_ocr_service
from app.services.intercept_service import get_intercept_service
from app.services.valve_controller import get_valve_controller

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("=" * 60)
    print(" [启动] 智慧物流分拨中心-快递面单扫描拦截系统")
    print("=" * 60)

    print("\n[启动步骤 1/5] 初始化数据库...")
    Base.metadata.create_all(bind=engine)
    init_database()
    print("  ✓ 数据库初始化完成")

    print("\n[启动步骤 2/5] 预初始化 OCR 服务 (加载模型+GPU预热)...")
    ocr_start = time.time()
    ocr_svc = get_ocr_service()
    ocr_stats = ocr_svc.get_performance_stats()
    ocr_elapsed = time.time() - ocr_start
    print(f"  ✓ OCR 服务初始化完成 ({ocr_elapsed:.2f}s)")
    print(f"    - 推理设备: {ocr_stats['device']}")
    print(f"    - 模型常驻内存: {ocr_stats['model_loaded']}")
    if ocr_stats.get("gpu_memory_allocated_mb"):
        print(f"    - GPU 显存占用: {ocr_stats['gpu_memory_allocated_mb']} MB")

    print("\n[启动步骤 3/5] 初始化拦截服务...")
    get_intercept_service()
    print("  ✓ 拦截服务初始化完成")

    print("\n[启动步骤 4/5] 初始化气动阀控制器...")
    get_valve_controller()
    print("  ✓ 气动阀控制器初始化完成")

    print("\n[启动步骤 5/5] 预热批处理引擎...")
    try:
        warmup_tasks = []
        for i in range(3):
            async def _do_warmup():
                dummy_bytes = b'\x00' * 1024
                try:
                    _ = await ocr_svc.recognize_waybill(dummy_bytes)
                except Exception:
                    pass
            warmup_tasks.append(_do_warmup())
        await asyncio.gather(*warmup_tasks)
        print("  ✓ 批处理引擎预热完成")
    except Exception as e:
        print(f"  ⚠ 批处理预热跳过: {e}")

    print("\n" + "=" * 60)
    print(" [就绪] 系统启动完成，等待产线请求")
    print("=" * 60 + "\n")

    yield

    print("\n[关闭] 正在清理系统资源...")
    try:
        from app.services.valve_controller import get_valve_controller
        get_valve_controller().cleanup()
        print("  ✓ GPIO 资源已释放")
    except Exception:
        pass
    print("[关闭] 系统已安全退出\n")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="智慧物流分拨中心快递面单无损扫描与智能拦截系统",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.middleware("http")
async def request_timing_middleware(request: Request, call_next):
    request.state.start_time = time.time()
    try:
        response = await call_next(request)
        return response
    except Exception as exc:
        raise exc
    finally:
        elapsed = (time.time() - request.state.start_time) * 1000
        if elapsed > 1000:
            path = request.url.path
            print(f"[慢请求警告] {request.method} {path} | 耗时: {elapsed:.0f}ms")


app.include_router(scan.router, prefix=settings.API_V1_STR, tags=["扫描识别"])
app.include_router(intercept.router, prefix=settings.API_V1_STR, tags=["拦截控制"])


@app.get("/")
async def root():
    ocr_stats = get_ocr_service().get_performance_stats()
    return {
        "name": settings.PROJECT_NAME,
        "version": "1.0.0",
        "status": "running",
        "inference_engine": {
            "device": ocr_stats["device"],
            "model_loaded": ocr_stats["model_loaded"],
            "gpu_available": ocr_stats["gpu_available"],
        },
    }


@app.get("/health")
async def health_check():
    ocr_stats = get_ocr_service().get_performance_stats()
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "ocr": {
            "ready": ocr_stats["model_loaded"],
            "device": ocr_stats["device"],
        },
    }
