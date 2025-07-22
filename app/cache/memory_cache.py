#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
L1 内存缓存层
提供进程内的高速缓存服务
"""

import time
import threading
import pickle
import sys
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
from collections import OrderedDict
import weakref
import gc


class CacheItem:
    """缓存项"""
    
    def __init__(self, value: Any, ttl: int = 300):
        self.value = value
        self.created_at = time.time()
        self.ttl = ttl
        self.access_count = 1
        self.last_access = self.created_at
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.ttl <= 0:  # 永不过期
            return False
        return time.time() - self.created_at > self.ttl
    
    def is_stale(self, max_age: int) -> bool:
        """检查是否陈旧"""
        return time.time() - self.created_at > max_age
    
    def touch(self):
        """更新访问时间"""
        self.access_count += 1
        self.last_access = time.time()
    
    def get_size(self) -> int:
        """获取缓存项大小（字节）"""
        try:
            return sys.getsizeof(pickle.dumps(self.value))
        except:
            return sys.getsizeof(str(self.value))


class MemoryCache:
    """L1 内存缓存"""
    
    def __init__(self, max_size: int = 500, max_items: int = 10000):
        self.max_size = max_size * 1024 * 1024  # 转换为字节
        self.max_items = max_items
        self.cache: OrderedDict[str, CacheItem] = OrderedDict()
        self.lock = threading.RLock()
        
        # 统计信息
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'evictions': 0,
            'size_evictions': 0,
            'ttl_evictions': 0
        }
        
        # 启动清理线程
        self._start_cleanup_thread()
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        with self.lock:
            item = self.cache.get(key)
            
            if item is None:
                self.stats['misses'] += 1
                return None
            
            if item.is_expired():
                del self.cache[key]
                self.stats['misses'] += 1
                self.stats['ttl_evictions'] += 1
                return None
            
            # 更新访问信息并移到末尾（LRU）
            item.touch()
            self.cache.move_to_end(key)
            self.stats['hits'] += 1
            
            return item.value
    
    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """设置缓存值"""
        with self.lock:
            try:
                item = CacheItem(value, ttl)
                
                # 检查是否需要清理空间
                if key not in self.cache:
                    self._ensure_space(item.get_size())
                
                self.cache[key] = item
                self.cache.move_to_end(key)
                self.stats['sets'] += 1
                
                return True
            except Exception as e:
                print(f"内存缓存设置失败: {e}")
                return False
    
    def delete(self, key: str) -> bool:
        """删除缓存项"""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                self.stats['deletes'] += 1
                return True
            return False
    
    def clear(self, pattern: str = '*') -> int:
        """清理缓存"""
        with self.lock:
            if pattern == '*':
                count = len(self.cache)
                self.cache.clear()
                return count
            
            # 模式匹配删除
            keys_to_delete = []
            for key in self.cache:
                if self._match_pattern(key, pattern):
                    keys_to_delete.append(key)
            
            for key in keys_to_delete:
                del self.cache[key]
            
            return len(keys_to_delete)
    
    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        with self.lock:
            item = self.cache.get(key)
            if item and not item.is_expired():
                return True
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self.lock:
            total_requests = self.stats['hits'] + self.stats['misses']
            hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0
            
            current_size = sum(item.get_size() for item in self.cache.values())
            
            return {
                'available': True,
                'hit_rate': hit_rate,
                'key_count': len(self.cache),
                'memory_usage': current_size / 1024 / 1024,  # MB
                'max_memory': self.max_size / 1024 / 1024,  # MB
                'memory_usage_percent': (current_size / self.max_size * 100) if self.max_size > 0 else 0,
                'stats': self.stats.copy()
            }
    
    def _ensure_space(self, needed_size: int):
        """确保有足够空间"""
        current_size = sum(item.get_size() for item in self.cache.values())
        
        # 检查数量限制
        while len(self.cache) >= self.max_items:
            self._evict_lru()
            self.stats['evictions'] += 1
        
        # 检查大小限制
        while current_size + needed_size > self.max_size and self.cache:
            evicted_size = self._evict_lru()
            current_size -= evicted_size
            self.stats['size_evictions'] += 1
    
    def _evict_lru(self) -> int:
        """淘汰最少使用的项"""
        if not self.cache:
            return 0
        
        # 获取最少使用的键
        key, item = self.cache.popitem(last=False)
        return item.get_size()
    
    def _cleanup_expired(self):
        """清理过期项"""
        with self.lock:
            expired_keys = []
            for key, item in self.cache.items():
                if item.is_expired():
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.cache[key]
                self.stats['ttl_evictions'] += 1
    
    def _start_cleanup_thread(self):
        """启动清理线程"""
        def cleanup_worker():
            while True:
                try:
                    time.sleep(60)  # 每分钟清理一次
                    self._cleanup_expired()
                    
                    # 强制垃圾回收
                    if len(self.cache) > 1000:
                        gc.collect()
                        
                except Exception as e:
                    print(f"内存缓存清理线程错误: {e}")
        
        thread = threading.Thread(target=cleanup_worker, daemon=True)
        thread.start()
    
    def _match_pattern(self, key: str, pattern: str) -> bool:
        """简单的模式匹配"""
        if pattern == '*':
            return True
        if pattern.endswith('*'):
            return key.startswith(pattern[:-1])
        if pattern.startswith('*'):
            return key.endswith(pattern[1:])
        return key == pattern


# 全局内存缓存实例
_memory_cache = None

def get_memory_cache() -> MemoryCache:
    """获取全局内存缓存实例"""
    global _memory_cache
    if _memory_cache is None:
        _memory_cache = MemoryCache()
    return _memory_cache
