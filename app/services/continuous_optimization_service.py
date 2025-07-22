#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
持续性优化服务
在服务器启动时和运行期间持续优化系统性能
"""

import os
import time
import psutil
import threading
from datetime import datetime, timedelta
from flask import current_app
from app import db
from app.models import SystemOptimizationLog

class ContinuousOptimizationService:
    """持续性优化服务"""
    
    def __init__(self):
        self.optimization_thread = None
        self.is_running = False
        self.last_optimization = None
        self.optimization_interval = 180  # 3分钟
        
    def init_app(self, app):
        """初始化服务"""
        self.app = app
        with app.app_context():
            # 服务器启动时执行初始优化
            self.startup_optimization()
            
            # 启动持续优化线程
            self.start_continuous_optimization()
    
    def startup_optimization(self):
        """服务器启动时的优化"""
        try:
            current_app.logger.info("🚀 执行启动时系统优化...")
            
            # 1. 检查并启用缓存系统
            self.check_and_enable_cache()
            
            # 2. 检查并启用优化系统
            self.check_and_enable_optimization()
            
            # 3. 清理临时文件
            self.cleanup_temp_files()
            
            # 4. 优化数据库连接
            self.optimize_database_connections()
            
            # 5. 预热缓存
            self.warmup_cache()
            
            # 记录优化日志
            self.log_optimization("startup", "启动时优化完成")
            current_app.logger.info("✅ 启动时系统优化完成")
            
        except Exception as e:
            current_app.logger.error(f"启动时优化失败: {e}")
    
    def check_and_enable_cache(self):
        """检查并启用缓存系统"""
        try:
            from app.cache_config import get_cache_manager
            cache_manager = get_cache_manager()
            
            # 测试缓存连接
            redis_client = cache_manager.redis_manager.get_client()
            if redis_client:
                redis_client.ping()
                current_app.logger.info("✅ 缓存系统正常运行")
                return True
            else:
                current_app.logger.warning("⚠️ 缓存系统连接失败")
                return False
                
        except Exception as e:
            current_app.logger.error(f"缓存系统检查失败: {e}")
            # 尝试重新初始化缓存
            try:
                from app.cache_config import RedisManager
                RedisManager._instance = None
                RedisManager._redis_client = None
                cache_manager = get_cache_manager()
                current_app.logger.info("🔄 缓存系统重新初始化成功")
                return True
            except Exception as retry_e:
                current_app.logger.error(f"缓存系统重新初始化失败: {retry_e}")
                return False
    
    def check_and_enable_optimization(self):
        """检查并启用优化系统"""
        try:
            # 检查性能监控是否启用
            from app.performance_monitor import PerformanceMonitor
            monitor = PerformanceMonitor()
            
            # 检查数据库优化是否启用
            from app.database_optimization import DatabaseOptimizer
            DatabaseOptimizer.check_and_create_indexes()
            
            current_app.logger.info("✅ 优化系统检查完成")
            return True
            
        except Exception as e:
            current_app.logger.error(f"优化系统检查失败: {e}")
            return False
    
    def cleanup_temp_files(self):
        """清理临时文件"""
        try:
            cleaned_files = 0
            cleaned_size = 0
            
            # 清理Python缓存文件
            for root, dirs, files in os.walk(current_app.root_path):
                for file in files:
                    if file.endswith(('.pyc', '.pyo')):
                        filepath = os.path.join(root, file)
                        try:
                            file_size = os.path.getsize(filepath)
                            os.remove(filepath)
                            cleaned_files += 1
                            cleaned_size += file_size
                        except:
                            pass
            
            if cleaned_files > 0:
                current_app.logger.info(f"🧹 清理临时文件: {cleaned_files} 个文件, {cleaned_size/1024:.1f} KB")
            
            return cleaned_files
            
        except Exception as e:
            current_app.logger.error(f"清理临时文件失败: {e}")
            return 0
    
    def optimize_database_connections(self):
        """优化数据库连接"""
        try:
            # 检查数据库连接池状态
            pool = db.engine.pool
            current_app.logger.info(f"📊 数据库连接池状态: {pool.checkedout()}/{pool.size()}")
            
            # 如果连接池使用率过高，进行优化
            if pool.checkedout() / pool.size() > 0.8:
                # 回收空闲连接
                pool.dispose()
                current_app.logger.info("🔄 数据库连接池已重置")
            
            return True
            
        except Exception as e:
            current_app.logger.error(f"数据库连接优化失败: {e}")
            return False
    
    def warmup_cache(self):
        """预热缓存"""
        try:
            from app.hot_data_cache import cache_warmup
            cache_warmup.warmup_basic_data_cache()
            current_app.logger.info("🔥 缓存预热完成")
            return True
            
        except Exception as e:
            current_app.logger.error(f"缓存预热失败: {e}")
            return False
    
    def start_continuous_optimization(self):
        """启动持续优化线程"""
        if not self.is_running:
            self.is_running = True
            self.optimization_thread = threading.Thread(
                target=self.continuous_optimization_loop,
                daemon=True
            )
            self.optimization_thread.start()
            current_app.logger.info("🔄 持续优化服务已启动")
    
    def stop_continuous_optimization(self):
        """停止持续优化"""
        self.is_running = False
        if self.optimization_thread:
            self.optimization_thread.join(timeout=5)
        current_app.logger.info("⏹️ 持续优化服务已停止")
    
    def continuous_optimization_loop(self):
        """持续优化循环"""
        while self.is_running:
            try:
                time.sleep(self.optimization_interval)
                
                if self.is_running:
                    with self.app.app_context():
                        self.periodic_optimization()
                        
            except Exception as e:
                with self.app.app_context():
                    current_app.logger.error(f"持续优化循环错误: {e}")
    
    def periodic_optimization(self):
        """定期优化"""
        try:
            current_app.logger.info("🔧 执行定期系统优化...")
            
            optimization_results = {
                'cache_check': False,
                'memory_check': False,
                'database_check': False,
                'cleanup': 0
            }
            
            # 1. 检查缓存系统状态
            optimization_results['cache_check'] = self.check_cache_health()
            
            # 2. 检查内存使用情况
            optimization_results['memory_check'] = self.check_memory_usage()
            
            # 3. 检查数据库性能
            optimization_results['database_check'] = self.check_database_performance()
            
            # 4. 轻量级清理
            optimization_results['cleanup'] = self.lightweight_cleanup()
            
            # 记录优化结果
            self.log_optimization("periodic", f"定期优化完成: {optimization_results}")
            
            # 如果发现问题，记录警告
            issues = []
            if not optimization_results['cache_check']:
                issues.append("缓存系统异常")
            if not optimization_results['memory_check']:
                issues.append("内存使用过高")
            if not optimization_results['database_check']:
                issues.append("数据库性能异常")
            
            if issues:
                current_app.logger.warning(f"⚠️ 发现问题: {', '.join(issues)}")
            else:
                current_app.logger.info("✅ 定期优化完成，系统状态良好")
                
        except Exception as e:
            current_app.logger.error(f"定期优化失败: {e}")
    
    def check_cache_health(self):
        """检查缓存健康状态"""
        try:
            from app.cache_config import get_cache_manager
            cache_manager = get_cache_manager()
            
            # 测试缓存读写
            test_key = f"health_check_{int(time.time())}"
            cache_manager.set('test', test_key, 'health_check', timeout=60)
            result = cache_manager.get('test', test_key)
            cache_manager.delete('test', test_key)
            
            return result == 'health_check'
            
        except Exception as e:
            current_app.logger.error(f"缓存健康检查失败: {e}")
            return False
    
    def check_memory_usage(self):
        """检查内存使用情况"""
        try:
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            if memory_percent > 85:
                current_app.logger.warning(f"⚠️ 内存使用率过高: {memory_percent:.1f}%")
                # 尝试清理缓存
                try:
                    from app.cache_config import get_cache_manager
                    cache_manager = get_cache_manager()
                    redis_client = cache_manager.redis_manager.get_client()
                    if redis_client:
                        # 清理过期的缓存
                        redis_client.flushdb()
                        current_app.logger.info("🧹 已清理缓存以释放内存")
                except:
                    pass
                return False
            
            return True
            
        except Exception as e:
            current_app.logger.error(f"内存检查失败: {e}")
            return False
    
    def check_database_performance(self):
        """检查数据库性能"""
        try:
            start_time = time.time()
            
            # 执行简单查询测试
            from app.models import User
            User.query.limit(1).all()
            
            query_time = time.time() - start_time
            
            if query_time > 1.0:  # 查询时间超过1秒
                current_app.logger.warning(f"⚠️ 数据库查询慢: {query_time:.3f}秒")
                return False
            
            return True
            
        except Exception as e:
            current_app.logger.error(f"数据库性能检查失败: {e}")
            return False
    
    def lightweight_cleanup(self):
        """轻量级清理"""
        try:
            cleaned_files = 0
            
            # 只清理最近的临时文件
            temp_dirs = [
                os.path.join(current_app.root_path, '__pycache__'),
                os.path.join(current_app.root_path, 'app', '__pycache__')
            ]
            
            for temp_dir in temp_dirs:
                if os.path.exists(temp_dir):
                    for file in os.listdir(temp_dir):
                        if file.endswith('.pyc'):
                            filepath = os.path.join(temp_dir, file)
                            try:
                                # 只删除1小时内创建的文件
                                if time.time() - os.path.getctime(filepath) < 3600:
                                    os.remove(filepath)
                                    cleaned_files += 1
                            except:
                                pass
            
            return cleaned_files
            
        except Exception as e:
            current_app.logger.error(f"轻量级清理失败: {e}")
            return 0
    
    def log_optimization(self, optimization_type, message):
        """记录优化日志"""
        try:
            log_entry = SystemOptimizationLog(
                optimization_type=optimization_type,
                message=message,
                timestamp=datetime.now()
            )
            db.session.add(log_entry)
            db.session.commit()
            
        except Exception as e:
            current_app.logger.error(f"记录优化日志失败: {e}")
    
    def get_optimization_status(self):
        """获取优化状态"""
        return {
            'is_running': self.is_running,
            'last_optimization': self.last_optimization,
            'optimization_interval': self.optimization_interval,
            'thread_alive': self.optimization_thread.is_alive() if self.optimization_thread else False
        }

# 全局实例
continuous_optimization_service = ContinuousOptimizationService()
