#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
缓存预热器
负责预计算和预热热点数据
"""

import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from flask import current_app
from flask_login import current_user

from .dual_cache_manager import get_dual_cache_manager
from app.models import Warehouse, User


class CacheWarmer:
    """缓存预热器"""
    
    def __init__(self):
        self.cache_manager = get_dual_cache_manager()
        self.is_warming = False
        self.warm_lock = threading.RLock()
    
    def warm_cache(self, cache_type: str = 'dashboard') -> Dict[str, Any]:
        """
        执行缓存预热
        
        Args:
            cache_type: 预热类型 ('dashboard', 'inventory', 'all')
        """
        if self.is_warming:
            return {'error': '预热正在进行中', 'warmed_items': 0}
        
        with self.warm_lock:
            self.is_warming = True
            start_time = time.time()
            result = {
                'warmed_items': 0,
                'errors': [],
                'duration': 0,
                'success_rate': 0
            }
            
            try:
                if cache_type == 'dashboard':
                    result = self._warm_dashboard_cache()
                elif cache_type == 'inventory':
                    result = self._warm_inventory_cache()
                elif cache_type == 'all':
                    dashboard_result = self._warm_dashboard_cache()
                    inventory_result = self._warm_inventory_cache()
                    
                    result = {
                        'warmed_items': dashboard_result['warmed_items'] + inventory_result['warmed_items'],
                        'errors': dashboard_result['errors'] + inventory_result['errors'],
                        'duration': time.time() - start_time,
                        'success_rate': 0
                    }
                else:
                    result['errors'].append(f'未知的预热类型: {cache_type}')
                
                # 计算成功率
                total_attempts = result['warmed_items'] + len(result['errors'])
                if total_attempts > 0:
                    result['success_rate'] = (result['warmed_items'] / total_attempts) * 100
                
                result['duration'] = time.time() - start_time
                
            except Exception as e:
                result['errors'].append(f'预热过程异常: {str(e)}')
            finally:
                self.is_warming = False
            
            return result
    
    def _warm_dashboard_cache(self) -> Dict[str, Any]:
        """预热仪表板缓存"""
        result = {'warmed_items': 0, 'errors': []}
        
        try:
            # 获取所有活跃仓库
            warehouses = Warehouse.query.filter_by(status='active').all()
            
            for warehouse in warehouses:
                try:
                    # 预热今日统计
                    today_data = self._calculate_today_stats(warehouse.id)
                    if today_data:
                        key = f"today_stats:{datetime.now().date()}:{warehouse.id}"
                        if self.cache_manager.set(key, today_data, cache_type='today_stats'):
                            result['warmed_items'] += 1
                    
                    # 预热库存概览
                    inventory_data = self._calculate_inventory_overview(warehouse.id)
                    if inventory_data:
                        key = f"inventory_overview:{warehouse.id}"
                        if self.cache_manager.set(key, inventory_data, cache_type='inventory_overview'):
                            result['warmed_items'] += 1
                    
                    # 预热仓库汇总
                    summary_data = self._calculate_warehouse_summary(warehouse.id)
                    if summary_data:
                        key = f"warehouse_summary:{warehouse.id}"
                        if self.cache_manager.set(key, summary_data, cache_type='warehouse_summary'):
                            result['warmed_items'] += 1
                    
                except Exception as e:
                    result['errors'].append(f'仓库{warehouse.warehouse_name}预热失败: {str(e)}')
            
            # 预热全局统计
            try:
                global_stats = self._calculate_global_stats()
                if global_stats:
                    key = "global_stats:today"
                    if self.cache_manager.set(key, global_stats, cache_type='dashboard_summary'):
                        result['warmed_items'] += 1
            except Exception as e:
                result['errors'].append(f'全局统计预热失败: {str(e)}')
            
        except Exception as e:
            result['errors'].append(f'仪表板预热异常: {str(e)}')
        
        return result
    
    def _warm_inventory_cache(self) -> Dict[str, Any]:
        """预热库存缓存"""
        result = {'warmed_items': 0, 'errors': []}
        
        try:
            from app.models import Inventory
            
            # 获取所有活跃仓库
            warehouses = Warehouse.query.filter_by(status='active').all()
            
            for warehouse in warehouses:
                try:
                    # 预热库存列表（分页）
                    for page in range(1, 4):  # 预热前3页
                        inventory_list = self._get_inventory_page(warehouse.id, page)
                        if inventory_list:
                            key = f"inventory_list:{warehouse.id}:page:{page}"
                            if self.cache_manager.set(key, inventory_list, cache_type='inventory_overview'):
                                result['warmed_items'] += 1
                    
                    # 预热库存统计
                    inventory_stats = self._calculate_inventory_stats(warehouse.id)
                    if inventory_stats:
                        key = f"inventory_stats:{warehouse.id}"
                        if self.cache_manager.set(key, inventory_stats, cache_type='inventory_overview'):
                            result['warmed_items'] += 1
                    
                except Exception as e:
                    result['errors'].append(f'仓库{warehouse.warehouse_name}库存预热失败: {str(e)}')
        
        except Exception as e:
            result['errors'].append(f'库存预热异常: {str(e)}')
        
        return result
    
    def _calculate_today_stats(self, warehouse_id: int) -> Optional[Dict[str, Any]]:
        """计算今日统计数据"""
        try:
            from app.models import InboundRecord, OutboundRecord
            from sqlalchemy import func
            
            today = datetime.now().date()
            
            # 入库统计
            inbound_stats = InboundRecord.query.filter(
                InboundRecord.operated_warehouse_id == warehouse_id,
                func.date(InboundRecord.inbound_time) == today
            ).with_entities(
                func.count(InboundRecord.id).label('count'),
                func.sum(InboundRecord.package_count).label('packages'),
                func.sum(InboundRecord.pallet_count).label('pallets')
            ).first()
            
            # 出库统计
            outbound_stats = OutboundRecord.query.filter(
                OutboundRecord.operated_warehouse_id == warehouse_id,
                func.date(OutboundRecord.outbound_time) == today
            ).with_entities(
                func.count(OutboundRecord.id).label('count'),
                func.sum(OutboundRecord.package_count).label('packages'),
                func.sum(OutboundRecord.pallet_count).label('pallets')
            ).first()
            
            return {
                'date': today.isoformat(),
                'warehouse_id': warehouse_id,
                'inbound': {
                    'count': inbound_stats.count or 0,
                    'packages': inbound_stats.packages or 0,
                    'pallets': inbound_stats.pallets or 0
                },
                'outbound': {
                    'count': outbound_stats.count or 0,
                    'packages': outbound_stats.packages or 0,
                    'pallets': outbound_stats.pallets or 0
                },
                'calculated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            if current_app:
                current_app.logger.error(f'计算今日统计失败: {e}')
            return None
    
    def _calculate_inventory_overview(self, warehouse_id: int) -> Optional[Dict[str, Any]]:
        """计算库存概览"""
        try:
            from app.models import Inventory
            from sqlalchemy import func
            
            # 库存统计
            inventory_stats = Inventory.query.filter(
                Inventory.operated_warehouse_id == warehouse_id
            ).with_entities(
                func.count(Inventory.id).label('total_items'),
                func.sum(Inventory.package_count).label('total_packages'),
                func.sum(Inventory.pallet_count).label('total_pallets'),
                func.sum(Inventory.weight).label('total_weight'),
                func.sum(Inventory.volume).label('total_volume')
            ).first()
            
            return {
                'warehouse_id': warehouse_id,
                'total_items': inventory_stats.total_items or 0,
                'total_packages': inventory_stats.total_packages or 0,
                'total_pallets': inventory_stats.total_pallets or 0,
                'total_weight': float(inventory_stats.total_weight or 0),
                'total_volume': float(inventory_stats.total_volume or 0),
                'calculated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            if current_app:
                current_app.logger.error(f'计算库存概览失败: {e}')
            return None
    
    def _calculate_warehouse_summary(self, warehouse_id: int) -> Optional[Dict[str, Any]]:
        """计算仓库汇总"""
        try:
            today_stats = self._calculate_today_stats(warehouse_id)
            inventory_overview = self._calculate_inventory_overview(warehouse_id)
            
            if not today_stats or not inventory_overview:
                return None
            
            return {
                'warehouse_id': warehouse_id,
                'today_stats': today_stats,
                'inventory_overview': inventory_overview,
                'calculated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            if current_app:
                current_app.logger.error(f'计算仓库汇总失败: {e}')
            return None
    
    def _calculate_global_stats(self) -> Optional[Dict[str, Any]]:
        """计算全局统计"""
        try:
            from app.models import InboundRecord, OutboundRecord, Inventory
            from sqlalchemy import func
            
            today = datetime.now().date()
            
            # 全局今日统计
            global_inbound = InboundRecord.query.filter(
                func.date(InboundRecord.inbound_time) == today
            ).with_entities(
                func.count(InboundRecord.id).label('count'),
                func.sum(InboundRecord.package_count).label('packages')
            ).first()
            
            global_outbound = OutboundRecord.query.filter(
                func.date(OutboundRecord.outbound_time) == today
            ).with_entities(
                func.count(OutboundRecord.id).label('count'),
                func.sum(OutboundRecord.package_count).label('packages')
            ).first()
            
            # 全局库存统计
            global_inventory = Inventory.query.with_entities(
                func.count(Inventory.id).label('total_items'),
                func.sum(Inventory.package_count).label('total_packages')
            ).first()
            
            return {
                'date': today.isoformat(),
                'global_inbound': {
                    'count': global_inbound.count or 0,
                    'packages': global_inbound.packages or 0
                },
                'global_outbound': {
                    'count': global_outbound.count or 0,
                    'packages': global_outbound.packages or 0
                },
                'global_inventory': {
                    'total_items': global_inventory.total_items or 0,
                    'total_packages': global_inventory.total_packages or 0
                },
                'calculated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            if current_app:
                current_app.logger.error(f'计算全局统计失败: {e}')
            return None
    
    def _get_inventory_page(self, warehouse_id: int, page: int, per_page: int = 20) -> Optional[Dict[str, Any]]:
        """获取库存分页数据"""
        try:
            from app.models import Inventory
            
            query = Inventory.query.filter(
                Inventory.operated_warehouse_id == warehouse_id
            ).order_by(Inventory.last_updated.desc())
            
            pagination = query.paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            return {
                'items': [item.to_dict() for item in pagination.items],
                'total': pagination.total,
                'page': page,
                'per_page': per_page,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev,
                'calculated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            if current_app:
                current_app.logger.error(f'获取库存分页失败: {e}')
            return None
    
    def _calculate_inventory_stats(self, warehouse_id: int) -> Optional[Dict[str, Any]]:
        """计算库存统计"""
        try:
            from app.models import Inventory
            from sqlalchemy import func
            
            # 基础统计
            basic_stats = Inventory.query.filter(
                Inventory.operated_warehouse_id == warehouse_id
            ).with_entities(
                func.count(Inventory.id).label('total_items'),
                func.sum(Inventory.package_count).label('total_packages'),
                func.sum(Inventory.pallet_count).label('total_pallets')
            ).first()
            
            # 按客户统计
            customer_stats = Inventory.query.filter(
                Inventory.operated_warehouse_id == warehouse_id
            ).with_entities(
                Inventory.customer_name,
                func.count(Inventory.id).label('items'),
                func.sum(Inventory.package_count).label('packages')
            ).group_by(Inventory.customer_name).limit(10).all()
            
            return {
                'warehouse_id': warehouse_id,
                'basic_stats': {
                    'total_items': basic_stats.total_items or 0,
                    'total_packages': basic_stats.total_packages or 0,
                    'total_pallets': basic_stats.total_pallets or 0
                },
                'top_customers': [
                    {
                        'customer_name': stat.customer_name,
                        'items': stat.items,
                        'packages': stat.packages
                    }
                    for stat in customer_stats
                ],
                'calculated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            if current_app:
                current_app.logger.error(f'计算库存统计失败: {e}')
            return None


# 全局缓存预热器实例
_cache_warmer = None

def get_cache_warmer() -> CacheWarmer:
    """获取全局缓存预热器实例"""
    global _cache_warmer
    if _cache_warmer is None:
        _cache_warmer = CacheWarmer()
    return _cache_warmer
