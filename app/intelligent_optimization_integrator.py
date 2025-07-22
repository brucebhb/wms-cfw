#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能优化集成器
将智能优化系统集成到现有的Flask应用中
"""

import threading
import time
from datetime import datetime
from typing import Optional

from .intelligent_optimizer import get_intelligent_optimizer, OptimizationLevel
from .optimization_config_manager import get_config_manager
from .optimization_dashboard import init_optimization_dashboard

class IntelligentOptimizationIntegrator:
    """智能优化集成器"""
    
    def __init__(self, app=None):
        self.app = app
        self.optimizer = None
        self.config_manager = None
        self.is_initialized = False
        self.integration_thread = None
        
    def init_app(self, app):
        """初始化应用"""
        self.app = app
        
        # 在后台线程中初始化，避免阻塞启动
        self.integration_thread = threading.Thread(
            target=self._background_init, 
            daemon=True
        )
        self.integration_thread.start()
        
        app.logger.info("🧠 智能优化系统正在后台初始化...")
    
    def _background_init(self):
        """后台初始化"""
        try:
            with self.app.app_context():
                # 等待应用完全启动
                time.sleep(2)
                
                self.app.logger.info("🔧 开始初始化智能优化系统...")
                
                # 1. 初始化配置管理器
                self.config_manager = get_config_manager()
                self.app.logger.info("✅ 配置管理器已初始化")
                
                # 2. 初始化智能优化器
                self.optimizer = get_intelligent_optimizer(self.app)
                self.app.logger.info("✅ 智能优化器已初始化")
                
                # 3. 集成现有组件
                self._integrate_existing_components()
                
                # 4. 初始化控制面板
                init_optimization_dashboard(self.app)
                self.app.logger.info("✅ 优化控制面板已初始化")
                
                # 5. 启动监控
                self.optimizer.start_monitoring()
                self.app.logger.info("✅ 智能监控已启动")
                
                # 6. 应用初始优化策略
                self._apply_initial_optimization()
                
                self.is_initialized = True
                self.app.logger.info("🎉 智能优化系统初始化完成")
                
        except Exception as e:
            self.app.logger.error(f"❌ 智能优化系统初始化失败: {e}")
    
    def _integrate_existing_components(self):
        """集成现有组件"""
        try:
            # 集成缓存系统
            self._integrate_cache_system()
            
            # 集成后台任务系统
            self._integrate_background_tasks()
            
            # 集成性能监控系统
            self._integrate_performance_monitoring()
            
            # 集成数据库优化
            self._integrate_database_optimization()
            
            self.app.logger.info("🔗 现有组件集成完成")
            
        except Exception as e:
            self.app.logger.warning(f"组件集成部分失败: {e}")
    
    def _integrate_cache_system(self):
        """集成缓存系统"""
        try:
            # 如果应用有缓存管理器，集成配置监听
            if hasattr(self.app, 'cache_manager'):
                def on_cache_config_change(config_type, config_data):
                    if config_type == 'cache':
                        # 动态调整缓存配置
                        cache_manager = getattr(self.app, 'cache_manager', None)
                        if cache_manager and hasattr(cache_manager, 'update_config'):
                            cache_manager.update_config({
                                'l1_size_mb': config_data.l1_cache_size_mb,
                                'l2_ttl': config_data.l2_cache_ttl_seconds,
                                'preload_count': config_data.preload_items_count
                            })
                
                self.config_manager.add_listener(on_cache_config_change)
                self.app.logger.info("🔄 缓存系统已集成")
                
        except Exception as e:
            self.app.logger.warning(f"缓存系统集成失败: {e}")
    
    def _integrate_background_tasks(self):
        """集成后台任务系统"""
        try:
            # 如果应用有调度器服务，集成配置监听
            if hasattr(self.app, 'scheduler_service'):
                def on_task_config_change(config_type, config_data):
                    if config_type == 'background_tasks':
                        # 动态调整任务调度
                        scheduler = getattr(self.app, 'scheduler_service', None)
                        if scheduler and hasattr(scheduler, 'update_intervals'):
                            scheduler.update_intervals({
                                'maintenance': config_data.maintenance_interval,
                                'optimization': config_data.optimization_interval,
                                'cleanup': config_data.cleanup_interval
                            })
                
                self.config_manager.add_listener(on_task_config_change)
                self.app.logger.info("⏰ 后台任务系统已集成")
                
        except Exception as e:
            self.app.logger.warning(f"后台任务系统集成失败: {e}")
    
    def _integrate_performance_monitoring(self):
        """集成性能监控系统"""
        try:
            # 集成现有的性能监控
            def on_monitor_config_change(config_type, config_data):
                if config_type == 'performance_monitor':
                    # 动态调整监控频率
                    if hasattr(self.optimizer, 'update_monitor_frequency'):
                        self.optimizer.update_monitor_frequency(config_data.monitor_frequency)
            
            self.config_manager.add_listener(on_monitor_config_change)
            self.app.logger.info("📊 性能监控系统已集成")
            
        except Exception as e:
            self.app.logger.warning(f"性能监控系统集成失败: {e}")
    
    def _integrate_database_optimization(self):
        """集成数据库优化"""
        try:
            # 集成数据库优化配置
            def on_db_config_change(config_type, config_data):
                if config_type == 'database':
                    # 这里可以调整数据库连接池等配置
                    pass
            
            self.config_manager.add_listener(on_db_config_change)
            self.app.logger.info("🗃️ 数据库优化已集成")
            
        except Exception as e:
            self.app.logger.warning(f"数据库优化集成失败: {e}")
    
    def _apply_initial_optimization(self):
        """应用初始优化策略"""
        try:
            # 根据系统当前状态选择合适的初始优化级别
            initial_level = self._determine_initial_optimization_level()
            
            self.optimizer.set_optimization_level(initial_level)
            self.config_manager.apply_optimization_level(initial_level.value)
            
            self.app.logger.info(f"🎯 初始优化级别已设置为: {initial_level.value}")
            
        except Exception as e:
            self.app.logger.warning(f"应用初始优化策略失败: {e}")
    
    def _determine_initial_optimization_level(self) -> OptimizationLevel:
        """确定初始优化级别"""
        try:
            # 收集当前系统指标
            import psutil
            
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # 根据系统负载决定初始级别
            if cpu_percent > 70 or memory_percent > 80:
                return OptimizationLevel.MINIMAL
            elif cpu_percent < 30 and memory_percent < 50:
                return OptimizationLevel.AGGRESSIVE
            else:
                return OptimizationLevel.BALANCED
                
        except Exception:
            # 如果无法获取系统指标，使用平衡模式
            return OptimizationLevel.BALANCED
    
    def get_optimization_status(self) -> dict:
        """获取优化状态"""
        if not self.is_initialized:
            return {
                'initialized': False,
                'message': '智能优化系统正在初始化中...'
            }
        
        try:
            optimizer_status = self.optimizer.get_current_status()
            config_summary = self.config_manager.get_optimization_summary()
            
            return {
                'initialized': True,
                'optimizer_status': optimizer_status,
                'config_summary': config_summary,
                'recommendations': self.optimizer.get_optimization_recommendations()
            }
            
        except Exception as e:
            return {
                'initialized': True,
                'error': str(e)
            }
    
    def manual_optimize(self, level: str) -> bool:
        """手动设置优化级别"""
        if not self.is_initialized:
            return False
        
        try:
            optimization_level = OptimizationLevel(level)
            self.optimizer.set_optimization_level(optimization_level)
            self.config_manager.apply_optimization_level(level)
            
            self.app.logger.info(f"手动设置优化级别为: {level}")
            return True
            
        except Exception as e:
            self.app.logger.error(f"手动优化失败: {e}")
            return False
    
    def toggle_monitoring(self, enable: bool) -> bool:
        """切换监控状态"""
        if not self.is_initialized:
            return False
        
        try:
            if enable:
                self.optimizer.start_monitoring()
            else:
                self.optimizer.stop_monitoring()
            
            return True
            
        except Exception as e:
            self.app.logger.error(f"切换监控状态失败: {e}")
            return False
    
    def get_performance_metrics(self) -> list:
        """获取性能指标"""
        if not self.is_initialized or not self.optimizer:
            return []
        
        try:
            # 返回最近的性能指标
            return [
                {
                    'timestamp': metric.timestamp.isoformat(),
                    'cpu_percent': metric.cpu_percent,
                    'memory_percent': metric.memory_percent,
                    'response_time': metric.response_time,
                    'active_connections': metric.active_connections
                }
                for metric in self.optimizer.metrics_history[-50:]  # 最近50个数据点
            ]
            
        except Exception as e:
            self.app.logger.error(f"获取性能指标失败: {e}")
            return []

# 全局集成器实例
intelligent_integrator = None

def get_intelligent_integrator(app=None):
    """获取智能优化集成器实例"""
    global intelligent_integrator
    if intelligent_integrator is None:
        intelligent_integrator = IntelligentOptimizationIntegrator(app)
    return intelligent_integrator

def init_intelligent_optimization(app):
    """初始化智能优化系统"""
    integrator = get_intelligent_integrator()
    integrator.init_app(app)
    
    # 添加到应用实例中，方便其他地方访问
    app.intelligent_optimizer = integrator
    
    return integrator
