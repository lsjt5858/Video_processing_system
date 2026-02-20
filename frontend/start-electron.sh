#!/bin/bash

echo "=========================================="
echo "一键美 - Electron 桌面应用"
echo "=========================================="

# 检查后端是否运行
if ! curl -s http://localhost:8000/docs > /dev/null 2>&1; then
    echo "⚠️  警告: 后端服务未运行"
    echo "请先启动后端服务："
    echo "  cd ../backend && bash run.sh"
    echo ""
    read -p "是否继续启动桌面应用？(y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "✓ 启动 Electron 桌面应用..."
npm run electron:dev
