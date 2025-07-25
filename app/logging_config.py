#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志配置模块
提供统一的日志配置和管理
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime


class LoggingConfig:
    """日志配置类"""

    @staticmethod
    def setup_logging(app):
        """设置应用日志配置"""

        # 确保日志目录存在
        if not os.path.exists('logs'):
            os.mkdir('logs')

        # 清理旧的处理器
        app.logger.handlers.clear()

        # 设置根日志级别
        logging.getLogger().setLevel(logging.INFO)

        if app.debug:
            # 开发模式：控制台输出
            LoggingConfig._setup_development_logging(app)
        else:
            # 生产模式：文件输出
            LoggingConfig._setup_production_logging(app)
    
    @staticmethod
    def _setup_development_logging(app):
        """设置开发模式日志"""
        # 设置控制台编码
        if sys.platform.startswith('win'):
            import codecs
            import io
            # 使用UTF-8编码的控制台输出
            console_handler = logging.StreamHandler(
                io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
            )
        else:
            console_handler = logging.StreamHandler(sys.stdout)

        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%H:%M:%S'
        ))
        console_handler.setLevel(logging.DEBUG)
        app.logger.addHandler(console_handler)
        app.logger.setLevel(logging.DEBUG)
        app.logger.info('开发模式日志已启用')
    
    @staticmethod
    def _setup_production_logging(app):
        """设置生产模式日志"""

        # 设置UTF-8编码格式化器
        utf8_formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        error_formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s [in %(pathname)s:%(lineno)d]',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # 1. 错误日志 - 只记录WARNING及以上级别
        error_handler = logging.handlers.RotatingFileHandler(
            'logs/error.log',
            maxBytes=10*1024*1024,  # 10MB (减小文件大小)
            backupCount=5,
            encoding='utf-8'  # 指定UTF-8编码
        )
        error_handler.setFormatter(error_formatter)
        error_handler.setLevel(logging.WARNING)
        app.logger.addHandler(error_handler)

        # 2. 业务日志 - 记录重要的业务操作
        business_handler = logging.handlers.RotatingFileHandler(
            'logs/business.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        business_handler.setFormatter(utf8_formatter)
        business_handler.setLevel(logging.INFO)
        business_handler.addFilter(BusinessLogFilter())
        app.logger.addHandler(business_handler)

        # 3. 系统日志 - 记录系统级别的信息
        system_handler = logging.handlers.RotatingFileHandler(
            'logs/system.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=3,
            encoding='utf-8'
        )
        system_handler.setFormatter(utf8_formatter)
        system_handler.setLevel(logging.INFO)
        system_handler.addFilter(SystemLogFilter())
        app.logger.addHandler(system_handler)

        # 4. 性能日志 - 记录性能相关信息
        performance_handler = logging.handlers.RotatingFileHandler(
            'logs/performance.log',
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        performance_handler.setFormatter(utf8_formatter)
        performance_handler.setLevel(logging.INFO)
        performance_handler.addFilter(PerformanceLogFilter())
        app.logger.addHandler(performance_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('生产模式日志已启用')


class BusinessLogFilter(logging.Filter):
    """业务日志过滤器 - 只记录重要的业务操作"""

    def filter(self, record):
        message = record.getMessage()

        # 记录的业务操作
        include_patterns = [
            '出库记录保存成功',
            '入库记录保存成功',
            '接收记录保存成功',
            '用户登录',
            '用户登出',
            '批次号生成',
            '创建出库记录',
            '创建入库记录',
            '创建接收记录',
            '库存更新成功',
            '库存清零',
            '数据导入',
            '数据导出',
            '打印操作',
            '标签打印',
            '单据打印',
            '维护完成',
            '清理完成',
            '权限变更',
            '用户创建',
            '用户删除',
            '密码修改'
        ]

        # 过滤掉的频繁信息
        exclude_patterns = [
            '检查仓库权限',
            '用户已认证',
            '用户仓库类型',
            '查看权限',
            '获取收货人列表',
            'Working outside of application context',
            '轻量级清理异常',
            '3分钟维护周期异常',
            '调度器已关闭',
            '调度器启动',
            '开始执行',
            '开始加载',
            '数据库表检查',
            '缓存系统',
            '性能监控',
            'GET /',
            'POST /',
            'API调用'
        ]

        # 如果包含重要业务操作，记录
        if any(pattern in message for pattern in include_patterns):
            return True

        # 如果包含要排除的模式，不记录
        if any(pattern in message for pattern in exclude_patterns):
            return False

        # 其他INFO级别的消息，根据级别决定
        return record.levelno >= logging.WARNING


class SystemLogFilter(logging.Filter):
    """系统日志过滤器 - 只记录系统级别的信息"""

    def filter(self, record):
        message = record.getMessage()

        # 系统级别的信息
        system_patterns = [
            '应用启动',
            '应用关闭',
            '数据库连接',
            '数据库初始化',
            '数据库表创建',
            '数据库优化',
            '缓存初始化',
            '缓存清理',
            '索引创建',
            '索引优化',
            '健康检查',
            '系统维护',
            '服务启动',
            '服务停止',
            '初始化完成',
            '配置加载',
            '蓝图注册',
            '扩展初始化'
        ]

        # 排除频繁的调试信息和调度器信息
        exclude_patterns = [
            'Working outside of application context',
            '检查仓库权限',
            '用户已认证',
            '获取收货人列表',
            '调度器已关闭',  # 过滤掉频繁的调度器关闭信息
            '调度器启动',
            '3分钟维护周期',
            '轻量级清理',
            '数据库表检查完成',  # 这个太频繁了
            '收货人信息初始化完成'
        ]

        # 如果包含要排除的模式，不记录
        if any(pattern in message for pattern in exclude_patterns):
            return False

        # 如果包含系统模式或者是WARNING以上级别，记录
        return (any(pattern in message for pattern in system_patterns) or
                record.levelno >= logging.WARNING)


class PerformanceLogFilter(logging.Filter):
    """性能日志过滤器 - 只记录性能相关的信息"""
    
    def filter(self, record):
        message = record.getMessage()
        
        performance_patterns = [
            '请求耗时',
            '查询耗时',
            '处理时间',
            '响应时间',
            '性能',
            '缓慢',
            '超时'
        ]
        
        return any(pattern in message for pattern in performance_patterns)


def get_logger(name):
    """获取指定名称的日志记录器"""
    return logging.getLogger(name)


def log_business_operation(operation, details=None, user=None):
    """记录业务操作"""
    logger = get_logger('business')
    message = f"业务操作: {operation}"
    if user:
        message += f" [用户: {user}]"
    if details:
        message += f" [详情: {details}]"
    logger.info(message)


def log_system_event(event, details=None):
    """记录系统事件"""
    logger = get_logger('system')
    message = f"系统事件: {event}"
    if details:
        message += f" [详情: {details}]"
    logger.info(message)


def log_performance_issue(operation, duration, threshold=1.0):
    """记录性能问题"""
    if duration > threshold:
        logger = get_logger('performance')
        logger.warning(f"性能警告: {operation} 耗时 {duration:.2f}秒 (阈值: {threshold}秒)")


def cleanup_old_logs(days=30):
    """清理旧的日志文件"""
    import glob
    import time

    log_files = glob.glob('logs/*.log*')
    current_time = time.time()
    cutoff_time = current_time - (days * 24 * 60 * 60)

    cleaned_count = 0
    for log_file in log_files:
        try:
            if os.path.getmtime(log_file) < cutoff_time:
                os.remove(log_file)
                cleaned_count += 1
                print(f"已删除旧日志文件: {log_file}")
        except Exception as e:
            print(f"删除日志文件失败 {log_file}: {e}")

    if cleaned_count > 0:
        logger = get_logger('system')
        logger.info(f"日志清理完成，删除了 {cleaned_count} 个旧文件")


def get_log_file_sizes():
    """获取日志文件大小信息"""
    import glob

    log_info = {}
    log_files = glob.glob('logs/*.log')

    for log_file in log_files:
        try:
            size = os.path.getsize(log_file)
            size_mb = size / (1024 * 1024)
            log_info[log_file] = {
                'size_bytes': size,
                'size_mb': round(size_mb, 2),
                'modified': datetime.fromtimestamp(os.path.getmtime(log_file))
            }
        except Exception as e:
            log_info[log_file] = {'error': str(e)}

    return log_info


def rotate_logs_manually():
    """手动轮转日志文件"""
    import glob
    import shutil

    log_files = ['logs/error.log', 'logs/business.log', 'logs/system.log', 'logs/performance.log']

    for log_file in log_files:
        if os.path.exists(log_file):
            try:
                # 创建备份文件名
                backup_name = f"{log_file}.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                shutil.move(log_file, backup_name)

                # 创建新的空日志文件
                open(log_file, 'w', encoding='utf-8').close()

                logger = get_logger('system')
                logger.info(f"手动轮转日志文件: {log_file} -> {backup_name}")

            except Exception as e:
                print(f"轮转日志文件失败 {log_file}: {e}")
