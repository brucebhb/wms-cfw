#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
后端仓API路由
提供后端仓相关的API接口
"""

from datetime import datetime, timedelta
from flask import jsonify, request
from flask_login import login_required, current_user
from sqlalchemy import func, and_
from app.api.bp import bp
from app import db
from app.models import OutboundRecord, Inventory, TransitCargo, ReceiveRecord
from app.auth.decorators import check_permission
from app.reports.statistics_service import StatisticsService

@bp.route('/backend/statistics', methods=['GET'])
def backend_statistics():
    """获取后端仓统计数据"""
    try:
        # 简单测试返回
        return jsonify({
            'success': True,
            'message': 'API正常工作',
            'data': {
                'today_outbound': 0,
                'current_inventory': 0,
                'pending_items': 0,
                'monthly_outbound': 0,
                'warehouse_name': '凭祥北投仓',
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'API错误: {str(e)}'
        }), 500

@bp.route('/backend/dashboard', methods=['GET'])
@login_required
def backend_dashboard():
    """获取后端仓仪表板数据"""
    try:
        # 使用统计服务获取详细数据
        stats_service = StatisticsService()
        
        # 创建一个临时用户对象，限制为后端仓
        class BackendUser:
            def __init__(self):
                self.warehouse_id = 4  # 后端仓ID
                
            def is_super_admin(self):
                return current_user.is_super_admin()
        
        backend_user = BackendUser()
        dashboard_data = stats_service.get_dashboard_data(backend_user)
        
        return jsonify({
            'success': True,
            'data': dashboard_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取仪表板数据失败: {str(e)}'
        }), 500
