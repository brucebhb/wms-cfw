#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
货量报表服务
提供货量统计、趋势分析、对比分析等功能
"""

from datetime import datetime, timedelta, date
from sqlalchemy import func, and_, or_, case, text
from flask import current_app
from app import db
from app.models import (
    InboundRecord, OutboundRecord, Inventory, TransitCargo,
    ReceiveRecord, Warehouse, User
)

class CargoVolumeService:
    """货量报表服务类"""

    def __init__(self):
        self.warehouse_names = {
            1: '平湖仓', 2: '昆山仓', 3: '成都仓', 4: '凭祥北投仓'
        }
        self.frontend_warehouses = [1, 2, 3]  # 前端仓
        self.backend_warehouses = [4]         # 后端仓（只有凭祥北投仓）

    def get_overview_data(self, user):
        """获取货量总览数据"""
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        
        # 获取今日数据
        today_inbound = self._get_daily_inbound_stats(today, user)
        today_outbound = self._get_daily_outbound_stats(today, user)
        
        # 获取昨日数据
        yesterday_inbound = self._get_daily_inbound_stats(yesterday, user)
        yesterday_outbound = self._get_daily_outbound_stats(yesterday, user)
        
        # 获取库存总量
        inventory_stats = self._get_inventory_stats(user)
        
        # 获取在途货物
        transit_stats = self._get_transit_stats(user)
        
        return {
            'today_inbound': today_inbound,
            'today_outbound': today_outbound,
            'yesterday_inbound': yesterday_inbound,
            'yesterday_outbound': yesterday_outbound,
            'inventory_stats': inventory_stats,
            'transit_stats': transit_stats,
            'comparison': {
                'inbound_growth': self._calculate_growth(today_inbound, yesterday_inbound),
                'outbound_growth': self._calculate_growth(today_outbound, yesterday_outbound)
            }
        }

    def get_trends_data(self, user, period='week'):
        """获取趋势数据（分前端仓和后端仓）"""
        if period == 'day':
            return self._get_daily_trends_separated(user)
        elif period == 'week':
            return self._get_weekly_trends_separated(user)
        elif period == 'month':
            return self._get_monthly_trends_separated(user)
        elif period == 'year':
            return self._get_yearly_trends_separated(user)
        else:
            return self._get_weekly_trends_separated(user)

    def get_warehouse_stats(self, user):
        """获取仓库统计数据（包含各仓库详细对比数据）"""
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        last_year = today.replace(year=today.year - 1)

        # 获取用户可访问的仓库
        accessible_warehouses = self._get_accessible_warehouses(user)

        # 初始化结果
        result = {
            'today_inbound': {'count': 0, 'pallets': 0, 'packages': 0},
            'today_outbound': {'count': 0, 'pallets': 0, 'packages': 0},
            'inventory_stats': {'count': 0, 'pallets': 0, 'packages': 0},
            'transit_stats': {'count': 0, 'pallets': 0, 'packages': 0},
            'warehouse_1': {},
            'warehouse_2': {},
            'warehouse_3': {},
            'warehouse_4': {},
            'frontend_summary': {'count': 0, 'pallets': 0, 'packages': 0},
            'backend_summary': {'count': 0, 'pallets': 0, 'packages': 0}
        }

        # 各仓库详细数据
        frontend_total = {'count': 0, 'pallets': 0, 'packages': 0}
        backend_total = {'count': 0, 'pallets': 0, 'packages': 0}

        for warehouse_id in [1, 2, 3, 4]:  # 平湖仓、昆山仓、成都仓、凭祥北投仓
            if warehouse_id in accessible_warehouses:
                warehouse_data = self._get_warehouse_detailed_stats(warehouse_id, today, yesterday, last_year)
                result[f'warehouse_{warehouse_id}'] = warehouse_data

                # 累计前端仓和后端仓数据
                today_data = warehouse_data.get('today', {})
                if warehouse_id in [1, 2, 3]:  # 前端仓
                    frontend_total['count'] += today_data.get('inbound', 0) + today_data.get('outbound', 0)
                    frontend_total['pallets'] += today_data.get('pallets', 0)
                    frontend_total['packages'] += today_data.get('packages', 0)
                elif warehouse_id == 4:  # 后端仓
                    backend_total['count'] += today_data.get('inbound', 0) + today_data.get('outbound', 0)
                    backend_total['pallets'] += today_data.get('pallets', 0)
                    backend_total['packages'] += today_data.get('packages', 0)

        # 计算总体统计
        total_inbound = {'count': 0, 'pallets': 0, 'packages': 0}
        total_outbound = {'count': 0, 'pallets': 0, 'packages': 0}
        total_inventory = {'count': 0, 'pallets': 0, 'packages': 0}
        total_transit = {'count': 0, 'pallets': 0, 'packages': 0}

        for warehouse_id in accessible_warehouses:
            warehouse_data = result.get(f'warehouse_{warehouse_id}', {})
            today_data = warehouse_data.get('today', {})
            inventory_data = warehouse_data.get('inventory', {})

            total_inbound['count'] += today_data.get('inbound', 0)
            total_inbound['pallets'] += today_data.get('pallets', 0)
            total_inbound['packages'] += today_data.get('packages', 0)

            total_outbound['count'] += today_data.get('outbound', 0)

            total_inventory['count'] += inventory_data.get('count', 0)
            total_inventory['pallets'] += inventory_data.get('pallets', 0)
            total_inventory['packages'] += inventory_data.get('packages', 0)

        result.update({
            'today_inbound': total_inbound,
            'today_outbound': total_outbound,
            'inventory_stats': total_inventory,
            'transit_stats': total_transit,
            'frontend_summary': frontend_total,
            'backend_summary': backend_total
        })

        return result

    def get_day_range_stats(self, user, start_date, end_date):
        """获取日期范围统计数据"""
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            raise ValueError('日期格式错误，请使用YYYY-MM-DD格式')

        # 验证日期范围
        if (end_date - start_date).days > 7:
            raise ValueError('日期范围不能超过7天')

        if start_date > end_date:
            raise ValueError('开始日期不能晚于结束日期')

        accessible_warehouses = self._get_accessible_warehouses(user)

        # 生成日期列表
        current_date = start_date
        daily_data = []
        summary = {'total_count': 0, 'total_pallets': 0, 'total_packages': 0}

        while current_date <= end_date:
            day_data = {
                'date': current_date.strftime('%Y-%m-%d'),
                'total': 0,
                'total_pallets': 0,
                'total_packages': 0
            }

            for warehouse_id in [1, 2, 3, 4]:
                if warehouse_id in accessible_warehouses:
                    # 获取当日进出库数据
                    inbound = self._get_warehouse_daily_inbound(warehouse_id, current_date)
                    outbound = self._get_warehouse_daily_outbound(warehouse_id, current_date)

                    warehouse_total = inbound['count'] + outbound['count']
                    warehouse_pallets = inbound['pallets'] + outbound['pallets']
                    warehouse_packages = inbound['packages'] + outbound['packages']

                    day_data[f'warehouse_{warehouse_id}'] = warehouse_total
                    day_data[f'warehouse_{warehouse_id}_pallets'] = warehouse_pallets
                    day_data[f'warehouse_{warehouse_id}_packages'] = warehouse_packages

                    day_data['total'] += warehouse_total
                    day_data['total_pallets'] += warehouse_pallets
                    day_data['total_packages'] += warehouse_packages

                    # 累计汇总数据
                    summary['total_count'] += warehouse_total
                    summary['total_pallets'] += warehouse_pallets
                    summary['total_packages'] += warehouse_packages
                else:
                    day_data[f'warehouse_{warehouse_id}'] = 0
                    day_data[f'warehouse_{warehouse_id}_pallets'] = 0
                    day_data[f'warehouse_{warehouse_id}_packages'] = 0

            daily_data.append(day_data)
            current_date += timedelta(days=1)

        return {
            'daily_data': daily_data,
            'summary': summary,
            'date_range': {
                'start': start_date.strftime('%Y-%m-%d'),
                'end': end_date.strftime('%Y-%m-%d'),
                'days': len(daily_data)
            }
        }

    def get_week_range_stats(self, user, first_year, first_month, first_week,
                           second_year=None, second_month=None, second_week=None):
        """获取周范围统计数据"""
        try:
            # 计算第一周的日期范围（使用年度周次）
            first_start_date, first_end_date = self._calculate_year_week_dates(first_year, first_week)

            # 计算第二周的日期范围（如果有）
            second_start_date = None
            second_end_date = None
            if all([second_year, second_month, second_week]):
                second_start_date, second_end_date = self._calculate_year_week_dates(second_year, second_week)

        except ValueError as e:
            raise ValueError(f'日期计算错误: {str(e)}')

        accessible_warehouses = self._get_accessible_warehouses(user)

        # 获取第一周数据 - 使用年周次格式
        first_week_data = self._get_week_data(
            accessible_warehouses,
            first_start_date,
            first_end_date,
            f"{first_year}年第{first_week}周"
        )

        # 获取第二周数据（如果有）- 使用年周次格式
        second_week_data = None
        if second_start_date and second_end_date:
            second_week_data = self._get_week_data(
                accessible_warehouses,
                second_start_date,
                second_end_date,
                f"{second_year}年第{second_week}周"
            )

        # 计算汇总数据
        summary = {
            'total_count': first_week_data['summary']['total_count'],
            'total_pallets': first_week_data['summary']['total_pallets'],
            'total_packages': first_week_data['summary']['total_packages']
        }

        if second_week_data:
            summary['total_count'] += second_week_data['summary']['total_count']
            summary['total_pallets'] += second_week_data['summary']['total_pallets']
            summary['total_packages'] += second_week_data['summary']['total_packages']

        result = {
            'first_week': first_week_data,
            'summary': summary,
            'week_info': {
                'first_year': first_year,
                'first_month': first_month,
                'first_week': first_week
            }
        }

        if second_week_data:
            result['second_week'] = second_week_data
            result['week_info']['second_year'] = second_year
            result['week_info']['second_month'] = second_month
            result['week_info']['second_week'] = second_week

            # 添加图表数据
            result['chart_data'] = {
                'categories': [first_week_data['name'], second_week_data['name']],
                'inbound': [
                    first_week_data['summary']['total_count'],
                    second_week_data['summary']['total_count']
                ],
                'outbound': [
                    first_week_data['summary']['total_count'],
                    second_week_data['summary']['total_count']
                ],
                'pallets': [
                    first_week_data['summary']['total_pallets'],
                    second_week_data['summary']['total_pallets']
                ],
                'packages': [
                    first_week_data['summary']['total_packages'],
                    second_week_data['summary']['total_packages']
                ]
            }

        return result

    def _calculate_week_dates(self, year, month, week_number):
        """计算指定年月第几周的开始和结束日期（月度周次）"""
        # 获取该月第一天
        first_day = date(year, month, 1)

        # 找到第一周的开始（周一）
        first_monday = first_day
        while first_monday.weekday() != 0:  # 0表示周一
            first_monday -= timedelta(days=1)

        # 计算指定周的开始日期
        week_start = first_monday + timedelta(weeks=week_number - 1)
        week_end = week_start + timedelta(days=6)

        # 确保日期在合理范围内
        if week_start.year < year - 1 or week_start.year > year + 1:
            raise ValueError(f'周次超出合理范围')

        return week_start, week_end

    def _calculate_year_week_dates(self, year, week_number):
        """计算指定年份第几周的开始和结束日期（年度周次，ISO标准）"""
        # 使用ISO周标准：第一周是包含1月4日的那一周
        jan_4 = date(year, 1, 4)

        # 找到1月4日所在周的周一
        days_since_monday = jan_4.weekday()  # 0=周一, 6=周日
        first_monday = jan_4 - timedelta(days=days_since_monday)

        # 计算指定周的周一
        week_start = first_monday + timedelta(weeks=week_number - 1)
        week_end = week_start + timedelta(days=6)

        # 验证周次范围
        if week_number < 1 or week_number > 53:
            raise ValueError(f'周次必须在1-53之间')

        return week_start, week_end

    def _get_week_data(self, accessible_warehouses, start_date, end_date, week_name):
        """获取指定周的数据"""
        current_date = start_date
        daily_data = []
        summary = {'total_count': 0, 'total_pallets': 0, 'total_packages': 0}

        while current_date <= end_date:
            day_data = {
                'date': current_date.strftime('%Y-%m-%d'),
                'total': 0,
                'total_pallets': 0,
                'total_packages': 0
            }

            for warehouse_id in [1, 2, 3, 4]:
                if warehouse_id in accessible_warehouses:
                    # 获取当日进出库数据
                    inbound = self._get_warehouse_daily_inbound(warehouse_id, current_date)
                    outbound = self._get_warehouse_daily_outbound(warehouse_id, current_date)

                    warehouse_total = inbound['count'] + outbound['count']
                    warehouse_pallets = inbound['pallets'] + outbound['pallets']
                    warehouse_packages = inbound['packages'] + outbound['packages']

                    day_data[f'warehouse_{warehouse_id}'] = warehouse_total
                    day_data[f'warehouse_{warehouse_id}_pallets'] = warehouse_pallets
                    day_data[f'warehouse_{warehouse_id}_packages'] = warehouse_packages

                    day_data['total'] += warehouse_total
                    day_data['total_pallets'] += warehouse_pallets
                    day_data['total_packages'] += warehouse_packages

                    # 累计汇总数据
                    summary['total_count'] += warehouse_total
                    summary['total_pallets'] += warehouse_pallets
                    summary['total_packages'] += warehouse_packages
                else:
                    day_data[f'warehouse_{warehouse_id}'] = 0
                    day_data[f'warehouse_{warehouse_id}_pallets'] = 0
                    day_data[f'warehouse_{warehouse_id}_packages'] = 0

            daily_data.append(day_data)
            current_date += timedelta(days=1)

        return {
            'name': week_name,
            'daily_data': daily_data,
            'summary': summary,
            'date_range': {
                'start': start_date.strftime('%Y-%m-%d'),
                'end': end_date.strftime('%Y-%m-%d'),
                'days': len(daily_data)
            }
        }

    def get_month_range_stats(self, user, start_year, start_month, end_year, end_month):
        """获取月份范围统计数据"""
        try:
            # 验证参数
            if start_year < 2020 or start_year > 2030 or end_year < 2020 or end_year > 2030:
                raise ValueError('年份必须在2020-2030之间')

            if start_month < 1 or start_month > 12 or end_month < 1 or end_month > 12:
                raise ValueError('月份必须在1-12之间')

            # 计算月份范围
            start_date = date(start_year, start_month, 1)

            # 计算结束月份的最后一天
            if end_month == 12:
                end_date = date(end_year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(end_year, end_month + 1, 1) - timedelta(days=1)

            # 验证日期范围（最多12个月）
            months_diff = (end_year - start_year) * 12 + (end_month - start_month) + 1
            if months_diff > 12:
                raise ValueError('月份范围不能超过12个月')

            if start_date > end_date:
                raise ValueError('开始月份不能晚于结束月份')

            accessible_warehouses = self._get_accessible_warehouses(user)

            # 生成月份数据
            month_data = []
            summary = {'total_count': 0, 'total_pallets': 0, 'total_packages': 0}

            current_year = start_year
            current_month = start_month

            while (current_year < end_year) or (current_year == end_year and current_month <= end_month):
                month_info = {
                    'year': current_year,
                    'month': current_month,
                    'month_name': f"{current_year}年{current_month}月",
                    'total': 0,
                    'total_pallets': 0,
                    'total_packages': 0
                }

                # 计算当月的日期范围
                month_start = date(current_year, current_month, 1)
                if current_month == 12:
                    month_end = date(current_year + 1, 1, 1) - timedelta(days=1)
                else:
                    month_end = date(current_year, current_month + 1, 1) - timedelta(days=1)

                # 获取各仓库当月数据
                for warehouse_id in [1, 2, 3, 4]:
                    if warehouse_id in accessible_warehouses:
                        month_stats = self._get_warehouse_monthly_stats(warehouse_id, month_start, month_end)

                        month_info[f'warehouse_{warehouse_id}'] = month_stats['count']
                        month_info[f'warehouse_{warehouse_id}_pallets'] = month_stats['pallets']
                        month_info[f'warehouse_{warehouse_id}_packages'] = month_stats['packages']

                        month_info['total'] += month_stats['count']
                        month_info['total_pallets'] += month_stats['pallets']
                        month_info['total_packages'] += month_stats['packages']

                        # 累计汇总数据
                        summary['total_count'] += month_stats['count']
                        summary['total_pallets'] += month_stats['pallets']
                        summary['total_packages'] += month_stats['packages']
                    else:
                        month_info[f'warehouse_{warehouse_id}'] = 0
                        month_info[f'warehouse_{warehouse_id}_pallets'] = 0
                        month_info[f'warehouse_{warehouse_id}_packages'] = 0

                month_data.append(month_info)

                # 移动到下一个月
                if current_month == 12:
                    current_year += 1
                    current_month = 1
                else:
                    current_month += 1

            return {
                'month_data': month_data,
                'summary': summary,
                'date_range': {
                    'start_year': start_year,
                    'start_month': start_month,
                    'end_year': end_year,
                    'end_month': end_month,
                    'months': len(month_data)
                }
            }

        except Exception as e:
            raise ValueError(f'月份统计数据获取失败: {str(e)}')

    def _get_warehouse_monthly_stats(self, warehouse_id, start_date, end_date):
        """获取指定仓库在指定月份的统计数据"""
        try:
            # 获取月度进库数据
            inbound_stats = db.session.query(
                func.coalesce(func.sum(InboundRecord.pallet_count), 0).label('pallets'),
                func.coalesce(func.sum(InboundRecord.package_count), 0).label('packages'),
                func.count(InboundRecord.id).label('count')
            ).filter(
                InboundRecord.operated_warehouse_id == warehouse_id,
                InboundRecord.inbound_time >= start_date,
                InboundRecord.inbound_time <= end_date
            ).first()

            # 获取月度出库数据
            outbound_stats = db.session.query(
                func.coalesce(func.sum(OutboundRecord.pallet_count), 0).label('pallets'),
                func.coalesce(func.sum(OutboundRecord.package_count), 0).label('packages'),
                func.count(OutboundRecord.id).label('count')
            ).filter(
                OutboundRecord.operated_warehouse_id == warehouse_id,
                OutboundRecord.outbound_time >= start_date,
                OutboundRecord.outbound_time <= end_date
            ).first()

            return {
                'count': (inbound_stats.count or 0) + (outbound_stats.count or 0),
                'pallets': (inbound_stats.pallets or 0) + (outbound_stats.pallets or 0),
                'packages': (inbound_stats.packages or 0) + (outbound_stats.packages or 0)
            }

        except Exception as e:
            current_app.logger.error(f'获取仓库{warehouse_id}月度统计失败: {str(e)}')
            return {'count': 0, 'pallets': 0, 'packages': 0}

    def get_year_range_stats(self, user, start_year, end_year):
        """获取年份范围统计数据"""
        try:
            # 验证参数
            if start_year < 2020 or start_year > 2030 or end_year < 2020 or end_year > 2030:
                raise ValueError('年份必须在2020-2030之间')

            if end_year < start_year:
                raise ValueError('结束年份不能早于开始年份')

            # 验证年份范围（最多5年）
            if end_year - start_year + 1 > 5:
                raise ValueError('年份范围不能超过5年')

            accessible_warehouses = self._get_accessible_warehouses(user)

            # 生成年度数据
            year_data = []
            summary = {'total_count': 0, 'total_pallets': 0, 'total_packages': 0}

            for year in range(start_year, end_year + 1):
                year_info = {
                    'year': year,
                    'year_name': f"{year}年",
                    'total': 0,
                    'total_pallets': 0,
                    'total_packages': 0
                }

                # 计算当年的日期范围
                year_start = date(year, 1, 1)
                year_end = date(year, 12, 31)

                # 获取各仓库当年数据
                for warehouse_id in [1, 2, 3, 4]:
                    if warehouse_id in accessible_warehouses:
                        year_stats = self._get_warehouse_yearly_stats(warehouse_id, year_start, year_end)

                        year_info[f'warehouse_{warehouse_id}'] = year_stats['count']
                        year_info[f'warehouse_{warehouse_id}_pallets'] = year_stats['pallets']
                        year_info[f'warehouse_{warehouse_id}_packages'] = year_stats['packages']

                        year_info['total'] += year_stats['count']
                        year_info['total_pallets'] += year_stats['pallets']
                        year_info['total_packages'] += year_stats['packages']

                        # 累计汇总数据
                        summary['total_count'] += year_stats['count']
                        summary['total_pallets'] += year_stats['pallets']
                        summary['total_packages'] += year_stats['packages']
                    else:
                        year_info[f'warehouse_{warehouse_id}'] = 0
                        year_info[f'warehouse_{warehouse_id}_pallets'] = 0
                        year_info[f'warehouse_{warehouse_id}_packages'] = 0

                year_data.append(year_info)

            return {
                'year_data': year_data,
                'summary': summary,
                'date_range': {
                    'start_year': start_year,
                    'end_year': end_year,
                    'years': len(year_data)
                }
            }

        except Exception as e:
            raise ValueError(f'年度统计数据获取失败: {str(e)}')

    def _get_warehouse_yearly_stats(self, warehouse_id, start_date, end_date):
        """获取指定仓库在指定年份的统计数据"""
        try:
            from datetime import datetime

            # 将date转换为datetime，确保正确的日期范围比较
            start_datetime = datetime.combine(start_date, datetime.min.time())
            end_datetime = datetime.combine(end_date, datetime.max.time())

            current_app.logger.info(f'查询仓库{warehouse_id}年度数据: {start_datetime} 到 {end_datetime}')

            # 获取年度进库数据
            inbound_stats = db.session.query(
                func.coalesce(func.sum(InboundRecord.pallet_count), 0).label('pallets'),
                func.coalesce(func.sum(InboundRecord.package_count), 0).label('packages'),
                func.count(InboundRecord.id).label('count')
            ).filter(
                InboundRecord.operated_warehouse_id == warehouse_id,
                InboundRecord.inbound_time >= start_datetime,
                InboundRecord.inbound_time <= end_datetime
            ).first()

            # 获取年度出库数据
            outbound_stats = db.session.query(
                func.coalesce(func.sum(OutboundRecord.pallet_count), 0).label('pallets'),
                func.coalesce(func.sum(OutboundRecord.package_count), 0).label('packages'),
                func.count(OutboundRecord.id).label('count')
            ).filter(
                OutboundRecord.operated_warehouse_id == warehouse_id,
                OutboundRecord.outbound_time >= start_datetime,
                OutboundRecord.outbound_time <= end_datetime
            ).first()

            result = {
                'count': (inbound_stats.count or 0) + (outbound_stats.count or 0),
                'pallets': (inbound_stats.pallets or 0) + (outbound_stats.pallets or 0),
                'packages': (inbound_stats.packages or 0) + (outbound_stats.packages or 0)
            }

            current_app.logger.info(f'仓库{warehouse_id}年度统计结果: {result}')
            return result

        except Exception as e:
            current_app.logger.error(f'获取仓库{warehouse_id}年度统计失败: {str(e)}')
            return {'count': 0, 'pallets': 0, 'packages': 0}

    def _get_warehouse_detailed_stats(self, warehouse_id, today, yesterday, last_year):
        """获取仓库详细统计数据（包含同比数据）"""
        # 今日数据
        today_inbound = self._get_warehouse_daily_inbound(warehouse_id, today)
        today_outbound = self._get_warehouse_daily_outbound(warehouse_id, today)

        # 昨日数据
        yesterday_inbound = self._get_warehouse_daily_inbound(warehouse_id, yesterday)
        yesterday_outbound = self._get_warehouse_daily_outbound(warehouse_id, yesterday)

        # 去年同期数据
        try:
            lastyear_inbound = self._get_warehouse_daily_inbound(warehouse_id, last_year)
            lastyear_outbound = self._get_warehouse_daily_outbound(warehouse_id, last_year)
        except:
            # 如果去年同期日期不存在（如闰年），使用空数据
            lastyear_inbound = {'count': 0, 'pallets': 0, 'packages': 0}
            lastyear_outbound = {'count': 0, 'pallets': 0, 'packages': 0}

        # 当前库存
        inventory_stats = self._get_warehouse_inventory(warehouse_id)

        return {
            'today': {
                'inbound': today_inbound['count'],
                'outbound': today_outbound['count'],
                'pallets': today_inbound['pallets'],
                'packages': today_inbound['packages'],
                'outbound_pallets': today_outbound['pallets'],
                'outbound_packages': today_outbound['packages']
            },
            'yesterday': {
                'count': yesterday_inbound['count'] + yesterday_outbound['count'],
                'pallets': yesterday_inbound['pallets'] + yesterday_outbound['pallets'],
                'packages': yesterday_inbound['packages'] + yesterday_outbound['packages']
            },
            'last_year': {
                'count': lastyear_inbound['count'] + lastyear_outbound['count'],
                'pallets': lastyear_inbound['pallets'] + lastyear_outbound['pallets'],
                'packages': lastyear_inbound['packages'] + lastyear_outbound['packages']
            },
            'inventory': inventory_stats
        }

    def get_comparison_data(self, user, compare_type='week'):
        """获取对比数据"""
        if compare_type == 'day':
            return self._get_daily_comparison(user)
        elif compare_type == 'week':
            return self._get_weekly_comparison(user)
        elif compare_type == 'month':
            return self._get_monthly_comparison(user)
        elif compare_type == 'year':
            return self._get_yearly_comparison(user)
        else:
            return self._get_weekly_comparison(user)

    def _get_daily_inbound_stats(self, date, user):
        """获取指定日期的入库统计 - 按识别编码去重计算票数"""
        query = db.session.query(
            func.count(func.distinct(InboundRecord.identification_code)).label('count'),
            func.coalesce(func.sum(InboundRecord.pallet_count), 0).label('pallets'),
            func.coalesce(func.sum(InboundRecord.package_count), 0).label('packages'),
            func.coalesce(func.sum(InboundRecord.weight), 0).label('weight'),
            func.coalesce(func.sum(InboundRecord.volume), 0).label('volume')
        ).filter(
            func.date(InboundRecord.inbound_time) == date
        )

        # 根据用户权限过滤仓库
        if not user.is_super_admin() and user.warehouse_id:
            query = query.filter(InboundRecord.operated_warehouse_id == user.warehouse_id)

        result = query.first()

        return {
            'count': result.count or 0,
            'pallets': float(result.pallets or 0),
            'packages': int(result.packages or 0),
            'weight': float(result.weight or 0),
            'volume': float(result.volume or 0)
        }

    def _get_daily_outbound_stats(self, date, user):
        """获取指定日期的出库统计 - 按识别编码去重计算票数"""
        query = db.session.query(
            func.count(func.distinct(OutboundRecord.identification_code)).label('count'),
            func.coalesce(func.sum(OutboundRecord.pallet_count), 0).label('pallets'),
            func.coalesce(func.sum(OutboundRecord.package_count), 0).label('packages'),
            func.coalesce(func.sum(OutboundRecord.weight), 0).label('weight'),
            func.coalesce(func.sum(OutboundRecord.volume), 0).label('volume')
        ).filter(
            func.date(OutboundRecord.outbound_time) == date
        )

        # 根据用户权限过滤仓库
        if not user.is_super_admin() and user.warehouse_id:
            query = query.filter(OutboundRecord.operated_warehouse_id == user.warehouse_id)

        result = query.first()

        return {
            'count': result.count or 0,
            'pallets': float(result.pallets or 0),
            'packages': int(result.packages or 0),
            'weight': float(result.weight or 0),
            'volume': float(result.volume or 0)
        }

    def _get_inventory_stats(self, user):
        """获取库存统计"""
        query = db.session.query(
            func.count(Inventory.id).label('count'),
            func.coalesce(func.sum(Inventory.pallet_count), 0).label('pallets'),
            func.coalesce(func.sum(Inventory.package_count), 0).label('packages'),
            func.coalesce(func.sum(Inventory.weight), 0).label('weight'),
            func.coalesce(func.sum(Inventory.volume), 0).label('volume')
        )
        
        # 根据用户权限过滤仓库
        if not user.is_super_admin() and user.warehouse_id:
            query = query.filter(Inventory.operated_warehouse_id == user.warehouse_id)
        
        result = query.first()
        
        return {
            'count': result.count or 0,
            'pallets': float(result.pallets or 0),
            'packages': int(result.packages or 0),
            'weight': float(result.weight or 0),
            'volume': float(result.volume or 0)
        }

    def _get_transit_stats(self, user):
        """获取在途货物统计"""
        query = db.session.query(
            func.count(TransitCargo.id).label('count'),
            func.coalesce(func.sum(TransitCargo.pallet_count), 0).label('pallets'),
            func.coalesce(func.sum(TransitCargo.package_count), 0).label('packages'),
            func.coalesce(func.sum(TransitCargo.weight), 0).label('weight'),
            func.coalesce(func.sum(TransitCargo.volume), 0).label('volume')
        ).filter(
            TransitCargo.status == 'in_transit'
        )
        
        # 根据用户权限过滤仓库
        if not user.is_super_admin() and user.warehouse_id:
            query = query.filter(
                or_(
                    TransitCargo.source_warehouse_id == user.warehouse_id,
                    TransitCargo.destination_warehouse_id == user.warehouse_id
                )
            )
        
        result = query.first()
        
        return {
            'count': result.count or 0,
            'pallets': float(result.pallets or 0),
            'packages': int(result.packages or 0),
            'weight': float(result.weight or 0),
            'volume': float(result.volume or 0)
        }

    def _calculate_growth(self, current_data, previous_data):
        """计算增长率"""
        growth = {}
        
        for key in ['count', 'pallets', 'packages', 'weight', 'volume']:
            current_val = current_data.get(key, 0)
            previous_val = previous_data.get(key, 0)
            
            if previous_val == 0:
                growth[key] = 100.0 if current_val > 0 else 0.0
            else:
                growth[key] = round(((current_val - previous_val) / previous_val) * 100, 2)
        
        return growth

    def _get_accessible_warehouses(self, user):
        """获取用户可访问的仓库列表"""
        try:
            # 检查是否为超级管理员
            is_super_admin = False
            if hasattr(user, 'is_super_admin') and callable(getattr(user, 'is_super_admin')):
                is_super_admin = user.is_super_admin()
            elif hasattr(user, 'is_admin') and user.is_admin:
                is_super_admin = True
            elif hasattr(user, 'username') and user.username == 'admin':
                is_super_admin = True

            if is_super_admin:
                return list(self.warehouse_names.keys())
            elif hasattr(user, 'warehouse_id') and user.warehouse_id:
                return [user.warehouse_id]
            else:
                # 默认返回所有仓库（用于管理员或测试）
                return list(self.warehouse_names.keys())
        except Exception as e:
            current_app.logger.error(f'获取用户可访问仓库失败: {str(e)}')
            # 出错时返回所有仓库
            return list(self.warehouse_names.keys())

    def _get_warehouse_daily_inbound(self, warehouse_id, date):
        """获取指定仓库指定日期的入库统计"""
        result = db.session.query(
            func.count(InboundRecord.id).label('count'),
            func.coalesce(func.sum(InboundRecord.pallet_count), 0).label('pallets'),
            func.coalesce(func.sum(InboundRecord.package_count), 0).label('packages')
        ).filter(
            InboundRecord.operated_warehouse_id == warehouse_id,
            func.date(InboundRecord.inbound_time) == date
        ).first()
        
        return {
            'count': result.count or 0,
            'pallets': float(result.pallets or 0),
            'packages': int(result.packages or 0)
        }

    def _get_warehouse_daily_outbound(self, warehouse_id, date):
        """获取指定仓库指定日期的出库统计"""
        result = db.session.query(
            func.count(OutboundRecord.id).label('count'),
            func.coalesce(func.sum(OutboundRecord.pallet_count), 0).label('pallets'),
            func.coalesce(func.sum(OutboundRecord.package_count), 0).label('packages')
        ).filter(
            OutboundRecord.operated_warehouse_id == warehouse_id,
            func.date(OutboundRecord.outbound_time) == date
        ).first()
        
        return {
            'count': result.count or 0,
            'pallets': float(result.pallets or 0),
            'packages': int(result.packages or 0)
        }

    def _get_warehouse_inventory(self, warehouse_id):
        """获取指定仓库的库存统计，包括超期库存"""
        from datetime import datetime, timedelta

        # 计算时间阈值
        now = datetime.now()
        one_day_ago = now - timedelta(days=1)
        three_days_ago = now - timedelta(days=3)

        # 基本库存统计 - 按识别编码去重计算票数
        basic_result = db.session.query(
            func.count(func.distinct(Inventory.identification_code)).label('count'),
            func.coalesce(func.sum(Inventory.pallet_count), 0).label('pallets'),
            func.coalesce(func.sum(Inventory.package_count), 0).label('packages')
        ).filter(
            Inventory.operated_warehouse_id == warehouse_id
        ).first()

        # 超出1天的库存统计 - 按识别编码去重计算票数
        overdue_1day_result = db.session.query(
            func.count(func.distinct(Inventory.identification_code)).label('count'),
            func.coalesce(func.sum(Inventory.pallet_count), 0).label('pallets'),
            func.coalesce(func.sum(Inventory.package_count), 0).label('packages')
        ).filter(
            Inventory.operated_warehouse_id == warehouse_id,
            Inventory.inbound_time < one_day_ago
        ).first()

        # 超出3天的库存统计 - 按识别编码去重计算票数
        overdue_3days_result = db.session.query(
            func.count(func.distinct(Inventory.identification_code)).label('count'),
            func.coalesce(func.sum(Inventory.pallet_count), 0).label('pallets'),
            func.coalesce(func.sum(Inventory.package_count), 0).label('packages')
        ).filter(
            Inventory.operated_warehouse_id == warehouse_id,
            Inventory.inbound_time < three_days_ago
        ).first()

        return {
            'count': basic_result.count or 0,
            'pallets': float(basic_result.pallets or 0),
            'packages': int(basic_result.packages or 0),
            'overdue_1day': {
                'count': overdue_1day_result.count or 0,
                'pallets': float(overdue_1day_result.pallets or 0),
                'packages': int(overdue_1day_result.packages or 0)
            },
            'overdue_3days': {
                'count': overdue_3days_result.count or 0,
                'pallets': float(overdue_3days_result.pallets or 0),
                'packages': int(overdue_3days_result.packages or 0)
            }
        }

    def _get_warehouse_group_total(self, warehouse_ids, date):
        """获取仓库组的总计数据"""
        inbound_result = db.session.query(
            func.count(InboundRecord.id).label('count'),
            func.coalesce(func.sum(InboundRecord.pallet_count), 0).label('pallets'),
            func.coalesce(func.sum(InboundRecord.package_count), 0).label('packages')
        ).filter(
            InboundRecord.operated_warehouse_id.in_(warehouse_ids),
            func.date(InboundRecord.inbound_time) == date
        ).first()

        outbound_result = db.session.query(
            func.count(OutboundRecord.id).label('count'),
            func.coalesce(func.sum(OutboundRecord.pallet_count), 0).label('pallets'),
            func.coalesce(func.sum(OutboundRecord.package_count), 0).label('packages')
        ).filter(
            OutboundRecord.operated_warehouse_id.in_(warehouse_ids),
            func.date(OutboundRecord.outbound_time) == date
        ).first()

        return {
            'inbound': {
                'count': inbound_result.count or 0,
                'pallets': float(inbound_result.pallets or 0),
                'packages': int(inbound_result.packages or 0)
            },
            'outbound': {
                'count': outbound_result.count or 0,
                'pallets': float(outbound_result.pallets or 0),
                'packages': int(outbound_result.packages or 0)
            }
        }

    def _get_weekly_trends(self, user):
        """获取周趋势数据"""
        today = datetime.now().date()
        # 获取本周一
        week_start = today - timedelta(days=today.weekday())

        trends_data = []

        for i in range(7):  # 一周7天
            date = week_start + timedelta(days=i)
            inbound_stats = self._get_daily_inbound_stats(date, user)
            outbound_stats = self._get_daily_outbound_stats(date, user)

            trends_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'weekday': date.strftime('%A'),
                'weekday_cn': ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][date.weekday()],
                'inbound': inbound_stats,
                'outbound': outbound_stats
            })

        return {
            'period': 'week',
            'start_date': week_start.strftime('%Y-%m-%d'),
            'end_date': (week_start + timedelta(days=6)).strftime('%Y-%m-%d'),
            'data': trends_data
        }

    def _get_daily_trends(self, user):
        """获取日趋势数据（最近7天）"""
        today = datetime.now().date()

        trends_data = []

        for i in range(7):  # 最近7天
            date = today - timedelta(days=6-i)
            inbound_stats = self._get_daily_inbound_stats(date, user)
            outbound_stats = self._get_daily_outbound_stats(date, user)

            trends_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'weekday_cn': ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][date.weekday()],
                'inbound': inbound_stats,
                'outbound': outbound_stats
            })

        return {
            'period': 'day',
            'start_date': (today - timedelta(days=6)).strftime('%Y-%m-%d'),
            'end_date': today.strftime('%Y-%m-%d'),
            'data': trends_data
        }

    def _get_monthly_trends(self, user):
        """获取月趋势数据（本自然月每日数据）"""
        today = datetime.now().date()

        # 获取本月第一天
        month_start = today.replace(day=1)

        # 获取本月最后一天
        if today.month == 12:
            month_end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            month_end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)

        trends_data = []
        current_date = month_start

        # 遍历本月每一天
        while current_date <= min(today, month_end):
            inbound_stats = self._get_daily_inbound_stats(current_date, user)
            outbound_stats = self._get_daily_outbound_stats(current_date, user)

            trends_data.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'day': current_date.day,
                'weekday_cn': ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][current_date.weekday()],
                'inbound': inbound_stats,
                'outbound': outbound_stats
            })

            current_date += timedelta(days=1)

        return {
            'period': 'month',
            'month_name': f'{today.year}年{today.month}月',
            'start_date': month_start.strftime('%Y-%m-%d'),
            'end_date': min(today, month_end).strftime('%Y-%m-%d'),
            'data': trends_data
        }

    def _get_monthly_trends_separated(self, user):
        """获取月趋势数据（分前端仓和后端仓）"""
        today = datetime.now().date()

        # 获取本月第一天
        month_start = today.replace(day=1)

        # 获取本月最后一天
        if today.month == 12:
            month_end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            month_end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)

        trends_data = []
        current_date = month_start

        # 遍历本月每一天
        while current_date <= min(today, month_end):
            # 分别获取前端仓和后端仓的数据
            frontend_inbound = self._get_daily_inbound_stats_by_warehouse_type(current_date, user, 'frontend')
            frontend_outbound = self._get_daily_outbound_stats_by_warehouse_type(current_date, user, 'frontend')
            backend_inbound = self._get_daily_inbound_stats_by_warehouse_type(current_date, user, 'backend')
            backend_outbound = self._get_daily_outbound_stats_by_warehouse_type(current_date, user, 'backend')

            trends_data.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'day': current_date.day,
                'weekday_cn': ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][current_date.weekday()],
                'frontend_inbound': frontend_inbound,
                'frontend_outbound': frontend_outbound,
                'backend_inbound': backend_inbound,
                'backend_outbound': backend_outbound
            })

            current_date += timedelta(days=1)

        return {
            'period': 'month',
            'month_name': f'{today.year}年{today.month}月',
            'start_date': month_start.strftime('%Y-%m-%d'),
            'end_date': min(today, month_end).strftime('%Y-%m-%d'),
            'data': trends_data,
            'separated': True  # 标识这是分离的数据
        }

    def _get_daily_inbound_stats_by_warehouse_type(self, date, user, warehouse_type):
        """按仓库类型获取每日进货统计"""
        if warehouse_type == 'frontend':
            warehouse_ids = self.frontend_warehouses
        else:
            warehouse_ids = self.backend_warehouses

        # 根据用户权限过滤仓库
        accessible_warehouses = self._filter_accessible_warehouses(user, warehouse_ids)

        if not accessible_warehouses:
            return {'count': 0, 'pallets': 0, 'packages': 0}

        query = db.session.query(
            func.count(func.distinct(InboundRecord.identification_code)).label('count'),
            func.coalesce(func.sum(InboundRecord.pallet_count), 0).label('pallets'),
            func.coalesce(func.sum(InboundRecord.package_count), 0).label('packages')
        ).filter(
            and_(
                func.date(InboundRecord.inbound_time) == date,
                InboundRecord.operated_warehouse_id.in_(accessible_warehouses)
            )
        )

        result = query.first()
        return {
            'count': result.count or 0,
            'pallets': int(result.pallets or 0),
            'packages': int(result.packages or 0)
        }

    def _get_daily_outbound_stats_by_warehouse_type(self, date, user, warehouse_type):
        """按仓库类型获取每日出货统计"""
        if warehouse_type == 'frontend':
            warehouse_ids = self.frontend_warehouses
        else:
            warehouse_ids = self.backend_warehouses

        # 根据用户权限过滤仓库
        accessible_warehouses = self._filter_accessible_warehouses(user, warehouse_ids)

        if not accessible_warehouses:
            return {'count': 0, 'pallets': 0, 'packages': 0}

        query = db.session.query(
            func.count(func.distinct(OutboundRecord.identification_code)).label('count'),
            func.coalesce(func.sum(OutboundRecord.pallet_count), 0).label('pallets'),
            func.coalesce(func.sum(OutboundRecord.package_count), 0).label('packages')
        ).filter(
            and_(
                func.date(OutboundRecord.departure_time) == date,
                OutboundRecord.operated_warehouse_id.in_(accessible_warehouses)
            )
        )

        result = query.first()
        return {
            'count': result.count or 0,
            'pallets': int(result.pallets or 0),
            'packages': int(result.packages or 0)
        }

    def _filter_accessible_warehouses(self, user, warehouse_ids):
        """过滤用户可访问的仓库列表"""
        if user.is_super_admin():
            return warehouse_ids
        elif hasattr(user, 'warehouse_id') and user.warehouse_id:
            return [user.warehouse_id] if user.warehouse_id in warehouse_ids else []
        else:
            return warehouse_ids  # 如果没有特定仓库限制，返回所有

    def _get_weekly_trends_separated(self, user):
        """获取周趋势数据（分前端仓和后端仓）"""
        today = datetime.now().date()
        monday = today - timedelta(days=today.weekday())

        trends_data = []

        for i in range(7):
            date = monday + timedelta(days=i)

            # 分别获取前端仓和后端仓的数据
            frontend_inbound = self._get_daily_inbound_stats_by_warehouse_type(date, user, 'frontend')
            frontend_outbound = self._get_daily_outbound_stats_by_warehouse_type(date, user, 'frontend')
            backend_inbound = self._get_daily_inbound_stats_by_warehouse_type(date, user, 'backend')
            backend_outbound = self._get_daily_outbound_stats_by_warehouse_type(date, user, 'backend')

            trends_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'weekday_cn': ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][i],
                'frontend_inbound': frontend_inbound,
                'frontend_outbound': frontend_outbound,
                'backend_inbound': backend_inbound,
                'backend_outbound': backend_outbound
            })

        return {
            'period': 'week',
            'start_date': monday.strftime('%Y-%m-%d'),
            'end_date': (monday + timedelta(days=6)).strftime('%Y-%m-%d'),
            'data': trends_data,
            'separated': True
        }

    def _get_daily_trends_separated(self, user):
        """获取日趋势数据（分前端仓和后端仓）"""
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)

        # 分别获取前端仓和后端仓的数据
        today_frontend_inbound = self._get_daily_inbound_stats_by_warehouse_type(today, user, 'frontend')
        today_frontend_outbound = self._get_daily_outbound_stats_by_warehouse_type(today, user, 'frontend')
        today_backend_inbound = self._get_daily_inbound_stats_by_warehouse_type(today, user, 'backend')
        today_backend_outbound = self._get_daily_outbound_stats_by_warehouse_type(today, user, 'backend')

        yesterday_frontend_inbound = self._get_daily_inbound_stats_by_warehouse_type(yesterday, user, 'frontend')
        yesterday_frontend_outbound = self._get_daily_outbound_stats_by_warehouse_type(yesterday, user, 'frontend')
        yesterday_backend_inbound = self._get_daily_inbound_stats_by_warehouse_type(yesterday, user, 'backend')
        yesterday_backend_outbound = self._get_daily_outbound_stats_by_warehouse_type(yesterday, user, 'backend')

        trends_data = [
            {
                'date': yesterday.strftime('%Y-%m-%d'),
                'weekday_cn': '昨天',
                'frontend_inbound': yesterday_frontend_inbound,
                'frontend_outbound': yesterday_frontend_outbound,
                'backend_inbound': yesterday_backend_inbound,
                'backend_outbound': yesterday_backend_outbound
            },
            {
                'date': today.strftime('%Y-%m-%d'),
                'weekday_cn': '今天',
                'frontend_inbound': today_frontend_inbound,
                'frontend_outbound': today_frontend_outbound,
                'backend_inbound': today_backend_inbound,
                'backend_outbound': today_backend_outbound
            }
        ]

        return {
            'period': 'day',
            'start_date': yesterday.strftime('%Y-%m-%d'),
            'end_date': today.strftime('%Y-%m-%d'),
            'data': trends_data,
            'separated': True
        }

    def _get_yearly_trends_separated(self, user):
        """获取年趋势数据（分前端仓和后端仓）"""
        today = datetime.now().date()
        year_start = today.replace(month=1, day=1)

        trends_data = []

        for month in range(1, today.month + 1):
            month_start = today.replace(month=month, day=1)
            if month == 12:
                month_end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                month_end = today.replace(month=month + 1, day=1) - timedelta(days=1)

            # 如果是当前月，只统计到今天
            if month == today.month:
                month_end = today

            # 分别获取前端仓和后端仓的数据
            frontend_inbound = self._get_period_stats_by_warehouse_type(month_start, month_end, user, 'inbound', 'frontend')
            frontend_outbound = self._get_period_stats_by_warehouse_type(month_start, month_end, user, 'outbound', 'frontend')
            backend_inbound = self._get_period_stats_by_warehouse_type(month_start, month_end, user, 'inbound', 'backend')
            backend_outbound = self._get_period_stats_by_warehouse_type(month_start, month_end, user, 'outbound', 'backend')

            trends_data.append({
                'month': month,
                'month_name': f'{month}月',
                'frontend_inbound': frontend_inbound,
                'frontend_outbound': frontend_outbound,
                'backend_inbound': backend_inbound,
                'backend_outbound': backend_outbound
            })

        return {
            'period': 'year',
            'year': today.year,
            'start_date': year_start.strftime('%Y-%m-%d'),
            'end_date': today.strftime('%Y-%m-%d'),
            'data': trends_data,
            'separated': True
        }

    def _get_period_stats_by_warehouse_type(self, start_date, end_date, user, stat_type, warehouse_type):
        """按仓库类型获取时间段统计"""
        if warehouse_type == 'frontend':
            warehouse_ids = self.frontend_warehouses
        else:
            warehouse_ids = self.backend_warehouses

        # 根据用户权限过滤仓库
        accessible_warehouses = self._filter_accessible_warehouses(user, warehouse_ids)

        if not accessible_warehouses:
            return {'count': 0, 'pallets': 0, 'packages': 0}

        if stat_type == 'inbound':
            query = db.session.query(
                func.count(InboundRecord.id).label('count'),
                func.coalesce(func.sum(InboundRecord.pallet_count), 0).label('pallets'),
                func.coalesce(func.sum(InboundRecord.package_count), 0).label('packages')
            ).filter(
                and_(
                    func.date(InboundRecord.inbound_time) >= start_date,
                    func.date(InboundRecord.inbound_time) <= end_date,
                    InboundRecord.operated_warehouse_id.in_(accessible_warehouses)
                )
            )
        else:  # outbound
            query = db.session.query(
                func.count(OutboundRecord.id).label('count'),
                func.coalesce(func.sum(OutboundRecord.pallet_count), 0).label('pallets'),
                func.coalesce(func.sum(OutboundRecord.package_count), 0).label('packages')
            ).filter(
                and_(
                    func.date(OutboundRecord.departure_time) >= start_date,
                    func.date(OutboundRecord.departure_time) <= end_date,
                    OutboundRecord.operated_warehouse_id.in_(accessible_warehouses)
                )
            )

        result = query.first()
        return {
            'count': result.count or 0,
            'pallets': int(result.pallets or 0),
            'packages': int(result.packages or 0)
        }

    def _get_yearly_trends(self, user):
        """获取年趋势数据（最近12个月）"""
        today = datetime.now().date()

        trends_data = []

        for i in range(12):  # 最近12个月
            # 计算月份
            year = today.year
            month = today.month - i
            if month <= 0:
                month += 12
                year -= 1

            # 获取该月的第一天和最后一天
            month_start = datetime(year, month, 1).date()
            if month == 12:
                month_end = datetime(year + 1, 1, 1).date() - timedelta(days=1)
            else:
                month_end = datetime(year, month + 1, 1).date() - timedelta(days=1)

            # 获取该月的统计数据
            inbound_stats = self._get_period_stats(month_start, month_end, user, 'inbound')
            outbound_stats = self._get_period_stats(month_start, month_end, user, 'outbound')

            trends_data.insert(0, {  # 插入到开头，保持时间顺序
                'year': year,
                'month': month,
                'month_name': f'{year}年{month}月',
                'start_date': month_start.strftime('%Y-%m-%d'),
                'end_date': month_end.strftime('%Y-%m-%d'),
                'inbound': inbound_stats,
                'outbound': outbound_stats
            })

        return {
            'period': 'year',
            'data': trends_data
        }

    def _get_period_stats(self, start_date, end_date, user, record_type):
        """获取指定时间段的统计数据"""
        if record_type == 'inbound':
            query = db.session.query(
                func.count(InboundRecord.id).label('count'),
                func.coalesce(func.sum(InboundRecord.pallet_count), 0).label('pallets'),
                func.coalesce(func.sum(InboundRecord.package_count), 0).label('packages'),
                func.coalesce(func.sum(InboundRecord.weight), 0).label('weight'),
                func.coalesce(func.sum(InboundRecord.volume), 0).label('volume')
            ).filter(
                func.date(InboundRecord.inbound_time) >= start_date,
                func.date(InboundRecord.inbound_time) <= end_date
            )

            if not user.is_super_admin() and user.warehouse_id:
                query = query.filter(InboundRecord.operated_warehouse_id == user.warehouse_id)

        else:  # outbound
            query = db.session.query(
                func.count(OutboundRecord.id).label('count'),
                func.coalesce(func.sum(OutboundRecord.pallet_count), 0).label('pallets'),
                func.coalesce(func.sum(OutboundRecord.package_count), 0).label('packages'),
                func.coalesce(func.sum(OutboundRecord.weight), 0).label('weight'),
                func.coalesce(func.sum(OutboundRecord.volume), 0).label('volume')
            ).filter(
                func.date(OutboundRecord.outbound_time) >= start_date,
                func.date(OutboundRecord.outbound_time) <= end_date
            )

            if not user.is_super_admin() and user.warehouse_id:
                query = query.filter(OutboundRecord.operated_warehouse_id == user.warehouse_id)

        result = query.first()

        return {
            'count': result.count or 0,
            'pallets': float(result.pallets or 0),
            'packages': int(result.packages or 0),
            'weight': float(result.weight or 0),
            'volume': float(result.volume or 0)
        }

    def _get_weekly_comparison(self, user):
        """获取周对比数据"""
        today = datetime.now().date()

        # 本周
        this_week_start = today - timedelta(days=today.weekday())
        this_week_end = this_week_start + timedelta(days=6)

        # 上周
        last_week_start = this_week_start - timedelta(days=7)
        last_week_end = last_week_start + timedelta(days=6)

        this_week_inbound = self._get_period_stats(this_week_start, this_week_end, user, 'inbound')
        this_week_outbound = self._get_period_stats(this_week_start, this_week_end, user, 'outbound')

        last_week_inbound = self._get_period_stats(last_week_start, last_week_end, user, 'inbound')
        last_week_outbound = self._get_period_stats(last_week_start, last_week_end, user, 'outbound')

        return {
            'compare_type': 'week',
            'current': {
                'period': f'{this_week_start.strftime("%Y-%m-%d")} 至 {this_week_end.strftime("%Y-%m-%d")}',
                'inbound': this_week_inbound,
                'outbound': this_week_outbound
            },
            'previous': {
                'period': f'{last_week_start.strftime("%Y-%m-%d")} 至 {last_week_end.strftime("%Y-%m-%d")}',
                'inbound': last_week_inbound,
                'outbound': last_week_outbound
            },
            'growth': {
                'inbound': self._calculate_growth(this_week_inbound, last_week_inbound),
                'outbound': self._calculate_growth(this_week_outbound, last_week_outbound)
            }
        }

    def _get_monthly_comparison(self, user):
        """获取月对比数据（自然月对比）"""
        today = datetime.now().date()

        # 本月（截止到今天）
        this_month_start = today.replace(day=1)
        this_month_end = today  # 只统计到今天

        # 上月（完整月份）
        if today.month == 1:
            last_month_start = today.replace(year=today.year - 1, month=12, day=1)
            last_month_end = today.replace(day=1) - timedelta(days=1)
        else:
            last_month_start = today.replace(month=today.month - 1, day=1)
            last_month_end = today.replace(day=1) - timedelta(days=1)

        # 为了公平对比，上月也只统计到相同的日期
        # 例如：如果今天是3月15日，那么对比2月1日-2月15日 vs 3月1日-3月15日
        if last_month_end.day >= today.day:
            last_month_comparison_end = last_month_start.replace(day=today.day)
        else:
            # 如果上月没有对应的日期（如2月没有30日），则使用上月最后一天
            last_month_comparison_end = last_month_end

        this_month_inbound = self._get_period_stats(this_month_start, this_month_end, user, 'inbound')
        this_month_outbound = self._get_period_stats(this_month_start, this_month_end, user, 'outbound')

        last_month_inbound = self._get_period_stats(last_month_start, last_month_comparison_end, user, 'inbound')
        last_month_outbound = self._get_period_stats(last_month_start, last_month_comparison_end, user, 'outbound')

        return {
            'compare_type': 'month',
            'current': {
                'period': f'{this_month_start.strftime("%Y年%m月")}（截至{today.day}日）',
                'date_range': f'{this_month_start.strftime("%m月%d日")} - {this_month_end.strftime("%m月%d日")}',
                'inbound': this_month_inbound,
                'outbound': this_month_outbound
            },
            'previous': {
                'period': f'{last_month_start.strftime("%Y年%m月")}（同期）',
                'date_range': f'{last_month_start.strftime("%m月%d日")} - {last_month_comparison_end.strftime("%m月%d日")}',
                'inbound': last_month_inbound,
                'outbound': last_month_outbound
            },
            'growth': {
                'inbound': self._calculate_growth(this_month_inbound, last_month_inbound),
                'outbound': self._calculate_growth(this_month_outbound, last_month_outbound)
            }
        }

    def _get_daily_comparison(self, user):
        """获取日对比数据"""
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)

        today_inbound = self._get_daily_inbound_stats(today, user)
        today_outbound = self._get_daily_outbound_stats(today, user)

        yesterday_inbound = self._get_daily_inbound_stats(yesterday, user)
        yesterday_outbound = self._get_daily_outbound_stats(yesterday, user)

        return {
            'compare_type': 'day',
            'current': {
                'period': today.strftime('%Y年%m月%d日'),
                'inbound': today_inbound,
                'outbound': today_outbound
            },
            'previous': {
                'period': yesterday.strftime('%Y年%m月%d日'),
                'inbound': yesterday_inbound,
                'outbound': yesterday_outbound
            },
            'growth': {
                'inbound': self._calculate_growth(today_inbound, yesterday_inbound),
                'outbound': self._calculate_growth(today_outbound, yesterday_outbound)
            }
        }

    def _get_yearly_comparison(self, user):
        """获取年对比数据"""
        today = datetime.now().date()

        # 今年
        this_year_start = today.replace(month=1, day=1)
        this_year_end = today.replace(month=12, day=31)

        # 去年
        last_year_start = today.replace(year=today.year - 1, month=1, day=1)
        last_year_end = today.replace(year=today.year - 1, month=12, day=31)

        this_year_inbound = self._get_period_stats(this_year_start, this_year_end, user, 'inbound')
        this_year_outbound = self._get_period_stats(this_year_start, this_year_end, user, 'outbound')

        last_year_inbound = self._get_period_stats(last_year_start, last_year_end, user, 'inbound')
        last_year_outbound = self._get_period_stats(last_year_start, last_year_end, user, 'outbound')

        return {
            'compare_type': 'year',
            'current': {
                'period': f'{today.year}年',
                'inbound': this_year_inbound,
                'outbound': this_year_outbound
            },
            'previous': {
                'period': f'{today.year - 1}年',
                'inbound': last_year_inbound,
                'outbound': last_year_outbound
            },
            'growth': {
                'inbound': self._calculate_growth(this_year_inbound, last_year_inbound),
                'outbound': self._calculate_growth(this_year_outbound, last_year_outbound)
            }
        }
