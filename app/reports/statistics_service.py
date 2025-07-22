#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统计报表服务 - 集成双层缓存
提供各类统计数据的查询和计算服务
"""

from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_, case, text
from flask_login import current_user
from flask import current_app
from app import db
from app.models import (
    InboundRecord, OutboundRecord, Inventory, TransitCargo,
    ReceiveRecord, Warehouse, User
)

# 导入缓存组件
from app.cache.dual_cache_manager import get_dual_cache_manager
from app.cache.cache_decorators import (
    dashboard_cached, stats_cached, inventory_cached,
    realtime_cached, historical_cached
)

class StatisticsService:
    """统计报表服务类 - 集成双层缓存"""

    def __init__(self):
        self.warehouse_names = {
            1: '平湖仓', 2: '昆山仓', 3: '成都仓', 4: '凭祥北投仓', 5: '凭祥保税仓'
        }
        self.cache_manager = get_dual_cache_manager()
    
    def get_dashboard_data(self, user):
        """获取仪表板数据 - 自动应用缓存"""
        # 直接调用缓存版本的方法
        return self._get_dashboard_data_cached(user)

    @dashboard_cached('dashboard_data', ttl=300)
    def _get_dashboard_data_cached(self, user):
        """获取仪表板数据 - 缓存版本（自动应用）"""
        return self._fetch_dashboard_data_from_db(user) or self._get_empty_dashboard_data()

    def _fetch_dashboard_data_from_db(self, user):
        """从数据库获取仪表板数据"""
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        this_week_start = today - timedelta(days=today.weekday())
        this_month_start = today.replace(day=1)
        last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)

        # 基础统计
        data = {}

        # 安全地获取每个数据项
        try:
            data['today_stats'] = self._get_daily_stats_cached(today, user)
        except Exception as e:
            if current_app:
                current_app.logger.error(f"获取今日统计失败: {e}")
            data['today_stats'] = {'inbound': {'count': 0, 'packages': 0}, 'outbound': {'count': 0, 'packages': 0}}

        try:
            data['yesterday_stats'] = self._get_daily_stats_cached(yesterday, user)
        except Exception as e:
            if current_app:
                current_app.logger.error(f"获取昨日统计失败: {e}")
            data['yesterday_stats'] = {'inbound': {'count': 0, 'packages': 0}, 'outbound': {'count': 0, 'packages': 0}}

        try:
            data['week_stats'] = self._get_period_stats_cached(this_week_start, today, user)
        except Exception as e:
            if current_app:
                current_app.logger.error(f"获取周统计失败: {e}")
            data['week_stats'] = {'inbound_daily': [], 'outbound_daily': []}

        try:
            data['month_stats'] = self._get_period_stats_cached(this_month_start, today, user)
        except Exception as e:
            if current_app:
                current_app.logger.error(f"获取月统计失败: {e}")
            data['month_stats'] = {'inbound_daily': [], 'outbound_daily': []}

        try:
            data['last_month_stats'] = self._get_period_stats_cached(last_month_start, this_month_start - timedelta(days=1), user)
        except Exception as e:
            if current_app:
                current_app.logger.error(f"获取上月统计失败: {e}")
            data['last_month_stats'] = {'inbound_daily': [], 'outbound_daily': []}

        try:
            data['warehouse_summary'] = self._get_warehouse_summary_cached(user)
        except Exception as e:
            if current_app:
                current_app.logger.error(f"获取仓库汇总失败: {e}")
            data['warehouse_summary'] = []

        try:
            data['inventory_overview'] = self._get_inventory_overview_cached(user)
        except Exception as e:
            if current_app:
                current_app.logger.error(f"获取库存概览失败: {e}")
            data['inventory_overview'] = {'total': {'items': 0, 'packages': 0}, 'by_warehouse': []}

        try:
            data['transit_overview'] = self._get_transit_overview_cached(user)
        except Exception as e:
            if current_app:
                current_app.logger.error(f"获取在途概览失败: {e}")
            data['transit_overview'] = {'in_transit': {'items': 0, 'packages': 0}}

        try:
            data['customer_overview'] = self._get_customer_overview_cached(user)
        except Exception as e:
            if current_app:
                current_app.logger.error(f"获取客户概览失败: {e}")
            data['customer_overview'] = {}

        try:
            data['top_customers'] = self._get_top_customers_cached(user, limit=10)
        except Exception as e:
            if current_app:
                current_app.logger.error(f"获取TOP客户失败: {e}")
            data['top_customers'] = []

        try:
            data['top_routes'] = self._get_top_routes_cached(user, limit=10)
        except Exception as e:
            if current_app:
                current_app.logger.error(f"获取热门路线失败: {e}")
            data['top_routes'] = []

        try:
            data['busy_warehouses'] = self._get_busy_warehouses(user, limit=4)
        except Exception as e:
            print(f"获取繁忙仓库失败: {e}")
            data['busy_warehouses'] = []

        try:
            data['weekly_trend'] = self._get_weekly_trend(user)
        except Exception as e:
            print(f"获取周趋势失败: {e}")
            data['weekly_trend'] = []

        try:
            data['monthly_trend'] = self._get_monthly_trend(user)
        except Exception as e:
            print(f"获取月趋势失败: {e}")
            data['monthly_trend'] = []

        try:
            data['alerts'] = self._get_system_alerts(user)
        except Exception as e:
            print(f"获取系统预警失败: {e}")
            data['alerts'] = []

        try:
            data['kpi_indicators'] = self._get_kpi_indicators(user)
        except Exception as e:
            print(f"获取KPI指标失败: {e}")
            data['kpi_indicators'] = {
                'inbound_growth': {'current': 0, 'last': 0, 'growth_rate': 0, 'trend': 'neutral'},
                'outbound_growth': {'current': 0, 'last': 0, 'growth_rate': 0, 'trend': 'neutral'},
                'package_throughput': {'inbound': 0, 'outbound': 0, 'net_flow': 0, 'efficiency': 0},
                'inventory_turnover': {'rate': 0, 'level': 'low'},
                'processing_efficiency': {'avg_days': 0, 'performance': 'good'}
            }

        try:
            data['realtime_stats'] = self._get_realtime_stats(user)
        except Exception as e:
            print(f"获取实时统计失败: {e}")
            data['realtime_stats'] = {
                'current_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'today_total': {'inbound': 0, 'outbound': 0},
                'recent_hour': {'inbound': 0, 'outbound': 0},
                'system_status': {'active_users': 0, 'pending_tasks': 0, 'system_load': 'normal'}
            }

        # 添加元数据
        data['generated_at'] = datetime.now().isoformat()
        data['cache_version'] = '2.0'

        return data

    def _get_empty_dashboard_data(self):
        """获取空的仪表板数据结构"""
        return {
            'today_stats': {'inbound': {'count': 0, 'packages': 0}, 'outbound': {'count': 0, 'packages': 0}},
            'yesterday_stats': {'inbound': {'count': 0, 'packages': 0}, 'outbound': {'count': 0, 'packages': 0}},
            'warehouse_summary': [],
            'inventory_overview': {'total_inventory': 0, 'over_one_day': 0, 'over_three_days': 0},
            'transit_overview': {'total_transit': 0, 'pending_receive': 0},
            'top_customers': [],
            'busy_warehouses': [],
            'week_stats': {'inbound_daily': [], 'outbound_daily': []},
            'month_stats': {'inbound_daily': [], 'outbound_daily': []},
            'generated_at': datetime.now().isoformat(),
            'cache_version': '2.0'
        }

    # 缓存版本的统计方法

    @stats_cached('daily_stats')
    def _get_daily_stats_cached(self, date, user):
        """获取日统计数据 - 缓存版本"""
        cache_key = f"daily_stats:{date}:user:{user.id}:warehouse:{getattr(user, 'warehouse_id', 'all')}"

        def fetch_daily_stats():
            # 尝试使用异步版本
            try:
                from app.async_database import run_async_in_flask, AsyncStatisticsService, AsyncDatabaseManager

                # 获取数据库URL
                database_url = current_app.config.get('SQLALCHEMY_DATABASE_URI', '')
                if database_url:
                    db_manager = AsyncDatabaseManager(database_url)
                    async_service = AsyncStatisticsService(db_manager)
                    warehouse_id = getattr(user, 'warehouse_id', 1)

                    # 运行异步函数
                    return run_async_in_flask(async_service.get_today_stats_async, warehouse_id)
            except Exception as e:
                current_app.logger.warning(f"异步查询失败，降级到同步: {e}")

            # 降级到同步版本
            return self._get_daily_stats(date, user)

        return self.cache_manager.get(
            key=cache_key,
            fallback=fetch_daily_stats,
            cache_type='today_stats'
        )

    @stats_cached('period_stats')
    def _get_period_stats_cached(self, start_date, end_date, user):
        """获取期间统计数据 - 缓存版本"""
        cache_key = f"period_stats:{start_date}:{end_date}:user:{user.id}:warehouse:{getattr(user, 'warehouse_id', 'all')}"

        def fetch_period_stats():
            return self._get_period_stats(start_date, end_date, user)

        return self.cache_manager.get(
            key=cache_key,
            fallback=fetch_period_stats,
            cache_type='historical_stats'
        )

    @inventory_cached('warehouse_summary')
    def _get_warehouse_summary_cached(self, user):
        """获取仓库汇总 - 缓存版本"""
        cache_key = f"warehouse_summary:user:{user.id}:warehouse:{getattr(user, 'warehouse_id', 'all')}"

        def fetch_warehouse_summary():
            return self._get_warehouse_summary(user)

        return self.cache_manager.get(
            key=cache_key,
            fallback=fetch_warehouse_summary,
            cache_type='warehouse_summary'
        )

    @inventory_cached('inventory_overview')
    def _get_inventory_overview_cached(self, user):
        """获取库存概览 - 缓存版本"""
        cache_key = f"inventory_overview:user:{user.id}:warehouse:{getattr(user, 'warehouse_id', 'all')}"

        def fetch_inventory_overview():
            return self._get_inventory_overview(user)

        return self.cache_manager.get(
            key=cache_key,
            fallback=fetch_inventory_overview,
            cache_type='inventory_overview'
        )

    @realtime_cached('transit_overview')
    def _get_transit_overview_cached(self, user):
        """获取在途概览 - 缓存版本"""
        cache_key = f"transit_overview:user:{user.id}:warehouse:{getattr(user, 'warehouse_id', 'all')}"

        def fetch_transit_overview():
            return self._get_transit_overview(user)

        return self.cache_manager.get(
            key=cache_key,
            fallback=fetch_transit_overview,
            cache_type='transit_overview'
        )

    @stats_cached('customer_overview')
    def _get_customer_overview_cached(self, user):
        """获取客户概览 - 缓存版本"""
        cache_key = f"customer_overview:user:{user.id}:warehouse:{getattr(user, 'warehouse_id', 'all')}"

        def fetch_customer_overview():
            return self._get_customer_overview(user)

        return self.cache_manager.get(
            key=cache_key,
            fallback=fetch_customer_overview,
            cache_type='customer_ranking'
        )

    @stats_cached('top_customers')
    def _get_top_customers_cached(self, user, limit=10):
        """获取TOP客户 - 缓存版本"""
        cache_key = f"top_customers:user:{user.id}:warehouse:{getattr(user, 'warehouse_id', 'all')}:limit:{limit}"

        def fetch_top_customers():
            return self._get_top_customers(user, limit)

        return self.cache_manager.get(
            key=cache_key,
            fallback=fetch_top_customers,
            cache_type='customer_ranking'
        )

    @stats_cached('top_routes')
    def _get_top_routes_cached(self, user, limit=10):
        """获取热门路线 - 缓存版本"""
        cache_key = f"top_routes:user:{user.id}:warehouse:{getattr(user, 'warehouse_id', 'all')}:limit:{limit}"

        def fetch_top_routes():
            return self._get_top_routes(user, limit)

        return self.cache_manager.get(
            key=cache_key,
            fallback=fetch_top_routes,
            cache_type='warehouse_summary'
        )

    # 缓存失效方法

    def invalidate_dashboard_cache(self, user_id=None, warehouse_id=None):
        """失效仪表板缓存"""
        patterns = [
            'dashboard_summary:*',
            'daily_stats:*',
            'warehouse_summary:*',
            'inventory_overview:*'
        ]

        if user_id:
            patterns.extend([
                f'dashboard_summary:user:{user_id}:*',
                f'daily_stats:*:user:{user_id}:*'
            ])

        if warehouse_id:
            patterns.extend([
                f'*:warehouse:{warehouse_id}',
                f'warehouse_summary:*:warehouse:{warehouse_id}'
            ])

        for pattern in patterns:
            try:
                self.cache_manager.clear_cache(pattern=pattern)
            except Exception as e:
                if current_app:
                    current_app.logger.error(f"清理缓存失败 {pattern}: {e}")

    def invalidate_inventory_cache(self, warehouse_id=None):
        """失效库存缓存"""
        patterns = [
            'inventory_overview:*',
            'warehouse_summary:*'
        ]

        if warehouse_id:
            patterns.extend([
                f'inventory_overview:*:warehouse:{warehouse_id}',
                f'warehouse_summary:*:warehouse:{warehouse_id}'
            ])

        for pattern in patterns:
            try:
                self.cache_manager.clear_cache(pattern=pattern)
            except Exception as e:
                if current_app:
                    current_app.logger.error(f"清理库存缓存失败 {pattern}: {e}")

    def invalidate_stats_cache(self, date=None, warehouse_id=None):
        """失效统计缓存"""
        patterns = [
            'daily_stats:*',
            'period_stats:*',
            'today_stats:*'
        ]

        if date:
            patterns.append(f'daily_stats:{date}:*')

        if warehouse_id:
            patterns.extend([
                f'*:warehouse:{warehouse_id}',
                f'daily_stats:*:warehouse:{warehouse_id}'
            ])

        for pattern in patterns:
            try:
                self.cache_manager.clear_cache(pattern=pattern)
            except Exception as e:
                if current_app:
                    current_app.logger.error(f"清理统计缓存失败 {pattern}: {e}")

    def _get_daily_stats(self, date, user):
        """获取指定日期的统计数据"""
        date_start = datetime.combine(date, datetime.min.time())
        date_end = datetime.combine(date, datetime.max.time())
        
        # 构建查询条件
        warehouse_filter = self._get_warehouse_filter(user)
        
        # 入库统计
        inbound_query = InboundRecord.query.filter(
            InboundRecord.inbound_time.between(date_start, date_end)
        )
        if warehouse_filter:
            inbound_query = inbound_query.filter(warehouse_filter)
        
        inbound_stats = inbound_query.with_entities(
            func.count(InboundRecord.id).label('count'),
            func.sum(InboundRecord.pallet_count).label('total_pallets'),
            func.sum(InboundRecord.package_count).label('total_packages'),
            func.sum(InboundRecord.weight).label('total_weight'),
            func.sum(InboundRecord.volume).label('total_volume')
        ).first()
        
        # 出库统计
        outbound_query = OutboundRecord.query.filter(
            OutboundRecord.outbound_time.between(date_start, date_end)
        )
        if warehouse_filter:
            outbound_query = outbound_query.filter(warehouse_filter)
        
        outbound_stats = outbound_query.with_entities(
            func.count(OutboundRecord.id).label('count'),
            func.sum(OutboundRecord.pallet_count).label('total_pallets'),
            func.sum(OutboundRecord.package_count).label('total_packages'),
            func.sum(OutboundRecord.weight).label('total_weight'),
            func.sum(OutboundRecord.volume).label('total_volume')
        ).first()
        
        return {
            'date': date.strftime('%Y-%m-%d'),
            'inbound': {
                'count': inbound_stats.count or 0,
                'pallets': inbound_stats.total_pallets or 0,
                'packages': inbound_stats.total_packages or 0,
                'weight': float(inbound_stats.total_weight or 0),
                'volume': float(inbound_stats.total_volume or 0)
            },
            'outbound': {
                'count': outbound_stats.count or 0,
                'pallets': outbound_stats.total_pallets or 0,
                'packages': outbound_stats.total_packages or 0,
                'weight': float(outbound_stats.total_weight or 0),
                'volume': float(outbound_stats.total_volume or 0)
            }
        }
    
    def _get_period_stats(self, start_date, end_date, user):
        """获取时间段统计数据"""
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        warehouse_filter = self._get_warehouse_filter(user)
        
        # 按日期分组的统计
        inbound_daily = db.session.query(
            func.date(InboundRecord.inbound_time).label('date'),
            func.count(InboundRecord.id).label('count'),
            func.sum(InboundRecord.pallet_count).label('pallets'),
            func.sum(InboundRecord.package_count).label('packages')
        ).filter(
            InboundRecord.inbound_time.between(start_datetime, end_datetime)
        )
        
        if warehouse_filter:
            inbound_daily = inbound_daily.filter(warehouse_filter)
        
        inbound_daily = inbound_daily.group_by(
            func.date(InboundRecord.inbound_time)
        ).all()
        
        outbound_daily = db.session.query(
            func.date(OutboundRecord.outbound_time).label('date'),
            func.count(OutboundRecord.id).label('count'),
            func.sum(OutboundRecord.pallet_count).label('pallets'),
            func.sum(OutboundRecord.package_count).label('packages')
        ).filter(
            OutboundRecord.outbound_time.between(start_datetime, end_datetime)
        )
        
        if warehouse_filter:
            outbound_daily = outbound_daily.filter(warehouse_filter)
        
        outbound_daily = outbound_daily.group_by(
            func.date(OutboundRecord.outbound_time)
        ).all()
        
        return {
            'period': f"{start_date} 至 {end_date}",
            'inbound_daily': [
                {
                    'date': item.date.strftime('%Y-%m-%d'),
                    'count': item.count,
                    'pallets': item.pallets or 0,
                    'packages': item.packages or 0
                } for item in inbound_daily
            ],
            'outbound_daily': [
                {
                    'date': item.date.strftime('%Y-%m-%d'),
                    'count': item.count,
                    'pallets': item.pallets or 0,
                    'packages': item.packages or 0
                } for item in outbound_daily
            ]
        }
    
    def _get_warehouse_summary(self, user):
        """获取仓库汇总数据"""
        warehouse_filter = self._get_warehouse_filter(user)
        
        # 各仓库入库统计
        inbound_by_warehouse = db.session.query(
            InboundRecord.operated_warehouse_id,
            func.count(InboundRecord.id).label('inbound_count'),
            func.sum(InboundRecord.pallet_count).label('inbound_pallets'),
            func.sum(InboundRecord.package_count).label('inbound_packages')
        ).filter(InboundRecord.operated_warehouse_id.isnot(None))  # 过滤NULL值

        if warehouse_filter:
            inbound_by_warehouse = inbound_by_warehouse.filter(warehouse_filter)

        inbound_by_warehouse = inbound_by_warehouse.group_by(
            InboundRecord.operated_warehouse_id
        ).all()
        
        # 各仓库出库统计
        outbound_by_warehouse = db.session.query(
            OutboundRecord.operated_warehouse_id,
            func.count(OutboundRecord.id).label('outbound_count'),
            func.sum(OutboundRecord.pallet_count).label('outbound_pallets'),
            func.sum(OutboundRecord.package_count).label('outbound_packages')
        ).filter(OutboundRecord.operated_warehouse_id.isnot(None))  # 过滤NULL值

        if warehouse_filter:
            outbound_by_warehouse = outbound_by_warehouse.filter(warehouse_filter)

        outbound_by_warehouse = outbound_by_warehouse.group_by(
            OutboundRecord.operated_warehouse_id
        ).all()
        
        # 合并数据
        warehouse_data = {}
        for item in inbound_by_warehouse:
            warehouse_id = item.operated_warehouse_id
            warehouse_data[warehouse_id] = {
                'warehouse_id': warehouse_id,
                'warehouse_name': self.warehouse_names.get(warehouse_id, f'仓库{warehouse_id}'),
                'inbound_count': item.inbound_count,
                'inbound_pallets': item.inbound_pallets or 0,
                'inbound_packages': item.inbound_packages or 0,
                'outbound_count': 0,
                'outbound_pallets': 0,
                'outbound_packages': 0
            }
        
        for item in outbound_by_warehouse:
            warehouse_id = item.operated_warehouse_id
            if warehouse_id not in warehouse_data:
                warehouse_data[warehouse_id] = {
                    'warehouse_id': warehouse_id,
                    'warehouse_name': self.warehouse_names.get(warehouse_id, f'仓库{warehouse_id}'),
                    'inbound_count': 0,
                    'inbound_pallets': 0,
                    'inbound_packages': 0,
                    'outbound_count': item.outbound_count,
                    'outbound_pallets': item.outbound_pallets or 0,
                    'outbound_packages': item.outbound_packages or 0
                }
            else:
                warehouse_data[warehouse_id].update({
                    'outbound_count': item.outbound_count,
                    'outbound_pallets': item.outbound_pallets or 0,
                    'outbound_packages': item.outbound_packages or 0
                })
        
        return list(warehouse_data.values())
    
    def _get_inventory_overview(self, user):
        """获取库存概览"""
        warehouse_filter = self._get_warehouse_filter(user, 'Inventory')
        
        inventory_query = Inventory.query
        if warehouse_filter:
            inventory_query = inventory_query.filter(warehouse_filter)
        
        inventory_stats = inventory_query.with_entities(
            func.count(Inventory.id).label('total_items'),
            func.sum(Inventory.pallet_count).label('total_pallets'),
            func.sum(Inventory.package_count).label('total_packages'),
            func.sum(Inventory.weight).label('total_weight'),
            func.sum(Inventory.volume).label('total_volume')
        ).first()
        
        # 按仓库分组的库存
        inventory_by_warehouse = inventory_query.filter(
            Inventory.operated_warehouse_id.isnot(None)  # 过滤NULL值
        ).with_entities(
            Inventory.operated_warehouse_id,
            func.count(Inventory.id).label('items'),
            func.sum(Inventory.pallet_count).label('pallets'),
            func.sum(Inventory.package_count).label('packages')
        ).group_by(Inventory.operated_warehouse_id).all()
        
        return {
            'total': {
                'items': inventory_stats.total_items or 0,
                'pallets': inventory_stats.total_pallets or 0,
                'packages': inventory_stats.total_packages or 0,
                'weight': float(inventory_stats.total_weight or 0),
                'volume': float(inventory_stats.total_volume or 0)
            },
            'by_warehouse': [
                {
                    'warehouse_id': item.operated_warehouse_id,
                    'warehouse_name': self.warehouse_names.get(item.operated_warehouse_id, f'仓库{item.operated_warehouse_id}'),
                    'items': item.items,
                    'pallets': item.pallets or 0,
                    'packages': item.packages or 0
                } for item in inventory_by_warehouse
            ]
        }
    
    def _get_transit_overview(self, user):
        """获取在途货物概览"""
        # 在途货物统计
        transit_stats = TransitCargo.query.filter(
            TransitCargo.status == 'in_transit'
        ).with_entities(
            func.count(TransitCargo.id).label('total_items'),
            func.sum(TransitCargo.pallet_count).label('total_pallets'),
            func.sum(TransitCargo.package_count).label('total_packages')
        ).first()
        
        # 按状态分组
        status_stats = db.session.query(
            TransitCargo.status,
            func.count(TransitCargo.id).label('count')
        ).group_by(TransitCargo.status).all()
        
        return {
            'in_transit': {
                'items': transit_stats.total_items or 0,
                'pallets': transit_stats.total_pallets or 0,
                'packages': transit_stats.total_packages or 0
            },
            'by_status': [
                {
                    'status': item.status,
                    'status_name': self._get_status_name(item.status),
                    'count': item.count
                } for item in status_stats
            ]
        }
    
    def _get_top_customers(self, user, limit=10):
        """获取TOP客户"""
        warehouse_filter = self._get_warehouse_filter(user)
        
        # 按入库量排序的客户
        customer_stats = db.session.query(
            InboundRecord.customer_name,
            func.count(InboundRecord.id).label('inbound_count'),
            func.sum(InboundRecord.pallet_count).label('total_pallets'),
            func.sum(InboundRecord.package_count).label('total_packages')
        )
        
        if warehouse_filter:
            customer_stats = customer_stats.filter(warehouse_filter)
        
        customer_stats = customer_stats.group_by(
            InboundRecord.customer_name
        ).order_by(
            func.sum(InboundRecord.package_count).desc()
        ).limit(limit).all()
        
        return [
            {
                'customer_name': item.customer_name,
                'inbound_count': item.inbound_count,
                'total_pallets': item.total_pallets or 0,
                'total_packages': item.total_packages or 0
            } for item in customer_stats
        ]
    
    def _get_system_alerts(self, user):
        """获取系统预警"""
        alerts = []
        
        # 库存预警 - 超过30天未出库的货物
        old_inventory = Inventory.query.filter(
            Inventory.last_updated < datetime.now() - timedelta(days=30)
        ).count()
        
        if old_inventory > 0:
            alerts.append({
                'type': 'warning',
                'title': '库存积压预警',
                'message': f'发现 {old_inventory} 票货物超过30天未出库',
                'action_url': '/inventory_list'
            })
        
        # 在途预警 - 超过预期到达时间的货物
        overdue_transit = TransitCargo.query.filter(
            and_(
                TransitCargo.status == 'in_transit',
                TransitCargo.expected_arrival_time < datetime.now()
            )
        ).count()
        
        if overdue_transit > 0:
            alerts.append({
                'type': 'danger',
                'title': '运输延误预警',
                'message': f'发现 {overdue_transit} 票货物运输延误',
                'action_url': '/transit/cargo_list'
            })
        
        return alerts
    
    def _get_warehouse_filter(self, user, model_name='InboundRecord'):
        """根据用户权限获取仓库过滤条件"""
        if user.is_super_admin():
            return None
        
        if user.warehouse_id:
            if model_name == 'InboundRecord':
                return InboundRecord.operated_warehouse_id == user.warehouse_id
            elif model_name == 'OutboundRecord':
                return OutboundRecord.operated_warehouse_id == user.warehouse_id
            elif model_name == 'Inventory':
                return Inventory.operated_warehouse_id == user.warehouse_id
        
        return None
    
    def _get_status_name(self, status):
        """获取状态中文名称"""
        status_map = {
            'in_transit': '运输中',
            'arrived': '已到达',
            'received': '已接收',
            'cancelled': '已取消'
        }
        return status_map.get(status, status)

    def _get_customer_overview(self, user):
        """获取客户概览"""
        warehouse_filter = self._get_warehouse_filter(user)

        # 客户总数
        customer_query = db.session.query(InboundRecord.customer_name).distinct()
        if warehouse_filter:
            customer_query = customer_query.filter(warehouse_filter)
        total_customers = customer_query.count()

        # 活跃客户（本月有业务）
        this_month_start = datetime.now().replace(day=1)
        active_customers = db.session.query(InboundRecord.customer_name).distinct().filter(
            InboundRecord.inbound_time >= this_month_start
        )
        if warehouse_filter:
            active_customers = active_customers.filter(warehouse_filter)
        active_count = active_customers.count()

        # 新客户（本月首次入库）
        new_customers = []
        for customer in active_customers.all():
            first_inbound = InboundRecord.query.filter_by(
                customer_name=customer.customer_name
            ).order_by(InboundRecord.inbound_time.asc()).first()

            if first_inbound and first_inbound.inbound_time >= this_month_start:
                new_customers.append(customer.customer_name)

        return {
            'total_customers': total_customers,
            'active_customers': active_count,
            'new_customers': len(new_customers),
            'customer_retention_rate': round((active_count / total_customers * 100) if total_customers > 0 else 0, 2)
        }

    def _get_top_routes(self, user, limit=10):
        """获取热门运输路线"""
        # 基于出库记录的目的地统计
        warehouse_filter = self._get_warehouse_filter(user, 'OutboundRecord')

        route_stats = db.session.query(
            OutboundRecord.operated_warehouse_id,
            OutboundRecord.destination,
            func.count(OutboundRecord.id).label('shipment_count'),
            func.sum(OutboundRecord.package_count).label('total_packages')
        )

        if warehouse_filter:
            route_stats = route_stats.filter(warehouse_filter)

        route_stats = route_stats.filter(
            OutboundRecord.destination.isnot(None),
            OutboundRecord.operated_warehouse_id.isnot(None)  # 过滤NULL值
        ).group_by(
            OutboundRecord.operated_warehouse_id,
            OutboundRecord.destination
        ).order_by(
            func.count(OutboundRecord.id).desc()
        ).limit(limit).all()

        return [
            {
                'source_warehouse': self.warehouse_names.get(item.operated_warehouse_id, f'仓库{item.operated_warehouse_id}'),
                'destination': item.destination,
                'shipment_count': item.shipment_count,
                'total_packages': item.total_packages or 0,
                'route_name': f"{self.warehouse_names.get(item.operated_warehouse_id, f'仓库{item.operated_warehouse_id}')} → {item.destination}"
            } for item in route_stats
        ]

    def _get_busy_warehouses(self, user, limit=4):
        """获取最繁忙的仓库"""
        today = datetime.now().date()
        week_start = today - timedelta(days=today.weekday())

        warehouse_filter = self._get_warehouse_filter(user)

        # 本周业务量统计
        inbound_stats = db.session.query(
            InboundRecord.operated_warehouse_id,
            func.count(InboundRecord.id).label('inbound_count')
        ).filter(
            InboundRecord.inbound_time >= week_start,
            InboundRecord.operated_warehouse_id.isnot(None)  # 过滤NULL值
        )

        if warehouse_filter:
            inbound_stats = inbound_stats.filter(warehouse_filter)

        inbound_stats = inbound_stats.group_by(
            InboundRecord.operated_warehouse_id
        ).subquery()

        outbound_stats = db.session.query(
            OutboundRecord.operated_warehouse_id,
            func.count(OutboundRecord.id).label('outbound_count')
        ).filter(
            OutboundRecord.outbound_time >= week_start,
            OutboundRecord.operated_warehouse_id.isnot(None)  # 过滤NULL值
        )

        if warehouse_filter:
            outbound_stats = outbound_stats.filter(warehouse_filter)

        outbound_stats = outbound_stats.group_by(
            OutboundRecord.operated_warehouse_id
        ).subquery()

        # 合并统计
        combined_stats = db.session.query(
            inbound_stats.c.operated_warehouse_id,
            func.coalesce(inbound_stats.c.inbound_count, 0).label('inbound'),
            func.coalesce(outbound_stats.c.outbound_count, 0).label('outbound')
        ).outerjoin(
            outbound_stats,
            inbound_stats.c.operated_warehouse_id == outbound_stats.c.operated_warehouse_id
        ).order_by(
            (func.coalesce(inbound_stats.c.inbound_count, 0) +
             func.coalesce(outbound_stats.c.outbound_count, 0)).desc()
        ).limit(limit).all()

        return [
            {
                'warehouse_id': item.operated_warehouse_id,
                'warehouse_name': self.warehouse_names.get(item.operated_warehouse_id, f'仓库{item.operated_warehouse_id}'),
                'inbound_count': item.inbound or 0,
                'outbound_count': item.outbound or 0,
                'total_operations': (item.inbound or 0) + (item.outbound or 0),
                'activity_level': self._get_activity_level((item.inbound or 0) + (item.outbound or 0))
            } for item in combined_stats
        ]

    def _get_activity_level(self, operations_count):
        """根据操作次数判断活跃度"""
        if operations_count >= 50:
            return '极高'
        elif operations_count >= 30:
            return '高'
        elif operations_count >= 15:
            return '中等'
        elif operations_count >= 5:
            return '低'
        else:
            return '极低'

    def _get_weekly_trend(self, user):
        """获取周趋势数据"""
        today = datetime.now().date()
        trend_data = []

        # 获取过去7天的数据
        for i in range(6, -1, -1):
            date = today - timedelta(days=i)
            daily_stats = self._get_daily_stats(date, user)
            trend_data.append({
                'date': date.strftime('%m-%d'),
                'weekday': ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][date.weekday()],
                'inbound_count': daily_stats['inbound']['count'],
                'outbound_count': daily_stats['outbound']['count'],
                'inbound_packages': daily_stats['inbound']['packages'],
                'outbound_packages': daily_stats['outbound']['packages']
            })

        return trend_data

    def _get_monthly_trend(self, user):
        """获取月趋势数据"""
        today = datetime.now().date()
        monthly_data = []

        # 获取过去6个月的数据
        for i in range(5, -1, -1):
            # 计算目标月份的第一天
            if today.month - i <= 0:
                target_month = today.month - i + 12
                target_year = today.year - 1
            else:
                target_month = today.month - i
                target_year = today.year

            month_start = datetime(target_year, target_month, 1).date()

            # 计算月末
            if target_month == 12:
                month_end = datetime(target_year + 1, 1, 1).date() - timedelta(days=1)
            else:
                month_end = datetime(target_year, target_month + 1, 1).date() - timedelta(days=1)

            # 确保不超过今天
            if month_end > today:
                month_end = today

            month_stats = self._get_period_stats(month_start, month_end, user)

            # 计算月度汇总
            total_inbound = sum(day['count'] for day in month_stats['inbound_daily'])
            total_outbound = sum(day['count'] for day in month_stats['outbound_daily'])
            total_inbound_packages = sum(day['packages'] for day in month_stats['inbound_daily'])
            total_outbound_packages = sum(day['packages'] for day in month_stats['outbound_daily'])

            monthly_data.append({
                'month': month_start.strftime('%Y-%m'),
                'month_name': month_start.strftime('%Y年%m月'),
                'inbound_count': total_inbound,
                'outbound_count': total_outbound,
                'inbound_packages': total_inbound_packages,
                'outbound_packages': total_outbound_packages,
                'net_flow': total_inbound_packages - total_outbound_packages
            })

        return monthly_data

    def _get_kpi_indicators(self, user):
        """获取KPI指标"""
        today = datetime.now().date()
        this_month_start = today.replace(day=1)
        last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)
        last_month_end = this_month_start - timedelta(days=1)

        # 本月数据
        current_month_stats = self._get_period_stats(this_month_start, today, user)
        current_inbound = sum(day['count'] for day in current_month_stats['inbound_daily'])
        current_outbound = sum(day['count'] for day in current_month_stats['outbound_daily'])
        current_packages_in = sum(day['packages'] for day in current_month_stats['inbound_daily'])
        current_packages_out = sum(day['packages'] for day in current_month_stats['outbound_daily'])

        # 上月数据
        last_month_stats = self._get_period_stats(last_month_start, last_month_end, user)
        last_inbound = sum(day['count'] for day in last_month_stats['inbound_daily'])
        last_outbound = sum(day['count'] for day in last_month_stats['outbound_daily'])
        last_packages_in = sum(day['packages'] for day in last_month_stats['inbound_daily'])
        last_packages_out = sum(day['packages'] for day in last_month_stats['outbound_daily'])

        # 计算增长率
        def calculate_growth_rate(current, last):
            if last == 0:
                return 100 if current > 0 else 0
            return round(((current - last) / last) * 100, 2)

        # 库存周转率（简化计算）
        inventory_stats = self._get_inventory_overview(user)
        current_inventory = inventory_stats['total']['packages']
        turnover_rate = round((current_packages_out / current_inventory) if current_inventory > 0 else 0, 2)

        # 平均处理时间（基于入库到出库的时间差）
        avg_processing_time = self._calculate_avg_processing_time(user)

        return {
            'inbound_growth': {
                'current': current_inbound,
                'last': last_inbound,
                'growth_rate': calculate_growth_rate(current_inbound, last_inbound),
                'trend': 'up' if current_inbound > last_inbound else 'down'
            },
            'outbound_growth': {
                'current': current_outbound,
                'last': last_outbound,
                'growth_rate': calculate_growth_rate(current_outbound, last_outbound),
                'trend': 'up' if current_outbound > last_outbound else 'down'
            },
            'package_throughput': {
                'inbound': current_packages_in,
                'outbound': current_packages_out,
                'net_flow': current_packages_in - current_packages_out,
                'efficiency': round((current_packages_out / current_packages_in * 100) if current_packages_in > 0 else 0, 2)
            },
            'inventory_turnover': {
                'rate': turnover_rate,
                'level': 'high' if turnover_rate > 0.5 else 'medium' if turnover_rate > 0.2 else 'low'
            },
            'processing_efficiency': {
                'avg_days': avg_processing_time,
                'performance': 'excellent' if avg_processing_time < 3 else 'good' if avg_processing_time < 7 else 'needs_improvement'
            }
        }

    def _calculate_avg_processing_time(self, user):
        """计算平均处理时间"""
        try:
            warehouse_filter = self._get_warehouse_filter(user, 'OutboundRecord')

            # 查询最近30天的出库记录，计算从入库到出库的平均时间
            thirty_days_ago = datetime.now() - timedelta(days=30)

            outbound_query = db.session.query(
                OutboundRecord.identification_code,
                OutboundRecord.outbound_time
            ).filter(
                OutboundRecord.outbound_time >= thirty_days_ago,
                OutboundRecord.identification_code.isnot(None)
            )

            if warehouse_filter:
                outbound_query = outbound_query.filter(warehouse_filter)

            outbound_records = outbound_query.all()

            total_days = 0
            valid_records = 0

            for record in outbound_records:
                # 查找对应的入库记录
                inbound_record = InboundRecord.query.filter_by(
                    identification_code=record.identification_code
                ).order_by(InboundRecord.inbound_time.desc()).first()

                if inbound_record and inbound_record.inbound_time:
                    days_diff = (record.outbound_time - inbound_record.inbound_time).days
                    if days_diff >= 0:  # 确保出库时间晚于入库时间
                        total_days += days_diff
                        valid_records += 1

            return round(total_days / valid_records, 1) if valid_records > 0 else 0
        except Exception:
            return 0

    def _get_realtime_stats(self, user):
        """获取实时统计数据"""
        today = datetime.now().date()
        today_start = datetime.combine(today, datetime.min.time())
        now = datetime.now()

        warehouse_filter = self._get_warehouse_filter(user)

        # 今日实时数据
        today_inbound_query = InboundRecord.query.filter(
            InboundRecord.inbound_time >= today_start
        )
        if warehouse_filter:
            today_inbound_query = today_inbound_query.filter(warehouse_filter)

        today_outbound_query = OutboundRecord.query.filter(
            OutboundRecord.outbound_time >= today_start
        )
        if warehouse_filter:
            today_outbound_query = today_outbound_query.filter(warehouse_filter)

        # 最近1小时的数据
        hour_ago = now - timedelta(hours=1)
        recent_inbound = today_inbound_query.filter(
            InboundRecord.inbound_time >= hour_ago
        ).count()

        recent_outbound = today_outbound_query.filter(
            OutboundRecord.outbound_time >= hour_ago
        ).count()

        # 当前在线用户数（简化统计）
        active_users = User.query.filter(
            User.last_login_at >= now - timedelta(hours=2)
        ).count()

        # 待处理任务数
        pending_tasks = self._get_pending_tasks_count(user)

        return {
            'current_time': now.strftime('%Y-%m-%d %H:%M:%S'),
            'today_total': {
                'inbound': today_inbound_query.count(),
                'outbound': today_outbound_query.count()
            },
            'recent_hour': {
                'inbound': recent_inbound,
                'outbound': recent_outbound
            },
            'system_status': {
                'active_users': active_users,
                'pending_tasks': pending_tasks,
                'system_load': 'normal'  # 可以后续接入真实的系统监控
            }
        }

    def _get_pending_tasks_count(self, user):
        """获取待处理任务数量"""
        try:
            warehouse_filter = self._get_warehouse_filter(user)

            # 待接收的在途货物
            pending_transit = TransitCargo.query.filter_by(status='arrived').count()

            # 超期库存（超过30天）
            thirty_days_ago = datetime.now() - timedelta(days=30)
            overdue_inventory = Inventory.query.filter(
                Inventory.last_updated < thirty_days_ago
            )
            if warehouse_filter:
                overdue_inventory = overdue_inventory.filter(warehouse_filter)
            overdue_count = overdue_inventory.count()

            return pending_transit + overdue_count
        except Exception:
            return 0

    def _get_weekly_trend(self, user):
        """获取周趋势数据"""
        today = datetime.now().date()
        week_dates = []

        # 获取过去7天的数据
        for i in range(6, -1, -1):
            date = today - timedelta(days=i)
            week_dates.append(date)

        trend_data = []
        for date in week_dates:
            daily_stats = self._get_daily_stats(date, user)
            trend_data.append({
                'date': date.strftime('%m-%d'),
                'weekday': ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][date.weekday()],
                'inbound_count': daily_stats['inbound']['count'],
                'outbound_count': daily_stats['outbound']['count'],
                'inbound_packages': daily_stats['inbound']['packages'],
                'outbound_packages': daily_stats['outbound']['packages']
            })

        return trend_data

    def _get_monthly_trend(self, user):
        """获取月趋势数据"""
        today = datetime.now().date()
        monthly_data = []

        # 获取过去6个月的数据
        for i in range(5, -1, -1):
            # 计算月份
            target_date = today.replace(day=1) - timedelta(days=i*30)
            month_start = target_date.replace(day=1)

            # 计算月末
            if month_start.month == 12:
                month_end = month_start.replace(year=month_start.year + 1, month=1) - timedelta(days=1)
            else:
                month_end = month_start.replace(month=month_start.month + 1) - timedelta(days=1)

            # 确保不超过今天
            if month_end > today:
                month_end = today

            month_stats = self._get_period_stats(month_start, month_end, user)

            # 计算月度汇总
            total_inbound = sum(day['count'] for day in month_stats['inbound_daily'])
            total_outbound = sum(day['count'] for day in month_stats['outbound_daily'])
            total_inbound_packages = sum(day['packages'] for day in month_stats['inbound_daily'])
            total_outbound_packages = sum(day['packages'] for day in month_stats['outbound_daily'])

            monthly_data.append({
                'month': month_start.strftime('%Y-%m'),
                'month_name': month_start.strftime('%Y年%m月'),
                'inbound_count': total_inbound,
                'outbound_count': total_outbound,
                'inbound_packages': total_inbound_packages,
                'outbound_packages': total_outbound_packages,
                'net_flow': total_inbound_packages - total_outbound_packages
            })

        return monthly_data

    def _get_kpi_indicators(self, user):
        """获取KPI指标"""
        today = datetime.now().date()
        this_month_start = today.replace(day=1)
        last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)
        last_month_end = this_month_start - timedelta(days=1)

        # 本月数据
        current_month_stats = self._get_period_stats(this_month_start, today, user)
        current_inbound = sum(day['count'] for day in current_month_stats['inbound_daily'])
        current_outbound = sum(day['count'] for day in current_month_stats['outbound_daily'])
        current_packages_in = sum(day['packages'] for day in current_month_stats['inbound_daily'])
        current_packages_out = sum(day['packages'] for day in current_month_stats['outbound_daily'])

        # 上月数据
        last_month_stats = self._get_period_stats(last_month_start, last_month_end, user)
        last_inbound = sum(day['count'] for day in last_month_stats['inbound_daily'])
        last_outbound = sum(day['count'] for day in last_month_stats['outbound_daily'])
        last_packages_in = sum(day['packages'] for day in last_month_stats['inbound_daily'])
        last_packages_out = sum(day['packages'] for day in last_month_stats['outbound_daily'])

        # 计算增长率
        def calculate_growth_rate(current, last):
            if last == 0:
                return 100 if current > 0 else 0
            return round(((current - last) / last) * 100, 2)

        # 库存周转率（简化计算）
        inventory_stats = self._get_inventory_overview(user)
        current_inventory = inventory_stats['total']['packages']
        turnover_rate = round((current_packages_out / current_inventory) if current_inventory > 0 else 0, 2)

        # 平均处理时间（基于入库到出库的时间差）
        avg_processing_time = self._calculate_avg_processing_time(user)

        return {
            'inbound_growth': {
                'current': current_inbound,
                'last': last_inbound,
                'growth_rate': calculate_growth_rate(current_inbound, last_inbound),
                'trend': 'up' if current_inbound > last_inbound else 'down'
            },
            'outbound_growth': {
                'current': current_outbound,
                'last': last_outbound,
                'growth_rate': calculate_growth_rate(current_outbound, last_outbound),
                'trend': 'up' if current_outbound > last_outbound else 'down'
            },
            'package_throughput': {
                'inbound': current_packages_in,
                'outbound': current_packages_out,
                'net_flow': current_packages_in - current_packages_out,
                'efficiency': round((current_packages_out / current_packages_in * 100) if current_packages_in > 0 else 0, 2)
            },
            'inventory_turnover': {
                'rate': turnover_rate,
                'level': 'high' if turnover_rate > 0.5 else 'medium' if turnover_rate > 0.2 else 'low'
            },
            'processing_efficiency': {
                'avg_days': avg_processing_time,
                'performance': 'excellent' if avg_processing_time < 3 else 'good' if avg_processing_time < 7 else 'needs_improvement'
            }
        }
