#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
L2 Redis缓存层
提供分布式缓存服务
"""

import json
import pickle
import time
import redis
from typing import Any, Optional, Dict, List, Union
from flask import current_app
import threading


class RedisCache:
    """L2 Redis缓存"""
    
    def __init__(self, 
                 host: str = 'localhost',
                 port: int = 6379,
                 db: int = 0,
                 password: Optional[str] = None,
                 decode_responses: bool = False,
                 max_connections: int = 20):
        
        self.config = {
            'host': host,
            'port': port,
            'db': db,
            'password': password,
            'decode_responses': decode_responses,
            'max_connections': max_connections,
            'socket_timeout': 5,
            'socket_connect_timeout': 5,
            'retry_on_timeout': True,
            'health_check_interval': 30
        }
        
        self.pool = None
        self.client = None
        self.available = False
        self.lock = threading.RLock()
        
        # 统计信息
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'errors': 0,
            'connections': 0
        }
        
        # 初始化连接
        self._init_connection()
    
    def _init_connection(self):
        """初始化Redis连接"""
        try:
            # 创建连接池
            self.pool = redis.ConnectionPool(**self.config)
            self.client = redis.Redis(connection_pool=self.pool)
            
            # 测试连接
            self.client.ping()
            self.available = True
            
            if current_app:
                current_app.logger.info("Redis缓存连接成功")
                
        except Exception as e:
            self.available = False
            if current_app:
                current_app.logger.warning(f"Redis缓存连接失败: {e}")
            else:
                print(f"Redis缓存连接失败: {e}")
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if not self.available:
            return None
        
        try:
            with self.lock:
                data = self.client.get(key)
                
                if data is None:
                    self.stats['misses'] += 1
                    return None
                
                # 尝试反序列化
                try:
                    value = pickle.loads(data)
                except:
                    try:
                        value = json.loads(data.decode('utf-8'))
                    except:
                        value = data.decode('utf-8')
                
                self.stats['hits'] += 1
                return value
                
        except Exception as e:
            self.stats['errors'] += 1
            self._handle_error(e)
            return None
    
    def set(self, key: str, value: Any, ttl: int = 1800) -> bool:
        """设置缓存值"""
        if not self.available:
            return False
        
        try:
            with self.lock:
                # 序列化数据
                if isinstance(value, (dict, list, tuple)):
                    try:
                        data = json.dumps(value, ensure_ascii=False)
                    except:
                        data = pickle.dumps(value)
                elif isinstance(value, str):
                    data = value
                else:
                    data = pickle.dumps(value)
                
                # 设置缓存
                result = self.client.setex(key, ttl, data)
                
                if result:
                    self.stats['sets'] += 1
                    return True
                return False
                
        except Exception as e:
            self.stats['errors'] += 1
            self._handle_error(e)
            return False
    
    def delete(self, key: str) -> bool:
        """删除缓存项"""
        if not self.available:
            return False
        
        try:
            with self.lock:
                result = self.client.delete(key)
                if result > 0:
                    self.stats['deletes'] += 1
                    return True
                return False
                
        except Exception as e:
            self.stats['errors'] += 1
            self._handle_error(e)
            return False
    
    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        if not self.available:
            return False
        
        try:
            return bool(self.client.exists(key))
        except Exception as e:
            self._handle_error(e)
            return False
    
    def clear(self, pattern: str = '*') -> int:
        """清理缓存"""
        if not self.available:
            return 0
        
        try:
            with self.lock:
                if pattern == '*':
                    # 清理所有键（危险操作，仅用于测试）
                    return self.client.flushdb()
                
                # 模式匹配删除
                keys = self.client.keys(pattern)
                if keys:
                    return self.client.delete(*keys)
                return 0
                
        except Exception as e:
            self.stats['errors'] += 1
            self._handle_error(e)
            return 0
    
    def mget(self, keys: List[str]) -> Dict[str, Any]:
        """批量获取"""
        if not self.available or not keys:
            return {}
        
        try:
            with self.lock:
                values = self.client.mget(keys)
                result = {}
                
                for key, data in zip(keys, values):
                    if data is not None:
                        try:
                            result[key] = pickle.loads(data)
                        except:
                            try:
                                result[key] = json.loads(data.decode('utf-8'))
                            except:
                                result[key] = data.decode('utf-8')
                
                return result
                
        except Exception as e:
            self._handle_error(e)
            return {}
    
    def mset(self, mapping: Dict[str, Any], ttl: int = 1800) -> bool:
        """批量设置"""
        if not self.available or not mapping:
            return False
        
        try:
            with self.lock:
                # 使用pipeline提高性能
                pipe = self.client.pipeline()
                
                for key, value in mapping.items():
                    # 序列化数据
                    if isinstance(value, (dict, list, tuple)):
                        try:
                            data = json.dumps(value, ensure_ascii=False)
                        except:
                            data = pickle.dumps(value)
                    elif isinstance(value, str):
                        data = value
                    else:
                        data = pickle.dumps(value)
                    
                    pipe.setex(key, ttl, data)
                
                results = pipe.execute()
                success_count = sum(1 for r in results if r)
                self.stats['sets'] += success_count
                
                return success_count == len(mapping)
                
        except Exception as e:
            self.stats['errors'] += 1
            self._handle_error(e)
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        try:
            if not self.available:
                return {
                    'available': False,
                    'hit_rate': 0,
                    'key_count': 0,
                    'memory_usage': 0,
                    'connections': 0,
                    'stats': self.stats.copy()
                }
            
            with self.lock:
                info = self.client.info()
                total_requests = self.stats['hits'] + self.stats['misses']
                hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0
                
                return {
                    'available': True,
                    'hit_rate': hit_rate,
                    'key_count': info.get('db0', {}).get('keys', 0),
                    'memory_usage': info.get('used_memory', 0) / 1024 / 1024,  # MB
                    'connections': info.get('connected_clients', 0),
                    'stats': self.stats.copy()
                }
                
        except Exception as e:
            self._handle_error(e)
            return {
                'available': False,
                'error': str(e),
                'stats': self.stats.copy()
            }
    
    def _handle_error(self, error: Exception):
        """处理错误"""
        if current_app:
            current_app.logger.error(f"Redis缓存错误: {error}")
        
        # 连接错误时尝试重连
        if "Connection" in str(error) or "timeout" in str(error).lower():
            self.available = False
            threading.Thread(target=self._reconnect, daemon=True).start()
    
    def _reconnect(self):
        """重连Redis"""
        max_retries = 3
        retry_delay = 5
        
        for i in range(max_retries):
            try:
                time.sleep(retry_delay)
                self._init_connection()
                if self.available:
                    if current_app:
                        current_app.logger.info("Redis缓存重连成功")
                    break
            except Exception as e:
                if current_app:
                    current_app.logger.warning(f"Redis重连失败 ({i+1}/{max_retries}): {e}")
                retry_delay *= 2


# 全局Redis缓存实例
_redis_cache = None

def get_redis_cache() -> RedisCache:
    """获取全局Redis缓存实例"""
    global _redis_cache
    if _redis_cache is None:
        _redis_cache = RedisCache()
    return _redis_cache
