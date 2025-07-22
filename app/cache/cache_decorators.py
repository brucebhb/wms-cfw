#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
缓存装饰器
提供方便的缓存装饰器功能
"""

import functools
import hashlib
import json
from typing import Any, Callable, Optional, Union, List
from flask_login import current_user

from .dual_cache_manager import get_dual_cache_manager


def generate_cache_key(prefix: str, *args, **kwargs) -> str:
    """生成缓存键"""
    # 构建键的组成部分
    key_parts = [prefix]
    
    # 添加用户ID（如果已登录）
    try:
        if current_user and current_user.is_authenticated:
            key_parts.append(f"user:{current_user.id}")
            if hasattr(current_user, 'warehouse_id') and current_user.warehouse_id:
                key_parts.append(f"warehouse:{current_user.warehouse_id}")
    except:
        pass
    
    # 添加参数
    if args:
        args_str = ':'.join(str(arg) for arg in args)
        key_parts.append(f"args:{args_str}")
    
    if kwargs:
        # 排序kwargs确保一致性
        sorted_kwargs = sorted(kwargs.items())
        kwargs_str = ':'.join(f"{k}={v}" for k, v in sorted_kwargs)
        key_parts.append(f"kwargs:{kwargs_str}")
    
    # 生成最终键
    cache_key = ':'.join(key_parts)
    
    # 如果键太长，使用哈希
    if len(cache_key) > 200:
        hash_obj = hashlib.md5(cache_key.encode('utf-8'))
        cache_key = f"{prefix}:hash:{hash_obj.hexdigest()}"
    
    return cache_key


def cached(cache_type: str = 'default',
           key_prefix: Optional[str] = None,
           l1_ttl: Optional[int] = None,
           l2_ttl: Optional[int] = None,
           key_generator: Optional[Callable] = None,
           condition: Optional[Callable] = None):
    """
    缓存装饰器
    
    Args:
        cache_type: 缓存类型，用于确定TTL策略
        key_prefix: 缓存键前缀，默认使用函数名
        l1_ttl: L1缓存TTL
        l2_ttl: L2缓存TTL
        key_generator: 自定义键生成器
        condition: 缓存条件函数，返回True时才缓存
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            cache_manager = get_dual_cache_manager()
            
            # 生成缓存键
            if key_generator:
                cache_key = key_generator(*args, **kwargs)
            else:
                prefix = key_prefix or f"func:{func.__name__}"
                cache_key = generate_cache_key(prefix, *args, **kwargs)
            
            # 检查缓存条件
            if condition and not condition(*args, **kwargs):
                return func(*args, **kwargs)
            
            # 定义fallback函数
            def fallback():
                return func(*args, **kwargs)
            
            # 获取缓存数据
            result = cache_manager.get(
                key=cache_key,
                fallback=fallback,
                cache_type=cache_type
            )
            
            return result
        
        # 添加缓存控制方法
        wrapper.cache_key = lambda *args, **kwargs: generate_cache_key(
            key_prefix or f"func:{func.__name__}", *args, **kwargs
        )
        wrapper.invalidate = lambda *args, **kwargs: get_dual_cache_manager().delete(
            wrapper.cache_key(*args, **kwargs)
        )
        
        return wrapper
    return decorator


def cache_invalidate(patterns: Union[str, List[str]], level: str = 'both'):
    """
    缓存失效装饰器
    在函数执行后清理相关缓存
    
    Args:
        patterns: 要清理的缓存模式
        level: 清理级别 ('l1', 'l2', 'both')
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 执行原函数
            result = func(*args, **kwargs)
            
            # 清理缓存
            cache_manager = get_dual_cache_manager()
            
            if isinstance(patterns, str):
                pattern_list = [patterns]
            else:
                pattern_list = patterns
            
            for pattern in pattern_list:
                try:
                    cache_manager.clear_cache(level=level, pattern=pattern)
                except Exception as e:
                    # 记录错误但不影响主流程
                    if hasattr(func, '__module__'):
                        print(f"缓存清理失败 {pattern}: {e}")
            
            return result
        return wrapper
    return decorator


# 预定义的缓存装饰器

def dashboard_cached(key_prefix: str = None, ttl: int = 300):
    """仪表板数据缓存装饰器"""
    return cached(
        cache_type='dashboard_summary',
        key_prefix=key_prefix,
        l1_ttl=ttl,
        l2_ttl=ttl * 6
    )


def realtime_cached(key_prefix: str = None):
    """实时数据缓存装饰器"""
    return cached(
        cache_type='realtime_metrics',
        key_prefix=key_prefix
    )


def inventory_cached(key_prefix: str = None):
    """库存数据缓存装饰器"""
    return cached(
        cache_type='inventory_overview',
        key_prefix=key_prefix
    )


def stats_cached(key_prefix: str = None, ttl: int = 600):
    """统计数据缓存装饰器"""
    return cached(
        cache_type='today_stats',
        key_prefix=key_prefix,
        l1_ttl=ttl,
        l2_ttl=ttl * 5
    )


def historical_cached(key_prefix: str = None):
    """历史数据缓存装饰器"""
    return cached(
        cache_type='historical_stats',
        key_prefix=key_prefix
    )


# 缓存失效装饰器预设

def invalidate_dashboard():
    """失效仪表板缓存"""
    return cache_invalidate([
        'dashboard_summary:*',
        'today_stats:*',
        'realtime_metrics:*'
    ])


def invalidate_inventory():
    """失效库存缓存"""
    return cache_invalidate([
        'inventory_overview:*',
        'dashboard_summary:*'
    ])


def invalidate_stats():
    """失效统计缓存"""
    return cache_invalidate([
        'today_stats:*',
        'dashboard_summary:*',
        'warehouse_summary:*'
    ])


# 条件缓存函数

def cache_if_authenticated(*args, **kwargs) -> bool:
    """仅在用户已认证时缓存"""
    try:
        return current_user and current_user.is_authenticated
    except:
        return False


def cache_if_not_admin(*args, **kwargs) -> bool:
    """非管理员用户才缓存"""
    try:
        return current_user and current_user.is_authenticated and not current_user.is_super_admin()
    except:
        return False


def cache_if_has_warehouse(*args, **kwargs) -> bool:
    """有仓库权限的用户才缓存"""
    try:
        return (current_user and 
                current_user.is_authenticated and 
                hasattr(current_user, 'warehouse_id') and 
                current_user.warehouse_id)
    except:
        return False


# 使用示例装饰器

class CacheExamples:
    """缓存使用示例"""
    
    @dashboard_cached('user_dashboard')
    def get_user_dashboard(self, user_id: int):
        """获取用户仪表板数据"""
        # 实际的数据查询逻辑
        pass
    
    @realtime_cached('current_stats')
    def get_current_stats(self, warehouse_id: int):
        """获取当前统计数据"""
        # 实际的统计查询逻辑
        pass
    
    @inventory_cached('warehouse_inventory')
    @cache_invalidate('inventory_overview:*')
    def update_inventory(self, warehouse_id: int, data: dict):
        """更新库存数据"""
        # 更新逻辑
        # 执行后会自动清理相关缓存
        pass
    
    @cached(
        cache_type='custom',
        condition=cache_if_authenticated,
        key_generator=lambda self, user_id: f"custom:user:{user_id}"
    )
    def get_custom_data(self, user_id: int):
        """自定义缓存示例"""
        pass
