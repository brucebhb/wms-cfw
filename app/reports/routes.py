#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统计报表路由
"""

from flask import render_template, request, jsonify, flash
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from functools import wraps
from app.reports import bp
from app.decorators import require_permission

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
@require_permission('CARGO_VOLUME_DASHBOARD')
def cargo_volume_dashboard():
    """货量报表仪表板"""
    return render_template('reports/cargo_volume_dashboard.html')

# ==================== 其他报表模块 ====================

@bp.route('/warehouse_operations')
@login_required
@require_permission('WAREHOUSE_OPERATIONS')
def warehouse_operations():
    """仓库运营分析"""
    return render_template('reports/warehouse_operations.html')

@bp.route('/customer_analysis')
@login_required
@require_permission('CUSTOMER_ANALYSIS')
def customer_analysis():
    """客户业务分析"""
    return render_template('reports/customer_analysis.html')

@bp.route('/trend_analysis')
@login_required
@require_permission('TREND_ANALYSIS')
def trend_analysis():
    """趋势预测分析"""
    return render_template('reports/trend_analysis.html')

# ==================== API接口 ====================

@bp.route('/api/cargo_volume/overview')
@api_login_required
@require_permission('STATISTICS_VIEW')
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
@require_permission('STATISTICS_VIEW')
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
@require_permission('STATISTICS_VIEW')
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
@require_permission('STATISTICS_VIEW')
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
@require_permission('STATISTICS_VIEW')
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
@require_permission('STATISTICS_VIEW')
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
