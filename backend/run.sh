#!/bin/bash

# 启动FastAPI应用

echo "启动视频水印去除工具后端服务..."

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "虚拟环境不存在，正在创建..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
echo "检查依赖..."
pip install -r requirements.txt

# 创建必要的目录
mkdir -p uploads outputs thumbnails

# 启动服务
echo "启动服务..."
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
