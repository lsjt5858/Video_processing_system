#!/bin/bash

# 备份脚本
# 用于备份数据库和视频文件

set -e

# 配置
BACKUP_DIR="backup"
DATE=$(date +%Y%m%d_%H%M%S)
DB_FILE="video_platform.db"
RETENTION_DAYS=30

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "=========================================="
echo "开始备份 - $(date)"
echo "=========================================="

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 备份数据库
if [ -f "$DB_FILE" ]; then
    echo -e "${YELLOW}备份数据库...${NC}"
    DB_BACKUP="$BACKUP_DIR/db_${DATE}.db"
    cp "$DB_FILE" "$DB_BACKUP"
    gzip "$DB_BACKUP"
    echo -e "${GREEN}✓ 数据库备份完成: ${DB_BACKUP}.gz${NC}"
else
    echo -e "${YELLOW}警告: 数据库文件不存在${NC}"
fi

# 备份上传的视频
if [ -d "uploads" ] && [ "$(ls -A uploads)" ]; then
    echo -e "${YELLOW}备份上传视频...${NC}"
    UPLOAD_BACKUP="$BACKUP_DIR/uploads_${DATE}.tar.gz"
    tar -czf "$UPLOAD_BACKUP" uploads/
    echo -e "${GREEN}✓ 上传视频备份完成: ${UPLOAD_BACKUP}${NC}"
else
    echo -e "${YELLOW}警告: uploads目录为空或不存在${NC}"
fi

# 备份处理后的视频
if [ -d "outputs" ] && [ "$(ls -A outputs)" ]; then
    echo -e "${YELLOW}备份输出视频...${NC}"
    OUTPUT_BACKUP="$BACKUP_DIR/outputs_${DATE}.tar.gz"
    tar -czf "$OUTPUT_BACKUP" outputs/
    echo -e "${GREEN}✓ 输出视频备份完成: ${OUTPUT_BACKUP}${NC}"
else
    echo -e "${YELLOW}警告: outputs目录为空或不存在${NC}"
fi

# 备份配置文件
echo -e "${YELLOW}备份配置文件...${NC}"
CONFIG_BACKUP="$BACKUP_DIR/config_${DATE}.tar.gz"
tar -czf "$CONFIG_BACKUP" .env 2>/dev/null || echo -e "${YELLOW}警告: .env文件不存在${NC}"
echo -e "${GREEN}✓ 配置文件备份完成${NC}"

# 清理旧备份
echo -e "${YELLOW}清理旧备份（保留${RETENTION_DAYS}天）...${NC}"
find "$BACKUP_DIR" -name "*.gz" -type f -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "*.tar.gz" -type f -mtime +$RETENTION_DAYS -delete
echo -e "${GREEN}✓ 旧备份清理完成${NC}"

# 显示备份信息
echo "=========================================="
echo -e "${GREEN}备份完成！${NC}"
echo "备份目录: $BACKUP_DIR"
echo "备份文件:"
ls -lh "$BACKUP_DIR" | grep "$DATE"
echo "=========================================="

# 计算备份大小
BACKUP_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
echo "总备份大小: $BACKUP_SIZE"
echo "备份时间: $(date)"
