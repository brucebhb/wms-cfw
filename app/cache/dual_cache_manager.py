#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
双层缓存管理器
Redis + 内存缓存双层架构的核心管理器
"""

import time
import threading
from typing import Any, Optional, Dict, List, Callable
from flask import current_app

from .memory_cache import get_memory_cache, MemoryCache
from .redis_cache import get_redis_cache, RedisCache

# 整合现有Redis实现
try:
    from app.cache_config import get_cache_manager as get_legacy_cache_manager
    LEGACY_CACHE_AVAILABLE = True
except ImportError:
    LEGACY_CACHE_AVAILABLE = False


class CacheLevel:
    """缓存级别枚举"""
    L1_ONLY = 'l1'
    L2_ONLY = 'l2'
    BOTH = 'both'


class DualCacheManager:
    """双层缓存管理器"""
    
    def __init__(self):
        self.l1_cache: MemoryCache = get_memory_cache()
        self.l2_cache: RedisCache = get_redis_cache()
        self.lock = threading.RLock()
        
        # 全系统缓存策略配置
        self.cache_config = {
            # ==================== 仪表板模块 ====================
            'dashboard_summary': {'l1_ttl': 300, 'l2_ttl': 1800},      # 5分钟/30分钟
            'today_stats': {'l1_ttl': 60, 'l2_ttl': 300},              # 1分钟/5分钟
            'realtime_metrics': {'l1_ttl': 30, 'l2_ttl': 120},         # 30秒/2分钟

            # ==================== 库存管理模块 ====================
            'inventory_list': {'l1_ttl': 180, 'l2_ttl': 900},          # 3分钟/15分钟
            'inventory_overview': {'l1_ttl': 120, 'l2_ttl': 600},      # 2分钟/10分钟
            'inventory_search': {'l1_ttl': 300, 'l2_ttl': 1800},       # 5分钟/30分钟
            'inventory_stats': {'l1_ttl': 600, 'l2_ttl': 3600},        # 10分钟/1小时

            # ==================== 入库管理模块 ====================
            'inbound_list': {'l1_ttl': 120, 'l2_ttl': 600},            # 2分钟/10分钟
            'inbound_batch': {'l1_ttl': 60, 'l2_ttl': 300},            # 1分钟/5分钟
            'inbound_stats': {'l1_ttl': 300, 'l2_ttl': 1800},          # 5分钟/30分钟

            # ==================== 出库管理模块 ====================
            'outbound_list': {'l1_ttl': 120, 'l2_ttl': 600},           # 2分钟/10分钟
            'outbound_batch': {'l1_ttl': 60, 'l2_ttl': 300},           # 1分钟/5分钟
            'outbound_stats': {'l1_ttl': 300, 'l2_ttl': 1800},         # 5分钟/30分钟

            # ==================== 在途货物模块 ====================
            'transit_list': {'l1_ttl': 180, 'l2_ttl': 900},            # 3分钟/15分钟
            'transit_overview': {'l1_ttl': 180, 'l2_ttl': 900},        # 3分钟/15分钟
            'transit_batch': {'l1_ttl': 120, 'l2_ttl': 600},           # 2分钟/10分钟

            # ==================== 收货管理模块 ====================
            'receive_list': {'l1_ttl': 120, 'l2_ttl': 600},            # 2分钟/10分钟
            'receive_batch': {'l1_ttl': 60, 'l2_ttl': 300},            # 1分钟/5分钟

            # ==================== 用户权限模块 ====================
            'user_list': {'l1_ttl': 600, 'l2_ttl': 3600},              # 10分钟/1小时
            'user_permissions': {'l1_ttl': 1800, 'l2_ttl': 7200},      # 30分钟/2小时
            'warehouse_users': {'l1_ttl': 900, 'l2_ttl': 3600},        # 15分钟/1小时

            # ==================== 客户数据模块 ====================
            'customer_list': {'l1_ttl': 900, 'l2_ttl': 3600},          # 15分钟/1小时
            'customer_ranking': {'l1_ttl': 900, 'l2_ttl': 7200},       # 15分钟/2小时
            'customer_stats': {'l1_ttl': 1800, 'l2_ttl': 7200},        # 30分钟/2小时

            # ==================== 仓库数据模块 ====================
            'warehouse_list': {'l1_ttl': 1800, 'l2_ttl': 7200},        # 30分钟/2小时
            'warehouse_summary': {'l1_ttl': 600, 'l2_ttl': 3600},      # 10分钟/1小时
            'warehouse_stats': {'l1_ttl': 900, 'l2_ttl': 3600},        # 15分钟/1小时

            # ==================== 报表模块 ====================
            'daily_report': {'l1_ttl': 1800, 'l2_ttl': 7200},          # 30分钟/2小时
            'weekly_report': {'l1_ttl': 3600, 'l2_ttl': 21600},        # 1小时/6小时
            'monthly_report': {'l1_ttl': 3600, 'l2_ttl': 86400},       # 1小时/24小时
            'historical_stats': {'l1_ttl': 1800, 'l2_ttl': 21600},     # 30分钟/6小时

            # ==================== 打印模块 ====================
            'print_templates': {'l1_ttl': 3600, 'l2_ttl': 86400},      # 1小时/24小时
            'print_queue': {'l1_ttl': 60, 'l2_ttl': 300},              # 1分钟/5分钟

            # ==================== 系统配置模块 ====================
            'system_config': {'l1_ttl': 3600, 'l2_ttl': 86400},        # 1小时/24小时
            'menu_permissions': {'l1_ttl': 1800, 'l2_ttl': 7200},      # 30分钟/2小时

            # ==================== 默认配置 ====================
            'default': {'l1_ttl': 300, 'l2_ttl': 1800},                # 5分钟/30分钟
        }
        
        # 统计信息
        self.stats = {
            'total_requests': 0,
            'l1_hits': 0,
            'l2_hits': 0,
            'misses': 0,
            'errors': 0,
            'fallback_count': 0
        }
    
    def get(self, key: str, fallback: Optional[Callable] = None, 
            cache_type: str = 'default', max_age: int = 0) -> Optional[Any]:
        """
        获取缓存数据
        
        Args:
            key: 缓存键
            fallback: 缓存未命中时的回调函数
            cache_type: 缓存类型，用于确定TTL策略
            max_age: 最大可接受的数据年龄（秒），0表示不限制
        """
        with self.lock:
            self.stats['total_requests'] += 1
            start_time = time.time()
            
            try:
                # 1. 尝试L1内存缓存
                value = self.l1_cache.get(key)
                if value is not None:
                    self.stats['l1_hits'] += 1
                    self._log_cache_hit('L1', key, time.time() - start_time)
                    return value
                
                # 2. 尝试L2 Redis缓存
                value = self.l2_cache.get(key)
                if value is not None:
                    self.stats['l2_hits'] += 1
                    
                    # 回填L1缓存
                    l1_ttl = self._get_ttl(cache_type, 'l1_ttl', 300)
                    self.l1_cache.set(key, value, l1_ttl)
                    
                    self._log_cache_hit('L2', key, time.time() - start_time)
                    return value
                
                # 3. 缓存未命中，使用fallback
                if fallback:
                    self.stats['misses'] += 1
                    value = fallback()
                    
                    if value is not None:
                        # 同时写入两层缓存
                        self.set(key, value, cache_type=cache_type)
                    
                    self._log_cache_miss(key, time.time() - start_time)
                    return value
                
                self.stats['misses'] += 1
                return None
                
            except Exception as e:
                self.stats['errors'] += 1
                self._log_error('get', key, e)
                
                # 降级处理：如果有fallback，尝试执行
                if fallback:
                    try:
                        self.stats['fallback_count'] += 1
                        return fallback()
                    except Exception as fallback_error:
                        self._log_error('fallback', key, fallback_error)
                
                return None
    
    def set(self, key: str, value: Any, cache_type: str = 'default', 
            l1_ttl: Optional[int] = None, l2_ttl: Optional[int] = None) -> bool:
        """
        设置缓存数据
        
        Args:
            key: 缓存键
            value: 缓存值
            cache_type: 缓存类型
            l1_ttl: L1缓存TTL，None则使用默认配置
            l2_ttl: L2缓存TTL，None则使用默认配置
        """
        try:
            # 获取TTL配置
            if l1_ttl is None:
                l1_ttl = self._get_ttl(cache_type, 'l1_ttl', 300)
            if l2_ttl is None:
                l2_ttl = self._get_ttl(cache_type, 'l2_ttl', 1800)
            
            # 同时写入两层缓存
            l1_success = self.l1_cache.set(key, value, l1_ttl)
            l2_success = self.l2_cache.set(key, value, l2_ttl)
            
            # 至少一层成功即可
            return l1_success or l2_success
            
        except Exception as e:
            self._log_error('set', key, e)
            return False
    
    def delete(self, key: str) -> bool:
        """删除缓存项"""
        try:
            l1_result = self.l1_cache.delete(key)
            l2_result = self.l2_cache.delete(key)
            return l1_result or l2_result
        except Exception as e:
            self._log_error('delete', key, e)
            return False
    
    def exists(self, key: str) -> bool:
        """检查缓存项是否存在"""
        try:
            return self.l1_cache.exists(key) or self.l2_cache.exists(key)
        except Exception as e:
            self._log_error('exists', key, e)
            return False
    
    def clear_cache(self, level: str = 'both', pattern: str = '*') -> Dict[str, int]:
        """
        清理缓存
        
        Args:
            level: 清理级别 ('l1', 'l2', 'both')
            pattern: 匹配模式
        """
        result = {'l1_cleared': 0, 'l2_cleared': 0, 'total_cleared': 0}
        
        try:
            if level in ['l1', 'both']:
                result['l1_cleared'] = self.l1_cache.clear(pattern)
            
            if level in ['l2', 'both']:
                result['l2_cleared'] = self.l2_cache.clear(pattern)
            
            result['total_cleared'] = result['l1_cleared'] + result['l2_cleared']
            
        except Exception as e:
            self._log_error('clear', pattern, e)
        
        return result
    
    def get_cache_status(self) -> Dict[str, Any]:
        """获取缓存状态"""
        try:
            l1_stats = self.l1_cache.get_stats()
            l2_stats = self.l2_cache.get_stats()
            
            # 计算整体统计
            total_requests = self.stats['total_requests']
            overall_hit_rate = 0
            if total_requests > 0:
                total_hits = self.stats['l1_hits'] + self.stats['l2_hits']
                overall_hit_rate = (total_hits / total_requests) * 100
            
            return {
                'l1_cache': l1_stats,
                'l2_cache': l2_stats,
                'overall': {
                    'hit_rate': overall_hit_rate,
                    'total_requests': total_requests,
                    'l1_hit_rate': (self.stats['l1_hits'] / total_requests * 100) if total_requests > 0 else 0,
                    'l2_hit_rate': (self.stats['l2_hits'] / total_requests * 100) if total_requests > 0 else 0,
                    'miss_rate': (self.stats['misses'] / total_requests * 100) if total_requests > 0 else 0,
                    'error_rate': (self.stats['errors'] / total_requests * 100) if total_requests > 0 else 0,
                    'avg_response_time': 0,  # TODO: 实现响应时间统计
                    'fallback_count': self.stats['fallback_count']
                }
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'l1_cache': {'available': False},
                'l2_cache': {'available': False},
                'overall': {'hit_rate': 0}
            }
    
    def warm_cache(self, cache_data: Dict[str, Any], cache_type: str = 'default') -> Dict[str, Any]:
        """
        缓存预热
        
        Args:
            cache_data: 要预热的数据字典
            cache_type: 缓存类型
        """
        result = {
            'warmed_items': 0,
            'errors': [],
            'duration': 0
        }
        
        start_time = time.time()
        
        try:
            for key, value in cache_data.items():
                try:
                    if self.set(key, value, cache_type=cache_type):
                        result['warmed_items'] += 1
                except Exception as e:
                    result['errors'].append(f"{key}: {str(e)}")
            
            result['duration'] = time.time() - start_time
            result['success_rate'] = (result['warmed_items'] / len(cache_data) * 100) if cache_data else 100
            
        except Exception as e:
            result['errors'].append(f"预热过程错误: {str(e)}")
        
        return result
    
    def _get_ttl(self, cache_type: str, ttl_type: str, default: int) -> int:
        """获取TTL配置"""
        config = self.cache_config.get(cache_type, {})
        return config.get(ttl_type, default)
    
    def _log_cache_hit(self, level: str, key: str, duration: float):
        """记录缓存命中日志"""
        if current_app and current_app.config.get('DEBUG'):
            current_app.logger.debug(f"缓存命中 [{level}] {key} ({duration*1000:.2f}ms)")
    
    def _log_cache_miss(self, key: str, duration: float):
        """记录缓存未命中日志"""
        if current_app and current_app.config.get('DEBUG'):
            current_app.logger.debug(f"缓存未命中 {key} ({duration*1000:.2f}ms)")
    
    def _log_error(self, operation: str, key: str, error: Exception):
        """记录错误日志"""
        if current_app:
            current_app.logger.error(f"缓存{operation}错误 {key}: {str(error)}")


# 全局双层缓存管理器实例
_dual_cache_manager = None

def get_dual_cache_manager() -> DualCacheManager:
    """获取全局双层缓存管理器实例"""
    global _dual_cache_manager
    if _dual_cache_manager is None:
        _dual_cache_manager = DualCacheManager()
    return _dual_cache_manager
