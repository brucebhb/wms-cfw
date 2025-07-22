#!/usr/bin/env python3
"""
维护管理路由
提供维护任务的Web界面管理
"""
from flask import Blueprint, render_template, jsonify, request, flash, redirect, url_for
from flask_login import login_required
from app.decorators import require_permission
from app.services.maintenance_service import maintenance_service
from app.services.scheduler_service import scheduler_service

# 创建蓝图
maintenance_bp = Blueprint('maintenance', __name__, url_prefix='/maintenance')

@maintenance_bp.route('/')
@login_required
@require_permission('ADMIN')
def index():
    """维护管理主页"""
    try:
        # 获取调度器状态
        scheduler_status = scheduler_service.get_job_status()
        
        # 获取系统健康状态
        health_result = maintenance_service.check_system_health()
        
        return render_template('maintenance/index.html',
                             scheduler_status=scheduler_status,
                             health_info=health_result.get('health_info', {}))
    except Exception as e:
        flash(f'获取维护信息失败: {e}', 'error')
        return render_template('maintenance/index.html',
                             scheduler_status={},
                             health_info={})

@maintenance_bp.route('/run_maintenance', methods=['POST'])
@login_required
@require_permission('ADMIN')
def run_maintenance():
    """手动执行维护"""
    try:
        result = maintenance_service.run_full_maintenance()
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'message': '维护任务执行完成',
                'result': result
            })
        else:
            return jsonify({
                'success': False,
                'message': result.get('message', '维护任务执行失败')
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'维护任务执行异常: {e}'
        })

@maintenance_bp.route('/clean_logs', methods=['POST'])
@login_required
@require_permission('ADMIN')
def clean_logs():
    """手动清理日志"""
    try:
        result = maintenance_service.clean_logs()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'日志清理失败: {e}'
        })

@maintenance_bp.route('/optimize_database', methods=['POST'])
@login_required
@require_permission('ADMIN')
def optimize_database():
    """手动优化数据库"""
    try:
        result = maintenance_service.optimize_database()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'数据库优化失败: {e}'
        })

@maintenance_bp.route('/health_check', methods=['GET'])
@login_required
@require_permission('ADMIN')
def health_check():
    """系统健康检查"""
    try:
        result = maintenance_service.check_system_health()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'健康检查失败: {e}'
        })

@maintenance_bp.route('/scheduler/status', methods=['GET'])
@login_required
@require_permission('ADMIN')
def scheduler_status():
    """获取调度器状态"""
    try:
        status = scheduler_service.get_job_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({
            'error': f'获取调度器状态失败: {e}'
        })

@maintenance_bp.route('/scheduler/run_job/<job_id>', methods=['POST'])
@login_required
@require_permission('ADMIN')
def run_job(job_id):
    """立即执行指定任务"""
    try:
        result = scheduler_service.run_job_now(job_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'执行任务失败: {e}'
        })

@maintenance_bp.route('/scheduler/pause_job/<job_id>', methods=['POST'])
@login_required
@require_permission('ADMIN')
def pause_job(job_id):
    """暂停任务"""
    try:
        result = scheduler_service.pause_job(job_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'暂停任务失败: {e}'
        })

@maintenance_bp.route('/scheduler/resume_job/<job_id>', methods=['POST'])
@login_required
@require_permission('ADMIN')
def resume_job(job_id):
    """恢复任务"""
    try:
        result = scheduler_service.resume_job(job_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'恢复任务失败: {e}'
        })

@maintenance_bp.route('/logs')
@login_required
@require_permission('ADMIN')
def view_logs():
    """查看维护日志"""
    try:
        import os
        import glob
        from flask import current_app
        
        log_dir = os.path.join(current_app.root_path, '..', 'logs')
        log_files = []
        
        if os.path.exists(log_dir):
            for log_file in glob.glob(os.path.join(log_dir, "*.log*")):
                try:
                    stat = os.stat(log_file)
                    log_files.append({
                        'filename': os.path.basename(log_file),
                        'size_mb': round(stat.st_size / 1024 / 1024, 2),
                        'modified': stat.st_mtime
                    })
                except Exception:
                    continue
        
        # 按修改时间排序
        log_files.sort(key=lambda x: x['modified'], reverse=True)
        
        return render_template('maintenance/logs.html', log_files=log_files)
        
    except Exception as e:
        flash(f'获取日志信息失败: {e}', 'error')
        return render_template('maintenance/logs.html', log_files=[])

@maintenance_bp.route('/settings')
@login_required
@require_permission('ADMIN')
def settings():
    """维护设置页面"""
    return render_template('maintenance/settings.html')
