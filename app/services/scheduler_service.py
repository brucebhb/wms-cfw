#!/usr/bin/env python3
"""
调度器服务模块
管理定时任务的执行
"""
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from flask import current_app
from .maintenance_service import maintenance_service

class SchedulerService:
    """调度器服务类"""

    def __init__(self):
        self.scheduler = None
        self.logger = logging.getLogger(__name__)
        self.is_running = False
        self.app = None  # 保存Flask应用实例

    def init_app(self, app):
        """初始化调度器"""
        try:
            self.app = app  # 保存应用实例
            self.scheduler = BackgroundScheduler(
                timezone='Asia/Shanghai',
                job_defaults={
                    'coalesce': True,  # 合并多个相同的任务
                    'max_instances': 1,  # 同一时间只运行一个实例
                    'misfire_grace_time': 300  # 错过执行时间的容忍度（秒）
                }
            )

            # 添加定时任务
            self._add_scheduled_jobs()

            # 启动调度器
            self.scheduler.start()
            self.is_running = True

            self.logger.info("调度器服务已启动")

            # 注册应用关闭时的清理函数（只在应用真正关闭时执行）
            import atexit
            atexit.register(self.shutdown)

        except Exception as e:
            self.logger.error(f"调度器初始化失败: {e}")
    
    def _add_scheduled_jobs(self):
        """添加定时任务"""
        try:
            # 每3分钟执行完整维护
            self.scheduler.add_job(
                func=self._run_maintenance_cycle,
                trigger=IntervalTrigger(minutes=3),
                id='maintenance_cycle',
                name='每3分钟维护任务',
                replace_existing=True,
                coalesce=True,  # 防止任务堆积
                max_instances=1  # 限制同时只能有一个实例运行
            )

            # 每30分钟执行轻量级日志清理（大幅减少频率）
            self.scheduler.add_job(
                func=self._run_light_cleanup,
                trigger=IntervalTrigger(minutes=30),
                id='light_cleanup',
                name='每30分钟轻量清理',
                replace_existing=True,
                coalesce=True,  # 防止任务堆积
                max_instances=1  # 限制同时只能有一个实例运行
            )

            # 每日凌晨2点执行深度维护
            self.scheduler.add_job(
                func=self._run_daily_maintenance,
                trigger=CronTrigger(hour=2, minute=0),
                id='daily_maintenance',
                name='每日深度维护',
                replace_existing=True
            )

            # 每周日凌晨3点执行数据库优化
            self.scheduler.add_job(
                func=self._run_database_optimization,
                trigger=CronTrigger(day_of_week=6, hour=3, minute=0),  # 周日
                id='weekly_db_optimization',
                name='每周数据库优化',
                replace_existing=True
            )

            # 每小时执行性能优化检查（减少频率）
            self.scheduler.add_job(
                func=self._run_performance_optimization_check,
                trigger=IntervalTrigger(hours=1),
                id='performance_optimization_check',
                name='每小时性能优化检查',
                replace_existing=True,
                coalesce=True,
                max_instances=1
            )

            # 每天凌晨4点执行综合性能优化
            self.scheduler.add_job(
                func=self._run_comprehensive_performance_optimization,
                trigger=CronTrigger(hour=4, minute=0),
                id='comprehensive_performance_optimization',
                name='综合性能优化',
                replace_existing=True
            )

            self.logger.info("定时任务已添加 - 优化后的任务频率")

        except Exception as e:
            self.logger.error(f"添加定时任务失败: {e}")

    def _run_maintenance_cycle(self):
        """执行每3分钟维护周期"""
        if not self.app:
            self.logger.warning("应用实例未初始化，跳过维护周期")
            return

        try:
            with self.app.app_context():
                # 只在有实际工作时记录日志
                result = maintenance_service.run_full_maintenance()

                if result.get('success'):
                    # 只在有清理操作时记录
                    if result.get('cleaned_count', 0) > 0:
                        self.logger.info(f"3分钟维护周期完成，清理了 {result.get('cleaned_count')} 项")
                else:
                    self.logger.warning(f"3分钟维护周期失败: {result.get('message', '未知错误')}")

        except Exception as e:
            self.logger.error(f"3分钟维护周期异常: {e}")

    def _run_light_cleanup(self):
        """执行轻量级清理"""
        if not self.app:
            self.logger.warning("应用实例未初始化，跳过轻量级清理")
            return

        try:
            with self.app.app_context():
                # 只清理大于20MB的日志文件
                result = maintenance_service.clean_logs(max_size_mb=20, keep_days=3)

                if result.get('success'):
                    cleaned_count = result.get('cleaned_count', 0)
                    if cleaned_count > 0:
                        self.logger.info(f"轻量级清理完成，清理了 {cleaned_count} 个文件")
                    # 无需清理时不记录日志
                else:
                    self.logger.warning(f"轻量级清理失败: {result.get('message')}")

        except Exception as e:
            self.logger.error(f"轻量级清理异常: {e}")

    def _run_daily_maintenance(self):
        """执行每日深度维护"""
        if not self.app:
            self.logger.warning("应用实例未初始化，跳过每日维护")
            return

        try:
            with self.app.app_context():
                self.logger.info("开始执行每日深度维护任务")

                # 执行完整维护
                result = maintenance_service.run_full_maintenance()

                # 额外的深度清理
                if result.get('success'):
                    # 清理更多测试数据
                    try:
                        from app.services.maintenance_service import maintenance_service
                        cleanup_result = maintenance_service._cleanup_test_data(days_to_keep=60)  # 保留60天
                        self.logger.info(f"深度清理了 {cleanup_result} 条旧数据")
                    except Exception as e:
                        self.logger.warning(f"深度数据清理失败: {e}")

                if result.get('success'):
                    self.logger.info("每日深度维护任务完成")
                else:
                    self.logger.error(f"每日深度维护任务失败: {result.get('message', '未知错误')}")

        except Exception as e:
            self.logger.error(f"每日深度维护任务异常: {e}")
    
    def _run_log_cleanup(self):
        """执行日志清理"""
        if not self.app:
            self.logger.warning("应用实例未初始化，跳过日志清理")
            return

        try:
            with self.app.app_context():
                self.logger.info("开始执行日志清理任务")
                result = maintenance_service.clean_logs()
                
                if result.get('success'):
                    self.logger.info(f"日志清理完成: {result.get('message')}")
                else:
                    self.logger.error(f"日志清理失败: {result.get('message')}")
                    
        except Exception as e:
            self.logger.error(f"日志清理任务异常: {e}")
    
    def _run_health_check(self):
        """执行系统健康检查"""
        if not self.app:
            self.logger.warning("应用实例未初始化，跳过健康检查")
            return

        try:
            with self.app.app_context():
                self.logger.info("开始执行系统健康检查")
                result = maintenance_service.check_system_health()
                
                if result.get('success'):
                    health_info = result.get('health_info', {})
                    recommendations = health_info.get('recommendations', [])
                    
                    if any('建议' in rec for rec in recommendations):
                        self.logger.warning(f"系统健康检查发现问题: {recommendations}")
                    else:
                        self.logger.info("系统健康检查正常")
                else:
                    self.logger.error(f"系统健康检查失败: {result.get('message')}")
                    
        except Exception as e:
            self.logger.error(f"系统健康检查异常: {e}")
    
    def _run_database_optimization(self):
        """执行数据库优化"""
        if not self.app:
            self.logger.warning("应用实例未初始化，跳过数据库优化")
            return

        try:
            with self.app.app_context():
                self.logger.info("开始执行数据库优化任务")
                result = maintenance_service.optimize_database()
                
                if result.get('success'):
                    self.logger.info(f"数据库优化完成: {result.get('message')}")
                else:
                    self.logger.error(f"数据库优化失败: {result.get('message')}")
                    
        except Exception as e:
            self.logger.error(f"数据库优化任务异常: {e}")

    def _run_performance_optimization_check(self):
        """执行性能优化检查"""
        if not self.app:
            self.logger.warning("应用实例未初始化，跳过性能优化检查")
            return

        try:
            with self.app.app_context():
                from app.integrated_performance_optimizer import integrated_optimizer

                # 获取快速状态检查
                status = integrated_optimizer.get_quick_status()

                # 检查是否需要优化
                needs_optimization = False

                if status.get('cache_hit_rate', 100) < 60:
                    needs_optimization = True
                    self.logger.info(f"缓存命中率较低: {status.get('cache_hit_rate')}%")

                if status.get('avg_query_time', 0) > 2.0:
                    needs_optimization = True
                    self.logger.info(f"平均查询时间过长: {status.get('avg_query_time')}秒")

                if status.get('slow_queries_count', 0) > 5:
                    needs_optimization = True
                    self.logger.info(f"慢查询过多: {status.get('slow_queries_count')}个")

                # 如果需要优化，执行轻量级优化
                if needs_optimization:
                    # 清理缓存
                    from app.cache_config import get_cache_manager
                    cache_manager = get_cache_manager()
                    cleared = cache_manager.delete_pattern('search_results*')
                    if cleared > 0:
                        self.logger.info(f"性能优化: 清理了 {cleared} 个搜索缓存")

        except Exception as e:
            self.logger.error(f"性能优化检查异常: {e}")

    def _run_comprehensive_performance_optimization(self):
        """执行综合性能优化"""
        if not self.app:
            self.logger.warning("应用实例未初始化，跳过综合性能优化")
            return

        try:
            with self.app.app_context():
                from app.integrated_performance_optimizer import integrated_optimizer

                self.logger.info("开始执行综合性能优化...")

                # 运行综合优化
                result = integrated_optimizer.run_comprehensive_optimization()

                if result:
                    # 记录优化结果
                    db_result = result.get('database_optimization', {})
                    cache_result = result.get('cache_optimization', {})
                    log_result = result.get('log_optimization', {})

                    self.logger.info(f"综合性能优化完成:")
                    self.logger.info(f"  数据库优化: {db_result.get('status', 'unknown')}")
                    self.logger.info(f"  缓存优化: {cache_result.get('status', 'unknown')}")
                    self.logger.info(f"  日志优化: {log_result.get('status', 'unknown')}")

                    # 如果有告警，记录
                    performance_report = result.get('performance_report', {})
                    alerts = performance_report.get('alerts', [])
                    if alerts:
                        self.logger.warning(f"性能告警: {len(alerts)} 个问题需要关注")

        except Exception as e:
            self.logger.error(f"综合性能优化异常: {e}")

    def get_job_status(self):
        """获取任务状态"""
        if not self.scheduler:
            return {'error': '调度器未初始化'}

        try:
            jobs = []
            for job in self.scheduler.get_jobs():
                jobs.append({
                    'id': job.id,
                    'name': job.name,
                    'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                    'trigger': str(job.trigger)
                })

            # 检查调度器是否真正在运行
            actual_running = self.scheduler.running if self.scheduler else False

            return {
                'scheduler_running': self.is_running and actual_running,
                'scheduler_state': self.scheduler.state if self.scheduler else 'unknown',
                'jobs': jobs,
                'total_jobs': len(jobs)
            }

        except Exception as e:
            self.logger.error(f"获取任务状态失败: {e}")
            return {'error': str(e)}

    def is_scheduler_running(self):
        """检查调度器是否真正在运行"""
        if not self.scheduler:
            return False

        try:
            return self.is_running and self.scheduler.running
        except Exception as e:
            self.logger.error(f"检查调度器状态失败: {e}")
            return False
    
    def run_job_now(self, job_id):
        """立即执行指定任务"""
        if not self.scheduler:
            return {'success': False, 'message': '调度器未初始化'}
        
        try:
            job = self.scheduler.get_job(job_id)
            if not job:
                return {'success': False, 'message': f'任务 {job_id} 不存在'}
            
            # 立即执行任务
            job.func()
            
            return {'success': True, 'message': f'任务 {job_id} 已执行'}
            
        except Exception as e:
            self.logger.error(f"执行任务 {job_id} 失败: {e}")
            return {'success': False, 'message': str(e)}
    
    def pause_job(self, job_id):
        """暂停任务"""
        if not self.scheduler:
            return {'success': False, 'message': '调度器未初始化'}
        
        try:
            self.scheduler.pause_job(job_id)
            return {'success': True, 'message': f'任务 {job_id} 已暂停'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def resume_job(self, job_id):
        """恢复任务"""
        if not self.scheduler:
            return {'success': False, 'message': '调度器未初始化'}
        
        try:
            self.scheduler.resume_job(job_id)
            return {'success': True, 'message': f'任务 {job_id} 已恢复'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def shutdown(self):
        """关闭调度器"""
        if self.scheduler and self.is_running:
            try:
                self.scheduler.shutdown(wait=False)
                self.is_running = False
                # 只在调试模式下记录关闭信息
                if hasattr(self.app, 'debug') and self.app.debug:
                    self.logger.info("调度器已关闭")
            except Exception as e:
                self.logger.error(f"关闭调度器失败: {e}")
        elif not self.is_running:
            # 避免重复关闭的日志
            pass

# 全局调度器服务实例
scheduler_service = SchedulerService()
