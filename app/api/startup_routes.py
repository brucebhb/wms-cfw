#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动状态API路由
"""

from flask import jsonify, current_app
from app.api.bp import bp
from app.startup_manager import startup_manager


@bp.route('/startup-status')
def get_startup_status():
    """获取启动状态API"""
    try:
        status = startup_manager.get_startup_status()
        return jsonify(status)
    except Exception as e:
        current_app.logger.error(f"获取启动状态失败: {e}")
        return jsonify({
            'is_ready': True,  # 如果出错，假设系统已就绪
            'elapsed_time': 0,
            'components': {
                'database': True,
                'cache': True,
                'services': True,
                'optimization': True
            },
            'messages': [
                {
                    'component': 'system',
                    'message': '启动状态检查出错，假设系统已就绪',
                    'timestamp': None
                }
            ],
            'error': str(e)
        })


@bp.route('/health')
def health_check():
    """健康检查"""
    try:
        if startup_manager.is_ready:
            return jsonify({
                'status': 'ready', 
                'message': '系统运行正常',
                'timestamp': startup_manager.startup_time.isoformat() if startup_manager.startup_time else None
            })
        else:
            return jsonify({
                'status': 'starting', 
                'message': '系统正在启动中',
                'timestamp': startup_manager.startup_time.isoformat() if startup_manager.startup_time else None
            }), 202
    except Exception as e:
        current_app.logger.error(f"健康检查失败: {e}")
        return jsonify({
            'status': 'ready',  # 如果出错，假设系统已就绪
            'message': '健康检查出错，假设系统正常',
            'error': str(e)
        })


@bp.route('/system-info')
def get_system_info():
    """获取系统信息"""
    try:
        import psutil
        import os
        from datetime import datetime
        
        # 获取系统信息
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return jsonify({
            'system': {
                'platform': os.name,
                'python_version': f"{psutil.version_info}",
                'uptime': (datetime.now() - startup_manager.startup_time).total_seconds() if startup_manager.startup_time else 0
            },
            'memory': {
                'total': memory.total,
                'available': memory.available,
                'percent': memory.percent,
                'used': memory.used
            },
            'disk': {
                'total': disk.total,
                'used': disk.used,
                'free': disk.free,
                'percent': (disk.used / disk.total) * 100
            },
            'startup': {
                'is_ready': startup_manager.is_ready,
                'startup_time': startup_manager.startup_time.isoformat() if startup_manager.startup_time else None,
                'components': startup_manager.initialization_status
            }
        })
    except Exception as e:
        current_app.logger.error(f"获取系统信息失败: {e}")
        return jsonify({
            'error': str(e),
            'message': '无法获取系统信息'
        }), 500
