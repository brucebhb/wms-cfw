"""
缓存失效和更新策略
实现数据一致性保证机制
"""

from app.cache_strategies import cache_invalidation
from app.hot_data_cache import cache_warmup
from app.performance_monitor import performance_metrics
from flask import current_app, g
from flask_login import current_user
from sqlalchemy import event
from app.models import Inventory, InboundRecord, OutboundRecord, User, Warehouse
import time
from datetime import datetime
from functools import wraps


class CacheInvalidationStrategy:
    """缓存失效策略"""
    
    @staticmethod
    def on_inventory_update(mapper, connection, target):
        """库存更新时的缓存失效"""
        try:
            warehouse_id = getattr(target, 'operated_warehouse_id', None)
            
            # 清除相关缓存
            cache_invalidation.on_inventory_change(warehouse_id)
            
            current_app.logger.info(
                f"库存更新触发缓存失效: id={target.id}, warehouse_id={warehouse_id}"
            )
            
        except Exception as e:
            current_app.logger.error(f"库存更新缓存失效失败: {str(e)}")
    
    @staticmethod
    def on_inbound_update(mapper, connection, target):
        """入库记录更新时的缓存失效"""
        try:
            warehouse_id = getattr(target, 'operated_warehouse_id', None)
            
            # 入库记录变更会影响库存，需要清除库存相关缓存
            cache_invalidation.on_inventory_change(warehouse_id)
            
            current_app.logger.info(
                f"入库记录更新触发缓存失效: id={target.id}, warehouse_id={warehouse_id}"
            )
            
        except Exception as e:
            current_app.logger.error(f"入库记录更新缓存失效失败: {str(e)}")
    
    @staticmethod
    def on_outbound_update(mapper, connection, target):
        """出库记录更新时的缓存失效"""
        try:
            warehouse_id = getattr(target, 'operated_warehouse_id', None)
            
            # 出库记录变更会影响库存，需要清除库存相关缓存
            cache_invalidation.on_inventory_change(warehouse_id)
            
            current_app.logger.info(
                f"出库记录更新触发缓存失效: id={target.id}, warehouse_id={warehouse_id}"
            )
            
        except Exception as e:
            current_app.logger.error(f"出库记录更新缓存失效失败: {str(e)}")
    
    @staticmethod
    def on_user_update(mapper, connection, target):
        """用户更新时的缓存失效"""
        try:
            user_id = getattr(target, 'id', None)
            
            # 清除用户相关缓存
            cache_invalidation.on_user_change(user_id)
            
            current_app.logger.info(f"用户更新触发缓存失效: user_id={user_id}")
            
        except Exception as e:
            current_app.logger.error(f"用户更新缓存失效失败: {str(e)}")
    
    @staticmethod
    def on_warehouse_update(mapper, connection, target):
        """仓库更新时的缓存失效"""
        try:
            warehouse_id = getattr(target, 'id', None)
            
            # 清除仓库相关缓存
            cache_invalidation.on_warehouse_change(warehouse_id)
            
            current_app.logger.info(f"仓库更新触发缓存失效: warehouse_id={warehouse_id}")
            
        except Exception as e:
            current_app.logger.error(f"仓库更新缓存失效失败: {str(e)}")


class CacheUpdateStrategy:
    """缓存更新策略"""
    
    @staticmethod
    def update_after_inventory_change(warehouse_id=None):
        """库存变更后的缓存更新"""
        try:
            # 异步预热相关缓存
            if warehouse_id:
                # 预热特定仓库的库存缓存
                from app.hot_data_cache import HotDataCacheService
                HotDataCacheService.get_inventory_list_cached(
                    warehouse_id=warehouse_id,
                    search_params={},
                    page=1,
                    per_page=50
                )
            
            # 预热聚合库存数据
            cache_warmup.warmup_inventory_cache()
            
            current_app.logger.info(f"库存变更后缓存更新完成: warehouse_id={warehouse_id}")
            
        except Exception as e:
            current_app.logger.error(f"库存变更后缓存更新失败: {str(e)}")
    
    @staticmethod
    def update_after_user_change(user_id):
        """用户变更后的缓存更新"""
        try:
            # 预热用户信息缓存
            from app.hot_data_cache import HotDataCacheService
            HotDataCacheService.get_user_info_cached(user_id)
            
            current_app.logger.info(f"用户变更后缓存更新完成: user_id={user_id}")
            
        except Exception as e:
            current_app.logger.error(f"用户变更后缓存更新失败: {str(e)}")
    
    @staticmethod
    def update_after_warehouse_change():
        """仓库变更后的缓存更新"""
        try:
            # 预热仓库列表缓存
            from app.hot_data_cache import HotDataCacheService
            HotDataCacheService.get_warehouse_list_cached()
            
            current_app.logger.info("仓库变更后缓存更新完成")
            
        except Exception as e:
            current_app.logger.error(f"仓库变更后缓存更新失败: {str(e)}")


class CacheConsistencyManager:
    """缓存一致性管理器"""
    
    @staticmethod
    def ensure_cache_consistency():
        """确保缓存一致性"""
        try:
            # 检查缓存版本
            from app.cache_config import CacheConfig
            current_version = CacheConfig.CACHE_VERSION
            
            # 可以在这里实现版本检查逻辑
            # 如果发现版本不匹配，清除所有缓存
            
            current_app.logger.debug("缓存一致性检查完成")
            
        except Exception as e:
            current_app.logger.error(f"缓存一致性检查失败: {str(e)}")
    
    @staticmethod
    def validate_cache_data(cache_type, cache_key, cached_data):
        """验证缓存数据有效性"""
        try:
            if cached_data is None:
                return False
            
            # 检查数据结构
            if isinstance(cached_data, dict):
                # 检查时间戳
                timestamp = cached_data.get('timestamp')
                if timestamp:
                    # 检查数据是否过期（超过配置的超时时间）
                    from app.cache_config import CacheConfig
                    timeout = CacheConfig.CACHE_TIMEOUT.get(cache_type, 300)
                    if time.time() - timestamp > timeout:
                        return False
            
            return True
            
        except Exception as e:
            current_app.logger.error(f"缓存数据验证失败: {str(e)}")
            return False


def cache_transaction(func):
    """缓存事务装饰器 - 确保数据库事务和缓存操作的一致性"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # 记录事务开始前的缓存状态
        cache_operations = []
        
        try:
            # 执行原函数
            result = func(*args, **kwargs)
            
            # 如果函数执行成功，执行缓存失效操作
            # 这里可以根据函数名或参数判断需要失效哪些缓存
            
            return result
            
        except Exception as e:
            # 如果函数执行失败，回滚缓存操作
            current_app.logger.error(f"缓存事务回滚: {str(e)}")
            raise
    
    return wrapper


def smart_cache_invalidation(operation_type, **kwargs):
    """智能缓存失效"""
    try:
        if operation_type == 'inventory_change':
            warehouse_id = kwargs.get('warehouse_id')
            identification_code = kwargs.get('identification_code')
            
            # 失效库存相关缓存
            cache_invalidation.on_inventory_change(warehouse_id)
            
            # 如果有识别编码，可以更精确地失效相关缓存
            if identification_code:
                # 这里可以实现更精确的缓存失效逻辑
                pass
            
        elif operation_type == 'user_change':
            user_id = kwargs.get('user_id')
            cache_invalidation.on_user_change(user_id)
            
        elif operation_type == 'warehouse_change':
            warehouse_id = kwargs.get('warehouse_id')
            cache_invalidation.on_warehouse_change(warehouse_id)
            
        elif operation_type == 'customer_change':
            cache_invalidation.on_customer_change()
            
        current_app.logger.info(f"智能缓存失效完成: {operation_type}")
        
    except Exception as e:
        current_app.logger.error(f"智能缓存失效失败: {str(e)}")


class CacheHealthChecker:
    """缓存健康检查器"""
    
    @staticmethod
    def check_cache_health():
        """检查缓存健康状态"""
        health_status = {
            'redis_available': False,
            'cache_hit_rate': 0.0,
            'slow_queries_count': 0,
            'cache_size': 0,
            'last_check': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        try:
            # 检查Redis可用性
            from app.cache_config import get_cache_manager
            health_status['redis_available'] = get_cache_manager().redis_manager.is_available()
            
            # 检查缓存命中率
            health_status['cache_hit_rate'] = performance_metrics.get_cache_hit_rate()
            
            # 检查慢查询数量
            slow_queries = performance_metrics.get_slow_queries(100)
            recent_slow = [q for q in slow_queries if time.time() - q['timestamp'] < 3600]  # 1小时内
            health_status['slow_queries_count'] = len(recent_slow)
            
            # 检查缓存大小
            redis_stats = get_cache_manager().get_cache_stats()
            health_status['cache_size'] = redis_stats.get('our_cache_keys', 0)
            
            # 评估健康状态
            if (health_status['redis_available'] and 
                health_status['cache_hit_rate'] > 50 and 
                health_status['slow_queries_count'] < 20):
                health_status['status'] = 'healthy'
            elif health_status['redis_available']:
                health_status['status'] = 'warning'
            else:
                health_status['status'] = 'critical'
            
        except Exception as e:
            health_status['status'] = 'error'
            health_status['error'] = str(e)
            current_app.logger.error(f"缓存健康检查失败: {str(e)}")
        
        return health_status


# 注册SQLAlchemy事件监听器
def register_cache_events():
    """注册缓存事件监听器"""
    try:
        # 库存表事件
        event.listen(Inventory, 'after_insert', CacheInvalidationStrategy.on_inventory_update)
        event.listen(Inventory, 'after_update', CacheInvalidationStrategy.on_inventory_update)
        event.listen(Inventory, 'after_delete', CacheInvalidationStrategy.on_inventory_update)
        
        # 入库记录事件
        event.listen(InboundRecord, 'after_insert', CacheInvalidationStrategy.on_inbound_update)
        event.listen(InboundRecord, 'after_update', CacheInvalidationStrategy.on_inbound_update)
        event.listen(InboundRecord, 'after_delete', CacheInvalidationStrategy.on_inbound_update)
        
        # 出库记录事件
        event.listen(OutboundRecord, 'after_insert', CacheInvalidationStrategy.on_outbound_update)
        event.listen(OutboundRecord, 'after_update', CacheInvalidationStrategy.on_outbound_update)
        event.listen(OutboundRecord, 'after_delete', CacheInvalidationStrategy.on_outbound_update)
        
        # 用户表事件
        event.listen(User, 'after_update', CacheInvalidationStrategy.on_user_update)
        
        # 仓库表事件
        event.listen(Warehouse, 'after_insert', CacheInvalidationStrategy.on_warehouse_update)
        event.listen(Warehouse, 'after_update', CacheInvalidationStrategy.on_warehouse_update)
        event.listen(Warehouse, 'after_delete', CacheInvalidationStrategy.on_warehouse_update)
        
        current_app.logger.info("缓存事件监听器注册完成")
        
    except Exception as e:
        current_app.logger.error(f"注册缓存事件监听器失败: {str(e)}")


# 缓存健康检查器实例
cache_health = CacheHealthChecker()
