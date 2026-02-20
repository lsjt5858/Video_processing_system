"""
异步任务处理模块

使用asyncio实现异步视频处理，通过WebSocket推送处理进度
"""

import asyncio
import uuid
from datetime import datetime
from typing import Optional, Callable, Dict, Any, List
from pathlib import Path

from .models import ProcessingTask, TaskStatus, WatermarkRegion, BoundingBox
from .watermark_removal import removal_engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update


class TaskProcessor:
    """异步任务处理器"""
    
    def __init__(self, max_concurrent_tasks: int = 3):
        """
        初始化任务处理器
        
        参数:
            max_concurrent_tasks: 最大并发任务数（批量操作时）
        """
        self.max_concurrent_tasks = max_concurrent_tasks
        self.active_tasks: Dict[str, asyncio.Task] = {}
    
    async def process_removal_task(
        self,
        db: AsyncSession,
        task_id: str,
        video_id: str,
        video_path: str,
        regions: List[Dict[str, Any]],
        video_metadata: Dict[str, Any],
        websocket_callback: Optional[Callable] = None,
        client_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        处理单个水印去除任务
        
        参数:
            db: 数据库会话
            task_id: 任务ID
            video_id: 视频ID
            video_path: 视频文件路径
            regions: 水印区域列表（字典格式）
            video_metadata: 视频元数据
            websocket_callback: WebSocket回调函数
            client_id: 客户端ID
        
        返回:
            Dict: 处理结果
        """
        try:
            # 更新任务状态为processing
            await self._update_task_status(
                db, task_id, TaskStatus.PROCESSING, started_at=datetime.now()
            )
            
            # 推送开始处理消息
            if websocket_callback and client_id:
                await websocket_callback(client_id, {
                    "type": "task_progress",
                    "task_id": task_id,
                    "video_id": video_id,
                    "status": "processing",
                    "progress": 0,
                    "message": "开始处理视频..."
                })
            
            # 转换水印区域为WatermarkRegion对象
            watermark_regions = []
            for region_data in regions:
                bbox = BoundingBox(
                    x=region_data['bbox']['x'],
                    y=region_data['bbox']['y'],
                    width=region_data['bbox']['width'],
                    height=region_data['bbox']['height']
                )
                watermark_region = WatermarkRegion(
                    region_id=region_data.get('region_id', f"reg_{uuid.uuid4().hex[:12]}"),
                    video_id=video_id,
                    bbox=bbox,
                    start_time=region_data.get('start_time', 0.0),
                    end_time=region_data.get('end_time', video_metadata.get('duration', 0.0)),
                    confidence=region_data.get('confidence', 1.0),
                    watermark_type=region_data.get('watermark_type', 'manual'),
                    detection_method=region_data.get('detection_method', 'manual')
                )
                watermark_regions.append(watermark_region)
            
            # 推送进度：30%
            if websocket_callback and client_id:
                await websocket_callback(client_id, {
                    "type": "task_progress",
                    "task_id": task_id,
                    "video_id": video_id,
                    "status": "processing",
                    "progress": 30,
                    "message": "分析水印区域..."
                })
            
            # 执行水印去除（在线程池中运行以避免阻塞）
            loop = asyncio.get_event_loop()
            removal_result = await loop.run_in_executor(
                None,
                removal_engine.crop_reconstruct,
                video_path,
                video_id,
                watermark_regions,
                video_metadata
            )
            
            # 推送进度：80%
            if websocket_callback and client_id:
                await websocket_callback(client_id, {
                    "type": "task_progress",
                    "task_id": task_id,
                    "video_id": video_id,
                    "status": "processing",
                    "progress": 80,
                    "message": "正在生成输出视频..."
                })
            
            # 构建结果
            result = {
                "output_video_id": removal_result.output_video_id,
                "output_path": removal_result.output_path,
                "processing_mode": removal_result.processing_mode.value,
                "processing_duration": removal_result.processing_duration,
                "parameters": removal_result.parameters
            }
            
            # 更新任务状态为completed
            await self._update_task_status(
                db,
                task_id,
                TaskStatus.COMPLETED,
                completed_at=datetime.now(),
                result=result
            )
            
            # 推送完成消息
            if websocket_callback and client_id:
                await websocket_callback(client_id, {
                    "type": "task_completed",
                    "task_id": task_id,
                    "video_id": video_id,
                    "status": "completed",
                    "progress": 100,
                    "message": "处理完成",
                    "result": result
                })
            
            return result
            
        except Exception as e:
            # 更新任务状态为failed
            error_message = str(e)
            await self._update_task_status(
                db,
                task_id,
                TaskStatus.FAILED,
                completed_at=datetime.now(),
                error_message=error_message
            )
            
            # 推送失败消息
            if websocket_callback and client_id:
                await websocket_callback(client_id, {
                    "type": "task_failed",
                    "task_id": task_id,
                    "video_id": video_id,
                    "status": "failed",
                    "message": f"处理失败: {error_message}",
                    "error": error_message
                })
            
            raise
    
    async def process_batch_removal(
        self,
        db: AsyncSession,
        batch_tasks: List[Dict[str, Any]],
        websocket_callback: Optional[Callable] = None,
        client_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        批量处理水印去除任务（最多3个视频并行）
        
        参数:
            db: 数据库会话
            batch_tasks: 批量任务列表，每个任务包含task_id, video_id, video_path, regions, video_metadata
            websocket_callback: WebSocket回调函数
            client_id: 客户端ID
        
        返回:
            List[Dict]: 批量处理结果列表
        """
        # 创建信号量限制并发数
        semaphore = asyncio.Semaphore(self.max_concurrent_tasks)
        
        async def process_with_semaphore(task_data: Dict[str, Any]) -> Dict[str, Any]:
            """使用信号量控制并发的任务处理"""
            async with semaphore:
                try:
                    result = await self.process_removal_task(
                        db=db,
                        task_id=task_data['task_id'],
                        video_id=task_data['video_id'],
                        video_path=task_data['video_path'],
                        regions=task_data['regions'],
                        video_metadata=task_data['video_metadata'],
                        websocket_callback=websocket_callback,
                        client_id=client_id
                    )
                    return {
                        "task_id": task_data['task_id'],
                        "video_id": task_data['video_id'],
                        "status": "completed",
                        "result": result
                    }
                except Exception as e:
                    return {
                        "task_id": task_data['task_id'],
                        "video_id": task_data['video_id'],
                        "status": "failed",
                        "error": str(e)
                    }
        
        # 并发处理所有任务
        tasks = [process_with_semaphore(task_data) for task_data in batch_tasks]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "task_id": batch_tasks[i]['task_id'],
                    "video_id": batch_tasks[i]['video_id'],
                    "status": "failed",
                    "error": str(result)
                })
            else:
                processed_results.append(result)
        
        # 推送批量处理完成消息
        if websocket_callback and client_id:
            completed_count = sum(1 for r in processed_results if r['status'] == 'completed')
            failed_count = sum(1 for r in processed_results if r['status'] == 'failed')
            
            await websocket_callback(client_id, {
                "type": "batch_completed",
                "total": len(batch_tasks),
                "completed": completed_count,
                "failed": failed_count,
                "message": f"批量处理完成: {completed_count}个成功, {failed_count}个失败"
            })
        
        return processed_results
    
    async def _update_task_status(
        self,
        db: AsyncSession,
        task_id: str,
        status: TaskStatus,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        error_message: Optional[str] = None,
        result: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        更新任务状态
        
        参数:
            db: 数据库会话
            task_id: 任务ID
            status: 新状态
            started_at: 开始时间
            completed_at: 完成时间
            error_message: 错误信息
            result: 处理结果
        """
        from .database import ProcessingTask as DBProcessingTask
        
        # 构建更新字典
        update_data = {"status": status.value}
        
        if started_at:
            update_data["started_at"] = started_at
        if completed_at:
            update_data["completed_at"] = completed_at
        if error_message:
            update_data["error_message"] = error_message
        if result:
            update_data["result"] = result
        
        # 执行更新
        stmt = (
            update(DBProcessingTask)
            .where(DBProcessingTask.task_id == task_id)
            .values(**update_data)
        )
        await db.execute(stmt)
        await db.commit()
    
    async def get_task_status(
        self,
        db: AsyncSession,
        task_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        获取任务状态
        
        参数:
            db: 数据库会话
            task_id: 任务ID
        
        返回:
            Optional[Dict]: 任务状态信息，如果任务不存在则返回None
        """
        from .database import ProcessingTask as DBProcessingTask
        
        stmt = select(DBProcessingTask).where(DBProcessingTask.task_id == task_id)
        result = await db.execute(stmt)
        task = result.scalar_one_or_none()
        
        if not task:
            return None
        
        return {
            "task_id": task.task_id,
            "user_id": task.user_id,
            "video_id": task.video_id,
            "task_type": task.task_type,
            "status": task.status,
            "parameters": task.parameters,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "error_message": task.error_message,
            "result": task.result
        }


# 创建全局任务处理器实例
task_processor = TaskProcessor(max_concurrent_tasks=3)
