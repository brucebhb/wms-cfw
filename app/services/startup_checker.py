#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动时检查和修复服务
检查缓存系统和优化系统是否被禁用，并自动修复
"""

import os
import re
import shutil
from datetime import datetime
from flask import current_app

class StartupChecker:
    """启动时检查器"""
    
    def __init__(self):
        self.app_init_file = None
        self.backup_dir = None
        
    def init_app(self, app):
        """初始化检查器"""
        self.app = app
        self.app_init_file = os.path.join(app.root_path, '__init__.py')
        self.backup_dir = os.path.join(os.path.dirname(app.root_path), 'backups', 'startup_fixes')
        
        # 确保备份目录存在
        os.makedirs(self.backup_dir, exist_ok=True)
        
        with app.app_context():
            self.perform_startup_checks()
    
    def perform_startup_checks(self):
        """执行启动检查"""
        current_app.logger.info("🔍 执行启动时系统检查...")
        
        checks_performed = []
        fixes_applied = []
        
        # 1. 检查缓存系统状态
        cache_status = self.check_cache_system()
        checks_performed.append(f"缓存系统: {'✅' if cache_status else '❌'}")
        if not cache_status:
            if self.fix_cache_system():
                fixes_applied.append("启用缓存系统")
        
        # 2. 检查优化系统状态
        optimization_status = self.check_optimization_system()
        checks_performed.append(f"优化系统: {'✅' if optimization_status else '❌'}")
        if not optimization_status:
            if self.fix_optimization_system():
                fixes_applied.append("启用优化系统")
        
        # 3. 检查性能监控状态
        monitoring_status = self.check_performance_monitoring()
        checks_performed.append(f"性能监控: {'✅' if monitoring_status else '❌'}")
        if not monitoring_status:
            if self.fix_performance_monitoring():
                fixes_applied.append("启用性能监控")
        
        # 4. 检查数据库优化状态
        db_optimization_status = self.check_database_optimization()
        checks_performed.append(f"数据库优化: {'✅' if db_optimization_status else '❌'}")
        
        # 5. 检查调度器状态
        scheduler_status = self.check_scheduler_status()
        checks_performed.append(f"调度器: {'✅' if scheduler_status else '❌'}")
        
        # 记录检查结果
        current_app.logger.info(f"📊 启动检查完成: {', '.join(checks_performed)}")
        
        if fixes_applied:
            current_app.logger.info(f"🔧 应用修复: {', '.join(fixes_applied)}")
            current_app.logger.warning("⚠️ 检测到系统配置问题并已自动修复，建议重启应用以确保所有修复生效")
        else:
            current_app.logger.info("✅ 所有系统组件状态正常")
    
    def check_cache_system(self):
        """检查缓存系统状态"""
        try:
            # 检查代码中是否启用缓存
            if self.is_cache_disabled_in_code():
                return False
            
            # 检查Redis连接
            from app.cache_config import get_cache_manager
            cache_manager = get_cache_manager()
            redis_client = cache_manager.redis_manager.get_client()
            if redis_client:
                redis_client.ping()
                return True
            else:
                return False
                
        except Exception as e:
            current_app.logger.error(f"缓存系统检查失败: {e}")
            return False
    
    def check_optimization_system(self):
        """检查优化系统状态"""
        try:
            # 检查代码中是否启用优化系统
            if self.is_optimization_disabled_in_code():
                return False
            
            # 检查优化组件是否可用
            from app.database_optimization import DatabaseOptimizer
            from app.hot_data_cache import cache_warmup
            return True
            
        except Exception as e:
            current_app.logger.error(f"优化系统检查失败: {e}")
            return False
    
    def check_performance_monitoring(self):
        """检查性能监控状态"""
        try:
            from app.performance_monitor import PerformanceMonitor
            monitor = PerformanceMonitor()
            return True
            
        except Exception as e:
            current_app.logger.error(f"性能监控检查失败: {e}")
            return False
    
    def check_database_optimization(self):
        """检查数据库优化状态"""
        try:
            from app.database_optimization import DatabaseOptimizer
            # 检查是否有必要的索引
            return DatabaseOptimizer.check_indexes_exist()
            
        except Exception as e:
            current_app.logger.error(f"数据库优化检查失败: {e}")
            return False
    
    def check_scheduler_status(self):
        """检查调度器状态"""
        try:
            from app.services.scheduler_service import scheduler_service
            return scheduler_service.is_running

        except Exception as e:
            current_app.logger.error(f"调度器检查失败: {e}")
            return False
    
    def is_cache_disabled_in_code(self):
        """检查代码中缓存是否被禁用"""
        try:
            with open(self.app_init_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查是否有注释掉的缓存初始化代码
            cache_patterns = [
                r'#\s*from app\.cache_config import get_cache_manager',
                r'#\s*get_cache_manager\(\)',
                r'缓存.*禁用',
                r'暂时禁用.*缓存'
            ]
            
            for pattern in cache_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    return True
            
            return False
            
        except Exception as e:
            current_app.logger.error(f"检查缓存代码状态失败: {e}")
            return False
    
    def is_optimization_disabled_in_code(self):
        """检查代码中优化系统是否被禁用"""
        try:
            with open(self.app_init_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查是否有注释掉的优化初始化代码
            optimization_patterns = [
                r'#\s*from app\.database_optimization import DatabaseOptimizer',
                r'#\s*DatabaseOptimizer\.create_indexes\(\)',
                r'#\s*from app\.hot_data_cache import cache_warmup',
                r'优化.*禁用',
                r'暂时禁用.*优化'
            ]
            
            for pattern in optimization_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    return True
            
            return False
            
        except Exception as e:
            current_app.logger.error(f"检查优化代码状态失败: {e}")
            return False
    
    def fix_cache_system(self):
        """修复缓存系统"""
        try:
            current_app.logger.info("🔧 尝试修复缓存系统...")
            
            # 备份原文件
            backup_file = os.path.join(
                self.backup_dir, 
                f"__init__.py.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            shutil.copy2(self.app_init_file, backup_file)
            
            # 读取文件内容
            with open(self.app_init_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 取消注释缓存相关代码
            fixes = [
                (r'#\s*(from app\.cache_config import get_cache_manager)', r'\1'),
                (r'#\s*(get_cache_manager\(\))', r'\1'),
                (r'#\s*(app\.logger\.info\("Redis缓存系统初始化完成"\))', r'\1'),
            ]
            
            modified = False
            for pattern, replacement in fixes:
                new_content = re.sub(pattern, replacement, content)
                if new_content != content:
                    content = new_content
                    modified = True
            
            if modified:
                # 写回文件
                with open(self.app_init_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                current_app.logger.info(f"✅ 缓存系统修复完成，备份文件: {backup_file}")
                return True
            else:
                current_app.logger.info("ℹ️ 缓存系统代码无需修复")
                return False
                
        except Exception as e:
            current_app.logger.error(f"缓存系统修复失败: {e}")
            return False
    
    def fix_optimization_system(self):
        """修复优化系统"""
        try:
            current_app.logger.info("🔧 尝试修复优化系统...")
            
            # 备份原文件
            backup_file = os.path.join(
                self.backup_dir, 
                f"__init__.py.optimization_backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            shutil.copy2(self.app_init_file, backup_file)
            
            # 读取文件内容
            with open(self.app_init_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 取消注释优化相关代码
            fixes = [
                (r'#\s*(from app\.database_optimization import DatabaseOptimizer)', r'\1'),
                (r'#\s*(DatabaseOptimizer\.create_indexes\(\))', r'\1'),
                (r'#\s*(from app\.hot_data_cache import cache_warmup)', r'\1'),
                (r'#\s*(cache_warmup\.warmup_basic_data_cache\(\))', r'\1'),
            ]
            
            modified = False
            for pattern, replacement in fixes:
                new_content = re.sub(pattern, replacement, content)
                if new_content != content:
                    content = new_content
                    modified = True
            
            if modified:
                # 写回文件
                with open(self.app_init_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                current_app.logger.info(f"✅ 优化系统修复完成，备份文件: {backup_file}")
                return True
            else:
                current_app.logger.info("ℹ️ 优化系统代码无需修复")
                return False
                
        except Exception as e:
            current_app.logger.error(f"优化系统修复失败: {e}")
            return False
    
    def fix_performance_monitoring(self):
        """修复性能监控"""
        try:
            current_app.logger.info("🔧 尝试修复性能监控...")
            
            # 检查性能监控是否需要初始化
            from app.performance_monitor import PerformanceMonitor
            monitor = PerformanceMonitor()
            monitor.start_monitoring()
            
            current_app.logger.info("✅ 性能监控修复完成")
            return True
            
        except Exception as e:
            current_app.logger.error(f"性能监控修复失败: {e}")
            return False

# 全局实例
startup_checker = StartupChecker()
