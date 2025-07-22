"""
热点数据缓存实现
实现库存数据、用户信息、仓库信息等热点数据的缓存机制
"""

from app.cache_strategies import (
    InventoryCacheStrategy, UserCacheStrategy, WarehouseCacheStrategy,
    CustomerCacheStrategy, StatisticsCacheStrategy, AggregatedDataCacheStrategy
)

# 整合新的全系统缓存
try:
    from app.cache.system_decorators import (
        inventory_cached, user_cached, warehouse_cached, statistics_cached,
        invalidate_inventory, invalidate_user
    )
    SYSTEM_CACHE_AVAILABLE = True
except ImportError:
    SYSTEM_CACHE_AVAILABLE = False
from app.database_optimization import QueryOptimizer, query_performance_monitor
from app.models import Inventory, User, Warehouse, InboundRecord, OutboundRecord
from app import db
from flask import current_app, g
from flask_login import current_user
import time
from datetime import datetime, timedelta
from collections import defaultdict


class HotDataCacheService:
    """热点数据缓存服务"""
    
    @staticmethod
    def get_inventory_list_cached(warehouse_id=None, search_params=None, page=1, per_page=50):
        """获取缓存的库存列表数据 - 自动应用双层缓存"""
        # 直接调用自动缓存版本
        return HotDataCacheService._get_inventory_list_with_cache(warehouse_id, search_params, page, per_page)

    @staticmethod
    @query_performance_monitor
    def _get_inventory_list_with_cache(warehouse_id=None, search_params=None, page=1, per_page=50):
        """内部方法：获取库存列表（自动应用缓存）"""
        if SYSTEM_CACHE_AVAILABLE:
            # 使用新的双层缓存系统
            from app.cache.system_decorators import inventory_cached

            @inventory_cached(use_legacy=True)
            def _fetch_inventory_data(wh_id, search_params, page, per_page):
                return HotDataCacheService._fetch_inventory_from_db(wh_id, search_params, page, per_page)

            return _fetch_inventory_data(warehouse_id, search_params, page, per_page)
        else:
            # 降级到现有缓存策略
            return HotDataCacheService._fetch_inventory_legacy(warehouse_id, search_params, page, per_page)

    @staticmethod
    def _fetch_inventory_from_db(warehouse_id, search_params, page, per_page):
        """从数据库获取库存数据"""
        current_app.logger.debug("从数据库查询库存列表")

        # 使用优化的查询
        query = QueryOptimizer.get_optimized_inventory_query(warehouse_id, search_params)

        # 分页查询
        total_count = query.count()
        offset = (page - 1) * per_page
        records = query.offset(offset).limit(per_page).all()

        # 构建返回数据
        result_data = {
            'items': [record.to_dict() for record in records],
            'total': total_count,
            'page': page,
            'per_page': per_page,
            'pages': (total_count + per_page - 1) // per_page,
            'cached_at': time.time()
        }

        return result_data

    @staticmethod
    def _fetch_inventory_legacy(warehouse_id, search_params, page, per_page):
        """使用现有缓存策略获取库存数据"""
        # 尝试从现有缓存获取
        cached_data = InventoryCacheStrategy.get_cached_inventory_list(
            warehouse_id, search_params, page, per_page
        )

        if cached_data is not None:
            current_app.logger.info("库存列表缓存命中（现有策略）")
            return cached_data

        # 缓存未命中，从数据库查询
        result_data = HotDataCacheService._fetch_inventory_from_db(warehouse_id, search_params, page, per_page)

        # 使用现有策略缓存结果
        InventoryCacheStrategy.cache_inventory_list(
            warehouse_id, search_params, page, per_page, result_data
        )

        return result_data
    
    @staticmethod
    @query_performance_monitor
    def get_aggregated_inventory_cached():
        """获取缓存的聚合库存数据"""
        # 尝试从缓存获取
        cached_data = AggregatedDataCacheStrategy.get_cached_aggregated_inventory()
        
        if cached_data is not None:
            current_app.logger.info("聚合库存数据缓存命中")
            return cached_data
        
        # 缓存未命中，计算聚合数据
        current_app.logger.info("聚合库存数据缓存未命中，重新计算")
        
        # 获取所有库存记录，按identification_code分组
        all_inventories = Inventory.query.options(
            db.joinedload(Inventory.operated_warehouse)
        ).all()
        
        inventory_groups = defaultdict(list)
        for inv in all_inventories:
            if inv.identification_code:
                inventory_groups[inv.identification_code].append(inv)
        
        aggregated_results = []
        
        # 对每个identification_code进行状态分离处理
        for identification_code, inventories in inventory_groups.items():
            if not inventories:
                continue
            
            # 获取基础信息（使用最早的入库记录）
            base_inventory = min(inventories, key=lambda x: x.inbound_time or datetime.min)
            
            # 获取出库记录
            outbound_records = OutboundRecord.query.filter_by(
                identification_code=identification_code
            ).all()
            
            # 计算出库到春疆货场/工厂的总数量
            chunjiang_outbound_pallet = sum(
                out.pallet_count or 0 for out in outbound_records
                if out.destination in ['春疆货场', '工厂']
            )
            chunjiang_outbound_package = sum(
                out.package_count or 0 for out in outbound_records
                if out.destination in ['春疆货场', '工厂']
            )
            
            # 基础信息模板
            base_info = {
                'identification_code': identification_code,
                'customer_name': base_inventory.customer_name,
                'inbound_time': base_inventory.inbound_time,
                'plate_number': base_inventory.plate_number,
                'order_type': base_inventory.order_type,
                'export_mode': base_inventory.export_mode,
                'customs_broker': base_inventory.customs_broker,
                'documents': base_inventory.documents,
                'service_staff': base_inventory.service_staff,
                'weight': base_inventory.weight,
                'volume': base_inventory.volume,
                'inbound_pallet_count': base_inventory.inbound_pallet_count,
                'inbound_package_count': base_inventory.inbound_package_count,
                'last_updated': max(inv.last_updated for inv in inventories)
            }
            
            # 按仓库分组当前库存
            warehouse_inventories = defaultdict(lambda: {'pallet_count': 0, 'package_count': 0, 'location': ''})
            
            for inv in inventories:
                if inv.operated_warehouse and (inv.pallet_count > 0 or inv.package_count > 0):
                    warehouse_id = inv.operated_warehouse_id
                    warehouse_inventories[warehouse_id]['pallet_count'] += inv.pallet_count or 0
                    warehouse_inventories[warehouse_id]['package_count'] += inv.package_count or 0
                    warehouse_inventories[warehouse_id]['warehouse'] = inv.operated_warehouse
                    if inv.location:
                        warehouse_inventories[warehouse_id]['location'] = inv.location
            
            # 为每个有库存的仓库创建记录
            for warehouse_id, warehouse_data in warehouse_inventories.items():
                if warehouse_data['pallet_count'] > 0 or warehouse_data['package_count'] > 0:
                    record = base_info.copy()
                    record.update({
                        'id': f"{identification_code}_{warehouse_id}",
                        'pallet_count': warehouse_data['pallet_count'],
                        'package_count': warehouse_data['package_count'],
                        'location': warehouse_data['location'],
                        'operated_warehouse': warehouse_data['warehouse'],
                        'operated_warehouse_id': warehouse_id,
                        'current_warehouse_id': warehouse_id
                    })
                    
                    # 添加货物状态
                    from app.main.routes import get_cargo_status
                    cargo_status_info = get_cargo_status(type('obj', (object,), record)())
                    record['cargo_status'] = cargo_status_info
                    record['current_status'] = cargo_status_info['status']
                    
                    aggregated_results.append(record)
            
            # 如果有出库到春疆货场/工厂的记录，创建一个"已出库"状态的记录
            if chunjiang_outbound_pallet > 0 or chunjiang_outbound_package > 0:
                record = base_info.copy()
                record.update({
                    'id': f"{identification_code}_shipped",
                    'pallet_count': chunjiang_outbound_pallet,
                    'package_count': chunjiang_outbound_package,
                    'location': '春疆货场/工厂',
                    'operated_warehouse': None,
                    'operated_warehouse_id': None,
                    'current_warehouse_id': None,
                    'cargo_status': {
                        'status': 'shipped_to_chunjiang',
                        'label': '已出库到春疆',
                        'class': 'success',
                        'icon': 'shipping-fast'
                    },
                    'current_status': 'shipped_to_chunjiang'
                })
                
                aggregated_results.append(record)
        
        # 缓存结果
        AggregatedDataCacheStrategy.cache_aggregated_inventory(aggregated_results)
        
        return aggregated_results
    
    @staticmethod
    @query_performance_monitor
    def get_user_info_cached(user_id):
        """获取缓存的用户信息"""
        # 尝试从缓存获取
        cached_data = UserCacheStrategy.get_cached_user_info(user_id)
        
        if cached_data is not None:
            current_app.logger.debug(f"用户信息缓存命中: user_id={user_id}")
            return cached_data
        
        # 缓存未命中，从数据库查询
        user = User.query.options(db.joinedload(User.warehouse)).get(user_id)
        
        if user:
            user_data = user.to_dict()
            # 缓存用户信息
            UserCacheStrategy.cache_user_info(user_id, user_data)
            return user_data
        
        return None
    
    @staticmethod
    @query_performance_monitor
    def get_warehouse_list_cached():
        """获取缓存的仓库列表"""
        # 尝试从缓存获取
        cached_data = WarehouseCacheStrategy.get_cached_warehouse_list()
        
        if cached_data is not None:
            current_app.logger.debug("仓库列表缓存命中")
            return cached_data
        
        # 缓存未命中，从数据库查询
        warehouses = Warehouse.query.order_by(Warehouse.warehouse_name).all()
        warehouse_data = [warehouse.to_dict() for warehouse in warehouses]
        
        # 缓存仓库列表
        WarehouseCacheStrategy.cache_warehouse_list(warehouse_data)
        
        return warehouse_data
    
    @staticmethod
    @query_performance_monitor
    def get_customer_list_cached(query_param=''):
        """获取缓存的客户列表"""
        # 尝试从缓存获取
        cached_data = CustomerCacheStrategy.get_cached_customer_list(query_param)
        
        if cached_data is not None:
            current_app.logger.debug(f"客户列表缓存命中: query={query_param}")
            return cached_data
        
        # 缓存未命中，从数据库查询
        customers_query = db.session.query(Inventory.customer_name).distinct()
        
        if query_param:
            customers_query = customers_query.filter(
                Inventory.customer_name.like(f'%{query_param}%')
            )
        
        customers_query = customers_query.order_by(Inventory.customer_name)
        customers = [row[0] for row in customers_query.all() if row[0]]
        
        # 缓存客户列表
        CustomerCacheStrategy.cache_customer_list(customers, query_param)
        
        return customers
    
    @staticmethod
    @query_performance_monitor
    def get_dashboard_stats_cached():
        """获取缓存的仪表板统计数据"""
        # 尝试从缓存获取
        cached_data = StatisticsCacheStrategy.get_cached_dashboard_stats()
        
        if cached_data is not None:
            current_app.logger.debug("仪表板统计缓存命中")
            return cached_data
        
        # 缓存未命中，计算统计数据
        stats = {}
        
        try:
            # 库存统计
            total_inventory = db.session.query(
                db.func.sum(Inventory.pallet_count),
                db.func.sum(Inventory.package_count)
            ).filter(
                db.or_(Inventory.pallet_count > 0, Inventory.package_count > 0)
            ).first()
            
            stats['total_pallets'] = total_inventory[0] or 0
            stats['total_packages'] = total_inventory[1] or 0
            
            # 今日入库统计
            today = datetime.now().date()
            today_inbound = db.session.query(
                db.func.sum(InboundRecord.pallet_count),
                db.func.sum(InboundRecord.package_count)
            ).filter(
                db.func.date(InboundRecord.inbound_time) == today
            ).first()
            
            stats['today_inbound_pallets'] = today_inbound[0] or 0
            stats['today_inbound_packages'] = today_inbound[1] or 0
            
            # 今日出库统计
            today_outbound = db.session.query(
                db.func.sum(OutboundRecord.pallet_count),
                db.func.sum(OutboundRecord.package_count)
            ).filter(
                db.func.date(OutboundRecord.outbound_time) == today
            ).first()
            
            stats['today_outbound_pallets'] = today_outbound[0] or 0
            stats['today_outbound_packages'] = today_outbound[1] or 0
            
            # 仓库数量统计
            warehouse_stats = db.session.query(
                Warehouse.warehouse_type,
                db.func.count(Warehouse.id)
            ).group_by(Warehouse.warehouse_type).all()
            
            stats['warehouse_counts'] = {wtype: count for wtype, count in warehouse_stats}
            
            # 用户数量统计
            user_count = db.session.query(db.func.count(User.id)).filter(
                User.status == 'active'
            ).scalar()
            
            stats['active_users'] = user_count or 0
            
            # 添加时间戳
            stats['timestamp'] = time.time()
            
        except Exception as e:
            current_app.logger.error(f"计算仪表板统计数据失败: {str(e)}")
            stats = {'error': str(e), 'timestamp': time.time()}
        
        # 缓存统计数据
        StatisticsCacheStrategy.cache_dashboard_stats(stats)
        
        return stats


class CacheWarmupService:
    """缓存预热服务"""
    
    @staticmethod
    def warmup_inventory_cache():
        """预热库存缓存"""
        try:
            current_app.logger.info("开始预热库存缓存")
            
            # 预热聚合库存数据
            HotDataCacheService.get_aggregated_inventory_cached()
            
            # 预热各仓库的库存数据
            warehouses = Warehouse.query.all()
            for warehouse in warehouses:
                HotDataCacheService.get_inventory_list_cached(
                    warehouse_id=warehouse.id,
                    search_params={},
                    page=1,
                    per_page=50
                )
            
            current_app.logger.info("库存缓存预热完成")
            
        except Exception as e:
            current_app.logger.error(f"库存缓存预热失败: {str(e)}")
    
    @staticmethod
    def warmup_basic_data_cache():
        """预热基础数据缓存"""
        try:
            current_app.logger.info("开始预热基础数据缓存")
            
            # 预热仓库列表
            HotDataCacheService.get_warehouse_list_cached()
            
            # 预热客户列表
            HotDataCacheService.get_customer_list_cached()
            
            # 预热仪表板统计
            HotDataCacheService.get_dashboard_stats_cached()
            
            current_app.logger.info("基础数据缓存预热完成")
            
        except Exception as e:
            current_app.logger.error(f"基础数据缓存预热失败: {str(e)}")
    
    @staticmethod
    def warmup_all_cache():
        """预热所有缓存"""
        CacheWarmupService.warmup_basic_data_cache()
        CacheWarmupService.warmup_inventory_cache()


# 热点数据缓存服务实例
hot_cache = HotDataCacheService()
cache_warmup = CacheWarmupService()
