#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能优化控制面板
提供Web界面管理和监控优化策略
"""

from flask import Blueprint, render_template, request, jsonify, current_app
from datetime import datetime, timedelta
import json
from .intelligent_optimizer import get_intelligent_optimizer, OptimizationLevel
from .optimization_config_manager import get_config_manager

optimization_bp = Blueprint('optimization', __name__, url_prefix='/optimization')

@optimization_bp.route('/dashboard')
def dashboard():
    """优化控制面板主页"""
    return render_template('optimization/dashboard.html')

@optimization_bp.route('/api/status')
def get_status():
    """获取当前优化状态"""
    try:
        optimizer = get_intelligent_optimizer()
        config_manager = get_config_manager()
        
        status = optimizer.get_current_status()
        config_summary = config_manager.get_optimization_summary()
        recommendations = optimizer.get_optimization_recommendations()
        
        return jsonify({
            'success': True,
            'data': {
                'status': status,
                'config': config_summary,
                'recommendations': recommendations,
                'timestamp': datetime.now().isoformat()
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@optimization_bp.route('/api/metrics')
def get_metrics():
    """获取系统指标"""
    try:
        optimizer = get_intelligent_optimizer()
        
        # 获取最近1小时的指标
        recent_metrics = []
        for metric in optimizer.metrics_history[-60:]:  # 最近60个数据点
            recent_metrics.append({
                'timestamp': metric.timestamp.isoformat(),
                'cpu_percent': metric.cpu_percent,
                'memory_percent': metric.memory_percent,
                'response_time': metric.response_time,
                'active_connections': metric.active_connections
            })
        
        return jsonify({
            'success': True,
            'data': {
                'metrics': recent_metrics,
                'summary': {
                    'avg_cpu': sum(m['cpu_percent'] for m in recent_metrics) / len(recent_metrics) if recent_metrics else 0,
                    'avg_memory': sum(m['memory_percent'] for m in recent_metrics) / len(recent_metrics) if recent_metrics else 0,
                    'avg_response_time': sum(m['response_time'] for m in recent_metrics) / len(recent_metrics) if recent_metrics else 0,
                    'total_connections': recent_metrics[-1]['active_connections'] if recent_metrics else 0
                }
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@optimization_bp.route('/api/set_level', methods=['POST'])
def set_optimization_level():
    """设置优化级别"""
    try:
        data = request.get_json()
        level_str = data.get('level')
        
        if level_str not in ['minimal', 'balanced', 'aggressive', 'adaptive']:
            return jsonify({
                'success': False,
                'error': '无效的优化级别'
            }), 400
        
        level = OptimizationLevel(level_str)
        optimizer = get_intelligent_optimizer()
        config_manager = get_config_manager()
        
        # 设置优化级别
        optimizer.set_optimization_level(level)
        config_manager.apply_optimization_level(level_str)
        
        current_app.logger.info(f"优化级别已手动设置为: {level_str}")
        
        return jsonify({
            'success': True,
            'message': f'优化级别已设置为: {level_str}',
            'level': level_str
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@optimization_bp.route('/api/update_config', methods=['POST'])
def update_config():
    """更新优化配置"""
    try:
        data = request.get_json()
        config_type = data.get('type')
        config_data = data.get('config', {})
        
        config_manager = get_config_manager()
        
        if config_type == 'cache':
            config_manager.update_cache_config(**config_data)
        elif config_type == 'background_tasks':
            config_manager.update_background_task_config(**config_data)
        elif config_type == 'performance_monitor':
            config_manager.update_performance_monitor_config(**config_data)
        elif config_type == 'database':
            config_manager.update_database_config(**config_data)
        else:
            return jsonify({
                'success': False,
                'error': '无效的配置类型'
            }), 400
        
        current_app.logger.info(f"配置已更新: {config_type}")
        
        return jsonify({
            'success': True,
            'message': f'{config_type} 配置已更新'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@optimization_bp.route('/api/toggle_monitoring', methods=['POST'])
def toggle_monitoring():
    """切换监控状态"""
    try:
        data = request.get_json()
        enable = data.get('enable', True)
        
        optimizer = get_intelligent_optimizer()
        
        if enable:
            optimizer.start_monitoring()
            message = "监控已启动"
        else:
            optimizer.stop_monitoring()
            message = "监控已停止"
        
        current_app.logger.info(message)
        
        return jsonify({
            'success': True,
            'message': message,
            'monitoring': enable
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@optimization_bp.route('/api/optimization_history')
def get_optimization_history():
    """获取优化历史"""
    try:
        # 这里可以从日志或数据库获取优化历史
        # 暂时返回模拟数据
        history = [
            {
                'timestamp': (datetime.now() - timedelta(hours=2)).isoformat(),
                'action': '自动调整为平衡模式',
                'reason': 'CPU使用率降低到40%',
                'level': 'balanced'
            },
            {
                'timestamp': (datetime.now() - timedelta(hours=4)).isoformat(),
                'action': '自动调整为最小模式',
                'reason': 'CPU使用率超过85%',
                'level': 'minimal'
            },
            {
                'timestamp': (datetime.now() - timedelta(hours=6)).isoformat(),
                'action': '手动设置为激进模式',
                'reason': '用户手动设置',
                'level': 'aggressive'
            }
        ]
        
        return jsonify({
            'success': True,
            'data': history
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@optimization_bp.route('/api/system_health')
def get_system_health():
    """获取系统健康状态"""
    try:
        optimizer = get_intelligent_optimizer()
        
        # 获取最新指标
        latest_metrics = optimizer.metrics_history[-1] if optimizer.metrics_history else None
        
        if not latest_metrics:
            return jsonify({
                'success': True,
                'data': {
                    'status': 'unknown',
                    'message': '暂无监控数据'
                }
            })
        
        # 评估系统健康状态
        health_score = 100
        issues = []
        
        if latest_metrics.cpu_percent > 80:
            health_score -= 30
            issues.append('CPU使用率过高')
        
        if latest_metrics.memory_percent > 85:
            health_score -= 25
            issues.append('内存使用率过高')
        
        if latest_metrics.response_time > 2.0:
            health_score -= 20
            issues.append('响应时间过长')
        
        if health_score >= 80:
            status = 'excellent'
            status_text = '优秀'
        elif health_score >= 60:
            status = 'good'
            status_text = '良好'
        elif health_score >= 40:
            status = 'warning'
            status_text = '警告'
        else:
            status = 'critical'
            status_text = '严重'
        
        return jsonify({
            'success': True,
            'data': {
                'status': status,
                'status_text': status_text,
                'score': health_score,
                'issues': issues,
                'metrics': {
                    'cpu_percent': latest_metrics.cpu_percent,
                    'memory_percent': latest_metrics.memory_percent,
                    'response_time': latest_metrics.response_time,
                    'active_connections': latest_metrics.active_connections
                }
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def init_optimization_dashboard(app):
    """初始化优化控制面板"""
    app.register_blueprint(optimization_bp)
    
    # 初始化智能优化器
    optimizer = get_intelligent_optimizer(app)
    
    # 添加配置变更监听器
    config_manager = get_config_manager()
    
    def on_config_change(config_type, config_data):
        app.logger.info(f"配置已更新: {config_type}")
        # 这里可以添加配置变更后的处理逻辑
    
    config_manager.add_listener(on_config_change)
    
    app.logger.info("智能优化控制面板已初始化")
