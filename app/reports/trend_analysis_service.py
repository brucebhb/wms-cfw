#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
趋势预测分析服务
提供货量趋势预测、季节性分析、增长率分析、异常检测、目标达成预测等功能
"""

from datetime import datetime, timedelta, date
from sqlalchemy import func, and_, or_, case, text, desc
from flask import current_app
from app import db
from app.models import (
    InboundRecord, OutboundRecord, Inventory, TransitCargo,
    ReceiveRecord, Warehouse, User
)
import numpy as np
from collections import defaultdict

class TrendAnalysisService:
    """趋势预测分析服务类"""

    def __init__(self):
        self.warehouse_names = {
            1: '平湖仓', 2: '昆山仓', 3: '成都仓', 4: '凭祥北投仓'
        }
        self.frontend_warehouses = [1, 2, 3]  # 前端仓
        self.backend_warehouses = [4]         # 后端仓

    def get_cargo_volume_forecast(self, user, forecast_months=3):
        """获取货量趋势预测"""
        try:
            accessible_warehouses = self._get_accessible_warehouses(user)
            end_date = datetime.now().date()
            
            # 获取历史12个月的数据用于预测
            historical_data = []
            for i in range(12):
                month_start = end_date.replace(day=1) - timedelta(days=30*i)
                month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                
                # 入库数据
                inbound_count = db.session.query(func.count(InboundRecord.id)).filter(
                    and_(
                        InboundRecord.inbound_time >= month_start,
                        InboundRecord.inbound_time <= month_end,
                        InboundRecord.operated_warehouse_id.in_(accessible_warehouses)
                    )
                ).scalar() or 0

                # 出库数据
                outbound_count = db.session.query(func.count(OutboundRecord.id)).filter(
                    and_(
                        OutboundRecord.outbound_time >= month_start,
                        OutboundRecord.outbound_time <= month_end,
                        OutboundRecord.operated_warehouse_id.in_(accessible_warehouses)
                    )
                ).scalar() or 0

                historical_data.append({
                    'month': month_start.strftime('%Y-%m'),
                    'inbound_count': inbound_count,
                    'outbound_count': outbound_count,
                    'total_count': inbound_count + outbound_count
                })

            # 按时间正序排列
            historical_data.reverse()

            # 简单的线性趋势预测
            forecast_data = self._predict_linear_trend(historical_data, forecast_months)

            return {
                'historical_data': historical_data,
                'forecast_data': forecast_data,
                'forecast_period': f"未来{forecast_months}个月",
                'analysis_date': end_date.strftime('%Y-%m-%d')
            }

        except Exception as e:
            current_app.logger.error(f"获取货量趋势预测失败: {str(e)}")
            return {
                'historical_data': [],
                'forecast_data': [],
                'forecast_period': '',
                'analysis_date': ''
            }

    def get_seasonal_analysis(self, user):
        """获取季节性分析"""
        try:
            accessible_warehouses = self._get_accessible_warehouses(user)
            end_date = datetime.now().date()
            
            # 获取最近24个月的数据进行季节性分析
            monthly_data = defaultdict(list)
            
            for i in range(24):
                month_start = end_date.replace(day=1) - timedelta(days=30*i)
                month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                month_key = month_start.month  # 1-12月
                
                # 总货量
                inbound_count = db.session.query(func.count(InboundRecord.id)).filter(
                    and_(
                        InboundRecord.inbound_time >= month_start,
                        InboundRecord.inbound_time <= month_end,
                        InboundRecord.operated_warehouse_id.in_(accessible_warehouses)
                    )
                ).scalar() or 0

                outbound_count = db.session.query(func.count(OutboundRecord.id)).filter(
                    and_(
                        OutboundRecord.outbound_time >= month_start,
                        OutboundRecord.outbound_time <= month_end,
                        OutboundRecord.operated_warehouse_id.in_(accessible_warehouses)
                    )
                ).scalar() or 0

                total_count = inbound_count + outbound_count
                monthly_data[month_key].append(total_count)

            # 计算每月平均值和季节性指数
            seasonal_analysis = []
            month_names = ['1月', '2月', '3月', '4月', '5月', '6月', 
                          '7月', '8月', '9月', '10月', '11月', '12月']
            
            overall_average = sum([sum(values) for values in monthly_data.values()]) / sum([len(values) for values in monthly_data.values()])
            
            for month in range(1, 13):
                if month in monthly_data and monthly_data[month]:
                    month_average = sum(monthly_data[month]) / len(monthly_data[month])
                    seasonal_index = (month_average / overall_average) * 100 if overall_average > 0 else 100
                    
                    seasonal_analysis.append({
                        'month': month,
                        'month_name': month_names[month-1],
                        'average_volume': round(month_average, 1),
                        'seasonal_index': round(seasonal_index, 1),
                        'trend': '高峰' if seasonal_index > 110 else '低谷' if seasonal_index < 90 else '正常'
                    })
                else:
                    seasonal_analysis.append({
                        'month': month,
                        'month_name': month_names[month-1],
                        'average_volume': 0,
                        'seasonal_index': 100,
                        'trend': '正常'
                    })

            return {
                'seasonal_analysis': seasonal_analysis,
                'overall_average': round(overall_average, 1),
                'analysis_period': '最近24个月数据'
            }

        except Exception as e:
            current_app.logger.error(f"获取季节性分析失败: {str(e)}")
            return {
                'seasonal_analysis': [],
                'overall_average': 0,
                'analysis_period': ''
            }

    def get_growth_rate_analysis(self, user):
        """获取增长率分析"""
        try:
            accessible_warehouses = self._get_accessible_warehouses(user)
            end_date = datetime.now().date()
            
            # 获取最近12个月的数据
            monthly_growth = []
            
            for i in range(12):
                current_month_start = end_date.replace(day=1) - timedelta(days=30*i)
                current_month_end = (current_month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                
                prev_month_start = current_month_start - timedelta(days=30)
                prev_month_end = (prev_month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                
                # 当月数据
                current_inbound = db.session.query(func.count(InboundRecord.id)).filter(
                    and_(
                        InboundRecord.inbound_time >= current_month_start,
                        InboundRecord.inbound_time <= current_month_end,
                        InboundRecord.operated_warehouse_id.in_(accessible_warehouses)
                    )
                ).scalar() or 0

                current_outbound = db.session.query(func.count(OutboundRecord.id)).filter(
                    and_(
                        OutboundRecord.outbound_time >= current_month_start,
                        OutboundRecord.outbound_time <= current_month_end,
                        OutboundRecord.operated_warehouse_id.in_(accessible_warehouses)
                    )
                ).scalar() or 0

                current_total = current_inbound + current_outbound

                # 上月数据
                prev_inbound = db.session.query(func.count(InboundRecord.id)).filter(
                    and_(
                        InboundRecord.inbound_time >= prev_month_start,
                        InboundRecord.inbound_time <= prev_month_end,
                        InboundRecord.operated_warehouse_id.in_(accessible_warehouses)
                    )
                ).scalar() or 0

                prev_outbound = db.session.query(func.count(OutboundRecord.id)).filter(
                    and_(
                        OutboundRecord.outbound_time >= prev_month_start,
                        OutboundRecord.outbound_time <= prev_month_end,
                        OutboundRecord.operated_warehouse_id.in_(accessible_warehouses)
                    )
                ).scalar() or 0

                prev_total = prev_inbound + prev_outbound

                # 计算增长率
                if prev_total > 0:
                    growth_rate = ((current_total - prev_total) / prev_total) * 100
                else:
                    growth_rate = 0 if current_total == 0 else 100

                monthly_growth.append({
                    'month': current_month_start.strftime('%Y-%m'),
                    'current_volume': current_total,
                    'previous_volume': prev_total,
                    'growth_rate': round(growth_rate, 2),
                    'growth_type': '增长' if growth_rate > 0 else '下降' if growth_rate < 0 else '持平'
                })

            # 按时间正序排列
            monthly_growth.reverse()

            # 计算平均增长率
            growth_rates = [item['growth_rate'] for item in monthly_growth if item['previous_volume'] > 0]
            avg_growth_rate = sum(growth_rates) / len(growth_rates) if growth_rates else 0

            return {
                'monthly_growth': monthly_growth,
                'average_growth_rate': round(avg_growth_rate, 2),
                'analysis_period': '最近12个月'
            }

        except Exception as e:
            current_app.logger.error(f"获取增长率分析失败: {str(e)}")
            return {
                'monthly_growth': [],
                'average_growth_rate': 0,
                'analysis_period': ''
            }

    def _predict_linear_trend(self, historical_data, forecast_months):
        """简单的线性趋势预测"""
        if len(historical_data) < 3:
            return []

        # 提取数据
        volumes = [item['total_count'] for item in historical_data]
        
        # 简单线性回归
        n = len(volumes)
        x = list(range(n))
        
        # 计算斜率和截距
        sum_x = sum(x)
        sum_y = sum(volumes)
        sum_xy = sum(x[i] * volumes[i] for i in range(n))
        sum_x2 = sum(x[i] ** 2 for i in range(n))
        
        if n * sum_x2 - sum_x ** 2 != 0:
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
            intercept = (sum_y - slope * sum_x) / n
        else:
            slope = 0
            intercept = sum_y / n if n > 0 else 0

        # 生成预测数据
        forecast_data = []
        last_month = datetime.strptime(historical_data[-1]['month'], '%Y-%m').date()
        
        for i in range(1, forecast_months + 1):
            forecast_month = last_month.replace(day=1) + timedelta(days=32*i)
            forecast_month = forecast_month.replace(day=1)
            
            predicted_volume = max(0, round(intercept + slope * (n + i - 1)))
            
            forecast_data.append({
                'month': forecast_month.strftime('%Y-%m'),
                'predicted_volume': predicted_volume,
                'confidence': 'medium'  # 简单预测，置信度中等
            })

        return forecast_data

    def get_anomaly_detection(self, user):
        """获取异常检测分析"""
        try:
            accessible_warehouses = self._get_accessible_warehouses(user)
            end_date = datetime.now().date()

            # 获取最近30天的每日数据
            daily_data = []
            for i in range(30):
                check_date = end_date - timedelta(days=i)

                # 当日数据
                inbound_count = db.session.query(func.count(InboundRecord.id)).filter(
                    and_(
                        func.date(InboundRecord.inbound_time) == check_date,
                        InboundRecord.operated_warehouse_id.in_(accessible_warehouses)
                    )
                ).scalar() or 0

                outbound_count = db.session.query(func.count(OutboundRecord.id)).filter(
                    and_(
                        func.date(OutboundRecord.outbound_time) == check_date,
                        OutboundRecord.operated_warehouse_id.in_(accessible_warehouses)
                    )
                ).scalar() or 0

                total_count = inbound_count + outbound_count

                daily_data.append({
                    'date': check_date.strftime('%Y-%m-%d'),
                    'volume': total_count
                })

            # 按时间正序排列
            daily_data.reverse()

            # 计算统计指标
            volumes = [item['volume'] for item in daily_data]
            if volumes:
                mean_volume = sum(volumes) / len(volumes)
                variance = sum((x - mean_volume) ** 2 for x in volumes) / len(volumes)
                std_dev = variance ** 0.5

                # 检测异常（使用3σ原则）
                anomalies = []
                for item in daily_data:
                    volume = item['volume']
                    z_score = abs(volume - mean_volume) / std_dev if std_dev > 0 else 0

                    if z_score > 2:  # 2σ以外认为是异常
                        anomaly_type = '异常高' if volume > mean_volume else '异常低'
                        anomalies.append({
                            'date': item['date'],
                            'volume': volume,
                            'expected_range': f"{round(mean_volume - 2*std_dev, 1)} - {round(mean_volume + 2*std_dev, 1)}",
                            'anomaly_type': anomaly_type,
                            'severity': '高' if z_score > 3 else '中'
                        })

                return {
                    'daily_data': daily_data,
                    'anomalies': anomalies,
                    'statistics': {
                        'mean_volume': round(mean_volume, 1),
                        'std_deviation': round(std_dev, 1),
                        'normal_range': f"{round(mean_volume - 2*std_dev, 1)} - {round(mean_volume + 2*std_dev, 1)}"
                    },
                    'analysis_period': '最近30天'
                }
            else:
                return {
                    'daily_data': [],
                    'anomalies': [],
                    'statistics': {'mean_volume': 0, 'std_deviation': 0, 'normal_range': '0 - 0'},
                    'analysis_period': '最近30天'
                }

        except Exception as e:
            current_app.logger.error(f"获取异常检测分析失败: {str(e)}")
            return {
                'daily_data': [],
                'anomalies': [],
                'statistics': {'mean_volume': 0, 'std_deviation': 0, 'normal_range': '0 - 0'},
                'analysis_period': ''
            }

    def get_target_achievement_forecast(self, user, monthly_target=None):
        """获取目标达成预测"""
        try:
            accessible_warehouses = self._get_accessible_warehouses(user)
            current_date = datetime.now().date()

            # 如果没有提供目标，使用历史平均值作为目标
            if monthly_target is None:
                # 计算过去6个月的平均值作为目标
                target_data = []
                for i in range(6):
                    month_start = current_date.replace(day=1) - timedelta(days=30*i)
                    month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)

                    monthly_volume = self._get_monthly_volume(month_start, month_end, accessible_warehouses)
                    target_data.append(monthly_volume)

                monthly_target = sum(target_data) / len(target_data) if target_data else 100

            # 获取当月数据
            month_start = current_date.replace(day=1)
            month_end = current_date

            current_month_volume = self._get_monthly_volume(month_start, month_end, accessible_warehouses)

            # 计算当月进度
            days_passed = (current_date - month_start).days + 1
            days_in_month = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            days_in_month = days_in_month.day

            expected_progress = (days_passed / days_in_month) * monthly_target
            actual_progress = current_month_volume

            # 预测月末完成情况
            if days_passed > 0:
                daily_average = current_month_volume / days_passed
                predicted_month_end = daily_average * days_in_month
            else:
                predicted_month_end = 0

            # 计算达成率
            achievement_rate = (predicted_month_end / monthly_target * 100) if monthly_target > 0 else 0

            # 预测状态
            if achievement_rate >= 100:
                forecast_status = '预计达成'
                status_color = 'success'
            elif achievement_rate >= 80:
                forecast_status = '接近达成'
                status_color = 'warning'
            else:
                forecast_status = '预计未达成'
                status_color = 'danger'

            return {
                'monthly_target': round(monthly_target, 1),
                'current_progress': current_month_volume,
                'expected_progress': round(expected_progress, 1),
                'predicted_month_end': round(predicted_month_end, 1),
                'achievement_rate': round(achievement_rate, 1),
                'forecast_status': forecast_status,
                'status_color': status_color,
                'days_passed': days_passed,
                'days_remaining': days_in_month - days_passed,
                'daily_average': round(daily_average, 1) if days_passed > 0 else 0,
                'required_daily_average': round((monthly_target - current_month_volume) / max(1, days_in_month - days_passed), 1),
                'analysis_date': current_date.strftime('%Y-%m-%d')
            }

        except Exception as e:
            current_app.logger.error(f"获取目标达成预测失败: {str(e)}")
            return {
                'monthly_target': 0,
                'current_progress': 0,
                'expected_progress': 0,
                'predicted_month_end': 0,
                'achievement_rate': 0,
                'forecast_status': '数据异常',
                'status_color': 'secondary',
                'days_passed': 0,
                'days_remaining': 0,
                'daily_average': 0,
                'required_daily_average': 0,
                'analysis_date': ''
            }

    def _get_monthly_volume(self, start_date, end_date, accessible_warehouses):
        """获取指定时间段的货量"""
        inbound_count = db.session.query(func.count(InboundRecord.id)).filter(
            and_(
                InboundRecord.inbound_time >= start_date,
                InboundRecord.inbound_time <= end_date,
                InboundRecord.operated_warehouse_id.in_(accessible_warehouses)
            )
        ).scalar() or 0

        outbound_count = db.session.query(func.count(OutboundRecord.id)).filter(
            and_(
                OutboundRecord.outbound_time >= start_date,
                OutboundRecord.outbound_time <= end_date,
                OutboundRecord.operated_warehouse_id.in_(accessible_warehouses)
            )
        ).scalar() or 0

        return inbound_count + outbound_count

    def _get_accessible_warehouses(self, user):
        """获取用户可访问的仓库列表"""
        if user.is_super_admin():
            return [1, 2, 3, 4]  # 管理员可以访问所有仓库
        else:
            # 普通用户只能访问自己的仓库
            return [user.warehouse_id] if user.warehouse_id else []
