#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
仓库运营分析服务
提供运营效率对比、库存分析、时效分析、货物流向分析、容量利用率等功能
"""

from datetime import datetime, timedelta, date
from sqlalchemy import func, and_, or_, case, text, desc
from flask import current_app
from app import db
from app.models import (
    InboundRecord, OutboundRecord, Inventory, TransitCargo,
    ReceiveRecord, Warehouse, User
)
from collections import defaultdict

class WarehouseOperationsService:
    """仓库运营分析服务类"""

    def __init__(self):
        self.warehouse_names = {
            1: '平湖仓', 2: '昆山仓', 3: '成都仓', 4: '凭祥北投仓'
        }
        self.frontend_warehouses = [1, 2, 3]  # 前端仓
        self.backend_warehouses = [4]         # 后端仓

    def get_operational_efficiency_comparison(self, user):
        """获取运营效率对比分析"""
        try:
            accessible_warehouses = self._get_accessible_warehouses(user)
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=30)  # 最近30天

            efficiency_data = []

            for warehouse_id in accessible_warehouses:
                warehouse_name = self.warehouse_names.get(warehouse_id, f'仓库{warehouse_id}')

                # 入库效率
                inbound_stats = db.session.query(
                    func.count(InboundRecord.id).label('inbound_count'),
                    func.sum(InboundRecord.pallet_count).label('total_pallets'),
                    func.sum(InboundRecord.package_count).label('total_packages')
                ).filter(
                    and_(
                        InboundRecord.inbound_time >= start_date,
                        InboundRecord.inbound_time <= end_date,
                        InboundRecord.operated_warehouse_id == warehouse_id
                    )
                ).first()

                # 计算活跃天数（入库）
                inbound_dates = db.session.query(InboundRecord.inbound_time).filter(
                    and_(
                        InboundRecord.inbound_time >= start_date,
                        InboundRecord.inbound_time <= end_date,
                        InboundRecord.operated_warehouse_id == warehouse_id
                    )
                ).all()
                inbound_active_days = len(set(record.inbound_time.date() for record in inbound_dates if record.inbound_time))

                # 出库效率
                outbound_stats = db.session.query(
                    func.count(OutboundRecord.id).label('outbound_count'),
                    func.sum(OutboundRecord.pallet_count).label('total_pallets'),
                    func.sum(OutboundRecord.package_count).label('total_packages')
                ).filter(
                    and_(
                        OutboundRecord.outbound_time >= start_date,
                        OutboundRecord.outbound_time <= end_date,
                        OutboundRecord.operated_warehouse_id == warehouse_id
                    )
                ).first()

                # 计算活跃天数（出库）
                outbound_dates = db.session.query(OutboundRecord.outbound_time).filter(
                    and_(
                        OutboundRecord.outbound_time >= start_date,
                        OutboundRecord.outbound_time <= end_date,
                        OutboundRecord.operated_warehouse_id == warehouse_id
                    )
                ).all()
                outbound_active_days = len(set(record.outbound_time.date() for record in outbound_dates if record.outbound_time))

                # 当前库存
                current_inventory = db.session.query(
                    func.count(Inventory.id).label('inventory_count'),
                    func.sum(Inventory.pallet_count).label('inventory_pallets'),
                    func.sum(Inventory.package_count).label('inventory_packages')
                ).filter(Inventory.warehouse_id == warehouse_id).first()

                # 计算效率指标
                total_operations = (inbound_stats.inbound_count or 0) + (outbound_stats.outbound_count or 0)
                total_active_days = max(inbound_active_days, outbound_active_days, 1)
                daily_throughput = total_operations / total_active_days

                # 库存周转率（简化计算：月出库量/平均库存）
                monthly_outbound = outbound_stats.outbound_count or 0
                avg_inventory = current_inventory.inventory_count or 1
                turnover_rate = (monthly_outbound / avg_inventory) if avg_inventory > 0 else 0

                efficiency_data.append({
                    'warehouse_id': warehouse_id,
                    'warehouse_name': warehouse_name,
                    'inbound_count': inbound_stats.inbound_count or 0,
                    'outbound_count': outbound_stats.outbound_count or 0,
                    'total_operations': total_operations,
                    'daily_throughput': round(daily_throughput, 2),
                    'inventory_count': current_inventory.inventory_count or 0,
                    'turnover_rate': round(turnover_rate, 2),
                    'efficiency_score': round((daily_throughput * 0.6 + turnover_rate * 40), 1)
                })

            return {
                'efficiency_comparison': efficiency_data,
                'analysis_period': f"{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}",
                'best_performer': max(efficiency_data, key=lambda x: x['efficiency_score']) if efficiency_data else None
            }

        except Exception as e:
            current_app.logger.error(f"获取运营效率对比失败: {str(e)}")
            return {
                'efficiency_comparison': [],
                'analysis_period': '',
                'best_performer': None
            }

    def get_inventory_analysis(self, user):
        """获取库存分析"""
        try:
            accessible_warehouses = self._get_accessible_warehouses(user)
            
            inventory_analysis = []
            total_inventory = {'count': 0, 'pallets': 0, 'packages': 0}

            for warehouse_id in accessible_warehouses:
                warehouse_name = self.warehouse_names.get(warehouse_id, f'仓库{warehouse_id}')

                # 当前库存统计
                inventory_stats = db.session.query(
                    func.count(Inventory.id).label('count'),
                    func.sum(Inventory.pallet_count).label('pallets'),
                    func.sum(Inventory.package_count).label('packages'),
                    func.avg(Inventory.pallet_count).label('avg_pallets_per_item')
                ).filter(Inventory.warehouse_id == warehouse_id).first()

                # 库存停留时间分析
                current_date = datetime.now().date()
                
                # 计算库存停留天数分布
                inventory_records = db.session.query(Inventory.inbound_time).filter(
                    Inventory.warehouse_id == warehouse_id
                ).all()

                staying_distribution = {'1-7天': 0, '8-15天': 0, '16-30天': 0, '30天以上': 0}

                for record in inventory_records:
                    if record.inbound_time:
                        staying_days = (current_date - record.inbound_time.date()).days
                        if staying_days <= 7:
                            staying_distribution['1-7天'] += 1
                        elif staying_days <= 15:
                            staying_distribution['8-15天'] += 1
                        elif staying_days <= 30:
                            staying_distribution['16-30天'] += 1
                        else:
                            staying_distribution['30天以上'] += 1

                # 最近30天的进出库对比
                end_date = current_date
                start_date = end_date - timedelta(days=30)

                monthly_inbound = db.session.query(func.count(InboundRecord.id)).filter(
                    and_(
                        InboundRecord.inbound_time >= start_date,
                        InboundRecord.inbound_time <= end_date,
                        InboundRecord.operated_warehouse_id == warehouse_id
                    )
                ).scalar() or 0

                monthly_outbound = db.session.query(func.count(OutboundRecord.id)).filter(
                    and_(
                        OutboundRecord.outbound_time >= start_date,
                        OutboundRecord.outbound_time <= end_date,
                        OutboundRecord.operated_warehouse_id == warehouse_id
                    )
                ).scalar() or 0

                # 库存健康度评分
                inventory_count = inventory_stats.count or 0
                if inventory_count > 0:
                    # 基于停留时间的健康度
                    health_score = (
                        staying_distribution['1-7天'] * 1.0 +
                        staying_distribution['8-15天'] * 0.8 +
                        staying_distribution['16-30天'] * 0.6 +
                        staying_distribution['30天以上'] * 0.3
                    ) / inventory_count * 100
                else:
                    health_score = 100

                warehouse_data = {
                    'warehouse_id': warehouse_id,
                    'warehouse_name': warehouse_name,
                    'current_inventory': {
                        'count': inventory_count,
                        'pallets': inventory_stats.pallets or 0,
                        'packages': inventory_stats.packages or 0,
                        'avg_pallets_per_item': round(inventory_stats.avg_pallets_per_item or 0, 2)
                    },
                    'staying_distribution': staying_distribution,
                    'monthly_flow': {
                        'inbound': monthly_inbound,
                        'outbound': monthly_outbound,
                        'net_change': monthly_inbound - monthly_outbound
                    },
                    'health_score': round(health_score, 1)
                }

                inventory_analysis.append(warehouse_data)

                # 累计总库存
                total_inventory['count'] += inventory_count
                total_inventory['pallets'] += inventory_stats.pallets or 0
                total_inventory['packages'] += inventory_stats.packages or 0

            return {
                'warehouse_inventory': inventory_analysis,
                'total_inventory': total_inventory,
                'analysis_date': current_date.strftime('%Y-%m-%d')
            }

        except Exception as e:
            current_app.logger.error(f"获取库存分析失败: {str(e)}")
            return {
                'warehouse_inventory': [],
                'total_inventory': {'count': 0, 'pallets': 0, 'packages': 0},
                'analysis_date': ''
            }

    def get_time_efficiency_analysis(self, user):
        """获取时效分析"""
        try:
            accessible_warehouses = self._get_accessible_warehouses(user)
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=30)

            time_analysis = []

            for warehouse_id in accessible_warehouses:
                warehouse_name = self.warehouse_names.get(warehouse_id, f'仓库{warehouse_id}')

                # 分析库存中货物的停留时间
                inventory_records = db.session.query(
                    Inventory.inbound_time
                ).filter(
                    Inventory.warehouse_id == warehouse_id
                ).all()

                staying_days_list = []
                for record in inventory_records:
                    if record.inbound_time:
                        staying_days = (end_date - record.inbound_time.date()).days
                        staying_days_list.append(staying_days)

                if staying_days_list:
                    avg_staying_time = sum(staying_days_list) / len(staying_days_list)
                    max_staying_time = max(staying_days_list)
                    min_staying_time = min(staying_days_list)

                    # 计算时效等级分布
                    fast_count = len([d for d in staying_days_list if d <= 7])
                    normal_count = len([d for d in staying_days_list if 7 < d <= 15])
                    slow_count = len([d for d in staying_days_list if d > 15])

                    time_efficiency_score = (fast_count * 100 + normal_count * 70 + slow_count * 30) / len(staying_days_list)
                else:
                    avg_staying_time = 0
                    max_staying_time = 0
                    min_staying_time = 0
                    fast_count = normal_count = slow_count = 0
                    time_efficiency_score = 100

                time_analysis.append({
                    'warehouse_id': warehouse_id,
                    'warehouse_name': warehouse_name,
                    'avg_staying_time': round(avg_staying_time, 1),
                    'max_staying_time': max_staying_time,
                    'min_staying_time': min_staying_time,
                    'time_distribution': {
                        'fast': fast_count,      # ≤7天
                        'normal': normal_count,  # 8-15天
                        'slow': slow_count       # >15天
                    },
                    'efficiency_score': round(time_efficiency_score, 1)
                })

            return {
                'time_analysis': time_analysis,
                'analysis_period': f"截至 {end_date.strftime('%Y-%m-%d')}",
                'best_efficiency': max(time_analysis, key=lambda x: x['efficiency_score']) if time_analysis else None
            }

        except Exception as e:
            current_app.logger.error(f"获取时效分析失败: {str(e)}")
            return {
                'time_analysis': [],
                'analysis_period': '',
                'best_efficiency': None
            }

    def get_cargo_flow_analysis(self, user):
        """获取货物流向分析"""
        try:
            accessible_warehouses = self._get_accessible_warehouses(user)
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=30)

            flow_data = {
                'warehouse_flows': [],
                'total_flows': {
                    'inbound_total': 0,
                    'outbound_total': 0,
                    'inter_warehouse_transfer': 0
                }
            }

            for warehouse_id in accessible_warehouses:
                warehouse_name = self.warehouse_names.get(warehouse_id, f'仓库{warehouse_id}')

                # 入库流向分析
                inbound_sources = db.session.query(
                    InboundRecord.delivery_plate_number,
                    func.count(InboundRecord.id).label('count'),
                    func.sum(InboundRecord.pallet_count).label('pallets')
                ).filter(
                    and_(
                        InboundRecord.inbound_time >= start_date,
                        InboundRecord.inbound_time <= end_date,
                        InboundRecord.operated_warehouse_id == warehouse_id,
                        InboundRecord.delivery_plate_number.isnot(None)
                    )
                ).group_by(InboundRecord.delivery_plate_number).limit(10).all()

                # 出库流向分析
                outbound_destinations = db.session.query(
                    OutboundRecord.destination,
                    func.count(OutboundRecord.id).label('count'),
                    func.sum(OutboundRecord.pallet_count).label('pallets')
                ).filter(
                    and_(
                        OutboundRecord.outbound_time >= start_date,
                        OutboundRecord.outbound_time <= end_date,
                        OutboundRecord.operated_warehouse_id == warehouse_id,
                        OutboundRecord.destination.isnot(None)
                    )
                ).group_by(OutboundRecord.destination).limit(10).all()

                # 仓库间流转（出库到其他仓库）
                inter_warehouse = db.session.query(
                    OutboundRecord.destination_warehouse_id,
                    func.count(OutboundRecord.id).label('count')
                ).filter(
                    and_(
                        OutboundRecord.outbound_time >= start_date,
                        OutboundRecord.outbound_time <= end_date,
                        OutboundRecord.operated_warehouse_id == warehouse_id,
                        OutboundRecord.destination_warehouse_id.isnot(None),
                        OutboundRecord.destination_warehouse_id != warehouse_id
                    )
                ).group_by(OutboundRecord.destination_warehouse_id).all()

                # 总计数据
                total_inbound = db.session.query(func.count(InboundRecord.id)).filter(
                    and_(
                        InboundRecord.inbound_time >= start_date,
                        InboundRecord.inbound_time <= end_date,
                        InboundRecord.operated_warehouse_id == warehouse_id
                    )
                ).scalar() or 0

                total_outbound = db.session.query(func.count(OutboundRecord.id)).filter(
                    and_(
                        OutboundRecord.outbound_time >= start_date,
                        OutboundRecord.outbound_time <= end_date,
                        OutboundRecord.operated_warehouse_id == warehouse_id
                    )
                ).scalar() or 0

                warehouse_flow = {
                    'warehouse_id': warehouse_id,
                    'warehouse_name': warehouse_name,
                    'inbound_sources': [
                        {
                            'source': source.delivery_plate_number or '未知来源',
                            'count': source.count,
                            'pallets': source.pallets or 0
                        } for source in inbound_sources
                    ],
                    'outbound_destinations': [
                        {
                            'destination': dest.destination or '未知目的地',
                            'count': dest.count,
                            'pallets': dest.pallets or 0
                        } for dest in outbound_destinations
                    ],
                    'inter_warehouse_transfers': [
                        {
                            'destination_warehouse_id': transfer.destination_warehouse_id,
                            'destination_warehouse_name': self.warehouse_names.get(transfer.destination_warehouse_id, f'仓库{transfer.destination_warehouse_id}'),
                            'count': transfer.count
                        } for transfer in inter_warehouse
                    ],
                    'totals': {
                        'inbound': total_inbound,
                        'outbound': total_outbound,
                        'net_flow': total_inbound - total_outbound
                    }
                }

                flow_data['warehouse_flows'].append(warehouse_flow)
                flow_data['total_flows']['inbound_total'] += total_inbound
                flow_data['total_flows']['outbound_total'] += total_outbound
                flow_data['total_flows']['inter_warehouse_transfer'] += sum(t['count'] for t in warehouse_flow['inter_warehouse_transfers'])

            flow_data['analysis_period'] = f"{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}"

            return flow_data

        except Exception as e:
            current_app.logger.error(f"获取货物流向分析失败: {str(e)}")
            return {
                'warehouse_flows': [],
                'total_flows': {
                    'inbound_total': 0,
                    'outbound_total': 0,
                    'inter_warehouse_transfer': 0
                },
                'analysis_period': ''
            }

    def get_capacity_utilization_analysis(self, user):
        """获取容量利用率分析"""
        try:
            accessible_warehouses = self._get_accessible_warehouses(user)

            # 假设的仓库容量（实际应该从配置或数据库获取）
            warehouse_capacities = {
                1: {'max_pallets': 1000, 'max_packages': 50000},  # 平湖仓
                2: {'max_pallets': 800, 'max_packages': 40000},   # 昆山仓
                3: {'max_pallets': 600, 'max_packages': 30000},   # 成都仓
                4: {'max_pallets': 1200, 'max_packages': 60000}   # 凭祥北投仓
            }

            utilization_data = []

            for warehouse_id in accessible_warehouses:
                warehouse_name = self.warehouse_names.get(warehouse_id, f'仓库{warehouse_id}')
                capacity = warehouse_capacities.get(warehouse_id, {'max_pallets': 1000, 'max_packages': 50000})

                # 当前库存
                current_inventory = db.session.query(
                    func.count(Inventory.id).label('count'),
                    func.sum(Inventory.pallet_count).label('pallets'),
                    func.sum(Inventory.package_count).label('packages')
                ).filter(Inventory.warehouse_id == warehouse_id).first()

                current_pallets = current_inventory.pallets or 0
                current_packages = current_inventory.packages or 0

                # 计算利用率
                pallet_utilization = (current_pallets / capacity['max_pallets']) * 100 if capacity['max_pallets'] > 0 else 0
                package_utilization = (current_packages / capacity['max_packages']) * 100 if capacity['max_packages'] > 0 else 0

                # 综合利用率（取较高值）
                overall_utilization = max(pallet_utilization, package_utilization)

                # 利用率状态
                if overall_utilization >= 90:
                    status = '接近满载'
                    status_color = 'danger'
                elif overall_utilization >= 70:
                    status = '高利用率'
                    status_color = 'warning'
                elif overall_utilization >= 40:
                    status = '正常'
                    status_color = 'success'
                else:
                    status = '低利用率'
                    status_color = 'info'

                # 最近7天的利用率趋势（简化计算）
                end_date = datetime.now().date()
                weekly_trend = []

                for i in range(7):
                    check_date = end_date - timedelta(days=i)

                    # 计算该日的库存变化（简化：基于当日进出库）
                    next_date = check_date + timedelta(days=1)

                    daily_inbound = db.session.query(func.sum(InboundRecord.pallet_count)).filter(
                        and_(
                            InboundRecord.inbound_time >= check_date,
                            InboundRecord.inbound_time < next_date,
                            InboundRecord.operated_warehouse_id == warehouse_id
                        )
                    ).scalar() or 0

                    daily_outbound = db.session.query(func.sum(OutboundRecord.pallet_count)).filter(
                        and_(
                            OutboundRecord.outbound_time >= check_date,
                            OutboundRecord.outbound_time < next_date,
                            OutboundRecord.operated_warehouse_id == warehouse_id
                        )
                    ).scalar() or 0

                    # 估算当日利用率（简化计算）
                    estimated_pallets = max(0, current_pallets - (daily_outbound - daily_inbound) * (i + 1))
                    estimated_utilization = (estimated_pallets / capacity['max_pallets']) * 100 if capacity['max_pallets'] > 0 else 0

                    weekly_trend.append({
                        'date': check_date.strftime('%Y-%m-%d'),
                        'utilization': round(estimated_utilization, 1)
                    })

                weekly_trend.reverse()  # 按时间正序

                utilization_data.append({
                    'warehouse_id': warehouse_id,
                    'warehouse_name': warehouse_name,
                    'capacity': capacity,
                    'current_inventory': {
                        'count': current_inventory.count or 0,
                        'pallets': current_pallets,
                        'packages': current_packages
                    },
                    'utilization': {
                        'pallet_utilization': round(pallet_utilization, 1),
                        'package_utilization': round(package_utilization, 1),
                        'overall_utilization': round(overall_utilization, 1)
                    },
                    'status': status,
                    'status_color': status_color,
                    'weekly_trend': weekly_trend,
                    'available_capacity': {
                        'pallets': capacity['max_pallets'] - current_pallets,
                        'packages': capacity['max_packages'] - current_packages
                    }
                })

            return {
                'utilization_analysis': utilization_data,
                'analysis_date': datetime.now().date().strftime('%Y-%m-%d'),
                'overall_status': self._calculate_overall_capacity_status(utilization_data)
            }

        except Exception as e:
            current_app.logger.error(f"获取容量利用率分析失败: {str(e)}")
            return {
                'utilization_analysis': [],
                'analysis_date': '',
                'overall_status': {'status': '数据异常', 'color': 'secondary'}
            }

    def _calculate_overall_capacity_status(self, utilization_data):
        """计算整体容量状态"""
        if not utilization_data:
            return {'status': '无数据', 'color': 'secondary'}

        avg_utilization = sum(item['utilization']['overall_utilization'] for item in utilization_data) / len(utilization_data)

        if avg_utilization >= 85:
            return {'status': '容量紧张', 'color': 'danger'}
        elif avg_utilization >= 70:
            return {'status': '容量较高', 'color': 'warning'}
        elif avg_utilization >= 40:
            return {'status': '容量正常', 'color': 'success'}
        else:
            return {'status': '容量充足', 'color': 'info'}

    def _get_accessible_warehouses(self, user):
        """获取用户可访问的仓库列表"""
        if user.is_super_admin():
            return [1, 2, 3, 4]  # 管理员可以访问所有仓库
        else:
            # 普通用户只能访问自己的仓库
            return [user.warehouse_id] if user.warehouse_id else []
