#!/bin/bash

echo "启动智慧物流分拨中心 - 后端服务..."

cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

echo "激活虚拟环境..."
source venv/bin/activate

echo "安装依赖..."
pip install -r requirements.txt

echo "启动 FastAPI 服务..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
