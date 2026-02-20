#!/bin/bash

# 开发环境启动脚本
# 用于本地开发，支持热重载

set -e

echo "=========================================="
echo "视频水印去除工具 - 开发环境启动"
echo "=========================================="

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查Python版本
echo -e "${YELLOW}检查Python版本...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}错误: Python3未安装${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python3已安装${NC}"

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
echo -e "${GREEN}✓ FFmpeg已安装${NC}"

# 检查环境变量文件
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}警告: .env文件不存在，从.env.example复制...${NC}"
    cp .env.example .env
fi

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}虚拟环境不存在，正在创建...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✓ 虚拟环境创建完成${NC}"
fi

# 激活虚拟环境
echo -e "${YELLOW}激活虚拟环境...${NC}"
source venv/bin/activate
echo -e "${GREEN}✓ 虚拟环境已激活${NC}"

# 安装/更新依赖
echo -e "${YELLOW}检查并安装依赖...${NC}"
pip install -q -r requirements.txt
echo -e "${GREEN}✓ 依赖检查完成${NC}"

# 创建必要的目录
echo -e "${YELLOW}创建必要的目录...${NC}"
mkdir -p uploads outputs thumbnails
echo -e "${GREEN}✓ 目录创建完成${NC}"

# 数据库初始化
echo -e "${YELLOW}初始化数据库...${NC}"
python3 -c "
import asyncio
from app.database import init_db

async def main():
    await init_db()

asyncio.run(main())
" 2>/dev/null || echo -e "${YELLOW}数据库已存在或初始化失败${NC}"

# 启动服务
echo "=========================================="
echo -e "${GREEN}启动开发服务器...${NC}"
echo "访问地址: http://localhost:8000"
echo "API文档: http://localhost:8000/docs"
echo "按 Ctrl+C 停止服务"
echo "=========================================="

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
