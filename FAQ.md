# 常见问题 / FAQ

视频水印去除工具的常见问题解答。

## 📋 目录 / Table of Contents

- [基础问题](#基础问题)
- [安装和部署](#安装和部署)
- [功能使用](#功能使用)
- [性能问题](#性能问题)
- [错误处理](#错误处理)
- [高级配置](#高级配置)

---

## 基础问题 / Basic Questions

### Q1: 这个工具是做什么的？

**A**: 视频水印去除工具是一个基于AI的视频处理系统，主要功能包括：
- 视频导入（本地上传、URL下载）
- 水印检测和标记
- 水印智能去除（裁剪重构模式）
- 批量处理
- 实时进度推送

### Q2: 支持哪些视频格式？

**A**: 目前支持以下格式：
- MP4
- AVI
- MOV
- MKV

这些是最常见的视频格式，覆盖了大部分使用场景。

### Q3: 单个文件大小限制是多少？

**A**: 默认限制为 **5GB**。

如果需要处理更大的文件，可以修改配置：
```bash
# 编辑 backend/.env 文件
MAX_FILE_SIZE=10737418240  # 10GB
```

同时需要调整Nginx配置（如果使用）：
```nginx
client_max_body_size 10G;
```

### Q4: 批量上传最多支持多少个文件？

**A**: 最多支持 **50个文件** 同时上传。

这个限制是为了防止系统过载。如果需要处理更多文件，建议分批上传。

### Q5: 这个工具是免费的吗？

**A**: 是的，这是一个开源项目，可以免费使用。

### Q6: 可以商用吗？

**A**: 可以，但请注意：
- 遵守MIT许可证
- 仅处理您拥有合法版权的视频
- 不得用于侵权行为

---

## 安装和部署 / Installation & Deployment

### Q7: 推荐的部署方式是什么？

**A**: 推荐使用 **Docker Compose** 部署，原因：
- 简单快速，一键启动
- 环境隔离，避免依赖冲突
- 易于维护和更新
- 适合生产环境

```bash
cd backend
docker-compose up -d
```

### Q8: 需要什么样的服务器配置？

**A**: 最低配置：
- CPU: 4核心
- 内存: 8GB
- 存储: 100GB
- 网络: 稳定连接

推荐配置：
- CPU: 8核心或以上
- 内存: 16GB或以上
- 存储: 500GB SSD
- 网络: 高速连接

### Q9: 可以在Windows上运行吗？

**A**: 可以，有两种方式：

1. **使用Docker Desktop**（推荐）
   - 安装Docker Desktop for Windows
   - 运行 `docker-compose up -d`

2. **本地开发模式**
   - 安装Python 3.10+
   - 安装FFmpeg
   - 安装Node.js 18+
   - 分别启动后端和前端

### Q10: 如何更新到最新版本？

**A**: 

**Docker部署**:
```bash
cd backend
git pull
docker-compose down
docker-compose up -d --build
```

**本地部署**:
```bash
# 更新代码
git pull

# 更新后端依赖
cd backend
pip install -r requirements.txt

# 更新前端依赖
cd frontend
npm install
npm run build
```

### Q11: 安装时遇到FFmpeg错误怎么办？

**A**: 

**Ubuntu/Debian**:
```bash
sudo apt-get update
sudo apt-get install -y ffmpeg
ffmpeg -version  # 验证安装
```

**macOS**:
```bash
brew install ffmpeg
ffmpeg -version
```

**Windows**:
1. 下载FFmpeg: https://ffmpeg.org/download.html
2. 解压到 `C:\ffmpeg`
3. 添加到系统PATH: `C:\ffmpeg\bin`
4. 重启命令行，运行 `ffmpeg -version`

---

## 功能使用 / Feature Usage

### Q12: 如何上传视频？

**A**: 有三种方式：

1. **本地上传**
   - 访问"视频上传"页面
   - 点击上传区域或拖拽文件
   - 等待上传完成

2. **URL下载**
   - 在上传页面输入视频URL
   - 点击"下载"按钮
   - 系统自动下载并导入

3. **批量上传**
   - 选择多个文件（最多50个）
   - 系统并行上传（最多5个同时）

### Q13: 如何标记水印？

**A**: 步骤：
1. 在视频列表中选择视频
2. 点击"标记水印"按钮
3. 在视频帧上拖拽绘制矩形框
4. 可以标记多个水印区域
5. 点击"保存"确认标记

**提示**: 
- 尽量精确框选水印区域
- 可以标记多个不同位置的水印
- 支持编辑和删除已标记的区域

### Q14: 水印去除有哪些模式？

**A**: 当前版本支持 **裁剪重构模式**：

- **工作原理**: 智能裁剪视频，去除包含水印的边缘区域
- **适用场景**: 水印位于视频边缘（角落、顶部、底部）
- **优点**: 处理速度快，效果稳定
- **缺点**: 会改变视频尺寸

未来版本计划支持：
- AI修复填充模式（保持原始尺寸）
- 局部模糊替换模式（快速处理）

### Q15: 如何查看处理进度？

**A**: 系统通过WebSocket实时推送进度：

1. **上传进度**: 在上传页面实时显示
2. **处理进度**: 在任务管理页面查看
3. **批量进度**: 显示每个视频的处理状态

如果进度不更新，检查：
- WebSocket连接是否正常
- 浏览器控制台是否有错误
- 后端服务是否正常运行

### Q16: 处理后的视频在哪里？

**A**: 处理完成后：

1. **在线下载**: 
   - 任务管理页面点击"下载"按钮
   - 或访问 `/api/videos/{video_id}/output`

2. **服务器文件**:
   - 位于 `backend/outputs/` 目录
   - 文件名格式: `{video_id}_output.{format}`

### Q17: 可以批量处理吗？

**A**: 可以，步骤：

1. 在视频列表中选择多个视频
2. 点击"批量处理"按钮
3. 统一设置处理参数
4. 开始批量处理
5. 查看每个视频的处理状态
6. 批量下载处理结果

**限制**:
- 并行处理最多3个视频（可配置）
- 建议分批处理大量视频

---

## 性能问题 / Performance Issues

### Q18: 视频处理速度如何？

**A**: 处理速度取决于多个因素：

**影响因素**:
- 视频大小和时长
- 视频分辨率
- 服务器性能（CPU、内存）
- 处理模式

**参考速度**（4核CPU，8GB内存）:
- 1GB视频: 2-3分钟
- 2GB视频: 4-6分钟
- 5GB视频: 10-15分钟

**优化建议**:
- 使用SSD存储
- 增加CPU核心数
- 启用FFmpeg硬件加速
- 增加并行处理数量

### Q19: 如何提升处理速度？

**A**: 几种优化方法：

1. **增加并行处理数量**
```bash
# 编辑 backend/.env
MAX_PARALLEL_PROCESS=5  # 根据CPU核心数调整
```

2. **使用硬件加速**
```bash
# 检查GPU支持
ffmpeg -hwaccels

# 如果支持CUDA，可以在代码中启用
```

3. **优化服务器配置**
- 使用SSD存储
- 增加内存
- 使用更快的CPU

4. **调整Worker数量**
```bash
# Gunicorn配置
--workers 9  # (2 × CPU核心数) + 1
```

### Q20: 为什么上传很慢？

**A**: 可能的原因和解决方案：

1. **网络带宽限制**
   - 检查网络速度
   - 使用有线连接
   - 避免高峰时段

2. **服务器性能**
   - 检查CPU和内存使用率
   - 减少并行上传数量

3. **文件过大**
   - 压缩视频后再上传
   - 使用更高效的编码格式

4. **代理或防火墙**
   - 检查网络配置
   - 确保端口开放

### Q21: 系统占用内存很高怎么办？

**A**: 优化内存使用：

1. **减少并行处理数量**
```bash
MAX_PARALLEL_UPLOAD=3
MAX_PARALLEL_PROCESS=2
```

2. **定期清理临时文件**
```bash
# 清理旧的上传文件
find uploads/ -mtime +7 -delete

# 清理旧的输出文件
find outputs/ -mtime +7 -delete
```

3. **重启服务**
```bash
docker-compose restart
# 或
systemctl restart videoapp-backend
```

4. **增加服务器内存**
- 升级到16GB或更高

---

## 错误处理 / Error Handling

### Q22: 上传失败，提示"文件过大"

**A**: 解决方案：

1. **增加文件大小限制**
```bash
# 编辑 backend/.env
MAX_FILE_SIZE=10737418240  # 10GB
```

2. **调整Nginx配置**（如果使用）
```nginx
client_max_body_size 10G;
```

3. **重启服务**
```bash
docker-compose restart
```

### Q23: 上传失败，提示"格式不支持"

**A**: 检查文件格式：

**支持的格式**: MP4, AVI, MOV, MKV

**解决方案**:
1. 使用FFmpeg转换格式：
```bash
ffmpeg -i input.flv -c copy output.mp4
```

2. 或使用在线转换工具

### Q24: 处理失败，提示"FFmpeg错误"

**A**: 可能的原因：

1. **视频文件损坏**
   - 重新下载或上传视频
   - 使用FFmpeg检查: `ffmpeg -i video.mp4`

2. **FFmpeg未安装或版本过低**
   - 安装FFmpeg 4.0+
   - 检查版本: `ffmpeg -version`

3. **磁盘空间不足**
   - 检查磁盘空间: `df -h`
   - 清理旧文件

4. **权限问题**
   - 检查目录权限
   - 确保应用有读写权限

### Q25: WebSocket连接失败

**A**: 排查步骤：

1. **检查后端服务**
```bash
curl http://localhost:8000/health
```

2. **检查Nginx配置**（如果使用）
```nginx
# 确保包含WebSocket配置
location /ws/ {
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

3. **检查防火墙**
```bash
sudo ufw status
sudo ufw allow 8000/tcp
```

4. **查看浏览器控制台**
- 打开开发者工具
- 查看Console和Network标签
- 检查WebSocket连接状态

### Q26: 视频下载失败（URL导入）

**A**: 可能的原因：

1. **URL无效或视频不可访问**
   - 检查URL是否正确
   - 在浏览器中测试URL

2. **网站限制**
   - 某些网站可能限制下载
   - 尝试使用其他下载方式

3. **网络问题**
   - 检查网络连接
   - 尝试使用代理

4. **yt-dlp问题**
   - 更新yt-dlp: `pip install -U yt-dlp`
   - 查看错误日志

### Q27: 数据库错误

**A**: 解决方案：

1. **重新初始化数据库**
```bash
cd backend
rm video_platform.db
python3 -c "
import asyncio
from app.database import init_db
asyncio.run(init_db())
"
```

2. **检查数据库文件权限**
```bash
ls -la video_platform.db
chmod 644 video_platform.db
```

3. **备份后重建**
```bash
cp video_platform.db video_platform.db.backup
rm video_platform.db
# 重启服务，数据库会自动创建
```

---

## 高级配置 / Advanced Configuration

### Q28: 如何配置HTTPS？

**A**: 使用Let's Encrypt获取免费SSL证书：

```bash
# 安装Certbot
sudo apt-get install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d yourdomain.com

# 自动续期
sudo certbot renew --dry-run
```

### Q29: 如何配置反向代理？

**A**: Nginx反向代理配置示例：

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost:80;  # 前端
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api/ {
        proxy_pass http://localhost:8000;  # 后端
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /ws/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### Q30: 如何配置数据库？

**A**: 

**SQLite（默认）**:
```bash
DATABASE_URL=sqlite+aiosqlite:///./video_platform.db
```

**PostgreSQL（推荐生产环境）**:
```bash
# 安装PostgreSQL
sudo apt-get install postgresql

# 创建数据库
sudo -u postgres createdb videoapp

# 配置环境变量
DATABASE_URL=postgresql+asyncpg://user:password@localhost/videoapp
```

### Q31: 如何配置日志？

**A**: 

**Docker日志**:
```bash
# 查看日志
docker-compose logs -f backend

# 配置日志驱动
# 编辑 docker-compose.yml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

**应用日志**:
```python
# 在 app/main.py 中配置
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
```

### Q32: 如何配置备份？

**A**: 创建备份脚本：

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backup/videoapp"
DATE=$(date +%Y%m%d)

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份数据库
cp backend/video_platform.db $BACKUP_DIR/db_$DATE.db

# 备份视频文件
tar -czf $BACKUP_DIR/videos_$DATE.tar.gz backend/uploads backend/outputs

# 删除30天前的备份
find $BACKUP_DIR -name "*.db" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

添加到crontab：
```bash
crontab -e
# 每天凌晨2点执行备份
0 2 * * * /path/to/backup.sh
```

### Q33: 如何监控系统状态？

**A**: 几种监控方式：

1. **健康检查**
```bash
# 创建监控脚本
#!/bin/bash
while true; do
    if ! curl -s http://localhost:8000/health > /dev/null; then
        echo "Service is down!"
        # 发送告警或重启服务
    fi
    sleep 60
done
```

2. **使用Prometheus + Grafana**
   - 安装Prometheus
   - 配置指标收集
   - 使用Grafana可视化

3. **日志监控**
   - 使用ELK Stack
   - 或使用Loki + Grafana

### Q34: 如何扩展系统？

**A**: 扩展方案：

1. **垂直扩展**
   - 增加CPU核心数
   - 增加内存
   - 使用SSD存储

2. **水平扩展**
   - 使用负载均衡（Nginx/HAProxy）
   - 部署多个后端实例
   - 使用共享存储（NFS/S3）

3. **数据库扩展**
   - 使用PostgreSQL主从复制
   - 或使用数据库集群

4. **缓存优化**
   - 使用Redis缓存元数据
   - 缓存处理结果

---

## 其他问题 / Other Questions

### Q35: 如何贡献代码？

**A**: 欢迎贡献！步骤：

1. Fork项目
2. 创建功能分支
3. 提交代码
4. 创建Pull Request

详见项目的CONTRIBUTING.md文件。

### Q36: 如何报告Bug？

**A**: 

1. 访问项目的GitHub Issues页面
2. 点击"New Issue"
3. 提供以下信息：
   - 问题描述
   - 复现步骤
   - 预期行为
   - 实际行为
   - 系统环境
   - 错误日志

### Q37: 有技术支持吗？

**A**: 

- **文档**: 查看README、API文档、部署指南
- **FAQ**: 本文档
- **Issues**: GitHub Issues
- **社区**: 项目讨论区

### Q38: 未来会添加哪些功能？

**A**: 计划中的功能：

- ✅ 裁剪重构模式（已实现）
- 🔄 AI修复填充模式（开发中）
- 🔄 局部模糊替换模式（开发中）
- 📋 自动水印检测（计划中）
- 📋 视频优化功能（计划中）
- 📋 用户认证系统（计划中）
- 📋 API密钥管理（计划中）

### Q39: 可以离线使用吗？

**A**: 可以，但有限制：

- ✅ 本地上传功能正常
- ✅ 水印标记和去除正常
- ❌ URL下载功能需要网络
- ❌ 某些视频格式转换可能需要在线资源

### Q40: 数据安全吗？

**A**: 安全措施：

- 所有数据存储在本地服务器
- 不会上传到第三方服务器
- 支持HTTPS加密传输
- 可以配置访问控制
- 建议定期备份数据

**注意**: 
- 请勿处理敏感或机密视频
- 定期清理不需要的文件
- 使用强密码保护服务器

---

## 📚 相关文档 / Related Documentation

- [README.md](./README.md) - 项目概述
- [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) - API文档
- [DEPLOYMENT.md](./DEPLOYMENT.md) - 部署指南

## 💬 还有问题？ / More Questions?

如果您的问题没有在这里找到答案：

1. 查看其他文档
2. 搜索GitHub Issues
3. 提交新的Issue
4. 参与社区讨论

---

**最后更新**: 2024-01-15
