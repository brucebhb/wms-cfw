"""
Redis缓存配置和连接管理
"""

import redis
import json
import pickle
import time
from datetime import datetime, timedelta
from flask import current_app, g
from functools import wraps
import hashlib


class CacheConfig:
    """缓存配置类"""
    
    # Redis连接配置
    REDIS_HOST = 'localhost'
    REDIS_PORT = 6379
    REDIS_DB = 0
    REDIS_PASSWORD = None  # 如果设置了密码，在这里填写
    REDIS_DECODE_RESPONSES = True
    
    # 连接池配置
    REDIS_MAX_CONNECTIONS = 20
    REDIS_SOCKET_TIMEOUT = 5
    REDIS_SOCKET_CONNECT_TIMEOUT = 5
    REDIS_RETRY_ON_TIMEOUT = True
    
    # 缓存过期时间配置（秒）
    CACHE_TIMEOUT = {
        'inventory_list': 3600,      # 库存列表 - 5分钟
        'user_info': 1800,          # 用户信息 - 30分钟
        'warehouse_info': 3600,     # 仓库信息 - 1小时
        'customer_list': 600,       # 客户列表 - 10分钟
        'statistics': 900,          # 统计数据 - 15分钟
        'permissions': 1800,        # 权限信息 - 30分钟
        'search_results': 180,      # 搜索结果 - 3分钟
        'aggregated_data': 600,     # 聚合数据 - 10分钟
    }
    
    # 缓存键前缀
    CACHE_KEY_PREFIX = 'warehouse_system'
    
    # 缓存版本（用于缓存失效）
    CACHE_VERSION = '1.0'


class RedisManager:
    """Redis连接管理器"""
    
    _instance = None
    _redis_client = None
    _connection_pool = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RedisManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._redis_client is None:
            self._init_redis()
    
    def _init_redis(self):
        """初始化Redis连接"""
        try:
            # 创建连接池
            self._connection_pool = redis.ConnectionPool(
                host=CacheConfig.REDIS_HOST,
                port=CacheConfig.REDIS_PORT,
                db=CacheConfig.REDIS_DB,
                password=CacheConfig.REDIS_PASSWORD,
                decode_responses=CacheConfig.REDIS_DECODE_RESPONSES,
                max_connections=CacheConfig.REDIS_MAX_CONNECTIONS,
                socket_timeout=CacheConfig.REDIS_SOCKET_TIMEOUT,
                socket_connect_timeout=CacheConfig.REDIS_SOCKET_CONNECT_TIMEOUT,
                retry_on_timeout=CacheConfig.REDIS_RETRY_ON_TIMEOUT
            )
            
            # 创建Redis客户端
            self._redis_client = redis.Redis(connection_pool=self._connection_pool)
            
            # 测试连接
            self._redis_client.ping()
            try:
                from flask import current_app
                current_app.logger.info("Redis连接初始化成功")
            except RuntimeError:
                # 在应用上下文之外，使用print
                print("Redis连接初始化成功")
            
        except redis.ConnectionError as e:
            try:
                from flask import current_app
                current_app.logger.error(f"Redis连接失败: {str(e)}")
            except RuntimeError:
                print(f"Redis连接失败: {str(e)}")
            self._redis_client = None
        except Exception as e:
            try:
                from flask import current_app
                current_app.logger.error(f"Redis初始化失败: {str(e)}")
            except RuntimeError:
                print(f"Redis初始化失败: {str(e)}")
            self._redis_client = None
    
    def get_client(self):
        """获取Redis客户端"""
        if self._redis_client is None:
            self._init_redis()
        return self._redis_client
    
    def is_available(self):
        """检查Redis是否可用"""
        try:
            if self._redis_client is None:
                return False
            self._redis_client.ping()
            return True
        except:
            return False
    
    def close(self):
        """关闭Redis连接"""
        if self._connection_pool:
            self._connection_pool.disconnect()
            self._connection_pool = None
            self._redis_client = None


class CacheManager:
    """缓存管理器"""
    
    def __init__(self):
        self.redis_manager = RedisManager()
    
    def _get_cache_key(self, key_type, identifier, user_id=None, warehouse_id=None):
        """生成缓存键"""
        key_parts = [CacheConfig.CACHE_KEY_PREFIX, CacheConfig.CACHE_VERSION, key_type]
        
        if user_id:
            key_parts.append(f"user_{user_id}")
        if warehouse_id:
            key_parts.append(f"warehouse_{warehouse_id}")
        
        key_parts.append(str(identifier))
        
        return ":".join(key_parts)
    
    def _serialize_data(self, data):
        """序列化数据"""
        try:
            # 对于简单数据类型使用JSON
            if isinstance(data, (dict, list, str, int, float, bool)) or data is None:
                return json.dumps(data, ensure_ascii=False, default=str)
            else:
                # 对于复杂对象使用pickle
                return pickle.dumps(data)
        except Exception as e:
            current_app.logger.error(f"数据序列化失败: {str(e)}")
            return None
    
    def _deserialize_data(self, data, use_pickle=False):
        """反序列化数据"""
        try:
            if use_pickle:
                return pickle.loads(data)
            else:
                return json.loads(data)
        except Exception as e:
            current_app.logger.error(f"数据反序列化失败: {str(e)}")
            return None
    
    def set(self, key_type, identifier, data, timeout=None, user_id=None, warehouse_id=None):
        """设置缓存"""
        try:
            redis_client = self.redis_manager.get_client()
            if not redis_client:
                return False
            
            cache_key = self._get_cache_key(key_type, identifier, user_id, warehouse_id)
            
            # 获取超时时间
            if timeout is None:
                timeout = CacheConfig.CACHE_TIMEOUT.get(key_type, 3600)
            
            # 序列化数据
            serialized_data = self._serialize_data(data)
            if serialized_data is None:
                return False
            
            # 设置缓存
            result = redis_client.setex(cache_key, timeout, serialized_data)
            
            if result:
                try:
                    from flask import current_app
                    current_app.logger.debug(f"缓存设置成功: {cache_key}")
                except RuntimeError:
                    pass

            return result

        except Exception as e:
            try:
                from flask import current_app
                current_app.logger.error(f"设置缓存失败: {str(e)}")
            except RuntimeError:
                print(f"设置缓存失败: {str(e)}")
            return False
    
    def get(self, key_type, identifier, user_id=None, warehouse_id=None):
        """获取缓存"""
        try:
            redis_client = self.redis_manager.get_client()
            if not redis_client:
                return None
            
            cache_key = self._get_cache_key(key_type, identifier, user_id, warehouse_id)
            
            # 获取缓存数据
            cached_data = redis_client.get(cache_key)
            if cached_data is None:
                return None
            
            # 反序列化数据
            try:
                # 首先尝试JSON反序列化
                data = self._deserialize_data(cached_data, use_pickle=False)
            except:
                # 如果JSON失败，尝试pickle反序列化
                data = self._deserialize_data(cached_data, use_pickle=True)
            
            if data is not None:
                current_app.logger.debug(f"缓存命中: {cache_key}")
            
            return data
            
        except Exception as e:
            current_app.logger.error(f"获取缓存失败: {str(e)}")
            return None
    
    def delete(self, key_type, identifier, user_id=None, warehouse_id=None):
        """删除缓存"""
        try:
            redis_client = self.redis_manager.get_client()
            if not redis_client:
                return False
            
            cache_key = self._get_cache_key(key_type, identifier, user_id, warehouse_id)
            
            result = redis_client.delete(cache_key)
            
            if result:
                current_app.logger.debug(f"缓存删除成功: {cache_key}")
            
            return bool(result)
            
        except Exception as e:
            current_app.logger.error(f"删除缓存失败: {str(e)}")
            return False
    
    def delete_pattern(self, pattern):
        """批量删除匹配模式的缓存"""
        try:
            redis_client = self.redis_manager.get_client()
            if not redis_client:
                return 0
            
            # 构建完整的模式
            full_pattern = f"{CacheConfig.CACHE_KEY_PREFIX}:{CacheConfig.CACHE_VERSION}:{pattern}"
            
            # 获取匹配的键
            keys = redis_client.keys(full_pattern)
            
            if keys:
                # 批量删除
                deleted_count = redis_client.delete(*keys)
                current_app.logger.info(f"批量删除缓存: {deleted_count} 个键")
                return deleted_count
            
            return 0
            
        except Exception as e:
            current_app.logger.error(f"批量删除缓存失败: {str(e)}")
            return 0
    
    def clear_user_cache(self, user_id):
        """清除用户相关缓存"""
        pattern = f"*user_{user_id}*"
        return self.delete_pattern(pattern)
    
    def clear_warehouse_cache(self, warehouse_id):
        """清除仓库相关缓存"""
        pattern = f"*warehouse_{warehouse_id}*"
        return self.delete_pattern(pattern)
    
    def clear_inventory_cache(self):
        """清除库存相关缓存"""
        patterns = ['inventory_list*', 'aggregated_data*', 'statistics*']
        total_deleted = 0
        for pattern in patterns:
            total_deleted += self.delete_pattern(pattern)
        return total_deleted
    
    def get_cache_stats(self):
        """获取缓存统计信息"""
        try:
            redis_client = self.redis_manager.get_client()
            if not redis_client:
                return {}
            
            info = redis_client.info()
            
            # 获取我们的缓存键数量
            our_keys = redis_client.keys(f"{CacheConfig.CACHE_KEY_PREFIX}:*")
            
            return {
                'redis_version': info.get('redis_version'),
                'used_memory': info.get('used_memory_human'),
                'connected_clients': info.get('connected_clients'),
                'total_commands_processed': info.get('total_commands_processed'),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'our_cache_keys': len(our_keys),
                'hit_rate': self._calculate_hit_rate(
                    info.get('keyspace_hits', 0),
                    info.get('keyspace_misses', 0)
                )
            }
            
        except Exception as e:
            current_app.logger.error(f"获取缓存统计失败: {str(e)}")
            return {}
    
    def _calculate_hit_rate(self, hits, misses):
        """计算缓存命中率"""
        total = hits + misses
        if total == 0:
            return 0.0
        return round((hits / total) * 100, 2)


# 全局缓存管理器实例 - 延迟初始化
cache_manager = None

def get_cache_manager():
    """获取缓存管理器实例"""
    global cache_manager
    if cache_manager is None:
        cache_manager = CacheManager()
    return cache_manager


def cached(key_type, timeout=None, key_func=None):
    """缓存装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存标识符
            if key_func:
                identifier = key_func(*args, **kwargs)
            else:
                # 使用函数名和参数生成标识符
                args_str = str(args) + str(sorted(kwargs.items()))
                identifier = hashlib.md5(args_str.encode()).hexdigest()
            
            # 尝试从缓存获取
            cached_result = cache_manager.get(key_type, identifier)
            if cached_result is not None:
                return cached_result
            
            # 执行函数
            result = func(*args, **kwargs)
            
            # 设置缓存
            cache_manager.set(key_type, identifier, result, timeout)
            
            return result
        
        return wrapper
    return decorator
