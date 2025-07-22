#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用启动状态管理器
解决首次加载时一直显示"加载中"的问题
"""

import time
import threading
from datetime import datetime
from flask import current_app


class StartupManager:
    """应用启动状态管理器"""
    
    def __init__(self):
        self.startup_time = datetime.now()
        self.is_ready = False
        self.initialization_status = {
            'database': False,
            'cache': False,
            'services': False,
            'optimization': False
        }
        self.startup_messages = []
        self._lock = threading.Lock()
    
    def mark_component_ready(self, component_name, message=None):
        """标记组件已就绪"""
        with self._lock:
            self.initialization_status[component_name] = True
            if message:
                self.startup_messages.append({
                    'component': component_name,
                    'message': message,
                    'timestamp': datetime.now()
                })
            
            # 检查是否所有组件都已就绪
            if all(self.initialization_status.values()):
                self.is_ready = True
                self.startup_messages.append({
                    'component': 'system',
                    'message': '系统启动完成',
                    'timestamp': datetime.now()
                })
    
    def get_startup_status(self):
        """获取启动状态"""
        with self._lock:
            elapsed_time = (datetime.now() - self.startup_time).total_seconds()
            return {
                'is_ready': self.is_ready,
                'elapsed_time': elapsed_time,
                'components': self.initialization_status.copy(),
                'messages': self.startup_messages.copy()
            }
    
    def wait_for_ready(self, timeout=30):
        """等待系统就绪"""
        start_time = time.time()
        while not self.is_ready and (time.time() - start_time) < timeout:
            time.sleep(0.1)
        return self.is_ready


# 全局启动管理器实例
startup_manager = StartupManager()


def init_startup_manager(app):
    """初始化启动管理器"""

    # 立即标记数据库为就绪（因为我们已经优化了数据库初始化）
    startup_manager.mark_component_ready('database', '数据库初始化完成')

    app.logger.info('启动管理器已初始化')
    return startup_manager


def mark_cache_ready():
    """标记缓存系统就绪"""
    startup_manager.mark_component_ready('cache', '缓存系统初始化完成')


def mark_services_ready():
    """标记服务系统就绪"""
    startup_manager.mark_component_ready('services', '后台服务初始化完成')


def mark_optimization_ready():
    """标记优化系统就绪"""
    startup_manager.mark_component_ready('optimization', '性能优化初始化完成')
