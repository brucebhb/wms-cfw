#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能优化管理器
根据系统负载和使用情况动态调整优化策略
"""

import os
import time
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class OptimizationLevel(Enum):
    """优化级别"""
    MINIMAL = "minimal"      # 最小优化 - 仅核心功能
    BALANCED = "balanced"    # 平衡模式 - 性能与功能平衡
    AGGRESSIVE = "aggressive" # 激进优化 - 最大性能
    ADAPTIVE = "adaptive"    # 自适应 - 根据负载动态调整

@dataclass
class SystemMetrics:
    """系统指标"""
    cpu_percent: float
    memory_percent: float
    disk_io_percent: float
    active_connections: int
    request_rate: float
    response_time: float
    timestamp: datetime

@dataclass
class OptimizationStrategy:
    """优化策略"""
    cache_preload_items: int
    background_task_interval: int
    performance_monitor_frequency: int
    database_optimization_level: str
    memory_cache_size: int
    redis_cache_ttl: int
    enable_advanced_features: bool

class IntelligentOptimizer:
    """智能优化管理器"""
    
    def __init__(self, app=None):
        self.app = app
        self.current_level = OptimizationLevel.BALANCED
        self.metrics_history: List[SystemMetrics] = []
        self.optimization_strategies = self._init_strategies()
        self.is_monitoring = False
        self.monitor_thread = None
        self.last_optimization = datetime.now()
        
        # 性能阈值
        self.thresholds = {
            'cpu_high': 80.0,
            'cpu_low': 30.0,
            'memory_high': 85.0,
            'memory_low': 50.0,
            'response_time_high': 2.0,
            'response_time_low': 0.5
        }
        
    def _init_strategies(self) -> Dict[OptimizationLevel, OptimizationStrategy]:
        """初始化优化策略"""
        return {
            OptimizationLevel.MINIMAL: OptimizationStrategy(
                cache_preload_items=5,
                background_task_interval=600,  # 10分钟
                performance_monitor_frequency=60,  # 1分钟
                database_optimization_level="basic",
                memory_cache_size=50,  # MB
                redis_cache_ttl=1800,  # 30分钟
                enable_advanced_features=False
            ),
            OptimizationLevel.BALANCED: OptimizationStrategy(
                cache_preload_items=10,
                background_task_interval=300,  # 5分钟
                performance_monitor_frequency=30,  # 30秒
                database_optimization_level="standard",
                memory_cache_size=100,  # MB
                redis_cache_ttl=3600,  # 1小时
                enable_advanced_features=True
            ),
            OptimizationLevel.AGGRESSIVE: OptimizationStrategy(
                cache_preload_items=20,
                background_task_interval=180,  # 3分钟
                performance_monitor_frequency=15,  # 15秒
                database_optimization_level="advanced",
                memory_cache_size=200,  # MB
                redis_cache_ttl=7200,  # 2小时
                enable_advanced_features=True
            ),
            OptimizationLevel.ADAPTIVE: OptimizationStrategy(
                cache_preload_items=15,
                background_task_interval=240,  # 4分钟
                performance_monitor_frequency=20,  # 20秒
                database_optimization_level="adaptive",
                memory_cache_size=150,  # MB
                redis_cache_ttl=5400,  # 1.5小时
                enable_advanced_features=True
            )
        }
    
    def start_monitoring(self):
        """开始系统监控"""
        if self.is_monitoring:
            return
            
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        if self.app:
            self.app.logger.info("🔍 智能优化监控已启动")
    
    def stop_monitoring(self):
        """停止系统监控"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
            
        if self.app:
            self.app.logger.info("⏹️ 智能优化监控已停止")
    
    def _monitor_loop(self):
        """监控循环"""
        while self.is_monitoring:
            try:
                # 收集系统指标
                metrics = self._collect_metrics()
                self.metrics_history.append(metrics)
                
                # 保持历史记录在合理范围内
                if len(self.metrics_history) > 100:
                    self.metrics_history = self.metrics_history[-50:]
                
                # 检查是否需要调整优化策略
                if self.current_level == OptimizationLevel.ADAPTIVE:
                    self._adaptive_optimization(metrics)
                
                # 等待下次检查
                time.sleep(30)  # 30秒检查一次
                
            except Exception as e:
                if self.app:
                    self.app.logger.error(f"监控循环异常: {e}")
                time.sleep(60)  # 出错时等待更长时间
    
    def _collect_metrics(self) -> SystemMetrics:
        """收集系统指标"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 内存使用率
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # 磁盘IO（简化版）
            disk_io = psutil.disk_io_counters()
            disk_io_percent = 0  # 简化处理
            
            # 网络连接数
            connections = len(psutil.net_connections())
            
            # 请求率和响应时间（从应用获取，如果可用）
            request_rate = self._get_request_rate()
            response_time = self._get_avg_response_time()
            
            return SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                disk_io_percent=disk_io_percent,
                active_connections=connections,
                request_rate=request_rate,
                response_time=response_time,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            if self.app:
                self.app.logger.warning(f"收集系统指标失败: {e}")
            return SystemMetrics(0, 0, 0, 0, 0, 0, datetime.now())
    
    def _get_request_rate(self) -> float:
        """获取请求率（每秒请求数）"""
        # 这里可以从Flask应用或性能监控器获取实际数据
        # 暂时返回模拟值
        return 10.0
    
    def _get_avg_response_time(self) -> float:
        """获取平均响应时间"""
        # 这里可以从Flask应用或性能监控器获取实际数据
        # 暂时返回模拟值
        return 0.8
    
    def _adaptive_optimization(self, current_metrics: SystemMetrics):
        """自适应优化"""
        # 获取最近5分钟的平均指标
        recent_metrics = [m for m in self.metrics_history 
                         if m.timestamp > datetime.now() - timedelta(minutes=5)]
        
        if len(recent_metrics) < 3:
            return
        
        avg_cpu = sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics)
        avg_memory = sum(m.memory_percent for m in recent_metrics) / len(recent_metrics)
        avg_response_time = sum(m.response_time for m in recent_metrics) / len(recent_metrics)
        
        # 决定优化级别
        new_level = self._determine_optimization_level(avg_cpu, avg_memory, avg_response_time)
        
        if new_level != self.current_level:
            self._apply_optimization_level(new_level)
    
    def _determine_optimization_level(self, cpu: float, memory: float, response_time: float) -> OptimizationLevel:
        """根据系统指标确定优化级别"""
        # 高负载情况 - 使用最小优化
        if (cpu > self.thresholds['cpu_high'] or 
            memory > self.thresholds['memory_high'] or 
            response_time > self.thresholds['response_time_high']):
            return OptimizationLevel.MINIMAL
        
        # 低负载情况 - 可以使用激进优化
        elif (cpu < self.thresholds['cpu_low'] and 
              memory < self.thresholds['memory_low'] and 
              response_time < self.thresholds['response_time_low']):
            return OptimizationLevel.AGGRESSIVE
        
        # 中等负载 - 平衡模式
        else:
            return OptimizationLevel.BALANCED
    
    def _apply_optimization_level(self, level: OptimizationLevel):
        """应用优化级别"""
        if level == self.current_level:
            return
            
        old_level = self.current_level
        self.current_level = level
        self.last_optimization = datetime.now()
        
        strategy = self.optimization_strategies[level]
        
        # 应用优化策略
        self._apply_cache_optimization(strategy)
        self._apply_background_task_optimization(strategy)
        self._apply_performance_monitor_optimization(strategy)
        self._apply_database_optimization(strategy)
        
        if self.app:
            self.app.logger.info(f"🔄 优化级别已从 {old_level.value} 调整为 {level.value}")
    
    def _apply_cache_optimization(self, strategy: OptimizationStrategy):
        """应用缓存优化"""
        try:
            # 调整缓存预加载项目数量
            if hasattr(self.app, 'cache_manager'):
                # 这里可以调用缓存管理器的方法
                pass
                
        except Exception as e:
            if self.app:
                self.app.logger.warning(f"应用缓存优化失败: {e}")
    
    def _apply_background_task_optimization(self, strategy: OptimizationStrategy):
        """应用后台任务优化"""
        try:
            # 调整后台任务执行间隔
            if hasattr(self.app, 'scheduler_service'):
                # 这里可以调用调度器服务的方法
                pass
                
        except Exception as e:
            if self.app:
                self.app.logger.warning(f"应用后台任务优化失败: {e}")
    
    def _apply_performance_monitor_optimization(self, strategy: OptimizationStrategy):
        """应用性能监控优化"""
        try:
            # 调整性能监控频率
            pass
                
        except Exception as e:
            if self.app:
                self.app.logger.warning(f"应用性能监控优化失败: {e}")
    
    def _apply_database_optimization(self, strategy: OptimizationStrategy):
        """应用数据库优化"""
        try:
            # 调整数据库优化级别
            pass
                
        except Exception as e:
            if self.app:
                self.app.logger.warning(f"应用数据库优化失败: {e}")
    
    def get_current_status(self) -> Dict:
        """获取当前优化状态"""
        latest_metrics = self.metrics_history[-1] if self.metrics_history else None
        strategy = self.optimization_strategies[self.current_level]
        
        return {
            'optimization_level': self.current_level.value,
            'is_monitoring': self.is_monitoring,
            'last_optimization': self.last_optimization.isoformat(),
            'current_metrics': {
                'cpu_percent': latest_metrics.cpu_percent if latest_metrics else 0,
                'memory_percent': latest_metrics.memory_percent if latest_metrics else 0,
                'response_time': latest_metrics.response_time if latest_metrics else 0,
            } if latest_metrics else {},
            'current_strategy': {
                'cache_preload_items': strategy.cache_preload_items,
                'background_task_interval': strategy.background_task_interval,
                'performance_monitor_frequency': strategy.performance_monitor_frequency,
                'database_optimization_level': strategy.database_optimization_level,
                'enable_advanced_features': strategy.enable_advanced_features
            }
        }
    
    def set_optimization_level(self, level: OptimizationLevel):
        """手动设置优化级别"""
        self._apply_optimization_level(level)
    
    def get_optimization_recommendations(self) -> List[str]:
        """获取优化建议"""
        recommendations = []
        
        if not self.metrics_history:
            return ["建议启动系统监控以获取优化建议"]
        
        latest = self.metrics_history[-1]
        
        if latest.cpu_percent > 80:
            recommendations.append("CPU使用率过高，建议减少后台任务频率")
        
        if latest.memory_percent > 85:
            recommendations.append("内存使用率过高，建议减少缓存大小")
        
        if latest.response_time > 2.0:
            recommendations.append("响应时间过长，建议启用更多缓存优化")
        
        if latest.cpu_percent < 30 and latest.memory_percent < 50:
            recommendations.append("系统负载较低，可以启用更多优化功能")
        
        return recommendations if recommendations else ["系统运行正常，当前优化策略适合"]

# 全局优化器实例
intelligent_optimizer = None

def get_intelligent_optimizer(app=None):
    """获取智能优化器实例"""
    global intelligent_optimizer
    if intelligent_optimizer is None:
        intelligent_optimizer = IntelligentOptimizer(app)
    return intelligent_optimizer

def init_intelligent_optimizer(app):
    """初始化智能优化器"""
    optimizer = get_intelligent_optimizer(app)
    optimizer.start_monitoring()
    return optimizer
