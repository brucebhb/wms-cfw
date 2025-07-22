#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运行时性能管理器
在系统运行时提供轻量级性能监控和优化
"""

import time
import threading
from datetime import datetime, timedelta
from collections import deque
from flask import current_app, g, request

class RuntimePerformanceManager:
    """运行时性能管理器"""
    
    def __init__(self):
        self.enabled = True
        self.metrics = {
            'request_times': deque(maxlen=500),
            'slow_requests': deque(maxlen=50),
            'cache_hits': 0,
            'cache_misses': 0,
            'db_queries': deque(maxlen=500)
        }
        self.thresholds = {
            'slow_request': 2.0,  # 2秒
            'slow_query': 1.0     # 1秒
        }
        
        # 启动后台监控线程
        self.start_background_monitoring()
    
    def start_background_monitoring(self):
        """启动后台监控"""
        def monitor():
            while self.enabled:
                try:
                    self.cleanup_old_metrics()
                    self.check_performance_alerts()
                    time.sleep(30)  # 每30秒检查一次
                except Exception as e:
                    if current_app:
                        current_app.logger.error(f"性能监控错误: {e}")
                    time.sleep(60)  # 出错时等待更长时间
        
        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()
    
    def record_request(self, endpoint, duration):
        """记录请求性能"""
        if not self.enabled:
            return
            
        timestamp = time.time()
        self.metrics['request_times'].append({
            'timestamp': timestamp,
            'endpoint': endpoint,
            'duration': duration
        })
        
        if duration > self.thresholds['slow_request']:
            self.metrics['slow_requests'].append({
                'timestamp': timestamp,
                'endpoint': endpoint,
                'duration': duration
            })
    
    def record_cache_hit(self):
        """记录缓存命中"""
        self.metrics['cache_hits'] += 1
    
    def record_cache_miss(self):
        """记录缓存未命中"""
        self.metrics['cache_misses'] += 1
    
    def record_db_query(self, query_type, duration):
        """记录数据库查询"""
        if not self.enabled:
            return
            
        self.metrics['db_queries'].append({
            'timestamp': time.time(),
            'type': query_type,
            'duration': duration
        })
    
    def get_performance_summary(self):
        """获取性能摘要"""
        now = time.time()
        recent_requests = [r for r in self.metrics['request_times'] 
                          if now - r['timestamp'] < 300]  # 最近5分钟
        
        if not recent_requests:
            return {"status": "no_data"}
        
        avg_response_time = sum(r['duration'] for r in recent_requests) / len(recent_requests)
        slow_requests_count = len([r for r in recent_requests 
                                 if r['duration'] > self.thresholds['slow_request']])
        
        cache_total = self.metrics['cache_hits'] + self.metrics['cache_misses']
        cache_hit_rate = (self.metrics['cache_hits'] / cache_total * 100) if cache_total > 0 else 0
        
        return {
            "status": "ok",
            "avg_response_time": round(avg_response_time, 3),
            "slow_requests_count": slow_requests_count,
            "total_requests": len(recent_requests),
            "cache_hit_rate": round(cache_hit_rate, 2)
        }
    
    def cleanup_old_metrics(self):
        """清理旧的性能指标"""
        # 这个方法会自动运行，因为我们使用了deque with maxlen
        pass
    
    def check_performance_alerts(self):
        """检查性能警报"""
        summary = self.get_performance_summary()
        
        if summary["status"] == "no_data":
            return
        
        # 检查平均响应时间
        if summary["avg_response_time"] > 3.0:
            if current_app:
                current_app.logger.warning(f"平均响应时间过高: {summary['avg_response_time']}秒")
        
        # 检查缓存命中率
        if summary["cache_hit_rate"] < 70:
            if current_app:
                current_app.logger.warning(f"缓存命中率过低: {summary['cache_hit_rate']}%")

# 全局实例
runtime_performance_manager = RuntimePerformanceManager()

def init_runtime_performance(app):
    """初始化运行时性能管理"""
    
    @app.before_request
    def before_request():
        g.start_time = time.time()
    
    @app.after_request
    def after_request(response):
        if hasattr(g, 'start_time'):
            duration = time.time() - g.start_time
            endpoint = request.endpoint or 'unknown'
            runtime_performance_manager.record_request(endpoint, duration)
        return response
    
    app.logger.info("运行时性能管理器已初始化")
    return runtime_performance_manager
