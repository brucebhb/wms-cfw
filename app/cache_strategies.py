"""
Redis缓存策略和数据结构设计 - 简化版本
"""

from app.cache_config import get_cache_manager
from flask import current_app, request, g
from flask_login import current_user
import time
import hashlib
from datetime import datetime, timedelta


class InventoryCacheStrategy:
    """库存数据缓存策略"""
    
    @staticmethod
    def get_cache_key(warehouse_id=None, search_params=None, page=1, per_page=50):
        """生成库存查询缓存键"""
        key_parts = ['inventory_query']
        
        if warehouse_id:
            key_parts.append(f'warehouse_{warehouse_id}')
        
        if search_params:
            # 将搜索参数排序后加入键
            sorted_params = sorted(search_params.items())
            params_str = '_'.join([f'{k}_{v}' for k, v in sorted_params if v])
            if params_str:
                key_parts.append(params_str)
        
        key_parts.extend([f'page_{page}', f'per_{per_page}'])
        
        return '_'.join(key_parts)
    
    @staticmethod
    def cache_inventory_list(warehouse_id, search_params, page, per_page, data):
        """缓存库存列表数据"""
        cache_key = InventoryCacheStrategy.get_cache_key(warehouse_id, search_params, page, per_page)
        
        # 缓存数据结构
        cache_data = {
            'data': data,
            'timestamp': time.time(),
            'warehouse_id': warehouse_id,
            'search_params': search_params,
            'page': page,
            'per_page': per_page
        }
        
        return get_cache_manager().set('inventory_list', cache_key, cache_data, timeout=3600)
    
    @staticmethod
    def get_cached_inventory_list(warehouse_id, search_params, page, per_page):
        """获取缓存的库存列表数据"""
        cache_key = InventoryCacheStrategy.get_cache_key(warehouse_id, search_params, page, per_page)
        
        cached_data = get_cache_manager().get('inventory_list', cache_key)
        
        if cached_data and isinstance(cached_data, dict):
            # 检查缓存是否过期（5分钟）
            if time.time() - cached_data.get('timestamp', 0) < 3600:
                return cached_data.get('data')
        
        return None
    
    @staticmethod
    def invalidate_inventory_cache(warehouse_id=None):
        """使库存缓存失效"""
        if warehouse_id:
            # 清除特定仓库的缓存
            pattern = f'inventory_list*warehouse_{warehouse_id}*'
        else:
            # 清除所有库存缓存
            pattern = 'inventory_list*'
        
        return get_cache_manager().delete_pattern(pattern)


class UserCacheStrategy:
    """用户数据缓存策略"""
    
    @staticmethod
    def cache_user_info(user_id, user_data):
        """缓存用户信息"""
        return get_cache_manager().set('user_info', user_id, user_data, timeout=1800)
    
    @staticmethod
    def get_cached_user_info(user_id):
        """获取缓存的用户信息"""
        return get_cache_manager().get('user_info', user_id)
    
    @staticmethod
    def cache_user_permissions(user_id, permissions):
        """缓存用户权限"""
        return get_cache_manager().set('permissions', user_id, permissions, timeout=1800)
    
    @staticmethod
    def get_cached_user_permissions(user_id):
        """获取缓存的用户权限"""
        return get_cache_manager().get('permissions', user_id)
    
    @staticmethod
    def invalidate_user_cache(user_id):
        """使用户缓存失效"""
        get_cache_manager().delete('user_info', user_id)
        get_cache_manager().delete('permissions', user_id)
        return get_cache_manager().clear_user_cache(user_id)


class WarehouseCacheStrategy:
    """仓库数据缓存策略"""
    
    @staticmethod
    def cache_warehouse_list(warehouses):
        """缓存仓库列表"""
        return get_cache_manager().set('warehouse_info', 'all_warehouses', warehouses, timeout=3600)
    
    @staticmethod
    def get_cached_warehouse_list():
        """获取缓存的仓库列表"""
        return get_cache_manager().get('warehouse_info', 'all_warehouses')
    
    @staticmethod
    def cache_warehouse_info(warehouse_id, warehouse_data):
        """缓存单个仓库信息"""
        return get_cache_manager().set('warehouse_info', warehouse_id, warehouse_data, timeout=3600)
    
    @staticmethod
    def get_cached_warehouse_info(warehouse_id):
        """获取缓存的仓库信息"""
        return get_cache_manager().get('warehouse_info', warehouse_id)
    
    @staticmethod
    def invalidate_warehouse_cache(warehouse_id=None):
        """使仓库缓存失效"""
        if warehouse_id:
            get_cache_manager().delete('warehouse_info', warehouse_id)
            return get_cache_manager().clear_warehouse_cache(warehouse_id)
        else:
            return get_cache_manager().delete_pattern('warehouse_info*')


class CustomerCacheStrategy:
    """客户数据缓存策略"""
    
    @staticmethod
    def cache_customer_list(customers, query_param=''):
        """缓存客户列表"""
        cache_key = f'customers_{hashlib.md5(query_param.encode()).hexdigest()}'
        
        cache_data = {
            'customers': customers,
            'timestamp': time.time(),
            'query_param': query_param
        }
        
        return get_cache_manager().set('customer_list', cache_key, cache_data, timeout=600)
    
    @staticmethod
    def get_cached_customer_list(query_param=''):
        """获取缓存的客户列表"""
        cache_key = f'customers_{hashlib.md5(query_param.encode()).hexdigest()}'
        
        cached_data = get_cache_manager().get('customer_list', cache_key)
        
        if cached_data and isinstance(cached_data, dict):
            # 检查缓存是否过期（10分钟）
            if time.time() - cached_data.get('timestamp', 0) < 600:
                return cached_data.get('customers')
        
        return None
    
    @staticmethod
    def invalidate_customer_cache():
        """使客户缓存失效"""
        return get_cache_manager().delete_pattern('customer_list*')


class CacheInvalidationManager:
    """缓存失效管理器"""
    
    @staticmethod
    def on_inventory_change(warehouse_id=None):
        """库存变更时的缓存失效"""
        # 清除库存相关缓存
        InventoryCacheStrategy.invalidate_inventory_cache(warehouse_id)
        
        try:
            from flask import current_app
            current_app.logger.info(f"库存变更缓存失效: warehouse_id={warehouse_id}")
        except RuntimeError:
            print(f"库存变更缓存失效: warehouse_id={warehouse_id}")
    
    @staticmethod
    def on_user_change(user_id):
        """用户变更时的缓存失效"""
        UserCacheStrategy.invalidate_user_cache(user_id)
        
        try:
            from flask import current_app
            current_app.logger.info(f"用户变更缓存失效: user_id={user_id}")
        except RuntimeError:
            print(f"用户变更缓存失效: user_id={user_id}")
    
    @staticmethod
    def on_warehouse_change(warehouse_id=None):
        """仓库变更时的缓存失效"""
        WarehouseCacheStrategy.invalidate_warehouse_cache(warehouse_id)
        
        # 如果是仓库信息变更，也需要清除相关的库存缓存
        if warehouse_id:
            InventoryCacheStrategy.invalidate_inventory_cache(warehouse_id)
        
        try:
            from flask import current_app
            current_app.logger.info(f"仓库变更缓存失效: warehouse_id={warehouse_id}")
        except RuntimeError:
            print(f"仓库变更缓存失效: warehouse_id={warehouse_id}")
    
    @staticmethod
    def on_customer_change():
        """客户变更时的缓存失效"""
        CustomerCacheStrategy.invalidate_customer_cache()
        
        try:
            from flask import current_app
            current_app.logger.info("客户变更缓存失效")
        except RuntimeError:
            print("客户变更缓存失效")
    
    @staticmethod
    def clear_all_cache():
        """清除所有缓存"""
        patterns = [
            'inventory_list*',
            'user_info*',
            'warehouse_info*',
            'customer_list*',
            'permissions*'
        ]
        
        total_deleted = 0
        for pattern in patterns:
            deleted = get_cache_manager().delete_pattern(pattern)
            total_deleted += deleted
        
        try:
            from flask import current_app
            current_app.logger.info(f"清除所有缓存: {total_deleted} 个键")
        except RuntimeError:
            print(f"清除所有缓存: {total_deleted} 个键")
        
        return total_deleted


class StatisticsCacheStrategy:
    """统计数据缓存策略"""

    @staticmethod
    def cache_dashboard_stats(stats_data):
        """缓存仪表板统计数据"""
        return get_cache_manager().set('statistics', 'dashboard', stats_data, timeout=900)

    @staticmethod
    def get_cached_dashboard_stats():
        """获取缓存的仪表板统计数据"""
        return get_cache_manager().get('statistics', 'dashboard')

    @staticmethod
    def cache_warehouse_stats(warehouse_id, stats_data):
        """缓存仓库统计数据"""
        return get_cache_manager().set('statistics', f'warehouse_{warehouse_id}', stats_data, timeout=900)

    @staticmethod
    def get_cached_warehouse_stats(warehouse_id):
        """获取缓存的仓库统计数据"""
        return get_cache_manager().get('statistics', f'warehouse_{warehouse_id}')

    @staticmethod
    def invalidate_statistics_cache():
        """使统计缓存失效"""
        return get_cache_manager().delete_pattern('statistics*')


class AggregatedDataCacheStrategy:
    """聚合数据缓存策略"""

    @staticmethod
    def cache_aggregated_inventory(aggregated_data):
        """缓存聚合库存数据"""
        cache_data = {
            'data': aggregated_data,
            'timestamp': time.time()
        }

        return get_cache_manager().set('aggregated_data', 'inventory', cache_data, timeout=600)

    @staticmethod
    def get_cached_aggregated_inventory():
        """获取缓存的聚合库存数据"""
        cached_data = get_cache_manager().get('aggregated_data', 'inventory')

        if cached_data and isinstance(cached_data, dict):
            # 检查缓存是否过期（10分钟）
            if time.time() - cached_data.get('timestamp', 0) < 600:
                return cached_data.get('data')

        return None

    @staticmethod
    def invalidate_aggregated_cache():
        """使聚合数据缓存失效"""
        return get_cache_manager().delete_pattern('aggregated_data*')


# 缓存失效管理器实例
cache_invalidation = CacheInvalidationManager()
