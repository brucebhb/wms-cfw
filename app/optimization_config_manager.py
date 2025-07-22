#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化配置管理器
动态管理各个组件的优化配置
"""

import json
import os
import threading
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

@dataclass
class CacheConfig:
    """缓存配置"""
    l1_cache_size_mb: int = 100
    l2_cache_ttl_seconds: int = 3600
    preload_items_count: int = 10
    auto_cleanup_interval: int = 300
    enable_compression: bool = True

@dataclass
class BackgroundTaskConfig:
    """后台任务配置"""
    maintenance_interval: int = 300  # 5分钟
    optimization_interval: int = 180  # 3分钟
    cleanup_interval: int = 600  # 10分钟
    max_concurrent_tasks: int = 3
    enable_smart_scheduling: bool = True

@dataclass
class PerformanceMonitorConfig:
    """性能监控配置"""
    monitor_frequency: int = 30  # 30秒
    metrics_retention_hours: int = 24
    alert_thresholds: Dict[str, float] = None
    enable_auto_optimization: bool = True
    detailed_logging: bool = False

@dataclass
class DatabaseConfig:
    """数据库配置"""
    connection_pool_size: int = 10
    query_timeout: int = 30
    enable_query_cache: bool = True
    auto_index_optimization: bool = True
    slow_query_threshold: float = 1.0

@dataclass
class OptimizationConfig:
    """完整优化配置"""
    cache: CacheConfig
    background_tasks: BackgroundTaskConfig
    performance_monitor: PerformanceMonitorConfig
    database: DatabaseConfig
    last_updated: str = ""

class OptimizationConfigManager:
    """优化配置管理器"""
    
    def __init__(self, config_file: str = "optimization_config.json"):
        self.config_file = config_file
        self.config: OptimizationConfig = self._load_default_config()
        self.lock = threading.RLock()
        self.listeners = []
        
        # 尝试加载现有配置
        self._load_config()
    
    def _load_default_config(self) -> OptimizationConfig:
        """加载默认配置"""
        return OptimizationConfig(
            cache=CacheConfig(),
            background_tasks=BackgroundTaskConfig(),
            performance_monitor=PerformanceMonitorConfig(
                alert_thresholds={
                    'cpu_percent': 80.0,
                    'memory_percent': 85.0,
                    'response_time': 2.0,
                    'error_rate': 5.0
                }
            ),
            database=DatabaseConfig(),
            last_updated=datetime.now().isoformat()
        )
    
    def _load_config(self):
        """从文件加载配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # 重建配置对象
                self.config = OptimizationConfig(
                    cache=CacheConfig(**data.get('cache', {})),
                    background_tasks=BackgroundTaskConfig(**data.get('background_tasks', {})),
                    performance_monitor=PerformanceMonitorConfig(**data.get('performance_monitor', {})),
                    database=DatabaseConfig(**data.get('database', {})),
                    last_updated=data.get('last_updated', datetime.now().isoformat())
                )
        except Exception as e:
            print(f"加载配置文件失败，使用默认配置: {e}")
    
    def _save_config(self):
        """保存配置到文件"""
        try:
            with self.lock:
                self.config.last_updated = datetime.now().isoformat()
                
                config_dict = {
                    'cache': asdict(self.config.cache),
                    'background_tasks': asdict(self.config.background_tasks),
                    'performance_monitor': asdict(self.config.performance_monitor),
                    'database': asdict(self.config.database),
                    'last_updated': self.config.last_updated
                }
                
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(config_dict, f, indent=2, ensure_ascii=False)
                    
        except Exception as e:
            print(f"保存配置文件失败: {e}")
    
    def update_cache_config(self, **kwargs):
        """更新缓存配置"""
        with self.lock:
            for key, value in kwargs.items():
                if hasattr(self.config.cache, key):
                    setattr(self.config.cache, key, value)
            
            self._save_config()
            self._notify_listeners('cache', self.config.cache)
    
    def update_background_task_config(self, **kwargs):
        """更新后台任务配置"""
        with self.lock:
            for key, value in kwargs.items():
                if hasattr(self.config.background_tasks, key):
                    setattr(self.config.background_tasks, key, value)
            
            self._save_config()
            self._notify_listeners('background_tasks', self.config.background_tasks)
    
    def update_performance_monitor_config(self, **kwargs):
        """更新性能监控配置"""
        with self.lock:
            for key, value in kwargs.items():
                if hasattr(self.config.performance_monitor, key):
                    setattr(self.config.performance_monitor, key, value)
            
            self._save_config()
            self._notify_listeners('performance_monitor', self.config.performance_monitor)
    
    def update_database_config(self, **kwargs):
        """更新数据库配置"""
        with self.lock:
            for key, value in kwargs.items():
                if hasattr(self.config.database, key):
                    setattr(self.config.database, key, value)
            
            self._save_config()
            self._notify_listeners('database', self.config.database)
    
    def get_cache_config(self) -> CacheConfig:
        """获取缓存配置"""
        with self.lock:
            return self.config.cache
    
    def get_background_task_config(self) -> BackgroundTaskConfig:
        """获取后台任务配置"""
        with self.lock:
            return self.config.background_tasks
    
    def get_performance_monitor_config(self) -> PerformanceMonitorConfig:
        """获取性能监控配置"""
        with self.lock:
            return self.config.performance_monitor
    
    def get_database_config(self) -> DatabaseConfig:
        """获取数据库配置"""
        with self.lock:
            return self.config.database
    
    def get_full_config(self) -> OptimizationConfig:
        """获取完整配置"""
        with self.lock:
            return self.config
    
    def add_listener(self, callback):
        """添加配置变更监听器"""
        self.listeners.append(callback)
    
    def remove_listener(self, callback):
        """移除配置变更监听器"""
        if callback in self.listeners:
            self.listeners.remove(callback)
    
    def _notify_listeners(self, config_type: str, config_data: Any):
        """通知配置变更监听器"""
        for listener in self.listeners:
            try:
                listener(config_type, config_data)
            except Exception as e:
                print(f"通知监听器失败: {e}")
    
    def apply_optimization_level(self, level: str):
        """应用优化级别"""
        if level == "minimal":
            self._apply_minimal_optimization()
        elif level == "balanced":
            self._apply_balanced_optimization()
        elif level == "aggressive":
            self._apply_aggressive_optimization()
        elif level == "adaptive":
            self._apply_adaptive_optimization()
    
    def _apply_minimal_optimization(self):
        """应用最小优化配置"""
        self.update_cache_config(
            l1_cache_size_mb=50,
            l2_cache_ttl_seconds=1800,
            preload_items_count=5,
            auto_cleanup_interval=600
        )
        
        self.update_background_task_config(
            maintenance_interval=600,
            optimization_interval=900,
            cleanup_interval=1200,
            max_concurrent_tasks=1
        )
        
        self.update_performance_monitor_config(
            monitor_frequency=60,
            enable_auto_optimization=False,
            detailed_logging=False
        )
    
    def _apply_balanced_optimization(self):
        """应用平衡优化配置"""
        self.update_cache_config(
            l1_cache_size_mb=100,
            l2_cache_ttl_seconds=3600,
            preload_items_count=10,
            auto_cleanup_interval=300
        )
        
        self.update_background_task_config(
            maintenance_interval=300,
            optimization_interval=180,
            cleanup_interval=600,
            max_concurrent_tasks=2
        )
        
        self.update_performance_monitor_config(
            monitor_frequency=30,
            enable_auto_optimization=True,
            detailed_logging=False
        )
    
    def _apply_aggressive_optimization(self):
        """应用激进优化配置"""
        self.update_cache_config(
            l1_cache_size_mb=200,
            l2_cache_ttl_seconds=7200,
            preload_items_count=20,
            auto_cleanup_interval=180
        )
        
        self.update_background_task_config(
            maintenance_interval=180,
            optimization_interval=120,
            cleanup_interval=300,
            max_concurrent_tasks=3
        )
        
        self.update_performance_monitor_config(
            monitor_frequency=15,
            enable_auto_optimization=True,
            detailed_logging=True
        )
    
    def _apply_adaptive_optimization(self):
        """应用自适应优化配置"""
        self.update_cache_config(
            l1_cache_size_mb=150,
            l2_cache_ttl_seconds=5400,
            preload_items_count=15,
            auto_cleanup_interval=240
        )
        
        self.update_background_task_config(
            maintenance_interval=240,
            optimization_interval=150,
            cleanup_interval=480,
            max_concurrent_tasks=2,
            enable_smart_scheduling=True
        )
        
        self.update_performance_monitor_config(
            monitor_frequency=20,
            enable_auto_optimization=True,
            detailed_logging=False
        )
    
    def get_optimization_summary(self) -> Dict[str, Any]:
        """获取优化配置摘要"""
        with self.lock:
            return {
                'cache': {
                    'memory_size_mb': self.cache_config.l1_cache_size_mb,
                    'redis_ttl_hours': self.cache_config.l2_cache_ttl_seconds / 3600,
                    'preload_items': self.cache_config.preload_items_count
                },
                'background_tasks': {
                    'maintenance_interval_min': self.background_task_config.maintenance_interval / 60,
                    'max_concurrent': self.background_task_config.max_concurrent_tasks,
                    'smart_scheduling': self.background_task_config.enable_smart_scheduling
                },
                'monitoring': {
                    'frequency_sec': self.performance_monitor_config.monitor_frequency,
                    'auto_optimization': self.performance_monitor_config.enable_auto_optimization,
                    'detailed_logging': self.performance_monitor_config.detailed_logging
                },
                'database': {
                    'pool_size': self.database_config.connection_pool_size,
                    'query_cache': self.database_config.enable_query_cache,
                    'auto_index': self.database_config.auto_index_optimization
                },
                'last_updated': datetime.now().isoformat()
            }

# 全局配置管理器实例
config_manager = None

def get_config_manager():
    """获取配置管理器实例"""
    global config_manager
    if config_manager is None:
        config_manager = OptimizationConfigManager()
    return config_manager
