#!/bin/bash

# 生产环境停止脚本

set -e

echo "=========================================="
echo "停止视频水印去除工具服务"
echo "=========================================="

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查PID文件
if [ ! -f "server.pid" ]; then
    echo -e "${YELLOW}警告: server.pid文件不存在${NC}"
    echo "尝试查找运行中的进程..."
    
    # 查找uvicorn或gunicorn进程
    PIDS=$(pgrep -f "uvicorn app.main:app|gunicorn app.main:app" || true)
    
    if [ -z "$PIDS" ]; then
        echo -e "${YELLOW}未找到运行中的服务进程${NC}"
        exit 0
    fi
    
    echo -e "${YELLOW}找到进程: $PIDS${NC}"
    echo -n "是否停止这些进程? (y/n): "
    read -r response
    
    if [ "$response" = "y" ] || [ "$response" = "Y" ]; then
        for pid in $PIDS; do
            echo -e "${YELLOW}停止进程 $pid...${NC}"
            kill -TERM $pid 2>/dev/null || true
        done
        sleep 2
        
        # 检查是否还在运行
        for pid in $PIDS; do
            if ps -p $pid > /dev/null 2>&1; then
                echo -e "${YELLOW}进程 $pid 未响应，强制停止...${NC}"
                kill -KILL $pid 2>/dev/null || true
            fi
        done
        
        echo -e "${GREEN}✓ 服务已停止${NC}"
    else
        echo "取消操作"
    fi
    
    exit 0
fi

# 读取PID
SERVER_PID=$(cat server.pid)
echo -e "${YELLOW}服务进程ID: $SERVER_PID${NC}"

# 检查进程是否存在
if ! ps -p $SERVER_PID > /dev/null 2>&1; then
    echo -e "${YELLOW}警告: 进程 $SERVER_PID 不存在${NC}"
    rm -f server.pid
    exit 0
fi

# 优雅停止
echo -e "${YELLOW}发送SIGTERM信号...${NC}"
kill -TERM $SERVER_PID 2>/dev/null || true

# 等待进程结束
echo -n "等待进程结束"
for i in {1..30}; do
    if ! ps -p $SERVER_PID > /dev/null 2>&1; then
        echo ""
        echo -e "${GREEN}✓ 服务已优雅停止${NC}"
        rm -f server.pid
        exit 0
    fi
    echo -n "."
    sleep 1
done

# 如果还在运行，强制停止
echo ""
echo -e "${YELLOW}进程未响应，强制停止...${NC}"
kill -KILL $SERVER_PID 2>/dev/null || true
sleep 1

if ! ps -p $SERVER_PID > /dev/null 2>&1; then
    echo -e "${GREEN}✓ 服务已强制停止${NC}"
    rm -f server.pid
else
    echo -e "${RED}错误: 无法停止进程 $SERVER_PID${NC}"
    exit 1
fi
