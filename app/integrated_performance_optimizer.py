#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
仓储管理系统整合性能优化器
整合现有的性能监控、缓存管理、数据库优化等功能
提供统一的性能优化接口，避免重复工作
"""

import os
import sys
import time
import psutil
import logging
from datetime import datetime, timedelta
from flask import current_app
from app.performance_monitor import performance_metrics, perf_dashboard, perf_alerts
from app.cache_config import get_cache_manager
from app.database_optimization import DatabaseOptimizer, QueryStats
from app.logging_config import get_log_file_sizes, cleanup_old_logs


class IntegratedPerformanceOptimizer:
    """整合的性能优化器 - 避免重复现有功能"""
    
    def __init__(self):
        self.logger = self._setup_logger()
        self.cache_manager = get_cache_manager()
        self.db_optimizer = DatabaseOptimizer()
        
    def _setup_logger(self):
        """设置性能优化日志"""
        logger = logging.getLogger('integrated_performance')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            # 确保logs目录存在
            os.makedirs('logs', exist_ok=True)
            
            handler = logging.FileHandler('logs/performance_optimization.log', encoding='utf-8')
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    def run_comprehensive_optimization(self):
        """运行综合性能优化"""
        self.logger.info("开始综合性能优化...")
        
        optimization_results = {
            'timestamp': datetime.now(),
            'database_optimization': self._optimize_database(),
            'cache_optimization': self._optimize_cache(),
            'log_optimization': self._optimize_logs(),
            'system_cleanup': self._system_cleanup(),
            'performance_report': self._generate_performance_report()
        }
        
        self.logger.info("综合性能优化完成")
        return optimization_results
    
    def _optimize_database(self):
        """数据库优化 - 使用现有的DatabaseOptimizer"""
        try:
            self.logger.info("开始数据库优化...")
            
            # 使用现有的数据库优化器
            self.db_optimizer.create_indexes()
            self.db_optimizer.analyze_tables()
            
            # 获取表统计
            table_stats = QueryStats.get_table_stats()
            
            return {
                'status': 'success',
                'message': '数据库优化完成',
                'table_stats': table_stats,
                'optimizations_applied': [
                    '创建复合索引',
                    '分析表统计信息',
                    '优化查询计划'
                ]
            }
            
        except Exception as e:
            self.logger.error(f"数据库优化失败: {e}")
            return {
                'status': 'error',
                'message': f'数据库优化失败: {str(e)}'
            }
    
    def _optimize_cache(self):
        """缓存优化 - 使用现有的缓存管理器"""
        try:
            self.logger.info("开始缓存优化...")
            
            # 获取缓存统计
            cache_stats = self.cache_manager.get_cache_stats()
            
            # 检查缓存命中率
            hit_rate = performance_metrics.get_cache_hit_rate()
            
            optimizations = []
            
            # 如果命中率低，清理一些缓存让新数据进入
            if hit_rate < 60:
                # 清理搜索结果缓存（最容易过期的）
                cleared = self.cache_manager.delete_pattern('search_results*')
                optimizations.append(f'清理搜索结果缓存: {cleared} 个键')
            
            # 清理过期的库存缓存
            if cache_stats.get('our_cache_keys', 0) > 1000:
                cleared_inventory = self.cache_manager.clear_inventory_cache()
                optimizations.append(f'清理库存缓存: {cleared_inventory} 个键')
            
            return {
                'status': 'success',
                'message': '缓存优化完成',
                'cache_stats': cache_stats,
                'hit_rate': hit_rate,
                'optimizations_applied': optimizations
            }
            
        except Exception as e:
            self.logger.error(f"缓存优化失败: {e}")
            return {
                'status': 'error',
                'message': f'缓存优化失败: {str(e)}'
            }
    
    def _optimize_logs(self):
        """日志优化 - 使用现有的日志管理功能"""
        try:
            self.logger.info("开始日志优化...")
            
            # 获取日志文件信息
            log_info = get_log_file_sizes()
            
            # 清理30天前的日志
            cleanup_old_logs(30)
            
            # 统计大文件
            large_files = []
            total_size = 0
            
            for log_file, info in log_info.items():
                if 'size_mb' in info:
                    total_size += info['size_mb']
                    if info['size_mb'] > 50:  # 大于50MB的文件
                        large_files.append({
                            'file': log_file,
                            'size_mb': info['size_mb']
                        })
            
            return {
                'status': 'success',
                'message': '日志优化完成',
                'total_log_size_mb': round(total_size, 2),
                'large_files': large_files,
                'optimizations_applied': [
                    '清理30天前的日志文件',
                    '统计日志文件大小'
                ]
            }
            
        except Exception as e:
            self.logger.error(f"日志优化失败: {e}")
            return {
                'status': 'error',
                'message': f'日志优化失败: {str(e)}'
            }
    
    def _system_cleanup(self):
        """系统清理"""
        try:
            self.logger.info("开始系统清理...")
            
            # 检查系统资源
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('.')
            
            cleanup_actions = []
            
            # 如果内存使用率过高，建议重启应用
            if memory.percent > 85:
                cleanup_actions.append('内存使用率过高，建议重启应用')
            
            # 如果磁盘空间不足，建议清理
            if disk.percent > 90:
                cleanup_actions.append('磁盘空间不足，建议清理临时文件')
            
            return {
                'status': 'success',
                'message': '系统清理检查完成',
                'system_stats': {
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'disk_percent': disk.percent
                },
                'cleanup_actions': cleanup_actions
            }
            
        except Exception as e:
            self.logger.error(f"系统清理失败: {e}")
            return {
                'status': 'error',
                'message': f'系统清理失败: {str(e)}'
            }
    
    def _generate_performance_report(self):
        """生成性能报告 - 使用现有的性能监控功能"""
        try:
            # 使用现有的性能仪表板
            performance_summary = perf_dashboard.get_performance_summary()
            
            # 检查性能告警
            alerts = perf_alerts.check_performance_alerts()
            
            return {
                'status': 'success',
                'performance_summary': performance_summary,
                'alerts': alerts,
                'recommendations': self._get_optimization_recommendations()
            }
            
        except Exception as e:
            self.logger.error(f"生成性能报告失败: {e}")
            return {
                'status': 'error',
                'message': f'生成性能报告失败: {str(e)}'
            }
    
    def _get_optimization_recommendations(self):
        """获取优化建议"""
        recommendations = []
        
        try:
            # 基于缓存命中率的建议
            hit_rate = performance_metrics.get_cache_hit_rate()
            if hit_rate < 70:
                recommendations.append({
                    'type': 'cache',
                    'priority': 'high',
                    'message': f'缓存命中率较低({hit_rate}%)，建议优化缓存策略'
                })
            
            # 基于慢查询的建议
            slow_queries = performance_metrics.get_slow_queries(10)
            if len(slow_queries) > 5:
                recommendations.append({
                    'type': 'database',
                    'priority': 'high',
                    'message': f'检测到{len(slow_queries)}个慢查询，建议优化数据库索引'
                })
            
            # 基于系统资源的建议
            try:
                memory = psutil.virtual_memory()
                if memory.percent > 80:
                    recommendations.append({
                        'type': 'system',
                        'priority': 'medium',
                        'message': f'内存使用率较高({memory.percent}%)，建议优化内存使用'
                    })
            except:
                pass
            
        except Exception as e:
            self.logger.error(f"获取优化建议失败: {e}")
        
        return recommendations
    
    def get_quick_status(self):
        """获取快速状态检查"""
        try:
            return {
                'cache_hit_rate': performance_metrics.get_cache_hit_rate(),
                'avg_query_time': performance_metrics.get_average_query_time(minutes=5),
                'slow_queries_count': len(performance_metrics.get_slow_queries(10)),
                'redis_available': self.cache_manager.redis_manager.is_available(),
                'system_memory_percent': psutil.virtual_memory().percent,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        except Exception as e:
            return {'error': str(e)}


# 全局优化器实例
integrated_optimizer = IntegratedPerformanceOptimizer()


def run_optimization():
    """运行优化的便捷函数"""
    return integrated_optimizer.run_comprehensive_optimization()


def get_performance_status():
    """获取性能状态的便捷函数"""
    return integrated_optimizer.get_quick_status()
