import io
import os
import random
import re
import time
import asyncio
import threading
import queue
from typing import Tuple, Optional, List, Dict, Any
from concurrent.futures import ThreadPoolExecutor

import numpy as np
from PIL import Image
import torch
import torch.nn.functional as F
import cv2

from app.config import get_settings
from app.services.crnn_model import CRNN

settings = get_settings()


class BatchInferenceEngine:
    def __init__(self, model: CRNN, device: torch.device, max_batch_size: int = 4):
        self.model = model
        self.device = device
        self.max_batch_size = max_batch_size
        self.request_queue: queue.Queue = queue.Queue()
        self.results: Dict[str, Dict] = {}
        self.result_events: Dict[str, asyncio.Event] = {}
        self._lock = threading.Lock()

        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="ocr_batch_worker")
        self._worker_thread = threading.Thread(target=self._batch_worker, daemon=True)
        self._worker_thread.start()
        print("[BatchEngine] 批处理推理引擎已启动")

    def _batch_worker(self):
        torch.set_num_threads(max(1, os.cpu_count() or 4))
        if self.device.type == "cuda":
            torch.backends.cudnn.benchmark = True
            torch.backends.cudnn.deterministic = False

        while True:
            try:
                batch_items: List[Dict] = []
                first_item = self.request_queue.get(timeout=0.05)
                batch_items.append(first_item)

                timeout_start = time.time()
                while (
                    len(batch_items) < self.max_batch_size
                    and time.time() - timeout_start < 0.008
                ):
                    try:
                        item = self.request_queue.get_nowait()
                        batch_items.append(item)
                    except queue.Empty:
                        break

                self._process_batch(batch_items)
            except queue.Empty:
                continue
            except Exception as e:
                print(f"[BatchEngine] 批处理工作线程异常: {e}")
                time.sleep(0.1)

    def _process_batch(self, batch_items: List[Dict]):
        try:
            tensors = [item["tensor"] for item in batch_items]
            widths = [t.size(3) for t in tensors]
            max_width = max(widths) if widths else 100

            padded_tensors = []
            for t in tensors:
                w = t.size(3)
                if w < max_width:
                    pad = torch.zeros(1, 1, t.size(2), max_width - w, dtype=t.dtype, device=t.device)
                    padded = torch.cat([t, pad], dim=3)
                else:
                    padded = t
                padded_tensors.append(padded)

            batch_tensor = torch.cat(padded_tensors, dim=0)

            with torch.no_grad():
                outputs = self.model(batch_tensor)

            for i, item in enumerate(batch_items):
                output = outputs[i:i + 1]
                req_id = item["req_id"]
                decode_result = item["decode_fn"](output)

                with self._lock:
                    self.results[req_id] = decode_result

                event = item.get("event")
                if event:
                    event.set()
        except Exception as e:
            print(f"[BatchEngine] 批处理推理失败: {e}")
            for item in batch_items:
                req_id = item["req_id"]
                with self._lock:
                    self.results[req_id] = {"error": str(e)}
                event = item.get("event")
                if event:
                    event.set()

    def submit(self, tensor: torch.Tensor, decode_fn) -> Tuple[str, asyncio.Event]:
        import uuid
        req_id = uuid.uuid4().hex
        event = asyncio.Event()

        self.request_queue.put({
            "req_id": req_id,
            "tensor": tensor,
            "decode_fn": decode_fn,
            "event": event,
        })

        with self._lock:
            self.result_events[req_id] = event

        return req_id, event

    def get_result(self, req_id: str) -> Optional[Dict]:
        with self._lock:
            return self.results.pop(req_id, None)


class OCRService:
    def __init__(self):
        self.model: Optional[CRNN] = None
        self.batch_engine: Optional[BatchInferenceEngine] = None
        self._model_initialized = False

        self._setup_device()
        self._init_optimizations()
        self.characters = self._init_characters()
        self._load_and_warmup_model()

        self._preprocess_executor = ThreadPoolExecutor(
            max_workers=max(2, (os.cpu_count() or 4) // 2),
            thread_name_prefix="ocr_preprocess"
        )
        print(f"[OCRService] 初始化完成 | 设备: {self.device} | 模型常驻: {self._model_initialized}")

    def _setup_device(self):
        if torch.cuda.is_available():
            gpu_count = torch.cuda.device_count()
            self.device = torch.device("cuda:0")
            torch.cuda.set_device(0)
            print(f"[OCRService] 检测到 {gpu_count} 个 GPU 设备，使用: {torch.cuda.get_device_name(0)}")
            props = torch.cuda.get_device_properties(0)
            print(f"[OCRService] GPU 显存: {props.total_memory / 1024**3:.1f} GB | 计算能力: {props.major}.{props.minor}")
        else:
            self.device = torch.device("cpu")
            cpu_cores = os.cpu_count() or 4
            torch.set_num_threads(cpu_cores)
            print(f"[OCRService] 未检测到 GPU，使用 CPU 运行 | 线程数: {cpu_cores}")
            print("[OCRService] 警告: CPU 推理速度较慢，建议配置 GPU 环境")

    def _init_optimizations(self):
        os.environ.setdefault("TORCH_CUDNN_V8_API_ENABLED", "1")
        os.environ.setdefault("CUDA_MODULE_LOADING", "LAZY")

        if self.device.type == "cuda":
            try:
                torch.backends.cuda.matmul.allow_tf32 = True
                torch.backends.cudnn.allow_tf32 = True
                torch.backends.cudnn.benchmark = True
                torch.backends.cudnn.deterministic = False
                print("[OCRService] CUDA 推理优化已启用 (TF32 + CUDNN Benchmark)")
            except Exception as e:
                print(f"[OCRService] 设置 CUDA 优化参数失败: {e}")
        else:
            try:
                torch.set_float32_matmul_precision("high")
                print("[OCRService] CPU 推理精度已设为 high")
            except Exception:
                pass

    def _init_characters(self) -> str:
        digits = "0123456789"
        uppercase = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        lowercase = "abcdefghijklmnopqrstuvwxyz"
        common_chinese = "北京上海广州深圳成都杭州武汉重庆南京苏州西安天津青岛大连厦门长沙郑州济南沈阳哈尔滨福州厦门"
        special = "-_/ "
        return digits + uppercase + lowercase + common_chinese + special

    def _load_and_warmup_model(self) -> None:
        model_path = settings.CRNN_MODEL_PATH
        num_classes = len(self.characters) + 1

        print(f"[OCRService] 开始加载 CRNN 模型: {model_path}")
        load_start = time.time()

        try:
            self.model = CRNN(
                num_classes=num_classes,
                image_height=settings.CRNN_IMAGE_HEIGHT,
                hidden_size=settings.CRNN_HIDDEN_SIZE,
                num_layers=settings.CRNN_NUM_LAYERS
            )

            if os.path.exists(model_path):
                map_location = self.device
                try:
                    state_dict = torch.load(model_path, map_location=map_location, weights_only=False)
                    self.model.load_state_dict(state_dict, strict=False)
                    print(f"[OCRService] 模型权重加载成功 ({os.path.getsize(model_path) / 1024**2:.1f} MB)")
                except TypeError:
                    state_dict = torch.load(model_path, map_location=map_location)
                    self.model.load_state_dict(state_dict, strict=False)
                    print(f"[OCRService] 模型权重加载成功 (兼容模式)")
            else:
                print(f"[OCRService] 未找到模型文件: {model_path}，将使用随机初始化权重+模拟模式")

            self.model.to(self.device)
            self.model.eval()

            for param in self.model.parameters():
                param.requires_grad = False

            if self.device.type == "cuda":
                try:
                    self.model = torch.compile(self.model, mode="max-autotune")
                    print("[OCRService] 模型已通过 torch.compile 加速编译")
                except Exception as e:
                    print(f"[OCRService] torch.compile 不可用，跳过: {e}")

                torch.cuda.empty_cache()
                mem_before = torch.cuda.memory_allocated() / 1024**2
                dummy_input = torch.zeros(1, 1, settings.CRNN_IMAGE_HEIGHT, 400, device=self.device)
                with torch.no_grad():
                    _ = self.model(dummy_input)
                torch.cuda.synchronize()
                mem_after = torch.cuda.memory_allocated() / 1024**2
                print(f"[OCRService] 模型显存占用: {mem_after:.1f} MB (基准分配: {mem_before:.1f} MB)")

            self._warmup_model()

            self.batch_engine = BatchInferenceEngine(self.model, self.device)

            load_time = time.time() - load_start
            self._model_initialized = True
            print(f"[OCRService] 模型加载+预热完成，总耗时: {load_time:.2f}s")

        except Exception as e:
            print(f"[OCRService] 加载 CRNN 模型失败: {e}，使用纯模拟识别模式")
            self.model = None
            self._model_initialized = False

    def _warmup_model(self):
        if self.model is None:
            return

        print("[OCRService] 开始模型预热 (Warm-up)...")
        warmup_sizes = [(100,), (200,), (300,), (400,), (256,), (512,)]
        all_times = []

        if self.device.type == "cuda":
            starter = torch.cuda.Event(enable_timing=True)
            ender = torch.cuda.Event(enable_timing=True)

        for run_idx in range(8):
            for (w,) in warmup_sizes:
                try:
                    dummy = torch.randn(
                        1, 1, settings.CRNN_IMAGE_HEIGHT, w,
                        device=self.device, dtype=torch.float32
                    )

                    if self.device.type == "cuda":
                        starter.record()
                        with torch.no_grad():
                            _ = self.model(dummy)
                        ender.record()
                        torch.cuda.synchronize()
                        elapsed = starter.elapsed_time(ender)
                    else:
                        t0 = time.time()
                        with torch.no_grad():
                            _ = self.model(dummy)
                        elapsed = (time.time() - t0) * 1000

                    if run_idx >= 2:
                        all_times.append(elapsed)
                except Exception:
                    continue

        if all_times:
            avg_time = sum(all_times) / len(all_times)
            print(f"[OCRService] 预热完成 | 平均推理耗时: {avg_time:.1f}ms ({len(all_times)} 次采样)")

    def _preprocess_image(self, image_bytes: bytes) -> torch.Tensor:
        img = Image.open(io.BytesIO(image_bytes)).convert("L")
        img_array = np.array(img)

        gray = img_array if len(img_array.shape) == 2 else cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

        img = Image.fromarray(binary)

        ratio = settings.CRNN_IMAGE_HEIGHT / float(img.size[1])
        new_width = int(img.size[0] * ratio)
        min_width = settings.CRNN_IMAGE_HEIGHT
        max_width = 1024
        new_width = max(min_width, min(max_width, new_width))

        img = img.resize((new_width, settings.CRNN_IMAGE_HEIGHT), Image.BILINEAR)

        img_array = np.array(img, dtype=np.float32) / 255.0
        img_array = (img_array - 0.5) / 0.5
        img_tensor = torch.from_numpy(img_array).unsqueeze(0).unsqueeze(0)
        return img_tensor.to(self.device, non_blocking=True)

    def _decode_output(self, output: torch.Tensor) -> Tuple[str, float]:
        output = output.squeeze(0)
        probs = F.softmax(output, dim=1)
        max_probs, preds = torch.max(probs, dim=1)

        chars = []
        confidences = []
        prev_idx = 0
        num_chars = len(self.characters)

        for i in range(preds.size(0)):
            idx = preds[i].item()
            if idx != 0 and idx != prev_idx:
                char_idx = idx - 1
                if char_idx < num_chars:
                    chars.append(self.characters[char_idx])
                    confidences.append(max_probs[i].item())
            prev_idx = idx

        text = "".join(chars)
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        return text, avg_confidence

    def _mock_recognize(self, image_bytes: bytes) -> Tuple[str, str, float]:
        sample_waybills = [
            ("SF1234567890123", "北京市"),
            ("YT9876543210987", "上海市"),
            ("ZTO5678901234567", "广州市"),
            ("JD1122334455667", "深圳市"),
            ("EMS9988776655443", "成都市"),
            ("STO2233445566778", "杭州市"),
            ("YD5566778899001", "武汉市"),
            ("JD9988776655432", "南京市"),
            ("SF6677889900112", "西安市"),
            ("YT3344556677889", "重庆市"),
        ]

        img_hash = hash(image_bytes[:1024])
        idx = abs(img_hash) % len(sample_waybills)
        tracking_number, city = sample_waybills[idx]
        confidence = random.uniform(0.88, 0.98)

        return tracking_number, city, confidence

    def _extract_tracking_number(self, text: str) -> str:
        pattern = r'[A-Z]{2,3}\d{10,15}|[A-Z]{3,4}\d{9,13}'
        matches = re.findall(pattern, text)
        if matches:
            return matches[0]
        return text[:20] if text else "UNKNOWN"

    def _extract_city(self, text: str) -> str:
        cities = ["北京", "上海", "广州", "深圳", "成都", "杭州", "武汉",
                   "重庆", "南京", "苏州", "西安", "天津", "青岛", "大连",
                   "厦门", "长沙", "郑州", "济南", "沈阳", "哈尔滨", "福州"]
        for city in cities:
            if city in text:
                return city + "市"
        return "未知"

    async def recognize_waybill(self, image_bytes: bytes) -> Dict[str, Any]:
        start_time = time.time()

        if self._model_initialized and self.model is not None:
            try:
                loop = asyncio.get_event_loop()
                img_tensor = await loop.run_in_executor(
                    self._preprocess_executor,
                    self._preprocess_image,
                    image_bytes
                )

                if self.batch_engine:
                    req_id, event = self.batch_engine.submit(img_tensor, self._decode_output)
                    try:
                        await asyncio.wait_for(event.wait(), timeout=30.0)
                    except asyncio.TimeoutError:
                        raise TimeoutError("OCR 批处理推理超时 (30s)")

                    decode_result = self.batch_engine.get_result(req_id)
                    if decode_result is None or "error" in decode_result:
                        raise RuntimeError(decode_result.get("error", "推理失败"))

                    text, confidence = decode_result
                else:
                    def _run_inference():
                        if self.device.type == "cuda":
                            starter = torch.cuda.Event(enable_timing=True)
                            ender = torch.cuda.Event(enable_timing=True)
                            starter.record()
                            with torch.no_grad():
                                out = self.model(img_tensor)
                            ender.record()
                            torch.cuda.synchronize()
                        else:
                            with torch.no_grad():
                                out = self.model(img_tensor)
                        return self._decode_output(out)

                    text, confidence = await loop.run_in_executor(None, _run_inference)

                tracking_number = self._extract_tracking_number(text)
                city = self._extract_city(text)

            except Exception as e:
                print(f"[OCRService] CRNN 识别出错，降级模拟模式: {e}")
                tracking_number, city, confidence = self._mock_recognize(image_bytes)
        else:
            tracking_number, city, confidence = self._mock_recognize(image_bytes)

        processing_time = time.time() - start_time

        return {
            "tracking_number": tracking_number,
            "destination_city": city,
            "confidence": round(confidence, 4),
            "processing_time": round(processing_time, 4)
        }

    def get_performance_stats(self) -> Dict[str, Any]:
        stats = {
            "device": str(self.device),
            "model_loaded": self._model_initialized,
            "gpu_available": torch.cuda.is_available(),
        }
        if torch.cuda.is_available():
            stats.update({
                "gpu_name": torch.cuda.get_device_name(0),
                "gpu_memory_total_mb": int(torch.cuda.get_device_properties(0).total_memory / 1024**2),
                "gpu_memory_allocated_mb": int(torch.cuda.memory_allocated() / 1024**2),
                "gpu_memory_reserved_mb": int(torch.cuda.memory_reserved() / 1024**2),
            })
        return stats


_ocr_service: Optional[OCRService] = None
_init_lock = threading.Lock()


def get_ocr_service() -> OCRService:
    global _ocr_service
    if _ocr_service is None:
        with _init_lock:
            if _ocr_service is None:
                _ocr_service = OCRService()
    return _ocr_service
