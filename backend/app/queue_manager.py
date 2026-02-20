"""
视频处理队列管理器

实现任务队列系统，限制并发处理，提供队列状态和位置信息
"""

import asyncio
import uuid
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum


class QueueStatus(Enum):
    """队列状态"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class QueuedTask:
    """队列任务"""
    task_id: str
    task_type: str  # "removal", "optimization", "detection"
    video_id: str
    priority: int = 0  # 优先级，数字越大优先级越高
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: QueueStatus = QueueStatus.QUEUED
    error: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    callback: Optional[Callable] = None
    callback_args: Dict[str, Any] = field(default_factory=dict)


class VideoProcessingQueue:
    """
    视频处理队列管理器
    
    功能:
    - 限制并发处理数量（避免系统过载）
    - 提供队列状态和位置信息
    - 支持任务优先级
    - 支持任务取消
    """
    
    def __init__(self, max_concurrent: int = 3):
        """
        初始化队列管理器
        
        参数:
            max_concurrent: 最大并发处理数量（默认3）
        """
        self.max_concurrent = max_concurrent
        self.queue: List[QueuedTask] = []
        self.processing: Dict[str, QueuedTask] = {}
        self.completed: Dict[str, QueuedTask] = {}
        self.lock = asyncio.Lock()
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.worker_task: Optional[asyncio.Task] = None
        self.is_running = False
    
    async def start(self):
        """启动队列处理器"""
        if not self.is_running:
            self.is_running = True
            self.worker_task = asyncio.create_task(self._process_queue())
    
    async def stop(self):
        """停止队列处理器"""
        self.is_running = False
        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass
    
    async def enqueue(
        self,
        task_id: str,
        task_type: str,
        video_id: str,
        priority: int = 0,
        callback: Optional[Callable] = None,
        **callback_args
    ) -> QueuedTask:
        """
        将任务加入队列
        
        参数:
            task_id: 任务ID
            task_type: 任务类型
            video_id: 视频ID
            priority: 优先级（默认0）
            callback: 任务完成后的回调函数
            **callback_args: 回调函数参数
        
        返回:
            QueuedTask: 队列任务对象
        """
        async with self.lock:
            task = QueuedTask(
                task_id=task_id,
                task_type=task_type,
                video_id=video_id,
                priority=priority,
                callback=callback,
                callback_args=callback_args
            )
            
            # 按优先级插入队列（优先级高的在前）
            inserted = False
            for i, queued_task in enumerate(self.queue):
                if task.priority > queued_task.priority:
                    self.queue.insert(i, task)
                    inserted = True
                    break
            
            if not inserted:
                self.queue.append(task)
            
            return task
    
    async def get_queue_position(self, task_id: str) -> Optional[int]:
        """
        获取任务在队列中的位置
        
        参数:
            task_id: 任务ID
        
        返回:
            Optional[int]: 队列位置（从1开始），如果任务不在队列中返回None
        """
        async with self.lock:
            for i, task in enumerate(self.queue):
                if task.task_id == task_id:
                    return i + 1
            return None
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务状态
        
        参数:
            task_id: 任务ID
        
        返回:
            Optional[Dict]: 任务状态信息
        """
        async with self.lock:
            # 检查是否在处理中
            if task_id in self.processing:
                task = self.processing[task_id]
                return {
                    "task_id": task.task_id,
                    "status": task.status.value,
                    "video_id": task.video_id,
                    "task_type": task.task_type,
                    "created_at": task.created_at.isoformat(),
                    "started_at": task.started_at.isoformat() if task.started_at else None,
                    "queue_position": None,
                    "estimated_wait_time": None
                }
            
            # 检查是否已完成
            if task_id in self.completed:
                task = self.completed[task_id]
                return {
                    "task_id": task.task_id,
                    "status": task.status.value,
                    "video_id": task.video_id,
                    "task_type": task.task_type,
                    "created_at": task.created_at.isoformat(),
                    "started_at": task.started_at.isoformat() if task.started_at else None,
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                    "error": task.error,
                    "result": task.result
                }
            
            # 检查是否在队列中
            for i, task in enumerate(self.queue):
                if task.task_id == task_id:
                    # 估算等待时间（基于队列位置和平均处理时间）
                    position = i + 1
                    avg_processing_time = self._calculate_avg_processing_time()
                    estimated_wait = position * avg_processing_time / self.max_concurrent
                    
                    return {
                        "task_id": task.task_id,
                        "status": task.status.value,
                        "video_id": task.video_id,
                        "task_type": task.task_type,
                        "created_at": task.created_at.isoformat(),
                        "queue_position": position,
                        "estimated_wait_time": estimated_wait
                    }
            
            return None
    
    async def get_queue_stats(self) -> Dict[str, Any]:
        """
        获取队列统计信息
        
        返回:
            Dict: 队列统计信息
        """
        async with self.lock:
            return {
                "queued_count": len(self.queue),
                "processing_count": len(self.processing),
                "completed_count": len(self.completed),
                "max_concurrent": self.max_concurrent,
                "avg_processing_time": self._calculate_avg_processing_time(),
                "is_running": self.is_running
            }
    
    async def cancel_task(self, task_id: str) -> bool:
        """
        取消任务
        
        参数:
            task_id: 任务ID
        
        返回:
            bool: 是否成功取消
        """
        async with self.lock:
            # 只能取消队列中的任务，不能取消正在处理的任务
            for i, task in enumerate(self.queue):
                if task.task_id == task_id:
                    task.status = QueueStatus.CANCELLED
                    self.queue.pop(i)
                    self.completed[task_id] = task
                    return True
            return False
    
    def _calculate_avg_processing_time(self) -> float:
        """
        计算平均处理时间（秒）
        
        返回:
            float: 平均处理时间
        """
        if not self.completed:
            return 60.0  # 默认60秒
        
        total_time = 0
        count = 0
        
        for task in self.completed.values():
            if task.started_at and task.completed_at:
                duration = (task.completed_at - task.started_at).total_seconds()
                total_time += duration
                count += 1
        
        if count == 0:
            return 60.0
        
        return total_time / count
    
    async def _process_queue(self):
        """队列处理工作线程"""
        while self.is_running:
            try:
                # 检查是否有任务可以处理
                async with self.lock:
                    if not self.queue or len(self.processing) >= self.max_concurrent:
                        # 没有任务或已达到并发限制
                        await asyncio.sleep(0.5)
                        continue
                    
                    # 获取下一个任务
                    task = self.queue.pop(0)
                    task.status = QueueStatus.PROCESSING
                    task.started_at = datetime.now()
                    self.processing[task.task_id] = task
                
                # 异步处理任务
                asyncio.create_task(self._execute_task(task))
                
            except Exception as e:
                print(f"队列处理错误: {e}")
                await asyncio.sleep(1)
    
    async def _execute_task(self, task: QueuedTask):
        """
        执行任务
        
        参数:
            task: 队列任务
        """
        try:
            async with self.semaphore:
                # 调用回调函数执行实际任务
                if task.callback:
                    result = await task.callback(**task.callback_args)
                    task.result = result
                    task.status = QueueStatus.COMPLETED
                else:
                    task.status = QueueStatus.FAILED
                    task.error = "No callback function provided"
                
                task.completed_at = datetime.now()
        
        except Exception as e:
            task.status = QueueStatus.FAILED
            task.error = str(e)
            task.completed_at = datetime.now()
        
        finally:
            # 将任务从处理中移到已完成
            async with self.lock:
                if task.task_id in self.processing:
                    del self.processing[task.task_id]
                self.completed[task.task_id] = task
                
                # 限制已完成任务的数量（保留最近1000个）
                if len(self.completed) > 1000:
                    # 删除最旧的任务
                    oldest_tasks = sorted(
                        self.completed.values(),
                        key=lambda t: t.completed_at or datetime.now()
                    )[:100]
                    for old_task in oldest_tasks:
                        del self.completed[old_task.task_id]


# 创建全局队列管理器实例
video_queue = VideoProcessingQueue(max_concurrent=3)
