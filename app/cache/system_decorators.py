#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全系统缓存装饰器
整合现有实现，提供统一的缓存装饰器
"""

import functools
import hashlib
import json
from typing import Any, Callable, Optional, Union, List
from flask_login import current_user
from flask import current_app

from .dual_cache_manager import get_dual_cache_manager
from .system_cache_config import SystemCacheConfig

# 整合现有缓存策略
try:
    from app.cache_strategies import (
        InventoryCacheStrategy, UserCacheStrategy, WarehouseCacheStrategy,
        CustomerCacheStrategy, StatisticsCacheStrategy
    )
    LEGACY_STRATEGIES_AVAILABLE = True
except ImportError:
    LEGACY_STRATEGIES_AVAILABLE = False


def system_cached(cache_type: str = 'default',
                  key_prefix: Optional[str] = None,
                  l1_ttl: Optional[int] = None,
                  l2_ttl: Optional[int] = None,
                  key_generator: Optional[Callable] = None,
                  condition: Optional[Callable] = None,
                  use_legacy: bool = False):
    """
    全系统统一缓存装饰器
    
    Args:
        cache_type: 缓存类型，对应SystemCacheConfig中的配置
        key_prefix: 缓存键前缀，默认使用函数名
        l1_ttl: L1缓存TTL，覆盖配置
        l2_ttl: L2缓存TTL，覆盖配置
        key_generator: 自定义键生成器
        condition: 缓存条件函数
        use_legacy: 是否使用现有的缓存策略
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 获取缓存配置
            cache_config = SystemCacheConfig.get_cache_config(cache_type)
            
            # 生成缓存键
            if key_generator:
                cache_key = key_generator(*args, **kwargs)
            else:
                prefix = key_prefix or f"func:{func.__name__}"
                cache_key = generate_system_cache_key(prefix, cache_type, *args, **kwargs)
            
            # 检查缓存条件
            if condition and not condition(*args, **kwargs):
                return func(*args, **kwargs)
            
            # 如果启用了现有策略且可用，优先使用
            if use_legacy and LEGACY_STRATEGIES_AVAILABLE:
                return _use_legacy_cache(func, cache_type, cache_key, *args, **kwargs)
            
            # 使用双层缓存管理器
            cache_manager = get_dual_cache_manager()
            
            # 定义fallback函数
            def fallback():
                return func(*args, **kwargs)
            
            # 获取TTL配置
            final_l1_ttl = l1_ttl or cache_config.get('l1_ttl', 300)
            final_l2_ttl = l2_ttl or cache_config.get('l2_ttl', 1800)
            
            # 获取缓存数据
            result = cache_manager.get(
                key=cache_key,
                fallback=fallback,
                cache_type=cache_type
            )
            
            return result
        
        # 添加缓存控制方法
        wrapper.cache_key = lambda *args, **kwargs: generate_system_cache_key(
            key_prefix or f"func:{func.__name__}", cache_type, *args, **kwargs
        )
        wrapper.invalidate = lambda *args, **kwargs: get_dual_cache_manager().delete(
            wrapper.cache_key(*args, **kwargs)
        )
        wrapper.cache_type = cache_type
        
        return wrapper
    return decorator


def _use_legacy_cache(func, cache_type, cache_key, *args, **kwargs):
    """使用现有的缓存策略"""
    try:
        # 根据缓存类型选择对应的策略
        if cache_type.startswith('inventory'):
            return _use_inventory_legacy_cache(func, cache_key, *args, **kwargs)
        elif cache_type.startswith('user'):
            return _use_user_legacy_cache(func, cache_key, *args, **kwargs)
        elif cache_type.startswith('warehouse'):
            return _use_warehouse_legacy_cache(func, cache_key, *args, **kwargs)
        elif cache_type.startswith('customer'):
            return _use_customer_legacy_cache(func, cache_key, *args, **kwargs)
        elif cache_type.startswith('statistics') or cache_type.endswith('_stats'):
            return _use_statistics_legacy_cache(func, cache_key, *args, **kwargs)
        else:
            # 降级到双层缓存
            return func(*args, **kwargs)
    except Exception as e:
        if current_app:
            current_app.logger.warning(f"现有缓存策略失败，降级到双层缓存: {e}")
        return func(*args, **kwargs)


def _use_inventory_legacy_cache(func, cache_key, *args, **kwargs):
    """使用现有的库存缓存策略"""
    # 尝试从现有缓存获取
    if hasattr(args[0], '__self__') and len(args) >= 4:
        # 假设是库存列表查询: self, warehouse_id, search_params, page, per_page
        warehouse_id = args[1] if len(args) > 1 else kwargs.get('warehouse_id')
        search_params = args[2] if len(args) > 2 else kwargs.get('search_params', {})
        page = args[3] if len(args) > 3 else kwargs.get('page', 1)
        per_page = args[4] if len(args) > 4 else kwargs.get('per_page', 50)
        
        cached_result = InventoryCacheStrategy.get_cached_inventory_list(
            warehouse_id, search_params, page, per_page
        )
        
        if cached_result is not None:
            return cached_result
    
    # 缓存未命中，执行函数并缓存结果
    result = func(*args, **kwargs)
    
    # 缓存结果（如果适用）
    if hasattr(args[0], '__self__') and len(args) >= 4:
        warehouse_id = args[1] if len(args) > 1 else kwargs.get('warehouse_id')
        search_params = args[2] if len(args) > 2 else kwargs.get('search_params', {})
        page = args[3] if len(args) > 3 else kwargs.get('page', 1)
        per_page = args[4] if len(args) > 4 else kwargs.get('per_page', 50)
        
        InventoryCacheStrategy.cache_inventory_list(
            warehouse_id, search_params, page, per_page, result
        )
    
    return result


def _use_user_legacy_cache(func, cache_key, *args, **kwargs):
    """使用现有的用户缓存策略"""
    # 尝试获取用户ID
    user_id = None
    if len(args) > 1:
        user_id = args[1]
    elif 'user_id' in kwargs:
        user_id = kwargs['user_id']
    elif current_user and current_user.is_authenticated:
        user_id = current_user.id
    
    if user_id:
        # 尝试从缓存获取
        if 'permission' in cache_key:
            cached_result = UserCacheStrategy.get_cached_user_permissions(user_id)
        else:
            cached_result = UserCacheStrategy.get_cached_user_info(user_id)
        
        if cached_result is not None:
            return cached_result
    
    # 执行函数
    result = func(*args, **kwargs)
    
    # 缓存结果
    if user_id and result:
        if 'permission' in cache_key:
            UserCacheStrategy.cache_user_permissions(user_id, result)
        else:
            UserCacheStrategy.cache_user_info(user_id, result)
    
    return result


def _use_warehouse_legacy_cache(func, cache_key, *args, **kwargs):
    """使用现有的仓库缓存策略"""
    # 执行函数（现有策略可能没有仓库缓存，直接执行）
    return func(*args, **kwargs)


def _use_customer_legacy_cache(func, cache_key, *args, **kwargs):
    """使用现有的客户缓存策略"""
    # 执行函数（现有策略可能没有客户缓存，直接执行）
    return func(*args, **kwargs)


def _use_statistics_legacy_cache(func, cache_key, *args, **kwargs):
    """使用现有的统计缓存策略"""
    # 执行函数（现有策略可能没有统计缓存，直接执行）
    return func(*args, **kwargs)


def generate_system_cache_key(prefix: str, cache_type: str, *args, **kwargs) -> str:
    """生成系统缓存键"""
    key_parts = [prefix, cache_type]
    
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
        # 过滤掉self参数
        filtered_args = args[1:] if args and hasattr(args[0], '__dict__') else args
        if filtered_args:
            args_str = ':'.join(str(arg) for arg in filtered_args)
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
        cache_key = f"{prefix}:{cache_type}:hash:{hash_obj.hexdigest()}"
    
    return cache_key


# ==================== 系统级缓存失效装饰器 ====================

def system_cache_invalidate(event_types: Union[str, List[str]], 
                           patterns: Optional[Union[str, List[str]]] = None,
                           level: str = 'both'):
    """
    系统级缓存失效装饰器
    
    Args:
        event_types: 事件类型或类型列表
        patterns: 额外的缓存模式
        level: 清理级别 ('l1', 'l2', 'both')
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 执行原函数
            result = func(*args, **kwargs)
            
            # 获取缓存管理器
            cache_manager = get_dual_cache_manager()
            
            # 处理事件类型
            if isinstance(event_types, str):
                event_list = [event_types]
            else:
                event_list = event_types
            
            # 失效相关缓存
            for event_type in event_list:
                try:
                    # 获取需要失效的缓存类型
                    cache_types = SystemCacheConfig.get_invalidation_targets(event_type)
                    
                    for cache_type in cache_types:
                        pattern = f"{cache_type}:*"
                        cache_manager.clear_cache(level=level, pattern=pattern)
                        
                        if current_app:
                            current_app.logger.debug(f"失效缓存: {pattern} (事件: {event_type})")
                
                except Exception as e:
                    if current_app:
                        current_app.logger.error(f"缓存失效失败 {event_type}: {e}")
            
            # 处理额外的模式
            if patterns:
                pattern_list = [patterns] if isinstance(patterns, str) else patterns
                for pattern in pattern_list:
                    try:
                        cache_manager.clear_cache(level=level, pattern=pattern)
                    except Exception as e:
                        if current_app:
                            current_app.logger.error(f"缓存清理失败 {pattern}: {e}")
            
            return result
        return wrapper
    return decorator


# ==================== 预定义的系统缓存装饰器 ====================

# 库存模块
def inventory_cached(key_prefix: str = None, use_legacy: bool = True):
    """库存数据缓存装饰器"""
    return system_cached(
        cache_type='inventory_list',
        key_prefix=key_prefix,
        use_legacy=use_legacy
    )

def inventory_stats_cached(key_prefix: str = None):
    """库存统计缓存装饰器"""
    return system_cached(
        cache_type='inventory_stats',
        key_prefix=key_prefix
    )

# 用户模块
def user_cached(key_prefix: str = None, use_legacy: bool = True):
    """用户数据缓存装饰器"""
    return system_cached(
        cache_type='user_info',
        key_prefix=key_prefix,
        use_legacy=use_legacy
    )

def user_permissions_cached(key_prefix: str = None, use_legacy: bool = True):
    """用户权限缓存装饰器"""
    return system_cached(
        cache_type='user_permissions',
        key_prefix=key_prefix,
        use_legacy=use_legacy
    )

# 仓库模块
def warehouse_cached(key_prefix: str = None):
    """仓库数据缓存装饰器"""
    return system_cached(
        cache_type='warehouse_info',
        key_prefix=key_prefix
    )

# 统计模块
def statistics_cached(key_prefix: str = None):
    """统计数据缓存装饰器"""
    return system_cached(
        cache_type='statistics',
        key_prefix=key_prefix
    )

# 搜索模块
def search_cached(key_prefix: str = None):
    """搜索结果缓存装饰器"""
    return system_cached(
        cache_type='search_results',
        key_prefix=key_prefix
    )

# 系统级失效装饰器
def invalidate_inventory():
    """失效库存相关缓存"""
    return system_cache_invalidate(['inventory_change'])

def invalidate_user():
    """失效用户相关缓存"""
    return system_cache_invalidate(['user_change'])

def invalidate_warehouse():
    """失效仓库相关缓存"""
    return system_cache_invalidate(['warehouse_change'])
