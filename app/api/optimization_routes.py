#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统优化监控API路由
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import psutil
from app import db
from app.models import SystemOptimizationLog
from app.decorators import require_permission

# 创建蓝图
optimization_api = Blueprint('optimization_api', __name__)

@optimization_api.route('/status')
@login_required
@require_permission('ADMIN_MANAGEMENT')
def get_optimization_status():
    """获取优化系统状态"""
    try:
        # 获取持续优化服务状态
        from app.services.continuous_optimization_service import continuous_optimization_service
        optimization_status = continuous_optimization_service.get_optimization_status()
        
        # 获取缓存系统状态
        cache_status = get_cache_status()
        
        # 获取系统资源状态
        system_status = get_system_status()
        
        # 获取最近的优化日志
        recent_logs = get_recent_optimization_logs()
        
        return jsonify({
            'success': True,
            'data': {
                'optimization_service': optimization_status,
                'cache_system': cache_status,
                'system_resources': system_status,
                'recent_logs': recent_logs,
                'timestamp': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取优化状态失败: {str(e)}'
        }), 500

@optimization_api.route('/cache/status')
@login_required
@require_permission('ADMIN_MANAGEMENT')
def get_cache_system_status():
    """获取缓存系统详细状态"""
    try:
        cache_status = get_cache_status()
        
        # 获取缓存统计信息
        cache_stats = get_cache_statistics()
        
        return jsonify({
            'success': True,
            'data': {
                'status': cache_status,
                'statistics': cache_stats,
                'timestamp': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取缓存状态失败: {str(e)}'
        }), 500

@optimization_api.route('/cache/clear', methods=['POST'])
@login_required
@require_permission('ADMIN_MANAGEMENT')
def clear_cache():
    """清空缓存"""
    try:
        from app.cache_config import get_cache_manager
        cache_manager = get_cache_manager()
        
        redis_client = cache_manager.redis_manager.get_client()
        if redis_client:
            redis_client.flushdb()
            
            # 记录操作日志
            log_entry = SystemOptimizationLog(
                optimization_type='manual_cache_clear',
                message=f'用户 {current_user.username} 手动清空缓存',
                timestamp=datetime.now()
            )
            db.session.add(log_entry)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': '缓存已清空'
            })
        else:
            return jsonify({
                'success': False,
                'message': '缓存系统不可用'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'清空缓存失败: {str(e)}'
        }), 500

@optimization_api.route('/cache/warmup', methods=['POST'])
@login_required
@require_permission('ADMIN_MANAGEMENT')
def warmup_cache():
    """预热缓存"""
    try:
        from app.hot_data_cache import cache_warmup
        cache_warmup.warmup_basic_data_cache()
        
        # 记录操作日志
        log_entry = SystemOptimizationLog(
            optimization_type='manual_cache_warmup',
            message=f'用户 {current_user.username} 手动预热缓存',
            timestamp=datetime.now()
        )
        db.session.add(log_entry)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '缓存预热完成'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'缓存预热失败: {str(e)}'
        }), 500

@optimization_api.route('/optimization/trigger', methods=['POST'])
@login_required
@require_permission('ADMIN_MANAGEMENT')
def trigger_optimization():
    """手动触发优化"""
    try:
        from app.services.continuous_optimization_service import continuous_optimization_service
        
        # 执行一次优化
        continuous_optimization_service.periodic_optimization()
        
        # 记录操作日志
        log_entry = SystemOptimizationLog(
            optimization_type='manual_trigger',
            message=f'用户 {current_user.username} 手动触发系统优化',
            timestamp=datetime.now()
        )
        db.session.add(log_entry)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '系统优化已执行'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'触发优化失败: {str(e)}'
        }), 500

@optimization_api.route('/logs')
@login_required
@require_permission('ADMIN_MANAGEMENT')
def get_optimization_logs():
    """获取优化日志"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        optimization_type = request.args.get('type', '')
        
        query = SystemOptimizationLog.query
        
        if optimization_type:
            query = query.filter(SystemOptimizationLog.optimization_type == optimization_type)
        
        logs = query.order_by(SystemOptimizationLog.timestamp.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'data': {
                'logs': [{
                    'id': log.id,
                    'optimization_type': log.optimization_type,
                    'message': log.message,
                    'timestamp': log.timestamp.isoformat()
                } for log in logs.items],
                'pagination': {
                    'page': logs.page,
                    'pages': logs.pages,
                    'per_page': logs.per_page,
                    'total': logs.total
                }
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取优化日志失败: {str(e)}'
        }), 500

def get_cache_status():
    """获取缓存状态"""
    try:
        from app.cache_config import get_cache_manager
        cache_manager = get_cache_manager()
        
        redis_client = cache_manager.redis_manager.get_client()
        if redis_client:
            redis_client.ping()
            return {
                'available': True,
                'connection': 'connected',
                'host': redis_client.connection_pool.connection_kwargs.get('host', 'unknown'),
                'port': redis_client.connection_pool.connection_kwargs.get('port', 'unknown'),
                'db': redis_client.connection_pool.connection_kwargs.get('db', 0)
            }
        else:
            return {
                'available': False,
                'connection': 'disconnected',
                'error': 'Redis client not available'
            }
            
    except Exception as e:
        return {
            'available': False,
            'connection': 'error',
            'error': str(e)
        }

def get_cache_statistics():
    """获取缓存统计信息"""
    try:
        from app.cache_config import get_cache_manager
        cache_manager = get_cache_manager()
        
        redis_client = cache_manager.redis_manager.get_client()
        if redis_client:
            info = redis_client.info()
            return {
                'memory_used': info.get('used_memory_human', 'unknown'),
                'memory_peak': info.get('used_memory_peak_human', 'unknown'),
                'connected_clients': info.get('connected_clients', 0),
                'total_commands_processed': info.get('total_commands_processed', 0),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'hit_rate': calculate_hit_rate(info.get('keyspace_hits', 0), info.get('keyspace_misses', 0))
            }
        else:
            return {}
            
    except Exception as e:
        return {'error': str(e)}

def calculate_hit_rate(hits, misses):
    """计算缓存命中率"""
    total = hits + misses
    if total == 0:
        return 0
    return round((hits / total) * 100, 2)

def get_system_status():
    """获取系统资源状态"""
    try:
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # 内存使用情况
        memory = psutil.virtual_memory()
        
        # 磁盘使用情况
        disk = psutil.disk_usage('/')
        
        return {
            'cpu': {
                'percent': cpu_percent,
                'status': 'normal' if cpu_percent < 80 else 'high'
            },
            'memory': {
                'percent': memory.percent,
                'available_mb': round(memory.available / 1024 / 1024, 1),
                'total_mb': round(memory.total / 1024 / 1024, 1),
                'status': 'normal' if memory.percent < 80 else 'high'
            },
            'disk': {
                'percent': round(disk.used / disk.total * 100, 1),
                'free_gb': round(disk.free / 1024 / 1024 / 1024, 1),
                'total_gb': round(disk.total / 1024 / 1024 / 1024, 1),
                'status': 'normal' if (disk.used / disk.total * 100) < 90 else 'high'
            }
        }
        
    except Exception as e:
        return {'error': str(e)}

def get_recent_optimization_logs(limit=10):
    """获取最近的优化日志"""
    try:
        logs = SystemOptimizationLog.query.order_by(
            SystemOptimizationLog.timestamp.desc()
        ).limit(limit).all()
        
        return [{
            'optimization_type': log.optimization_type,
            'message': log.message,
            'timestamp': log.timestamp.isoformat()
        } for log in logs]
        
    except Exception as e:
        return []
