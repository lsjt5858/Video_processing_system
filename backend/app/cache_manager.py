"""
缓存管理器

实现内存缓存机制，用于缓存视频元数据、缩略图和帧数据
"""

import asyncio
import hashlib
import time
from typing import Any, Optional, Dict, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    created_at: float
    expires_at: Optional[float]
    access_count: int = 0
    last_accessed: float = 0.0
    size_bytes: int = 0


class CacheManager:
    """
    内存缓存管理器
    
    功能:
    - LRU缓存策略
    - 支持过期时间
    - 支持缓存大小限制
    - 支持缓存统计
    """
    
    def __init__(
        self,
        max_size_mb: int = 500,
        default_ttl: int = 3600,
        cleanup_interval: int = 300
    ):
        """
        初始化缓存管理器
        
        参数:
            max_size_mb: 最大缓存大小（MB）
            default_ttl: 默认过期时间（秒）
            cleanup_interval: 清理间隔（秒）
        """
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.default_ttl = default_ttl
        self.cleanup_interval = cleanup_interval
        
        self.cache: Dict[str, CacheEntry] = {}
        self.current_size = 0
        self.lock = asyncio.Lock()
        
        # 统计信息
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        
        # 启动清理任务
        self.cleanup_task: Optional[asyncio.Task] = None
        self.is_running = False
    
    async def start(self):
        """启动缓存管理器"""
        if not self.is_running:
            self.is_running = True
            self.cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def stop(self):
        """停止缓存管理器"""
        self.is_running = False
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
    
    def _generate_key(self, namespace: str, identifier: str) -> str:
        """
        生成缓存键
        
        参数:
            namespace: 命名空间（如"metadata", "thumbnail", "frame"）
            identifier: 标识符（如video_id）
        
        返回:
            str: 缓存键
        """
        return f"{namespace}:{identifier}"
    
    def _estimate_size(self, value: Any) -> int:
        """
        估算对象大小（字节）
        
        参数:
            value: 要估算的对象
        
        返回:
            int: 估算的大小（字节）
        """
        import sys
        
        if isinstance(value, (str, bytes)):
            return len(value)
        elif isinstance(value, dict):
            return sum(self._estimate_size(k) + self._estimate_size(v) for k, v in value.items())
        elif isinstance(value, (list, tuple)):
            return sum(self._estimate_size(item) for item in value)
        else:
            return sys.getsizeof(value)
    
    async def get(self, namespace: str, identifier: str) -> Optional[Any]:
        """
        从缓存获取数据
        
        参数:
            namespace: 命名空间
            identifier: 标识符
        
        返回:
            Optional[Any]: 缓存的值，如果不存在或已过期返回None
        """
        key = self._generate_key(namespace, identifier)
        
        async with self.lock:
            if key not in self.cache:
                self.misses += 1
                return None
            
            entry = self.cache[key]
            
            # 检查是否过期
            current_time = time.time()
            if entry.expires_at and current_time > entry.expires_at:
                # 已过期，删除
                self._remove_entry(key)
                self.misses += 1
                return None
            
            # 更新访问信息
            entry.access_count += 1
            entry.last_accessed = current_time
            
            self.hits += 1
            return entry.value
    
    async def set(
        self,
        namespace: str,
        identifier: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        设置缓存数据
        
        参数:
            namespace: 命名空间
            identifier: 标识符
            value: 要缓存的值
            ttl: 过期时间（秒），None表示使用默认值
        
        返回:
            bool: 是否成功设置
        """
        key = self._generate_key(namespace, identifier)
        size = self._estimate_size(value)
        
        # 检查大小是否超过最大缓存大小
        if size > self.max_size_bytes:
            return False
        
        async with self.lock:
            current_time = time.time()
            ttl_seconds = ttl if ttl is not None else self.default_ttl
            expires_at = current_time + ttl_seconds if ttl_seconds > 0 else None
            
            # 如果键已存在，先删除旧条目
            if key in self.cache:
                self._remove_entry(key)
            
            # 确保有足够空间
            while self.current_size + size > self.max_size_bytes and self.cache:
                self._evict_lru()
            
            # 添加新条目
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=current_time,
                expires_at=expires_at,
                last_accessed=current_time,
                size_bytes=size
            )
            
            self.cache[key] = entry
            self.current_size += size
            
            return True
    
    async def delete(self, namespace: str, identifier: str) -> bool:
        """
        删除缓存数据
        
        参数:
            namespace: 命名空间
            identifier: 标识符
        
        返回:
            bool: 是否成功删除
        """
        key = self._generate_key(namespace, identifier)
        
        async with self.lock:
            if key in self.cache:
                self._remove_entry(key)
                return True
            return False
    
    async def clear(self, namespace: Optional[str] = None):
        """
        清空缓存
        
        参数:
            namespace: 命名空间，如果为None则清空所有缓存
        """
        async with self.lock:
            if namespace is None:
                self.cache.clear()
                self.current_size = 0
            else:
                keys_to_remove = [
                    key for key in self.cache.keys()
                    if key.startswith(f"{namespace}:")
                ]
                for key in keys_to_remove:
                    self._remove_entry(key)
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        返回:
            Dict: 统计信息
        """
        async with self.lock:
            total_requests = self.hits + self.misses
            hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
            
            return {
                "entries": len(self.cache),
                "size_mb": self.current_size / (1024 * 1024),
                "max_size_mb": self.max_size_bytes / (1024 * 1024),
                "usage_percent": (self.current_size / self.max_size_bytes * 100) if self.max_size_bytes > 0 else 0,
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": hit_rate,
                "evictions": self.evictions
            }
    
    def _remove_entry(self, key: str):
        """
        删除缓存条目（内部方法，不加锁）
        
        参数:
            key: 缓存键
        """
        if key in self.cache:
            entry = self.cache[key]
            self.current_size -= entry.size_bytes
            del self.cache[key]
    
    def _evict_lru(self):
        """
        驱逐最少使用的缓存条目（LRU策略）
        """
        if not self.cache:
            return
        
        # 找到最少使用的条目
        lru_key = min(
            self.cache.keys(),
            key=lambda k: (self.cache[k].last_accessed, self.cache[k].access_count)
        )
        
        self._remove_entry(lru_key)
        self.evictions += 1
    
    async def _cleanup_loop(self):
        """定期清理过期缓存"""
        while self.is_running:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"缓存清理错误: {e}")
    
    async def _cleanup_expired(self):
        """清理过期的缓存条目"""
        async with self.lock:
            current_time = time.time()
            keys_to_remove = []
            
            for key, entry in self.cache.items():
                if entry.expires_at and current_time > entry.expires_at:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                self._remove_entry(key)
            
            if keys_to_remove:
                print(f"清理了 {len(keys_to_remove)} 个过期缓存条目")


# 创建全局缓存管理器实例
cache_manager = CacheManager(
    max_size_mb=500,  # 500MB缓存
    default_ttl=3600,  # 1小时过期
    cleanup_interval=300  # 5分钟清理一次
)


# 便捷函数
async def cache_video_metadata(video_id: str, metadata: Dict[str, Any], ttl: int = 7200):
    """缓存视频元数据（2小时）"""
    await cache_manager.set("metadata", video_id, metadata, ttl=ttl)


async def get_cached_metadata(video_id: str) -> Optional[Dict[str, Any]]:
    """获取缓存的视频元数据"""
    return await cache_manager.get("metadata", video_id)


async def cache_thumbnail(video_id: str, frame_idx: int, thumbnail_path: str, ttl: int = 3600):
    """缓存缩略图路径（1小时）"""
    identifier = f"{video_id}_frame_{frame_idx}"
    await cache_manager.set("thumbnail", identifier, thumbnail_path, ttl=ttl)


async def get_cached_thumbnail(video_id: str, frame_idx: int) -> Optional[str]:
    """获取缓存的缩略图路径"""
    identifier = f"{video_id}_frame_{frame_idx}"
    return await cache_manager.get("thumbnail", identifier)


async def cache_frames(video_id: str, frames: list, ttl: int = 1800):
    """缓存提取的帧列表（30分钟）"""
    await cache_manager.set("frames", video_id, frames, ttl=ttl)


async def get_cached_frames(video_id: str) -> Optional[list]:
    """获取缓存的帧列表"""
    return await cache_manager.get("frames", video_id)


async def invalidate_video_cache(video_id: str):
    """使视频相关的所有缓存失效"""
    await cache_manager.delete("metadata", video_id)
    await cache_manager.delete("frames", video_id)
    # 注意：缩略图缓存需要遍历删除，这里简化处理
