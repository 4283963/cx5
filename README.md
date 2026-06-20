# 智慧物流分拨中心 - 快递面单无损扫描与拦截系统

## 项目简介

本系统是一套面向智慧物流分拨中心的快递面单无损扫描与智能拦截系统。采用前端 React + 后端 FastAPI + PyTorch CRNN 模型的技术架构，实现快递面单的 OCR 文字识别、包裹状态校验和三级拦截功能。

## 系统架构

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│   前端操作台     │  HTTP │   后端服务       │  GPU  │   CRNN 模型      │
│   (React)       │──────▶│  (FastAPI)      │──────▶│  (PyTorch)      │
│  传送带界面      │       │  拦截逻辑       │       │  文字识别        │
│  拦截告警       │◀──────│  气动阀控制      │◀──────│  单号提取        │
└─────────────────┘       └─────────────────┘       └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │   数据库         │
                        │  (SQLite)        │
                        │  包裹状态管理     │
                        └─────────────────┘
```

## 功能特性

- ✅ **面单无损扫描**: 高空相机拍摄，非接触式扫描
- ✅ **CRNN 文字识别**: 基于卷积循环神经网络的端到端文字识别
- ✅ **单号自动提取**: 自动识别运单号和目的地城市
- ✅ **三级拦截机制**: 客户拦截、疑似违禁品自动触发三级拦截
- ✅ **物理气动阀**: 拦截信号驱动硬件气动阀执行物理拦截
- ✅ **实时告警**: 红色弹窗告警，声光提示
- ✅ **扫描记录**: 完整的扫描和拦截历史记录

## 项目结构

### 后端 (backend/)

```
backend/
├── app/
│   ├── api/              # API 路由层
│   │   ├── scan.py       # 扫描识别接口
│   │   └── intercept.py  # 拦截控制接口
│   ├── models/           # 数据模型层
│   │   ├── models.py     # SQLAlchemy ORM 模型
│   │   └── schemas.py    # Pydantic 数据校验模型
│   ├── services/         # 业务服务层
│   │   ├── crnn_model.py      # CRNN 模型定义
│   │   ├── ocr_service.py     # OCR 识别服务
│   │   ├── intercept_service.py  # 拦截服务
│   │   └── valve_controller.py   # 气动阀控制器
│   ├── db/               # 数据库层
│   │   ├── database.py   # 数据库连接
│   │   └── init_db.py    # 初始化数据
│   ├── config.py         # 配置管理
│   └── main.py           # 应用入口
├── requirements.txt      # Python 依赖
├── run.sh               # Linux 启动脚本
├── run.bat              # Windows 启动脚本
└── .env.example         # 环境变量示例
```

### 前端 (frontend/)

```
frontend/
├── src/
│   ├── components/       # React 组件
│   │   ├── ConveyorBelt.jsx   # 传送带操作台
│   │   ├── ScanPanel.jsx      # 扫描操作面板
│   │   ├── InterceptAlert.jsx # 三级拦截告警弹窗
│   │   ├── PackageInfo.jsx    # 包裹信息展示
│   │   ├── ScanRecords.jsx    # 扫描记录列表
│   │   └── ValveStatus.jsx    # 气动阀状态
│   ├── services/         # API 服务
│   │   └── api.js        # Axios API 封装
│   ├── styles/           # 样式文件
│   ├── App.jsx           # 主应用组件
│   └── main.jsx          # 应用入口
├── package.json          # Node 依赖
├── vite.config.js        # Vite 配置
└── index.html            # HTML 入口
```

## 快速开始

### 后端启动

1. 进入后端目录
```bash
cd backend
```

2. 创建虚拟环境并安装依赖
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate    # Windows

pip install -r requirements.txt
```

3. 配置环境变量（可选）
```bash
cp .env.example .env
# 编辑 .env 文件
```

4. 启动服务
```bash
# Linux/Mac
./run.sh

# Windows
run.bat

# 或直接运行
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

后端服务将在 http://localhost:8000 启动

API 文档: http://localhost:8000/docs

### 前端启动

1. 进入前端目录
```bash
cd frontend
```

2. 安装依赖
```bash
npm install
```

3. 启动开发服务器
```bash
npm run dev
```

前端将在 http://localhost:5173 启动

## 拦截级别说明

| 级别 | 颜色 | 触发条件 | 处理方式 |
|------|------|----------|----------|
| 一级拦截 | 黄色 | 超时未取件 | 系统记录 |
| 二级拦截 | 橙色 | 地址异常 | 人工复核 |
| **三级拦截** | **红色** | **客户拦截 / 疑似违禁品** | **自动物理拦截 + 告警** |

## 测试数据

系统预置了以下测试包裹数据：

| 运单号 | 目的地 | 状态 |
|--------|--------|------|
| SF1234567890123 | 北京市 | 正常 |
| YT9876543210987 | 上海市 | 客户拦截 |
| ZTO5678901234567 | 广州市 | 疑似违禁品 |
| JD1122334455667 | 深圳市 | 正常 |
| EMS9988776655443 | 成都市 | 客户拦截 |
| STO2233445566778 | 杭州市 | 正常 |
| YD5566778899001 | 武汉市 | 疑似违禁品 |

## API 接口

### 扫描识别

- `POST /api/v1/scan/waybill` - 上传图片进行面单识别
- `POST /api/v1/scan/waybill/base64` - Base64 图片识别
- `GET /api/v1/scan/records` - 获取扫描记录列表
- `GET /api/v1/scan/records/{id}` - 获取单条扫描记录

### 拦截控制

- `GET /api/v1/intercept/active` - 获取活跃拦截列表
- `GET /api/v1/intercept/history` - 获取拦截历史
- `POST /api/v1/intercept/check/{tracking_number}` - 检查包裹是否需拦截
- `POST /api/v1/intercept/handle/{tracking_number}` - 处理拦截记录
- `GET /api/v1/intercept/valves` - 获取所有气动阀状态
- `POST /api/v1/intercept/valves/control` - 控制气动阀
- `POST /api/v1/intercept/valves/{valve_id}/trigger` - 触发气动阀脉冲

## 技术栈

### 后端
- **框架**: FastAPI
- **数据库**: SQLite + SQLAlchemy
- **深度学习**: PyTorch + TorchVision
- **图像处理**: OpenCV + Pillow
- **硬件控制**: RPi.GPIO (树莓派)

### 前端
- **框架**: React 18
- **构建工具**: Vite
- **HTTP 客户端**: Axios
- **样式**: CSS3

## 部署说明

### 生产环境部署

1. 后端部署
```bash
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

2. 前端构建
```bash
npm run build
# 将 dist 目录部署到静态文件服务器
```

### 树莓派硬件连接

- 气动阀控制引脚: GPIO 18 (可配置)
- 建议使用继电器模块控制工业气动阀
- 相机建议使用 USB 工业相机或 CSI 摄像头

## 注意事项

1. 系统默认识别模式为模拟模式，需配置 CRNN 模型路径启用真实识别
2. 气动阀控制需要在树莓派等支持 GPIO 的设备上运行
3. 生产环境建议使用 PostgreSQL 或 MySQL 替代 SQLite
4. 建议配置 HTTPS 确保传输安全

## 许可证

本项目仅供学习和内部使用。
