#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化后的调度器服务模块
提供更智能的任务调度和监控
"""
import logging
import threading
import time
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_MISSED
from flask import current_app
from .maintenance_service import maintenance_service


class OptimizedSchedulerService:
    """优化后的调度器服务类"""
    
    def __init__(self):
        self.scheduler = None
        self.logger = logging.getLogger(__name__)
        self.is_running = False
        self.job_stats = {}  # 任务执行统计
        self.last_shutdown_time = None
        self.startup_time = None
        self._lock = threading.Lock()
        
    def init_app(self, app):
        """初始化调度器"""
        try:
            self.startup_time = datetime.now()
            
            # 检查是否频繁重启
            if self._is_frequent_restart():
                self.logger.warning("检测到频繁重启，延迟启动调度器")
                time.sleep(5)  # 延迟5秒启动
            
            self.scheduler = BackgroundScheduler(
                timezone='Asia/Shanghai',
                job_defaults={
                    'coalesce': True,
                    'max_instances': 1,
                    'misfire_grace_time': 600  # 增加容忍度到10分钟
                }
            )
            
            # 添加事件监听器
            self._add_event_listeners()
            
            # 添加智能定时任务
            self._add_smart_scheduled_jobs()
            
            # 启动调度器
            self.scheduler.start()
            self.is_running = True
            
            self.logger.info(f"优化调度器服务已启动 (启动时间: {self.startup_time})")
            
            # 注册优雅关闭
            import atexit
            atexit.register(self._graceful_shutdown)
                
        except Exception as e:
            self.logger.error(f"调度器初始化失败: {e}")
    
    def _is_frequent_restart(self):
        """检查是否频繁重启"""
        if self.last_shutdown_time:
            time_diff = datetime.now() - self.last_shutdown_time
            return time_diff.total_seconds() < 30  # 30秒内重启视为频繁
        return False
    
    def _add_event_listeners(self):
        """添加事件监听器"""
        def job_listener(event):
            job_id = event.job_id
            
            with self._lock:
                if job_id not in self.job_stats:
                    self.job_stats[job_id] = {
                        'executed': 0,
                        'errors': 0,
                        'missed': 0,
                        'last_run': None,
                        'last_error': None
                    }
                
                if event.code == EVENT_JOB_EXECUTED:
                    self.job_stats[job_id]['executed'] += 1
                    self.job_stats[job_id]['last_run'] = datetime.now()
                elif event.code == EVENT_JOB_ERROR:
                    self.job_stats[job_id]['errors'] += 1
                    self.job_stats[job_id]['last_error'] = datetime.now()
                    self.logger.error(f"任务 {job_id} 执行失败: {event.exception}")
                elif event.code == EVENT_JOB_MISSED:
                    self.job_stats[job_id]['missed'] += 1
                    self.logger.warning(f"任务 {job_id} 错过执行时间")
        
        self.scheduler.add_listener(job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR | EVENT_JOB_MISSED)
    
    def _add_smart_scheduled_jobs(self):
        """添加智能定时任务"""
        try:
            # 1. 智能维护任务 - 根据系统负载调整频率
            self.scheduler.add_job(
                func=self._smart_maintenance_cycle,
                trigger=IntervalTrigger(minutes=5),  # 改为5分钟，减少频率
                id='smart_maintenance',
                name='智能维护任务',
                replace_existing=True
            )

            # 2. 轻量级监控 - 每10分钟检查一次
            self.scheduler.add_job(
                func=self._light_monitoring,
                trigger=IntervalTrigger(minutes=10),
                id='light_monitoring',
                name='轻量级监控',
                replace_existing=True
            )

            # 3. 每日维护 - 凌晨2点
            self.scheduler.add_job(
                func=self._daily_maintenance,
                trigger=CronTrigger(hour=2, minute=0),
                id='daily_maintenance',
                name='每日深度维护',
                replace_existing=True
            )

            # 4. 每周优化 - 周日凌晨3点
            self.scheduler.add_job(
                func=self._weekly_optimization,
                trigger=CronTrigger(day_of_week=6, hour=3, minute=0),
                id='weekly_optimization',
                name='每周系统优化',
                replace_existing=True
            )

            # 5. 健康检查 - 每小时
            self.scheduler.add_job(
                func=self._health_check,
                trigger=IntervalTrigger(hours=1),
                id='health_check',
                name='系统健康检查',
                replace_existing=True
            )

            self.logger.info("智能定时任务已配置完成")

        except Exception as e:
            self.logger.error(f"添加定时任务失败: {e}")

    def _smart_maintenance_cycle(self):
        """智能维护周期 - 根据系统状态调整"""
        try:
            if not self._should_run_maintenance():
                return
                
            with current_app.app_context():
                result = maintenance_service.run_full_maintenance()
                
                if result.get('success'):
                    cleaned_count = result.get('cleaned_count', 0)
                    if cleaned_count > 0:
                        self.logger.info(f"智能维护完成，处理了 {cleaned_count} 项")
                else:
                    self.logger.warning(f"智能维护失败: {result.get('message')}")

        except Exception as e:
            if "Working outside of application context" not in str(e):
                self.logger.error(f"智能维护异常: {e}")

    def _should_run_maintenance(self):
        """判断是否应该运行维护任务"""
        # 检查系统负载、时间等因素
        current_hour = datetime.now().hour
        
        # 工作时间(9-18点)降低维护频率
        if 9 <= current_hour <= 18:
            # 工作时间内，只在必要时运行
            return self._is_maintenance_needed()
        
        return True
    
    def _is_maintenance_needed(self):
        """检查是否需要维护"""
        try:
            # 检查日志文件大小
            import os
            import glob
            
            log_dir = 'logs'
            if os.path.exists(log_dir):
                for log_file in glob.glob(os.path.join(log_dir, "*.log")):
                    if os.path.getsize(log_file) > 50 * 1024 * 1024:  # 50MB
                        return True
            
            return False
        except:
            return False

    def _light_monitoring(self):
        """轻量级监控"""
        try:
            with current_app.app_context():
                # 只记录重要的监控信息
                stats = self.get_scheduler_stats()
                
                # 检查是否有任务失败
                failed_jobs = [job_id for job_id, stat in stats.get('job_stats', {}).items() 
                              if stat.get('errors', 0) > 0]
                
                if failed_jobs:
                    self.logger.warning(f"发现失败任务: {failed_jobs}")

        except Exception as e:
            if "Working outside of application context" not in str(e):
                self.logger.error(f"监控任务异常: {e}")

    def _daily_maintenance(self):
        """每日深度维护"""
        try:
            with current_app.app_context():
                self.logger.info("开始每日深度维护")
                
                # 执行完整维护
                result = maintenance_service.run_full_maintenance()
                
                # 重置任务统计
                with self._lock:
                    self.job_stats.clear()
                
                self.logger.info("每日深度维护完成")

        except Exception as e:
            self.logger.error(f"每日维护异常: {e}")

    def _weekly_optimization(self):
        """每周系统优化"""
        try:
            with current_app.app_context():
                self.logger.info("开始每周系统优化")
                
                # 数据库优化
                result = maintenance_service.optimize_database()
                
                # 清理旧备份
                self._cleanup_old_backups()
                
                self.logger.info("每周系统优化完成")

        except Exception as e:
            self.logger.error(f"每周优化异常: {e}")

    def _health_check(self):
        """系统健康检查"""
        try:
            with current_app.app_context():
                result = maintenance_service.check_system_health()
                
                if not result.get('success'):
                    self.logger.warning(f"健康检查发现问题: {result.get('message')}")

        except Exception as e:
            if "Working outside of application context" not in str(e):
                self.logger.error(f"健康检查异常: {e}")

    def _cleanup_old_backups(self):
        """清理旧备份文件"""
        try:
            import os
            import glob
            
            backup_dirs = glob.glob('logs/backup_*')
            cutoff_time = datetime.now() - timedelta(days=30)
            
            for backup_dir in backup_dirs:
                try:
                    dir_time = datetime.fromtimestamp(os.path.getmtime(backup_dir))
                    if dir_time < cutoff_time:
                        import shutil
                        shutil.rmtree(backup_dir)
                        self.logger.info(f"清理旧备份: {backup_dir}")
                except Exception as e:
                    self.logger.warning(f"清理备份失败 {backup_dir}: {e}")

        except Exception as e:
            self.logger.error(f"清理备份异常: {e}")

    def get_scheduler_stats(self):
        """获取调度器统计信息"""
        if not self.scheduler:
            return {'error': '调度器未初始化'}
        
        try:
            jobs = []
            for job in self.scheduler.get_jobs():
                job_stat = self.job_stats.get(job.id, {})
                jobs.append({
                    'id': job.id,
                    'name': job.name,
                    'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                    'trigger': str(job.trigger),
                    'executed': job_stat.get('executed', 0),
                    'errors': job_stat.get('errors', 0),
                    'missed': job_stat.get('missed', 0),
                    'last_run': job_stat.get('last_run').isoformat() if job_stat.get('last_run') else None
                })
            
            return {
                'scheduler_running': self.is_running,
                'startup_time': self.startup_time.isoformat() if self.startup_time else None,
                'jobs': jobs,
                'total_jobs': len(jobs),
                'job_stats': self.job_stats
            }
            
        except Exception as e:
            self.logger.error(f"获取统计信息失败: {e}")
            return {'error': str(e)}

    def _graceful_shutdown(self):
        """优雅关闭调度器"""
        if self.scheduler and self.is_running:
            try:
                self.last_shutdown_time = datetime.now()
                self.scheduler.shutdown(wait=True)  # 等待任务完成
                self.is_running = False
                
                # 只在非频繁重启时记录
                if not self._is_frequent_restart():
                    self.logger.info("调度器已优雅关闭")
                    
            except Exception as e:
                self.logger.error(f"关闭调度器失败: {e}")

# 全局优化调度器服务实例
optimized_scheduler_service = OptimizedSchedulerService()
