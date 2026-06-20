@echo off
echo 启动智慧物流分拨中心 - 后端服务...

cd /d "%~dp0"

if not exist "venv" (
    echo 创建虚拟环境...
    python -m venv venv
)

echo 激活虚拟环境...
call venv\Scripts\activate.bat

echo 安装依赖...
pip install -r requirements.txt

echo 启动 FastAPI 服务...
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

pause
