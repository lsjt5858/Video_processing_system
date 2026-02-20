#!/bin/bash

# 生产环境启动脚本
# 用于生产环境部署，包含数据库初始化和健康检查

set -e  # 遇到错误立即退出

echo "=========================================="
echo "视频水印去除工具 - 生产环境启动"
echo "=========================================="

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查Python版本
echo -e "${YELLOW}检查Python版本...${NC}"
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
REQUIRED_VERSION="3.10"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo -e "${RED}错误: 需要Python $REQUIRED_VERSION 或更高版本，当前版本: $PYTHON_VERSION${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python版本: $PYTHON_VERSION${NC}"

# 检查FFmpeg
echo -e "${YELLOW}检查FFmpeg...${NC}"
if ! command -v ffmpeg &> /dev/null; then
    echo -e "${RED}错误: FFmpeg未安装${NC}"
    echo "请安装FFmpeg:"
    echo "  Ubuntu/Debian: sudo apt-get install ffmpeg"
    echo "  CentOS/RHEL: sudo yum install ffmpeg"
    echo "  macOS: brew install ffmpeg"
    exit 1
fi
echo -e "${GREEN}✓ FFmpeg已安装: $(ffmpeg -version | head -n1)${NC}"

# 检查环境变量文件
echo -e "${YELLOW}检查环境变量配置...${NC}"
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}警告: .env文件不存在，从.env.example复制...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}请编辑.env文件配置生产环境参数${NC}"
fi
echo -e "${GREEN}✓ 环境变量配置文件存在${NC}"

# 创建必要的目录
echo -e "${YELLOW}创建必要的目录...${NC}"
mkdir -p uploads outputs thumbnails logs
echo -e "${GREEN}✓ 目录创建完成${NC}"

# 检查虚拟环境
echo -e "${YELLOW}检查虚拟环境...${NC}"
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}虚拟环境不存在，正在创建...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✓ 虚拟环境创建完成${NC}"
fi

# 激活虚拟环境
echo -e "${YELLOW}激活虚拟环境...${NC}"
source venv/bin/activate
echo -e "${GREEN}✓ 虚拟环境已激活${NC}"

# 升级pip
echo -e "${YELLOW}升级pip...${NC}"
pip install --upgrade pip > /dev/null 2>&1
echo -e "${GREEN}✓ pip已升级${NC}"

# 安装依赖
echo -e "${YELLOW}安装Python依赖...${NC}"
pip install -r requirements.txt
echo -e "${GREEN}✓ 依赖安装完成${NC}"

# 数据库初始化
echo -e "${YELLOW}初始化数据库...${NC}"
python3 -c "
import asyncio
from app.database import init_db

async def main():
    await init_db()
    print('数据库初始化完成')

asyncio.run(main())
"
echo -e "${GREEN}✓ 数据库初始化完成${NC}"

# 健康检查函数
health_check() {
    local max_attempts=30
    local attempt=1
    
    echo -e "${YELLOW}等待服务启动...${NC}"
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            echo -e "${GREEN}✓ 服务健康检查通过${NC}"
            return 0
        fi
        echo -n "."
        sleep 1
        attempt=$((attempt + 1))
    done
    
    echo -e "${RED}错误: 服务启动失败或健康检查超时${NC}"
    return 1
}

# 启动服务
echo -e "${YELLOW}启动生产服务...${NC}"
echo "=========================================="

# 使用gunicorn启动（生产环境推荐）
# 如果没有安装gunicorn，使用uvicorn
if command -v gunicorn &> /dev/null; then
    echo -e "${GREEN}使用Gunicorn启动服务${NC}"
    gunicorn app.main:app \
        --workers 4 \
        --worker-class uvicorn.workers.UvicornWorker \
        --bind 0.0.0.0:8000 \
        --access-logfile logs/access.log \
        --error-logfile logs/error.log \
        --log-level info \
        --timeout 300 \
        --graceful-timeout 30 \
        --keep-alive 5 &
else
    echo -e "${YELLOW}Gunicorn未安装，使用Uvicorn启动服务${NC}"
    echo -e "${YELLOW}生产环境建议安装Gunicorn: pip install gunicorn${NC}"
    uvicorn app.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --workers 4 \
        --log-level info \
        --access-log \
        --no-use-colors &
fi

# 保存进程ID
SERVER_PID=$!
echo $SERVER_PID > server.pid
echo -e "${GREEN}✓ 服务已启动 (PID: $SERVER_PID)${NC}"

# 执行健康检查
if health_check; then
    echo "=========================================="
    echo -e "${GREEN}服务启动成功！${NC}"
    echo "访问地址: http://localhost:8000"
    echo "API文档: http://localhost:8000/docs"
    echo "进程ID: $SERVER_PID"
    echo "日志目录: logs/"
    echo "=========================================="
    echo "使用 'kill $SERVER_PID' 或 './stop-production.sh' 停止服务"
else
    echo -e "${RED}服务启动失败，请检查日志${NC}"
    kill $SERVER_PID 2>/dev/null || true
    exit 1
fi

# 等待进程
wait $SERVER_PID
