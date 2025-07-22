#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级分析报表
提供深度数据分析和预测功能
"""

from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_, case, text
from app import db
from app.models import InboundRecord, OutboundRecord, Inventory, TransitCargo

class AdvancedAnalytics:
    """高级分析服务"""
    
    def __init__(self):
        self.warehouse_names = {
            1: '平湖仓', 2: '昆山仓', 3: '成都仓', 4: '凭祥北投仓'
        }
    
    def get_efficiency_analysis(self, user, start_date, end_date):
        """仓库效率分析"""
        # 计算各仓库的处理效率
        efficiency_data = []
        
        for warehouse_id, warehouse_name in self.warehouse_names.items():
            # 如果用户有权限限制，跳过无权限的仓库
            if not user.is_super_admin() and user.warehouse_id != warehouse_id:
                continue
            
            # 入库效率 (每日平均入库量)
            inbound_avg = db.session.query(
                func.avg(func.count(InboundRecord.id))
            ).filter(
                and_(
                    InboundRecord.operated_warehouse_id == warehouse_id,
                    InboundRecord.inbound_time.between(start_date, end_date)
                )
            ).group_by(func.date(InboundRecord.inbound_time)).scalar() or 0
            
            # 出库效率 (每日平均出库量)
            outbound_avg = db.session.query(
                func.avg(func.count(OutboundRecord.id))
            ).filter(
                and_(
                    OutboundRecord.operated_warehouse_id == warehouse_id,
                    OutboundRecord.outbound_time.between(start_date, end_date)
                )
            ).group_by(func.date(OutboundRecord.outbound_time)).scalar() or 0
            
            # 库存周转率 (出库量/平均库存)
            total_outbound = OutboundRecord.query.filter(
                and_(
                    OutboundRecord.operated_warehouse_id == warehouse_id,
                    OutboundRecord.outbound_time.between(start_date, end_date)
                )
            ).count()
            
            avg_inventory = Inventory.query.filter(
                Inventory.operated_warehouse_id == warehouse_id
            ).count()
            
            turnover_rate = (total_outbound / avg_inventory * 100) if avg_inventory > 0 else 0
            
            efficiency_data.append({
                'warehouse_id': warehouse_id,
                'warehouse_name': warehouse_name,
                'inbound_efficiency': round(inbound_avg, 2),
                'outbound_efficiency': round(outbound_avg, 2),
                'turnover_rate': round(turnover_rate, 2),
                'efficiency_score': round((inbound_avg + outbound_avg + turnover_rate) / 3, 2)
            })
        
        return efficiency_data
    
    def get_customer_value_analysis(self, user, start_date, end_date):
        """客户价值分析"""
        # RFM分析 (Recency, Frequency, Monetary)
        customer_analysis = []
        
        # 获取客户数据
        customers = db.session.query(
            InboundRecord.customer_name,
            func.max(InboundRecord.inbound_time).label('last_inbound'),
            func.count(InboundRecord.id).label('frequency'),
            func.sum(InboundRecord.package_count).label('total_packages'),
            func.sum(InboundRecord.weight).label('total_weight')
        ).filter(
            InboundRecord.inbound_time.between(start_date, end_date)
        )
        
        # 权限过滤
        if not user.is_super_admin() and user.warehouse_id:
            customers = customers.filter(
                InboundRecord.operated_warehouse_id == user.warehouse_id
            )
        
        customers = customers.group_by(InboundRecord.customer_name).all()
        
        for customer in customers:
            # 计算最近一次业务距今天数
            recency = (datetime.now() - customer.last_inbound).days
            
            # 客户价值评分
            frequency_score = min(customer.frequency / 10 * 100, 100)  # 频次评分
            monetary_score = min(customer.total_packages / 1000 * 100, 100)  # 货量评分
            recency_score = max(100 - recency / 30 * 100, 0)  # 活跃度评分
            
            value_score = (frequency_score + monetary_score + recency_score) / 3
            
            # 客户分类
            if value_score >= 80:
                customer_type = '重要客户'
            elif value_score >= 60:
                customer_type = '价值客户'
            elif value_score >= 40:
                customer_type = '潜力客户'
            else:
                customer_type = '一般客户'
            
            customer_analysis.append({
                'customer_name': customer.customer_name,
                'last_inbound': customer.last_inbound.strftime('%Y-%m-%d'),
                'frequency': customer.frequency,
                'total_packages': customer.total_packages or 0,
                'total_weight': round(customer.total_weight or 0, 2),
                'recency_days': recency,
                'value_score': round(value_score, 2),
                'customer_type': customer_type
            })
        
        # 按价值评分排序
        customer_analysis.sort(key=lambda x: x['value_score'], reverse=True)
        
        return customer_analysis
    
    def get_route_optimization_analysis(self, user, start_date, end_date):
        """运输路线优化分析"""
        # 分析前端仓到后端仓的运输效率
        route_analysis = []
        
        # 查询运输数据
        transit_data = db.session.query(
            TransitCargo.source_warehouse_id,
            TransitCargo.destination_warehouse_id,
            func.count(TransitCargo.id).label('shipment_count'),
            func.avg(
                func.timestampdiff(
                    text('HOUR'),
                    TransitCargo.departure_time,
                    TransitCargo.actual_arrival_time
                )
            ).label('avg_transit_hours'),
            func.sum(TransitCargo.package_count).label('total_packages')
        ).filter(
            and_(
                TransitCargo.departure_time.between(start_date, end_date),
                TransitCargo.actual_arrival_time.isnot(None)
            )
        ).group_by(
            TransitCargo.source_warehouse_id,
            TransitCargo.destination_warehouse_id
        ).all()
        
        for route in transit_data:
            source_name = self.warehouse_names.get(route.source_warehouse_id, f'仓库{route.source_warehouse_id}')
            dest_name = self.warehouse_names.get(route.destination_warehouse_id, f'仓库{route.destination_warehouse_id}')
            
            # 计算效率指标
            avg_hours = route.avg_transit_hours or 0
            packages_per_shipment = (route.total_packages or 0) / route.shipment_count
            
            # 效率评分 (基于时间和货量)
            time_score = max(100 - avg_hours / 24 * 100, 0)  # 时间越短分数越高
            volume_score = min(packages_per_shipment / 100 * 100, 100)  # 货量越大分数越高
            efficiency_score = (time_score + volume_score) / 2
            
            route_analysis.append({
                'source_warehouse': source_name,
                'destination_warehouse': dest_name,
                'route_name': f'{source_name} → {dest_name}',
                'shipment_count': route.shipment_count,
                'avg_transit_hours': round(avg_hours, 2),
                'total_packages': route.total_packages or 0,
                'packages_per_shipment': round(packages_per_shipment, 2),
                'efficiency_score': round(efficiency_score, 2)
            })
        
        # 按效率评分排序
        route_analysis.sort(key=lambda x: x['efficiency_score'], reverse=True)
        
        return route_analysis
    
    def get_inventory_optimization_suggestions(self, user):
        """库存优化建议"""
        suggestions = []
        
        # 查询库存数据
        inventory_query = Inventory.query
        if not user.is_super_admin() and user.warehouse_id:
            inventory_query = inventory_query.filter(
                Inventory.operated_warehouse_id == user.warehouse_id
            )
        
        # 积压货物分析 (超过30天未出库)
        old_inventory = inventory_query.filter(
            Inventory.last_updated < datetime.now() - timedelta(days=30)
        ).all()
        
        if old_inventory:
            total_old_packages = sum(inv.package_count or 0 for inv in old_inventory)
            suggestions.append({
                'type': 'warning',
                'category': '积压预警',
                'title': f'发现 {len(old_inventory)} 票积压货物',
                'description': f'总计 {total_old_packages} 件货物超过30天未出库，建议联系客户处理',
                'priority': 'high',
                'action': '联系客户安排出库'
            })
        
        # 快速周转货物分析 (7天内入库出库)
        recent_date = datetime.now() - timedelta(days=7)
        fast_turnover = db.session.query(
            InboundRecord.customer_name,
            func.count(InboundRecord.id).label('count')
        ).filter(
            InboundRecord.inbound_time >= recent_date
        ).group_by(InboundRecord.customer_name).having(
            func.count(InboundRecord.id) >= 5
        ).all()
        
        if fast_turnover:
            suggestions.append({
                'type': 'info',
                'category': '效率优化',
                'title': f'发现 {len(fast_turnover)} 个高频客户',
                'description': '这些客户货物周转快，建议优化库位分配',
                'priority': 'medium',
                'action': '优化库位分配策略'
            })
        
        # 库存不平衡分析
        warehouse_inventory = db.session.query(
            Inventory.operated_warehouse_id,
            func.count(Inventory.id).label('item_count'),
            func.sum(Inventory.package_count).label('total_packages')
        ).group_by(Inventory.operated_warehouse_id).all()
        
        if len(warehouse_inventory) > 1:
            max_packages = max(inv.total_packages or 0 for inv in warehouse_inventory)
            min_packages = min(inv.total_packages or 0 for inv in warehouse_inventory)
            
            if max_packages > min_packages * 2:  # 最大库存是最小库存的2倍以上
                suggestions.append({
                    'type': 'warning',
                    'category': '库存平衡',
                    'title': '仓库间库存不平衡',
                    'description': '部分仓库库存过多，建议调配货物',
                    'priority': 'medium',
                    'action': '考虑仓库间货物调配'
                })
        
        return suggestions
    
    def get_predictive_analysis(self, user, days_ahead=30):
        """预测分析"""
        # 基于历史数据预测未来业务量
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)  # 使用过去90天数据
        
        # 获取历史数据
        daily_stats = db.session.query(
            func.date(InboundRecord.inbound_time).label('date'),
            func.count(InboundRecord.id).label('inbound_count'),
            func.sum(InboundRecord.package_count).label('inbound_packages')
        ).filter(
            InboundRecord.inbound_time.between(start_date, end_date)
        )
        
        if not user.is_super_admin() and user.warehouse_id:
            daily_stats = daily_stats.filter(
                InboundRecord.operated_warehouse_id == user.warehouse_id
            )
        
        daily_stats = daily_stats.group_by(
            func.date(InboundRecord.inbound_time)
        ).all()
        
        if not daily_stats:
            return {'prediction': '数据不足，无法进行预测'}
        
        # 简单的移动平均预测
        recent_avg = sum(stat.inbound_count for stat in daily_stats[-7:]) / 7
        monthly_avg = sum(stat.inbound_count for stat in daily_stats) / len(daily_stats)
        
        # 预测未来30天
        predicted_daily = (recent_avg + monthly_avg) / 2
        predicted_monthly = predicted_daily * days_ahead
        
        # 趋势分析
        first_half = daily_stats[:len(daily_stats)//2]
        second_half = daily_stats[len(daily_stats)//2:]
        
        first_avg = sum(stat.inbound_count for stat in first_half) / len(first_half)
        second_avg = sum(stat.inbound_count for stat in second_half) / len(second_half)
        
        trend = 'increasing' if second_avg > first_avg else 'decreasing' if second_avg < first_avg else 'stable'
        trend_percentage = abs((second_avg - first_avg) / first_avg * 100) if first_avg > 0 else 0
        
        return {
            'predicted_daily_average': round(predicted_daily, 2),
            'predicted_monthly_total': round(predicted_monthly, 2),
            'trend': trend,
            'trend_percentage': round(trend_percentage, 2),
            'confidence': 'medium',  # 简单预测的置信度
            'recommendation': self._get_prediction_recommendation(trend, trend_percentage)
        }
    
    def _get_prediction_recommendation(self, trend, percentage):
        """根据预测趋势给出建议"""
        if trend == 'increasing' and percentage > 20:
            return '业务量呈上升趋势，建议增加人员配置和库存空间'
        elif trend == 'decreasing' and percentage > 20:
            return '业务量呈下降趋势，建议优化成本控制'
        elif trend == 'stable':
            return '业务量相对稳定，保持当前运营策略'
        else:
            return '业务量变化较小，继续观察趋势'
