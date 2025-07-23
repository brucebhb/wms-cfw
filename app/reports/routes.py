#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统计报表路由
"""

from flask import render_template, request, jsonify, flash
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from functools import wraps
from sqlalchemy import func
from app import db
from app.reports import bp
from app.decorators import require_permission
from app.models import InboundRecord, OutboundRecord

def api_login_required(f):
    """API专用的登录验证装饰器，返回JSON而不是重定向"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({
                'success': False,
                'message': '请先登录系统',
                'error_code': 'AUTHENTICATION_REQUIRED'
            }), 401
        return f(*args, **kwargs)
    return decorated_function
from app.reports.cargo_volume_service import CargoVolumeService
from app.reports.customer_analysis_service import CustomerAnalysisService
from app.reports.trend_analysis_service import TrendAnalysisService
from app.reports.warehouse_operations_service import WarehouseOperationsService

# ==================== 货量报表仪表板 ====================

@bp.route('/cargo_volume_dashboard')
@login_required
# @require_permission('CARGO_VOLUME_DASHBOARD')  # 临时禁用权限检查
def cargo_volume_dashboard():
    """货量报表仪表板"""
    return render_template('reports/cargo_volume_dashboard.html')

@bp.route('/api/cargo_volume_comparison', methods=['POST'])
@login_required
def cargo_volume_comparison():
    """货量对比分析API"""
    try:
        data = request.get_json()
        period = data.get('period')

        if period == 'day':
            result = get_daily_comparison(data)
        elif period == 'week':
            result = get_weekly_comparison(data)
        elif period == 'month':
            result = get_monthly_comparison(data)
        elif period == 'year':
            result = get_yearly_comparison(data)
        else:
            return jsonify({'error': '不支持的对比周期'}), 400

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': '查询失败，请重试'}), 500

def get_daily_comparison(data):
    """日对比分析"""
    from datetime import datetime, timedelta

    start_date = datetime.strptime(data['startDate'], '%Y-%m-%d').date()
    end_date = datetime.strptime(data['endDate'], '%Y-%m-%d').date()

    # 计算日期范围
    date_range = []
    current_date = start_date
    while current_date <= end_date:
        date_range.append(current_date)
        current_date += timedelta(days=1)

    if len(date_range) > 7:
        return {'error': '日期范围不能超过7天'}

    # 查询每日数据
    daily_data = []
    for date in date_range:
        # 入库数据
        inbound_query = db.session.query(
            func.count(InboundRecord.id).label('count'),
            func.sum(InboundRecord.pallet_count).label('pallets'),
            func.sum(InboundRecord.package_count).label('packages')
        ).filter(
            func.date(InboundRecord.inbound_time) == date
        ).first()

        # 出库数据
        outbound_query = db.session.query(
            func.count(OutboundRecord.id).label('count'),
            func.sum(OutboundRecord.pallet_count).label('pallets'),
            func.sum(OutboundRecord.package_count).label('packages')
        ).filter(
            func.date(OutboundRecord.outbound_time) == date
        ).first()

        daily_data.append({
            'date': date.strftime('%Y-%m-%d'),
            'label': date.strftime('%m月%d日'),
            'inbound': inbound_query.count or 0,
            'outbound': outbound_query.count or 0,
            'pallets': (inbound_query.pallets or 0) + (outbound_query.pallets or 0),
            'packages': (inbound_query.packages or 0) + (outbound_query.packages or 0)
        })

    # 计算对比（第一天 vs 最后一天）
    if len(daily_data) >= 2:
        first_day = daily_data[0]
        last_day = daily_data[-1]

        comparison = calculate_comparison(first_day, last_day)

        return {
            'period1': first_day,
            'period2': last_day,
            'comparison': comparison,
            'chartData': {
                'categories': [d['label'] for d in daily_data],
                'inbound': [d['inbound'] for d in daily_data],
                'outbound': [d['outbound'] for d in daily_data]
            }
        }
    else:
        return {'error': '数据不足，无法进行对比'}

def get_weekly_comparison(data):
    """周对比分析"""
    from datetime import datetime, timedelta

    year = int(data['year'])
    week1 = int(data['week1'])
    week2 = int(data['week2'])

    # 如果提供了具体的日期范围，使用它们
    if data.get('week1_start') and data.get('week1_end'):
        week1_start = datetime.strptime(data['week1_start'], '%Y-%m-%d').date()
        week1_end = datetime.strptime(data['week1_end'], '%Y-%m-%d').date()
    else:
        # 否则计算周的日期范围（ISO周标准）
        week1_start, week1_end = get_iso_week_dates(year, week1)

    if data.get('week2_start') and data.get('week2_end'):
        week2_start = datetime.strptime(data['week2_start'], '%Y-%m-%d').date()
        week2_end = datetime.strptime(data['week2_end'], '%Y-%m-%d').date()
    else:
        week2_start, week2_end = get_iso_week_dates(year, week2)

    # 查询两周的数据
    week1_label = f"{year}年第{week1}周 ({week1_start.strftime('%m/%d')} ~ {week1_end.strftime('%m/%d')})"
    week2_label = f"{year}年第{week2}周 ({week2_start.strftime('%m/%d')} ~ {week2_end.strftime('%m/%d')})"

    week1_data = get_period_data(week1_start, week1_end, week1_label)
    week2_data = get_period_data(week2_start, week2_end, week2_label)

    comparison = calculate_comparison(week1_data, week2_data)

    return {
        'period1': week1_data,
        'period2': week2_data,
        'comparison': comparison,
        'chartData': {
            'categories': [f'第{week1}周', f'第{week2}周'],
            'inbound': [week1_data['inbound'], week2_data['inbound']],
            'outbound': [week1_data['outbound'], week2_data['outbound']]
        }
    }

def get_iso_week_dates(year, week):
    """获取ISO周标准的日期范围（周一到周日）"""
    from datetime import datetime, timedelta

    # 找到该年第一周的周一
    jan1 = datetime(year, 1, 1)
    # ISO周标准：第一周是包含1月4日的那一周
    jan4 = datetime(year, 1, 4)

    # 找到1月4日所在周的周一
    days_since_monday = jan4.weekday()
    first_monday = jan4 - timedelta(days=days_since_monday)

    # 计算目标周的周一
    target_monday = first_monday + timedelta(weeks=week-1)
    target_sunday = target_monday + timedelta(days=6)

    return target_monday.date(), target_sunday.date()

def get_monthly_comparison(data):
    """月对比分析"""
    from datetime import datetime
    import calendar

    year = int(data['year'])
    month1 = int(data['month1'])
    month2 = int(data['month2'])

    # 计算月份的日期范围
    def get_month_dates(year, month):
        start_date = datetime(year, month, 1).date()
        _, last_day = calendar.monthrange(year, month)
        end_date = datetime(year, month, last_day).date()
        return start_date, end_date

    month1_start, month1_end = get_month_dates(year, month1)
    month2_start, month2_end = get_month_dates(year, month2)

    # 查询两个月的数据
    month1_data = get_period_data(month1_start, month1_end, f"{year}年{month1}月")
    month2_data = get_period_data(month2_start, month2_end, f"{year}年{month2}月")

    comparison = calculate_comparison(month1_data, month2_data)

    return {
        'period1': month1_data,
        'period2': month2_data,
        'comparison': comparison,
        'chartData': {
            'categories': [f'{month1}月', f'{month2}月'],
            'inbound': [month1_data['inbound'], month2_data['inbound']],
            'outbound': [month1_data['outbound'], month2_data['outbound']]
        }
    }

def get_yearly_comparison(data):
    """年对比分析"""
    from datetime import datetime

    year1 = int(data['year1'])
    year2 = int(data['year2'])

    # 计算年份的日期范围
    year1_start = datetime(year1, 1, 1).date()
    year1_end = datetime(year1, 12, 31).date()
    year2_start = datetime(year2, 1, 1).date()
    year2_end = datetime(year2, 12, 31).date()

    # 查询两年的数据
    year1_data = get_period_data(year1_start, year1_end, f"{year1}年")
    year2_data = get_period_data(year2_start, year2_end, f"{year2}年")

    comparison = calculate_comparison(year1_data, year2_data)

    return {
        'period1': year1_data,
        'period2': year2_data,
        'comparison': comparison,
        'chartData': {
            'categories': [f'{year1}年', f'{year2}年'],
            'inbound': [year1_data['inbound'], year2_data['inbound']],
            'outbound': [year1_data['outbound'], year2_data['outbound']]
        }
    }

def get_period_data(start_date, end_date, label):
    """获取指定时间段的数据"""
    # 入库数据
    inbound_query = db.session.query(
        func.count(InboundRecord.id).label('count'),
        func.sum(InboundRecord.pallet_count).label('pallets'),
        func.sum(InboundRecord.package_count).label('packages')
    ).filter(
        func.date(InboundRecord.inbound_time) >= start_date,
        func.date(InboundRecord.inbound_time) <= end_date
    ).first()

    # 出库数据
    outbound_query = db.session.query(
        func.count(OutboundRecord.id).label('count'),
        func.sum(OutboundRecord.pallet_count).label('pallets'),
        func.sum(OutboundRecord.package_count).label('packages')
    ).filter(
        func.date(OutboundRecord.outbound_time) >= start_date,
        func.date(OutboundRecord.outbound_time) <= end_date
    ).first()

    return {
        'label': label,
        'inbound': inbound_query.count or 0,
        'outbound': outbound_query.count or 0,
        'pallets': (inbound_query.pallets or 0) + (outbound_query.pallets or 0),
        'packages': (inbound_query.packages or 0) + (outbound_query.packages or 0)
    }

def calculate_comparison(period1, period2):
    """计算对比数据"""
    def safe_divide(a, b):
        return round((a / b * 100), 1) if b != 0 else 0

    inbound_change = period2['inbound'] - period1['inbound']
    outbound_change = period2['outbound'] - period1['outbound']
    pallets_change = period2['pallets'] - period1['pallets']
    packages_change = period2['packages'] - period1['packages']

    return {
        'inbound_change': inbound_change,
        'inbound_percent': safe_divide(inbound_change, period1['inbound']) if period1['inbound'] > 0 else 0,
        'outbound_change': outbound_change,
        'outbound_percent': safe_divide(outbound_change, period1['outbound']) if period1['outbound'] > 0 else 0,
        'pallets_change': pallets_change,
        'pallets_percent': safe_divide(pallets_change, period1['pallets']) if period1['pallets'] > 0 else 0,
        'packages_change': packages_change,
        'packages_percent': safe_divide(packages_change, period1['packages']) if period1['packages'] > 0 else 0
    }

# ==================== 其他报表模块 ====================

@bp.route('/warehouse_operations')
@login_required
# @require_permission('WAREHOUSE_OPERATIONS')  # 临时禁用权限检查
def warehouse_operations():
    """仓库运营分析"""
    return render_template('reports/warehouse_operations.html')

@bp.route('/customer_analysis')
@login_required
# @require_permission('CUSTOMER_ANALYSIS')  # 临时禁用权限检查
def customer_analysis():
    """客户业务分析"""
    return render_template('reports/customer_analysis.html')

@bp.route('/trend_analysis')
@login_required
# @require_permission('TREND_ANALYSIS')  # 临时禁用权限检查
def trend_analysis():
    """趋势预测分析"""
    return render_template('reports/trend_analysis.html')

# ==================== API接口 ====================

@bp.route('/api/cargo_volume/overview')
@api_login_required
# @require_permission('STATISTICS_VIEW')  # 临时禁用权限检查
def api_cargo_volume_overview():
    """获取货量总览数据"""
    try:
        service = CargoVolumeService()
        data = service.get_overview_data(current_user)
        return jsonify({
            'success': True,
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@bp.route('/api/cargo_volume/trends')
@login_required
# @require_permission('STATISTICS_VIEW')  # 临时禁用权限检查
def api_cargo_volume_trends():
    """获取货量趋势数据"""
    try:
        period = request.args.get('period', 'week')  # day, week, month, year
        service = CargoVolumeService()
        data = service.get_trends_data(current_user, period)
        return jsonify({
            'success': True,
            'data': data,
            'period': period,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@bp.route('/api/cargo_volume/warehouse_stats')
@api_login_required
# @require_permission('STATISTICS_VIEW')  # 临时禁用权限检查
def api_cargo_volume_warehouse_stats():
    """获取仓库货量统计数据"""
    try:
        service = CargoVolumeService()
        data = service.get_warehouse_stats(current_user)
        return jsonify({
            'success': True,
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@bp.route('/api/cargo_volume/comparison')
@api_login_required
# @require_permission('STATISTICS_VIEW')  # 临时禁用权限检查
def api_cargo_volume_comparison():
    """获取货量对比数据"""
    try:
        compare_type = request.args.get('type', 'week')  # day, week, month, year
        service = CargoVolumeService()
        data = service.get_comparison_data(current_user, compare_type)
        return jsonify({
            'success': True,
            'data': data,
            'compare_type': compare_type,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@bp.route('/api/cargo_volume/day_range')
@login_required
# @require_permission('STATISTICS_VIEW')  # 临时禁用权限检查
def api_cargo_volume_day_range():
    """获取日期范围货量统计数据"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        if not start_date or not end_date:
            return jsonify({
                'success': False,
                'message': '请提供开始和结束日期',
                'timestamp': datetime.now().isoformat()
            }), 400

        service = CargoVolumeService()
        data = service.get_day_range_stats(current_user, start_date, end_date)

        return jsonify({
            'success': True,
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@bp.route('/api/cargo_volume/week_range')
@login_required
# @require_permission('STATISTICS_VIEW')  # 临时禁用权限检查
def api_cargo_volume_week_range():
    """获取周范围货量统计数据"""
    try:
        first_year = request.args.get('first_year', type=int)
        first_month = request.args.get('first_month', type=int)
        first_week = request.args.get('first_week', type=int)

        second_year = request.args.get('second_year', type=int)
        second_month = request.args.get('second_month', type=int)
        second_week = request.args.get('second_week', type=int)

        if not all([first_year, first_month, first_week]):
            return jsonify({
                'success': False,
                'message': '请提供第一周的年份、月份和周次',
                'timestamp': datetime.now().isoformat()
            }), 400

        service = CargoVolumeService()
        data = service.get_week_range_stats(
            current_user,
            first_year, first_month, first_week,
            second_year, second_month, second_week
        )

        return jsonify({
            'success': True,
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

def get_month_from_week(year, week_number):
    """根据年份和周次计算月份"""
    from datetime import date, timedelta

    # 使用ISO周计算方式
    # 第1周是包含1月4日的那一周
    jan_4 = date(year, 1, 4)

    # 找到第1周的周一
    days_since_monday = jan_4.weekday()  # 0=周一, 6=周日
    first_monday = jan_4 - timedelta(days=days_since_monday)

    # 计算指定周的周一日期
    target_monday = first_monday + timedelta(weeks=week_number-1)

    # 如果计算出的日期超出了当年，说明周次有问题
    if target_monday.year != year:
        # 简单估算：每月约4.33周
        estimated_month = min(12, max(1, int((week_number - 1) / 4.33) + 1))
        return estimated_month

    return target_monday.month

@bp.route('/api/cargo_volume/week_comparison')
@login_required
# @require_permission('STATISTICS_VIEW')  # 临时禁用权限检查
def api_cargo_volume_week_comparison():
    """简化的周对比API"""
    try:
        year = request.args.get('year', type=int)
        first_week = request.args.get('first_week', type=int)
        second_week = request.args.get('second_week', type=int)

        if not all([year, first_week, second_week]):
            return jsonify({
                'success': False,
                'message': '请提供年份和两个周次',
                'timestamp': datetime.now().isoformat()
            }), 400

        # 根据周次计算正确的月份
        first_month = get_month_from_week(year, first_week)
        second_month = get_month_from_week(year, second_week)

        service = CargoVolumeService()
        data = service.get_week_range_stats(
            current_user,
            year, first_month, first_week,
            year, second_month, second_week
        )

        return jsonify({
            'success': True,
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@bp.route('/api/cargo_volume/year_comparison')
@login_required
# @require_permission('STATISTICS_VIEW')  # 临时禁用权限检查
def api_cargo_volume_year_comparison():
    """简化的年对比API"""
    try:
        first_year = request.args.get('first_year', type=int)
        second_year = request.args.get('second_year', type=int)

        if not all([first_year, second_year]):
            return jsonify({
                'success': False,
                'message': '请提供两个年份',
                'timestamp': datetime.now().isoformat()
            }), 400

        service = CargoVolumeService()
        data = service.get_year_range_stats(
            current_user,
            first_year, second_year
        )

        return jsonify({
            'success': True,
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@bp.route('/api/cargo_volume/month_range')
@login_required
@require_permission('STATISTICS_VIEW')
def api_cargo_volume_month_range():
    """获取月份范围货量统计数据"""
    try:
        start_year = request.args.get('start_year', type=int)
        start_month = request.args.get('start_month', type=int)
        end_year = request.args.get('end_year', type=int)
        end_month = request.args.get('end_month', type=int)

        if not all([start_year, start_month, end_year, end_month]):
            return jsonify({
                'success': False,
                'message': '请提供开始和结束年月',
                'timestamp': datetime.now().isoformat()
            }), 400

        service = CargoVolumeService()
        data = service.get_month_range_stats(current_user, start_year, start_month, end_year, end_month)

        return jsonify({
            'success': True,
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@bp.route('/api/cargo_volume/year_range')
@login_required
@require_permission('STATISTICS_VIEW')
def api_cargo_volume_year_range():
    """获取年份范围货量统计数据"""
    try:
        start_year = request.args.get('start_year', type=int)
        end_year = request.args.get('end_year', type=int)

        if not start_year or not end_year:
            return jsonify({
                'success': False,
                'message': '请提供开始和结束年份',
                'timestamp': datetime.now().isoformat()
            }), 400

        service = CargoVolumeService()
        data = service.get_year_range_stats(current_user, start_year, end_year)

        return jsonify({
            'success': True,
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

# ==================== 客户业务分析API ====================

@bp.route('/api/customer/ranking')
@login_required
@require_permission('STATISTICS_VIEW')
def api_customer_ranking():
    """获取客户货量排行榜"""
    try:
        period = request.args.get('period', 'month')  # week, month, quarter, year
        limit = int(request.args.get('limit', 10))

        service = CustomerAnalysisService()
        data = service.get_customer_ranking(current_user, period, limit)

        return jsonify({
            'success': True,
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@bp.route('/api/customer/activity')
@login_required
@require_permission('STATISTICS_VIEW')
def api_customer_activity():
    """获取客户活跃度分析"""
    try:
        service = CustomerAnalysisService()
        data = service.get_customer_activity_analysis(current_user)

        return jsonify({
            'success': True,
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@bp.route('/api/customer/value')
@login_required
@require_permission('STATISTICS_VIEW')
def api_customer_value():
    """获取客户价值分析"""
    try:
        limit = int(request.args.get('limit', 20))

        service = CustomerAnalysisService()
        data = service.get_customer_value_analysis(current_user, limit)

        return jsonify({
            'success': True,
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@bp.route('/api/customer/growth')
@login_required
@require_permission('STATISTICS_VIEW')
def api_customer_growth():
    """获取客户增长趋势"""
    try:
        service = CustomerAnalysisService()
        data = service.get_customer_growth_trends(current_user)

        return jsonify({
            'success': True,
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@bp.route('/api/customer/distribution')
@login_required
@require_permission('STATISTICS_VIEW')
def api_customer_distribution():
    """获取客户分布分析"""
    try:
        service = CustomerAnalysisService()
        data = service.get_customer_distribution_analysis(current_user)

        return jsonify({
            'success': True,
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

# ==================== 趋势预测分析API ====================

@bp.route('/api/trend/forecast')
@login_required
@require_permission('STATISTICS_VIEW')
def api_trend_forecast():
    """获取货量趋势预测"""
    try:
        forecast_months = int(request.args.get('months', 3))

        service = TrendAnalysisService()
        data = service.get_cargo_volume_forecast(current_user, forecast_months)

        return jsonify({
            'success': True,
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@bp.route('/api/trend/seasonal')
@login_required
@require_permission('STATISTICS_VIEW')
def api_trend_seasonal():
    """获取季节性分析"""
    try:
        service = TrendAnalysisService()
        data = service.get_seasonal_analysis(current_user)

        return jsonify({
            'success': True,
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@bp.route('/api/trend/growth')
@login_required
@require_permission('STATISTICS_VIEW')
def api_trend_growth():
    """获取增长率分析"""
    try:
        service = TrendAnalysisService()
        data = service.get_growth_rate_analysis(current_user)

        return jsonify({
            'success': True,
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@bp.route('/api/trend/anomaly')
@login_required
@require_permission('STATISTICS_VIEW')
def api_trend_anomaly():
    """获取异常检测分析"""
    try:
        service = TrendAnalysisService()
        data = service.get_anomaly_detection(current_user)

        return jsonify({
            'success': True,
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@bp.route('/api/trend/target')
@login_required
@require_permission('STATISTICS_VIEW')
def api_trend_target():
    """获取目标达成预测"""
    try:
        monthly_target = request.args.get('target', type=float)

        service = TrendAnalysisService()
        data = service.get_target_achievement_forecast(current_user, monthly_target)

        return jsonify({
            'success': True,
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

# ==================== 仓库运营分析API ====================

@bp.route('/api/warehouse/efficiency')
@login_required
@require_permission('STATISTICS_VIEW')
def api_warehouse_efficiency():
    """获取运营效率对比分析"""
    try:
        service = WarehouseOperationsService()
        data = service.get_operational_efficiency_comparison(current_user)

        return jsonify({
            'success': True,
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@bp.route('/api/warehouse/inventory')
@login_required
@require_permission('STATISTICS_VIEW')
def api_warehouse_inventory():
    """获取库存分析"""
    try:
        service = WarehouseOperationsService()
        data = service.get_inventory_analysis(current_user)

        return jsonify({
            'success': True,
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@bp.route('/api/warehouse/time_efficiency')
@login_required
@require_permission('STATISTICS_VIEW')
def api_warehouse_time_efficiency():
    """获取时效分析"""
    try:
        service = WarehouseOperationsService()
        data = service.get_time_efficiency_analysis(current_user)

        return jsonify({
            'success': True,
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@bp.route('/api/warehouse/cargo_flow')
@login_required
@require_permission('STATISTICS_VIEW')
def api_warehouse_cargo_flow():
    """获取货物流向分析"""
    try:
        service = WarehouseOperationsService()
        data = service.get_cargo_flow_analysis(current_user)

        return jsonify({
            'success': True,
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@bp.route('/api/warehouse/capacity')
@login_required
@require_permission('STATISTICS_VIEW')
def api_warehouse_capacity():
    """获取容量利用率分析"""
    try:
        service = WarehouseOperationsService()
        data = service.get_capacity_utilization_analysis(current_user)

        return jsonify({
            'success': True,
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500
