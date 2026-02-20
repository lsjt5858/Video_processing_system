"""
分片上传模块

实现大文件分片上传，支持断点续传和进度跟踪
"""

import os
import hashlib
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field


@dataclass
class UploadSession:
    """上传会话"""
    session_id: str
    filename: str
    total_size: int
    chunk_size: int
    total_chunks: int
    uploaded_chunks: set = field(default_factory=set)
    temp_dir: Path = None
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    file_hash: Optional[str] = None
    user_id: str = "default_user"


class ChunkedUploadManager:
    """
    分片上传管理器
    
    功能:
    - 支持大文件分片上传（>100MB）
    - 支持断点续传
    - 支持并发上传多个分片
    - 自动清理过期会话
    """
    
    def __init__(
        self,
        upload_dir: Path,
        chunk_size: int = 5 * 1024 * 1024,  # 5MB per chunk
        session_timeout: int = 3600,  # 1 hour
        cleanup_interval: int = 600  # 10 minutes
    ):
        """
        初始化分片上传管理器
        
        参数:
            upload_dir: 上传目录
            chunk_size: 分片大小（字节）
            session_timeout: 会话超时时间（秒）
            cleanup_interval: 清理间隔（秒）
        """
        self.upload_dir = upload_dir
        self.chunk_size = chunk_size
        self.session_timeout = session_timeout
        self.cleanup_interval = cleanup_interval
        
        self.sessions: Dict[str, UploadSession] = {}
        self.lock = asyncio.Lock()
        
        # 创建临时目录
        self.temp_dir = upload_dir / "temp_chunks"
        self.temp_dir.mkdir(exist_ok=True)
        
        # 清理任务
        self.cleanup_task: Optional[asyncio.Task] = None
        self.is_running = False
    
    async def start(self):
        """启动管理器"""
        if not self.is_running:
            self.is_running = True
            self.cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def stop(self):
        """停止管理器"""
        self.is_running = False
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
    
    async def create_session(
        self,
        filename: str,
        total_size: int,
        user_id: str = "default_user",
        file_hash: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        创建上传会话
        
        参数:
            filename: 文件名
            total_size: 文件总大小（字节）
            user_id: 用户ID
            file_hash: 文件哈希（可选，用于去重）
        
        返回:
            Dict: 会话信息
        """
        async with self.lock:
            # 生成会话ID
            session_id = hashlib.md5(
                f"{filename}_{total_size}_{datetime.now().isoformat()}".encode()
            ).hexdigest()
            
            # 计算分片数量
            total_chunks = (total_size + self.chunk_size - 1) // self.chunk_size
            
            # 创建会话临时目录
            session_temp_dir = self.temp_dir / session_id
            session_temp_dir.mkdir(exist_ok=True)
            
            # 创建会话
            session = UploadSession(
                session_id=session_id,
                filename=filename,
                total_size=total_size,
                chunk_size=self.chunk_size,
                total_chunks=total_chunks,
                temp_dir=session_temp_dir,
                file_hash=file_hash,
                user_id=user_id
            )
            
            self.sessions[session_id] = session
            
            return {
                "session_id": session_id,
                "chunk_size": self.chunk_size,
                "total_chunks": total_chunks,
                "uploaded_chunks": list(session.uploaded_chunks)
            }
    
    async def upload_chunk(
        self,
        session_id: str,
        chunk_index: int,
        chunk_data: bytes
    ) -> Dict[str, Any]:
        """
        上传分片
        
        参数:
            session_id: 会话ID
            chunk_index: 分片索引（从0开始）
            chunk_data: 分片数据
        
        返回:
            Dict: 上传结果
        """
        async with self.lock:
            if session_id not in self.sessions:
                raise ValueError(f"会话 {session_id} 不存在")
            
            session = self.sessions[session_id]
            
            # 验证分片索引
            if chunk_index < 0 or chunk_index >= session.total_chunks:
                raise ValueError(f"无效的分片索引: {chunk_index}")
            
            # 验证分片大小
            expected_size = self.chunk_size
            if chunk_index == session.total_chunks - 1:
                # 最后一个分片可能小于chunk_size
                expected_size = session.total_size - (chunk_index * self.chunk_size)
            
            if len(chunk_data) != expected_size:
                raise ValueError(
                    f"分片大小不匹配: 期望 {expected_size} 字节，实际 {len(chunk_data)} 字节"
                )
            
            # 保存分片
            chunk_path = session.temp_dir / f"chunk_{chunk_index}"
            with open(chunk_path, "wb") as f:
                f.write(chunk_data)
            
            # 更新会话
            session.uploaded_chunks.add(chunk_index)
            session.last_activity = datetime.now()
            
            # 计算进度
            progress = len(session.uploaded_chunks) / session.total_chunks * 100
            
            return {
                "session_id": session_id,
                "chunk_index": chunk_index,
                "uploaded_chunks": len(session.uploaded_chunks),
                "total_chunks": session.total_chunks,
                "progress": progress,
                "is_complete": len(session.uploaded_chunks) == session.total_chunks
            }
    
    async def merge_chunks(
        self,
        session_id: str,
        output_filename: Optional[str] = None
    ) -> str:
        """
        合并分片
        
        参数:
            session_id: 会话ID
            output_filename: 输出文件名（可选）
        
        返回:
            str: 合并后的文件路径
        """
        async with self.lock:
            if session_id not in self.sessions:
                raise ValueError(f"会话 {session_id} 不存在")
            
            session = self.sessions[session_id]
            
            # 验证所有分片都已上传
            if len(session.uploaded_chunks) != session.total_chunks:
                missing_chunks = set(range(session.total_chunks)) - session.uploaded_chunks
                raise ValueError(
                    f"还有 {len(missing_chunks)} 个分片未上传: {sorted(missing_chunks)[:10]}"
                )
            
            # 确定输出文件名
            if output_filename is None:
                output_filename = session.filename
            
            output_path = self.upload_dir / output_filename
            
            # 合并分片
            with open(output_path, "wb") as output_file:
                for chunk_index in range(session.total_chunks):
                    chunk_path = session.temp_dir / f"chunk_{chunk_index}"
                    
                    if not chunk_path.exists():
                        raise ValueError(f"分片 {chunk_index} 不存在")
                    
                    with open(chunk_path, "rb") as chunk_file:
                        output_file.write(chunk_file.read())
            
            # 验证文件大小
            actual_size = output_path.stat().st_size
            if actual_size != session.total_size:
                output_path.unlink()
                raise ValueError(
                    f"合并后文件大小不匹配: 期望 {session.total_size} 字节，实际 {actual_size} 字节"
                )
            
            # 清理临时文件
            await self._cleanup_session(session_id)
            
            return str(output_path)
    
    async def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        获取会话状态
        
        参数:
            session_id: 会话ID
        
        返回:
            Optional[Dict]: 会话状态信息
        """
        async with self.lock:
            if session_id not in self.sessions:
                return None
            
            session = self.sessions[session_id]
            progress = len(session.uploaded_chunks) / session.total_chunks * 100
            
            return {
                "session_id": session_id,
                "filename": session.filename,
                "total_size": session.total_size,
                "chunk_size": session.chunk_size,
                "total_chunks": session.total_chunks,
                "uploaded_chunks": len(session.uploaded_chunks),
                "progress": progress,
                "is_complete": len(session.uploaded_chunks) == session.total_chunks,
                "created_at": session.created_at.isoformat(),
                "last_activity": session.last_activity.isoformat()
            }
    
    async def cancel_session(self, session_id: str) -> bool:
        """
        取消上传会话
        
        参数:
            session_id: 会话ID
        
        返回:
            bool: 是否成功取消
        """
        async with self.lock:
            if session_id in self.sessions:
                await self._cleanup_session(session_id)
                return True
            return False
    
    async def _cleanup_session(self, session_id: str):
        """
        清理会话（删除临时文件）
        
        参数:
            session_id: 会话ID
        """
        if session_id not in self.sessions:
            return
        
        session = self.sessions[session_id]
        
        # 删除临时目录及其内容
        if session.temp_dir and session.temp_dir.exists():
            import shutil
            shutil.rmtree(session.temp_dir, ignore_errors=True)
        
        # 删除会话
        del self.sessions[session_id]
    
    async def _cleanup_loop(self):
        """定期清理过期会话"""
        while self.is_running:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self._cleanup_expired_sessions()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"会话清理错误: {e}")
    
    async def _cleanup_expired_sessions(self):
        """清理过期的会话"""
        async with self.lock:
            current_time = datetime.now()
            expired_sessions = []
            
            for session_id, session in self.sessions.items():
                time_since_activity = (current_time - session.last_activity).total_seconds()
                if time_since_activity > self.session_timeout:
                    expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                await self._cleanup_session(session_id)
            
            if expired_sessions:
                print(f"清理了 {len(expired_sessions)} 个过期上传会话")


# 创建全局分片上传管理器实例
# 注意：需要在应用启动时初始化
chunked_upload_manager: Optional[ChunkedUploadManager] = None


def init_chunked_upload_manager(upload_dir: Path):
    """初始化分片上传管理器"""
    global chunked_upload_manager
    chunked_upload_manager = ChunkedUploadManager(
        upload_dir=upload_dir,
        chunk_size=5 * 1024 * 1024,  # 5MB
        session_timeout=3600,  # 1小时
        cleanup_interval=600  # 10分钟
    )
    return chunked_upload_manager
