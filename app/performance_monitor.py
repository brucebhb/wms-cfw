"""
查询性能监控和缓存命中率统计
"""

import time
import functools
from datetime import datetime, timedelta
from collections import defaultdict, deque
from flask import current_app, g, request
from app.cache_config import get_cache_manager
import threading
import json


class PerformanceMetrics:
    """性能指标收集器"""
    
    def __init__(self):
        self.query_times = deque(maxlen=500)  # 最近1000次查询时间
        self.cache_hits = 0
        self.cache_misses = 0
        self.slow_queries = deque(maxlen=50)  # 最近100次慢查询
        self.query_stats = defaultdict(list)  # 按查询类型统计
        self.lock = threading.Lock()
    
    def record_query_time(self, query_type, execution_time, is_slow=False):
        """记录查询时间"""
        with self.lock:
            timestamp = time.time()
            
            self.query_times.append({
                'timestamp': timestamp,
                'query_type': query_type,
                'execution_time': execution_time,
                'is_slow': is_slow
            })
            
            self.query_stats[query_type].append({
                'timestamp': timestamp,
                'execution_time': execution_time
            })
            
            # 保持每个查询类型最多100条记录
            if len(self.query_stats[query_type]) > 100:
                self.query_stats[query_type] = self.query_stats[query_type][-100:]
            
            if is_slow:
                self.slow_queries.append({
                    'timestamp': timestamp,
                    'query_type': query_type,
                    'execution_time': execution_time,
                    'datetime': datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                })
    
    def record_cache_hit(self):
        """记录缓存命中"""
        with self.lock:
            self.cache_hits += 1
    
    def record_cache_miss(self):
        """记录缓存未命中"""
        with self.lock:
            self.cache_misses += 1
    
    def get_cache_hit_rate(self):
        """获取缓存命中率"""
        total = self.cache_hits + self.cache_misses
        if total == 0:
            return 0.0
        return round((self.cache_hits / total) * 100, 2)
    
    def get_average_query_time(self, query_type=None, minutes=10):
        """获取平均查询时间"""
        with self.lock:
            cutoff_time = time.time() - (minutes * 60)
            
            if query_type:
                recent_queries = [
                    q for q in self.query_stats.get(query_type, [])
                    if q['timestamp'] > cutoff_time
                ]
            else:
                recent_queries = [
                    q for q in self.query_times
                    if q['timestamp'] > cutoff_time
                ]
            
            if not recent_queries:
                return 0.0
            
            total_time = sum(q['execution_time'] for q in recent_queries)
            return round(total_time / len(recent_queries), 3)
    
    def get_slow_queries(self, limit=10):
        """获取慢查询列表"""
        with self.lock:
            return list(self.slow_queries)[-limit:]
    
    def get_query_stats_summary(self):
        """获取查询统计摘要"""
        with self.lock:
            summary = {}
            
            for query_type, queries in self.query_stats.items():
                if queries:
                    times = [q['execution_time'] for q in queries]
                    summary[query_type] = {
                        'count': len(queries),
                        'avg_time': round(sum(times) / len(times), 3),
                        'max_time': round(max(times), 3),
                        'min_time': round(min(times), 3)
                    }
            
            return summary
    
    def reset_stats(self):
        """重置统计数据"""
        with self.lock:
            self.cache_hits = 0
            self.cache_misses = 0
            self.query_times.clear()
            self.slow_queries.clear()
            self.query_stats.clear()


# 全局性能指标实例
performance_metrics = PerformanceMetrics()


def performance_monitor(query_type=None, slow_threshold=1.0):
    """性能监控装饰器"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            # 确定查询类型
            monitor_type = query_type or func.__name__
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # 判断是否为慢查询
                is_slow = execution_time > slow_threshold
                
                # 记录性能指标
                performance_metrics.record_query_time(monitor_type, execution_time, is_slow)
                
                # 记录日志
                if is_slow:
                    current_app.logger.warning(
                        f"慢查询检测: {monitor_type} 执行时间: {execution_time:.3f}秒"
                    )
                else:
                    current_app.logger.debug(
                        f"查询性能: {monitor_type} 执行时间: {execution_time:.3f}秒"
                    )
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                performance_metrics.record_query_time(monitor_type, execution_time, True)
                
                current_app.logger.error(
                    f"查询错误: {monitor_type} 执行时间: {execution_time:.3f}秒, 错误: {str(e)}"
                )
                raise
        
        return wrapper
    return decorator


def cache_monitor(cache_type):
    """缓存监控装饰器"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 检查是否有缓存键参数
            cache_key = None
            if len(args) > 0:
                cache_key = str(args[0])
            
            # 尝试从缓存获取
            cached_result = None
            if cache_key:
                try:
                    cached_result = get_cache_manager().get(cache_type, cache_key)
                except:
                    pass
            
            if cached_result is not None:
                # 缓存命中
                performance_metrics.record_cache_hit()
                current_app.logger.debug(f"缓存命中: {cache_type}:{cache_key}")
                return cached_result
            else:
                # 缓存未命中
                performance_metrics.record_cache_miss()
                current_app.logger.debug(f"缓存未命中: {cache_type}:{cache_key}")
                
                # 执行原函数
                result = func(*args, **kwargs)
                
                # 缓存结果
                if cache_key and result is not None:
                    try:
                        get_cache_manager().set(cache_type, cache_key, result)
                    except:
                        pass
                
                return result
        
        return wrapper
    return decorator


class PerformanceDashboard:
    """性能监控仪表板"""
    
    @staticmethod
    def get_performance_summary():
        """获取性能摘要"""
        try:
            # 获取Redis缓存统计
            redis_stats = get_cache_manager().get_cache_stats()
            
            # 获取应用层缓存统计
            app_cache_hit_rate = performance_metrics.get_cache_hit_rate()
            
            # 获取查询统计
            query_stats = performance_metrics.get_query_stats_summary()
            
            # 获取慢查询
            slow_queries = performance_metrics.get_slow_queries()
            
            # 获取平均查询时间
            avg_query_time = performance_metrics.get_average_query_time()
            
            return {
                'redis_stats': redis_stats,
                'app_cache_hit_rate': app_cache_hit_rate,
                'app_cache_hits': performance_metrics.cache_hits,
                'app_cache_misses': performance_metrics.cache_misses,
                'query_stats': query_stats,
                'slow_queries': slow_queries,
                'avg_query_time': avg_query_time,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            current_app.logger.error(f"获取性能摘要失败: {str(e)}")
            return {'error': str(e)}
    
    @staticmethod
    def get_detailed_stats(query_type=None):
        """获取详细统计信息"""
        try:
            summary = {
                'cache_performance': {
                    'hit_rate': performance_metrics.get_cache_hit_rate(),
                    'hits': performance_metrics.cache_hits,
                    'misses': performance_metrics.cache_misses,
                    'total_requests': performance_metrics.cache_hits + performance_metrics.cache_misses
                },
                'query_performance': {},
                'slow_queries': performance_metrics.get_slow_queries(20),
                'redis_info': get_cache_manager().get_cache_stats()
            }
            
            # 查询性能统计
            if query_type:
                summary['query_performance'][query_type] = {
                    'avg_time_1min': performance_metrics.get_average_query_time(query_type, 1),
                    'avg_time_5min': performance_metrics.get_average_query_time(query_type, 5),
                    'avg_time_10min': performance_metrics.get_average_query_time(query_type, 10)
                }
            else:
                # 所有查询类型的统计
                query_stats = performance_metrics.get_query_stats_summary()
                for qtype in query_stats.keys():
                    summary['query_performance'][qtype] = {
                        'avg_time_1min': performance_metrics.get_average_query_time(qtype, 1),
                        'avg_time_5min': performance_metrics.get_average_query_time(qtype, 5),
                        'avg_time_10min': performance_metrics.get_average_query_time(qtype, 10),
                        'stats': query_stats[qtype]
                    }
            
            return summary
            
        except Exception as e:
            current_app.logger.error(f"获取详细统计失败: {str(e)}")
            return {'error': str(e)}


class PerformanceAlerts:
    """性能告警"""
    
    @staticmethod
    def check_performance_alerts():
        """检查性能告警"""
        alerts = []
        
        try:
            # 检查缓存命中率
            hit_rate = performance_metrics.get_cache_hit_rate()
            if hit_rate < 70:  # 命中率低于70%
                alerts.append({
                    'type': 'cache_hit_rate_low',
                    'message': f'缓存命中率过低: {hit_rate}%',
                    'severity': 'warning',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
            
            # 检查平均查询时间
            avg_time = performance_metrics.get_average_query_time(minutes=5)
            if avg_time > 2.0:  # 平均查询时间超过2秒
                alerts.append({
                    'type': 'slow_query_average',
                    'message': f'平均查询时间过长: {avg_time}秒',
                    'severity': 'warning',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
            
            # 检查慢查询数量
            slow_queries = performance_metrics.get_slow_queries(50)
            recent_slow = [q for q in slow_queries if time.time() - q['timestamp'] < 300]  # 5分钟内
            if len(recent_slow) > 10:  # 5分钟内超过10个慢查询
                alerts.append({
                    'type': 'too_many_slow_queries',
                    'message': f'5分钟内慢查询过多: {len(recent_slow)}个',
                    'severity': 'error',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
            
            # 检查Redis连接状态
            if not get_cache_manager().redis_manager.is_available():
                alerts.append({
                    'type': 'redis_unavailable',
                    'message': 'Redis缓存服务不可用',
                    'severity': 'error',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
            
        except Exception as e:
            alerts.append({
                'type': 'monitoring_error',
                'message': f'性能监控检查失败: {str(e)}',
                'severity': 'error',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return alerts


def log_request_performance():
    """记录请求性能"""
    if hasattr(g, 'start_time'):
        request_time = time.time() - g.start_time
        
        # 记录请求性能
        performance_metrics.record_query_time(
            f"request_{request.endpoint}",
            request_time,
            request_time > 3.0  # 请求超过3秒视为慢请求
        )


# 性能监控仪表板实例
perf_dashboard = PerformanceDashboard()
perf_alerts = PerformanceAlerts()


class PerformanceMonitor:
    """性能监控器 - 简化版本"""
    
    def __init__(self):
        self.metrics = PerformanceMetrics()
        self.enabled = True
    
    def start_monitoring(self):
        """启动监控"""
        pass
    
    def stop_monitoring(self):
        """停止监控"""
        pass
    
    def get_metrics(self):
        """获取性能指标"""
        return self.metrics
    
    def record_query(self, query_type, execution_time):
        """记录查询性能"""
        if self.enabled:
            self.metrics.record_query_time(query_type, execution_time)

# 全局性能监控实例
performance_monitor = PerformanceMonitor()
