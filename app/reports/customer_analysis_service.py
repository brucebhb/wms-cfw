#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
客户业务分析服务
提供客户货量排行、客户活跃度分析、客户价值分析等功能
"""

from datetime import datetime, timedelta, date
from sqlalchemy import func, and_, or_, case, text, desc
from flask import current_app
from app import db
from app.models import (
    InboundRecord, OutboundRecord, Inventory, TransitCargo,
    ReceiveRecord, Warehouse, User
)

class CustomerAnalysisService:
    """客户业务分析服务类"""

    def __init__(self):
        self.warehouse_names = {
            1: '平湖仓', 2: '昆山仓', 3: '成都仓', 4: '凭祥北投仓'
        }
        self.frontend_warehouses = [1, 2, 3]  # 前端仓
        self.backend_warehouses = [4]         # 后端仓

    def get_customer_ranking(self, user, period='month', limit=10):
        """获取客户货量排行榜"""
        try:
            # 计算时间范围
            end_date = datetime.now().date()
            if period == 'week':
                start_date = end_date - timedelta(days=7)
            elif period == 'month':
                start_date = end_date - timedelta(days=30)
            elif period == 'quarter':
                start_date = end_date - timedelta(days=90)
            elif period == 'year':
                start_date = end_date - timedelta(days=365)
            else:
                start_date = end_date - timedelta(days=30)

            # 获取用户可访问的仓库
            accessible_warehouses = self._get_accessible_warehouses(user)

            # 查询入库数据
            inbound_query = db.session.query(
                InboundRecord.customer_name,
                func.count(InboundRecord.id).label('inbound_count'),
                func.sum(InboundRecord.pallet_count).label('inbound_pallets'),
                func.sum(InboundRecord.package_count).label('inbound_packages'),
                func.sum(InboundRecord.weight).label('inbound_weight'),
                func.sum(InboundRecord.volume).label('inbound_volume')
            ).filter(
                and_(
                    InboundRecord.inbound_time >= start_date,
                    InboundRecord.inbound_time <= end_date,
                    InboundRecord.operated_warehouse_id.in_(accessible_warehouses)
                )
            ).group_by(InboundRecord.customer_name)

            # 查询出库数据
            outbound_query = db.session.query(
                OutboundRecord.customer_name,
                func.count(OutboundRecord.id).label('outbound_count'),
                func.sum(OutboundRecord.pallet_count).label('outbound_pallets'),
                func.sum(OutboundRecord.package_count).label('outbound_packages'),
                func.sum(OutboundRecord.weight).label('outbound_weight'),
                func.sum(OutboundRecord.volume).label('outbound_volume')
            ).filter(
                and_(
                    OutboundRecord.outbound_time >= start_date,
                    OutboundRecord.outbound_time <= end_date,
                    OutboundRecord.operated_warehouse_id.in_(accessible_warehouses)
                )
            ).group_by(OutboundRecord.customer_name)

            # 合并数据
            customer_data = {}
            
            # 处理入库数据
            for row in inbound_query.all():
                customer_data[row.customer_name] = {
                    'customer_name': row.customer_name,
                    'inbound_count': row.inbound_count or 0,
                    'inbound_pallets': row.inbound_pallets or 0,
                    'inbound_packages': row.inbound_packages or 0,
                    'inbound_weight': row.inbound_weight or 0,
                    'inbound_volume': row.inbound_volume or 0,
                    'outbound_count': 0,
                    'outbound_pallets': 0,
                    'outbound_packages': 0,
                    'outbound_weight': 0,
                    'outbound_volume': 0
                }

            # 处理出库数据
            for row in outbound_query.all():
                if row.customer_name in customer_data:
                    customer_data[row.customer_name].update({
                        'outbound_count': row.outbound_count or 0,
                        'outbound_pallets': row.outbound_pallets or 0,
                        'outbound_packages': row.outbound_packages or 0,
                        'outbound_weight': row.outbound_weight or 0,
                        'outbound_volume': row.outbound_volume or 0
                    })
                else:
                    customer_data[row.customer_name] = {
                        'customer_name': row.customer_name,
                        'inbound_count': 0,
                        'inbound_pallets': 0,
                        'inbound_packages': 0,
                        'inbound_weight': 0,
                        'inbound_volume': 0,
                        'outbound_count': row.outbound_count or 0,
                        'outbound_pallets': row.outbound_pallets or 0,
                        'outbound_packages': row.outbound_packages or 0,
                        'outbound_weight': row.outbound_weight or 0,
                        'outbound_volume': row.outbound_volume or 0
                    }

            # 计算总货量并排序
            for customer in customer_data.values():
                customer['total_count'] = customer['inbound_count'] + customer['outbound_count']
                customer['total_pallets'] = customer['inbound_pallets'] + customer['outbound_pallets']
                customer['total_packages'] = customer['inbound_packages'] + customer['outbound_packages']
                customer['total_weight'] = customer['inbound_weight'] + customer['outbound_weight']
                customer['total_volume'] = customer['inbound_volume'] + customer['outbound_volume']

            # 按总票数排序并取前N名
            ranking = sorted(customer_data.values(), key=lambda x: x['total_count'], reverse=True)[:limit]

            return {
                'period': period,
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'ranking': ranking,
                'total_customers': len(customer_data)
            }

        except Exception as e:
            current_app.logger.error(f"获取客户排行榜失败: {str(e)}")
            return {
                'period': period,
                'start_date': '',
                'end_date': '',
                'ranking': [],
                'total_customers': 0
            }

    def get_customer_activity_analysis(self, user):
        """获取客户活跃度分析"""
        try:
            today = datetime.now().date()
            accessible_warehouses = self._get_accessible_warehouses(user)

            # 最近7天活跃客户
            week_ago = today - timedelta(days=7)
            recent_active = self._get_active_customers_in_period(week_ago, today, accessible_warehouses)

            # 最近30天活跃客户
            month_ago = today - timedelta(days=30)
            month_active = self._get_active_customers_in_period(month_ago, today, accessible_warehouses)

            # 沉睡客户（30天前有业务，但最近30天没有业务）
            three_months_ago = today - timedelta(days=90)
            old_customers = self._get_active_customers_in_period(three_months_ago, month_ago, accessible_warehouses)
            sleeping_customers = [c for c in old_customers if c not in month_active]

            # 新客户（最近30天首次出现）
            new_customers = []
            for customer in month_active:
                # 检查该客户在30天前是否有记录
                old_records = db.session.query(InboundRecord).filter(
                    and_(
                        InboundRecord.customer_name == customer,
                        InboundRecord.inbound_time < month_ago,
                        InboundRecord.operated_warehouse_id.in_(accessible_warehouses)
                    )
                ).first()
                
                if not old_records:
                    # 也检查出库记录
                    old_outbound = db.session.query(OutboundRecord).filter(
                        and_(
                            OutboundRecord.customer_name == customer,
                            OutboundRecord.outbound_time < month_ago,
                            OutboundRecord.operated_warehouse_id.in_(accessible_warehouses)
                        )
                    ).first()
                    
                    if not old_outbound:
                        new_customers.append(customer)

            return {
                'recent_active_count': len(recent_active),
                'recent_active_customers': recent_active[:10],  # 只返回前10个
                'month_active_count': len(month_active),
                'sleeping_count': len(sleeping_customers),
                'sleeping_customers': sleeping_customers[:10],  # 只返回前10个
                'new_customers_count': len(new_customers),
                'new_customers': new_customers[:10]  # 只返回前10个
            }

        except Exception as e:
            current_app.logger.error(f"获取客户活跃度分析失败: {str(e)}")
            return {
                'recent_active_count': 0,
                'recent_active_customers': [],
                'month_active_count': 0,
                'sleeping_count': 0,
                'sleeping_customers': [],
                'new_customers_count': 0,
                'new_customers': []
            }

    def _get_accessible_warehouses(self, user):
        """获取用户可访问的仓库列表"""
        if user.is_super_admin():
            return [1, 2, 3, 4]  # 管理员可以访问所有仓库
        else:
            # 普通用户只能访问自己的仓库
            return [user.warehouse_id] if user.warehouse_id else []

    def _get_active_customers_in_period(self, start_date, end_date, accessible_warehouses):
        """获取指定时间段内的活跃客户"""
        # 入库客户
        inbound_customers = db.session.query(InboundRecord.customer_name.distinct()).filter(
            and_(
                InboundRecord.inbound_time >= start_date,
                InboundRecord.inbound_time <= end_date,
                InboundRecord.operated_warehouse_id.in_(accessible_warehouses)
            )
        ).all()

        # 出库客户
        outbound_customers = db.session.query(OutboundRecord.customer_name.distinct()).filter(
            and_(
                OutboundRecord.outbound_time >= start_date,
                OutboundRecord.outbound_time <= end_date,
                OutboundRecord.operated_warehouse_id.in_(accessible_warehouses)
            )
        ).all()

        # 合并去重
        all_customers = set()
        for customer in inbound_customers:
            all_customers.add(customer[0])
        for customer in outbound_customers:
            all_customers.add(customer[0])

        return list(all_customers)

    def get_customer_value_analysis(self, user, limit=20):
        """获取客户价值分析"""
        try:
            # 计算最近3个月的数据
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=90)
            accessible_warehouses = self._get_accessible_warehouses(user)

            # 查询客户的综合数据
            customer_stats = {}

            # 入库数据
            inbound_data = db.session.query(
                InboundRecord.customer_name,
                func.count(InboundRecord.id).label('inbound_frequency'),
                func.sum(InboundRecord.pallet_count).label('total_pallets'),
                func.sum(InboundRecord.package_count).label('total_packages'),
                func.avg(InboundRecord.pallet_count).label('avg_pallets_per_shipment'),
                func.max(InboundRecord.inbound_time).label('last_inbound_time')
            ).filter(
                and_(
                    InboundRecord.inbound_time >= start_date,
                    InboundRecord.inbound_time <= end_date,
                    InboundRecord.operated_warehouse_id.in_(accessible_warehouses)
                )
            ).group_by(InboundRecord.customer_name).all()

            for row in inbound_data:
                customer_stats[row.customer_name] = {
                    'customer_name': row.customer_name,
                    'inbound_frequency': row.inbound_frequency or 0,
                    'total_pallets': row.total_pallets or 0,
                    'total_packages': row.total_packages or 0,
                    'avg_pallets_per_shipment': float(row.avg_pallets_per_shipment or 0),
                    'last_inbound_time': row.last_inbound_time,
                    'outbound_frequency': 0,
                    'last_outbound_time': None
                }

            # 出库数据
            outbound_data = db.session.query(
                OutboundRecord.customer_name,
                func.count(OutboundRecord.id).label('outbound_frequency'),
                func.max(OutboundRecord.outbound_time).label('last_outbound_time')
            ).filter(
                and_(
                    OutboundRecord.outbound_time >= start_date,
                    OutboundRecord.outbound_time <= end_date,
                    OutboundRecord.operated_warehouse_id.in_(accessible_warehouses)
                )
            ).group_by(OutboundRecord.customer_name).all()

            for row in outbound_data:
                if row.customer_name in customer_stats:
                    customer_stats[row.customer_name]['outbound_frequency'] = row.outbound_frequency or 0
                    customer_stats[row.customer_name]['last_outbound_time'] = row.last_outbound_time
                else:
                    customer_stats[row.customer_name] = {
                        'customer_name': row.customer_name,
                        'inbound_frequency': 0,
                        'total_pallets': 0,
                        'total_packages': 0,
                        'avg_pallets_per_shipment': 0,
                        'last_inbound_time': None,
                        'outbound_frequency': row.outbound_frequency or 0,
                        'last_outbound_time': row.last_outbound_time
                    }

            # 计算客户价值评分
            for customer in customer_stats.values():
                # 业务频率评分 (40%)
                total_frequency = customer['inbound_frequency'] + customer['outbound_frequency']
                frequency_score = min(total_frequency * 2, 40)  # 最高40分

                # 货量规模评分 (30%)
                volume_score = min(customer['total_pallets'] * 0.5, 30)  # 最高30分

                # 业务稳定性评分 (20%)
                last_activity = customer['last_inbound_time'] or customer['last_outbound_time']
                if last_activity:
                    days_since_last = (end_date - last_activity.date()).days
                    stability_score = max(20 - days_since_last * 0.5, 0)  # 最高20分
                else:
                    stability_score = 0

                # 平均单次货量评分 (10%)
                avg_score = min(customer['avg_pallets_per_shipment'] * 0.2, 10)  # 最高10分

                customer['value_score'] = frequency_score + volume_score + stability_score + avg_score
                customer['last_activity_days'] = (end_date - last_activity.date()).days if last_activity else 999

            # 按价值评分排序
            high_value_customers = sorted(customer_stats.values(), key=lambda x: x['value_score'], reverse=True)[:limit]

            return {
                'high_value_customers': high_value_customers,
                'analysis_period': f"{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}",
                'total_analyzed': len(customer_stats)
            }

        except Exception as e:
            current_app.logger.error(f"获取客户价值分析失败: {str(e)}")
            return {
                'high_value_customers': [],
                'analysis_period': '',
                'total_analyzed': 0
            }

    def get_customer_growth_trends(self, user):
        """获取客户增长趋势"""
        try:
            accessible_warehouses = self._get_accessible_warehouses(user)
            end_date = datetime.now().date()

            # 获取最近12个月的数据
            monthly_data = []
            for i in range(12):
                month_start = end_date.replace(day=1) - timedelta(days=30*i)
                month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)

                # 该月活跃客户数
                active_customers = self._get_active_customers_in_period(month_start, month_end, accessible_warehouses)

                # 该月新客户数（在该月首次出现的客户）
                new_customers = []
                for customer in active_customers:
                    # 检查该客户在该月之前是否有记录
                    old_inbound = db.session.query(InboundRecord).filter(
                        and_(
                            InboundRecord.customer_name == customer,
                            InboundRecord.inbound_time < month_start,
                            InboundRecord.operated_warehouse_id.in_(accessible_warehouses)
                        )
                    ).first()

                    old_outbound = db.session.query(OutboundRecord).filter(
                        and_(
                            OutboundRecord.customer_name == customer,
                            OutboundRecord.outbound_time < month_start,
                            OutboundRecord.operated_warehouse_id.in_(accessible_warehouses)
                        )
                    ).first()

                    if not old_inbound and not old_outbound:
                        new_customers.append(customer)

                monthly_data.append({
                    'month': month_start.strftime('%Y-%m'),
                    'active_customers': len(active_customers),
                    'new_customers': len(new_customers)
                })

            # 按时间正序排列
            monthly_data.reverse()

            return {
                'monthly_trends': monthly_data,
                'period': f"最近12个月 ({monthly_data[0]['month']} 至 {monthly_data[-1]['month']})"
            }

        except Exception as e:
            current_app.logger.error(f"获取客户增长趋势失败: {str(e)}")
            return {
                'monthly_trends': [],
                'period': ''
            }

    def get_customer_distribution_analysis(self, user):
        """获取客户分布分析"""
        try:
            accessible_warehouses = self._get_accessible_warehouses(user)
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=90)  # 最近3个月

            # 按仓库分布
            warehouse_distribution = {}
            for warehouse_id in accessible_warehouses:
                warehouse_name = self.warehouse_names.get(warehouse_id, f'仓库{warehouse_id}')

                # 该仓库的客户
                inbound_customers = db.session.query(InboundRecord.customer_name.distinct()).filter(
                    and_(
                        InboundRecord.inbound_time >= start_date,
                        InboundRecord.inbound_time <= end_date,
                        InboundRecord.operated_warehouse_id == warehouse_id
                    )
                ).all()

                outbound_customers = db.session.query(OutboundRecord.customer_name.distinct()).filter(
                    and_(
                        OutboundRecord.outbound_time >= start_date,
                        OutboundRecord.outbound_time <= end_date,
                        OutboundRecord.operated_warehouse_id == warehouse_id
                    )
                ).all()

                # 合并客户
                customers = set()
                for customer in inbound_customers:
                    customers.add(customer[0])
                for customer in outbound_customers:
                    customers.add(customer[0])

                warehouse_distribution[warehouse_name] = {
                    'warehouse_id': warehouse_id,
                    'warehouse_name': warehouse_name,
                    'customer_count': len(customers),
                    'customers': list(customers)[:10]  # 只返回前10个客户名
                }

            # 按业务类型分布
            business_type_distribution = {
                'inbound_only': [],  # 只有入库业务
                'outbound_only': [], # 只有出库业务
                'both': []           # 既有入库又有出库
            }

            # 获取所有客户
            all_inbound_customers = set()
            all_outbound_customers = set()

            inbound_customers = db.session.query(InboundRecord.customer_name.distinct()).filter(
                and_(
                    InboundRecord.inbound_time >= start_date,
                    InboundRecord.inbound_time <= end_date,
                    InboundRecord.operated_warehouse_id.in_(accessible_warehouses)
                )
            ).all()

            outbound_customers = db.session.query(OutboundRecord.customer_name.distinct()).filter(
                and_(
                    OutboundRecord.outbound_time >= start_date,
                    OutboundRecord.outbound_time <= end_date,
                    OutboundRecord.operated_warehouse_id.in_(accessible_warehouses)
                )
            ).all()

            for customer in inbound_customers:
                all_inbound_customers.add(customer[0])
            for customer in outbound_customers:
                all_outbound_customers.add(customer[0])

            # 分类客户
            for customer in all_inbound_customers:
                if customer in all_outbound_customers:
                    business_type_distribution['both'].append(customer)
                else:
                    business_type_distribution['inbound_only'].append(customer)

            for customer in all_outbound_customers:
                if customer not in all_inbound_customers:
                    business_type_distribution['outbound_only'].append(customer)

            return {
                'warehouse_distribution': warehouse_distribution,
                'business_type_distribution': {
                    'inbound_only_count': len(business_type_distribution['inbound_only']),
                    'outbound_only_count': len(business_type_distribution['outbound_only']),
                    'both_count': len(business_type_distribution['both']),
                    'inbound_only_customers': business_type_distribution['inbound_only'][:10],
                    'outbound_only_customers': business_type_distribution['outbound_only'][:10],
                    'both_customers': business_type_distribution['both'][:10]
                },
                'analysis_period': f"{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}",
                'total_customers': len(all_inbound_customers | all_outbound_customers)
            }

        except Exception as e:
            current_app.logger.error(f"获取客户分布分析失败: {str(e)}")
            return {
                'warehouse_distribution': {},
                'business_type_distribution': {
                    'inbound_only_count': 0,
                    'outbound_only_count': 0,
                    'both_count': 0,
                    'inbound_only_customers': [],
                    'outbound_only_customers': [],
                    'both_customers': []
                },
                'analysis_period': '',
                'total_customers': 0
            }
