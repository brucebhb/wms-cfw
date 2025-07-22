#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
缓存调度器
负责定期预热缓存和清理过期数据
"""

import time
import threading
from datetime import datetime, timedelta
from flask import current_app
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from .dual_cache_manager import get_dual_cache_manager
from .cache_warmer import get_cache_warmer


class CacheScheduler:
    """缓存调度器"""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.cache_manager = get_dual_cache_manager()
        self.cache_warmer = get_cache_warmer()
        self.is_running = False
        
        # 配置调度任务
        self._setup_jobs()
    
    def _setup_jobs(self):
        """设置调度任务"""
        
        # 1. 每5分钟预热仪表板数据
        self.scheduler.add_job(
            func=self._warm_dashboard_cache,
            trigger=IntervalTrigger(minutes=5),
            id='warm_dashboard_cache',
            name='预热仪表板缓存',
            max_instances=1,
            coalesce=True
        )
        
        # 2. 每10分钟预热库存数据
        self.scheduler.add_job(
            func=self._warm_inventory_cache,
            trigger=IntervalTrigger(minutes=10),
            id='warm_inventory_cache',
            name='预热库存缓存',
            max_instances=1,
            coalesce=True
        )
        
        # 3. 每小时清理过期缓存
        self.scheduler.add_job(
            func=self._cleanup_expired_cache,
            trigger=IntervalTrigger(hours=1),
            id='cleanup_expired_cache',
            name='清理过期缓存',
            max_instances=1,
            coalesce=True
        )
        
        # 4. 每天凌晨2点深度清理
        self.scheduler.add_job(
            func=self._deep_cleanup_cache,
            trigger=CronTrigger(hour=2, minute=0),
            id='deep_cleanup_cache',
            name='深度清理缓存',
            max_instances=1,
            coalesce=True
        )
        
        # 5. 每30秒更新实时统计
        self.scheduler.add_job(
            func=self._update_realtime_stats,
            trigger=IntervalTrigger(seconds=30),
            id='update_realtime_stats',
            name='更新实时统计',
            max_instances=1,
            coalesce=True
        )
        
        # 6. 每15分钟检查缓存健康状态
        self.scheduler.add_job(
            func=self._check_cache_health,
            trigger=IntervalTrigger(minutes=15),
            id='check_cache_health',
            name='检查缓存健康状态',
            max_instances=1,
            coalesce=True
        )
    
    def start(self):
        """启动调度器"""
        if not self.is_running:
            try:
                self.scheduler.start()
                self.is_running = True
                if current_app:
                    current_app.logger.info("缓存调度器已启动")
                else:
                    print("缓存调度器已启动")
            except Exception as e:
                if current_app:
                    current_app.logger.error(f"缓存调度器启动失败: {e}")
                else:
                    print(f"缓存调度器启动失败: {e}")
    
    def stop(self):
        """停止调度器"""
        if self.is_running:
            try:
                self.scheduler.shutdown()
                self.is_running = False
                if current_app:
                    current_app.logger.info("缓存调度器已停止")
                else:
                    print("缓存调度器已停止")
            except Exception as e:
                if current_app:
                    current_app.logger.error(f"缓存调度器停止失败: {e}")
                else:
                    print(f"缓存调度器停止失败: {e}")
    
    def get_job_status(self):
        """获取任务状态"""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            })
        
        return {
            'is_running': self.is_running,
            'jobs': jobs,
            'job_count': len(jobs)
        }
    
    def _warm_dashboard_cache(self):
        """预热仪表板缓存"""
        try:
            if current_app:
                with current_app.app_context():
                    result = self.cache_warmer.warm_cache('dashboard')
                    current_app.logger.debug(f"仪表板缓存预热完成: {result.get('warmed_items', 0)} 项")
            else:
                result = self.cache_warmer.warm_cache('dashboard')
                print(f"仪表板缓存预热完成: {result.get('warmed_items', 0)} 项")
                
        except Exception as e:
            if current_app:
                current_app.logger.error(f"仪表板缓存预热失败: {e}")
            else:
                print(f"仪表板缓存预热失败: {e}")
    
    def _warm_inventory_cache(self):
        """预热库存缓存"""
        try:
            if current_app:
                with current_app.app_context():
                    result = self.cache_warmer.warm_cache('inventory')
                    current_app.logger.debug(f"库存缓存预热完成: {result.get('warmed_items', 0)} 项")
            else:
                result = self.cache_warmer.warm_cache('inventory')
                print(f"库存缓存预热完成: {result.get('warmed_items', 0)} 项")
                
        except Exception as e:
            if current_app:
                current_app.logger.error(f"库存缓存预热失败: {e}")
            else:
                print(f"库存缓存预热失败: {e}")
    
    def _cleanup_expired_cache(self):
        """清理过期缓存"""
        try:
            # 清理L1内存缓存中的过期项（由内存缓存自动处理）
            # 这里主要是触发清理检查
            
            if current_app:
                current_app.logger.debug("执行缓存过期清理检查")
            else:
                print("执行缓存过期清理检查")
                
        except Exception as e:
            if current_app:
                current_app.logger.error(f"清理过期缓存失败: {e}")
            else:
                print(f"清理过期缓存失败: {e}")
    
    def _deep_cleanup_cache(self):
        """深度清理缓存"""
        try:
            # 清理超过24小时的历史数据缓存
            patterns_to_clean = [
                'historical_stats:*',
                'monthly_report:*',
                'old_dashboard:*'
            ]
            
            total_cleaned = 0
            for pattern in patterns_to_clean:
                result = self.cache_manager.clear_cache(pattern=pattern)
                total_cleaned += result.get('total_cleared', 0)
            
            if current_app:
                current_app.logger.info(f"深度缓存清理完成，清理了 {total_cleaned} 项")
            else:
                print(f"深度缓存清理完成，清理了 {total_cleaned} 项")
                
        except Exception as e:
            if current_app:
                current_app.logger.error(f"深度清理缓存失败: {e}")
            else:
                print(f"深度清理缓存失败: {e}")
    
    def _update_realtime_stats(self):
        """更新实时统计"""
        try:
            # 更新实时指标缓存
            current_time = datetime.now()
            
            # 生成实时统计数据
            realtime_data = {
                'timestamp': current_time.isoformat(),
                'active_connections': 1,  # 简化实现
                'cache_hit_rate': 0,
                'system_load': 'normal'
            }
            
            # 获取缓存状态
            try:
                cache_status = self.cache_manager.get_cache_status()
                realtime_data['cache_hit_rate'] = cache_status.get('overall', {}).get('hit_rate', 0)
            except:
                pass
            
            # 更新实时缓存
            self.cache_manager.set(
                'realtime_metrics:current',
                realtime_data,
                cache_type='realtime_metrics'
            )
            
        except Exception as e:
            if current_app:
                current_app.logger.error(f"更新实时统计失败: {e}")
            else:
                print(f"更新实时统计失败: {e}")
    
    def _check_cache_health(self):
        """检查缓存健康状态"""
        try:
            status = self.cache_manager.get_cache_status()
            
            # 检查L1缓存
            l1_status = status.get('l1_cache', {})
            if not l1_status.get('available', False):
                if current_app:
                    current_app.logger.warning("L1内存缓存不可用")
                else:
                    print("L1内存缓存不可用")
            
            # 检查L2缓存
            l2_status = status.get('l2_cache', {})
            if not l2_status.get('available', False):
                if current_app:
                    current_app.logger.warning("L2Redis缓存不可用")
                else:
                    print("L2Redis缓存不可用")
            
            # 检查命中率
            overall = status.get('overall', {})
            hit_rate = overall.get('hit_rate', 0)
            if hit_rate < 50:  # 命中率低于50%
                if current_app:
                    current_app.logger.warning(f"缓存命中率偏低: {hit_rate:.1f}%")
                else:
                    print(f"缓存命中率偏低: {hit_rate:.1f}%")
            
        except Exception as e:
            if current_app:
                current_app.logger.error(f"检查缓存健康状态失败: {e}")
            else:
                print(f"检查缓存健康状态失败: {e}")


# 全局缓存调度器实例
_cache_scheduler = None

def get_cache_scheduler() -> CacheScheduler:
    """获取全局缓存调度器实例"""
    global _cache_scheduler
    if _cache_scheduler is None:
        _cache_scheduler = CacheScheduler()
    return _cache_scheduler

def init_cache_scheduler(app):
    """初始化缓存调度器"""
    scheduler = get_cache_scheduler()
    
    # 在应用启动时启动调度器
    @app.before_first_request
    def start_cache_scheduler():
        scheduler.start()
    
    # 在应用关闭时停止调度器
    import atexit
    atexit.register(scheduler.stop)
    
    return scheduler
