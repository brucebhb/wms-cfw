#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调度器配置文件
集中管理所有定时任务的配置
"""

from datetime import time

class SchedulerConfig:
    """调度器配置类"""
    
    # 基础配置
    TIMEZONE = 'Asia/Shanghai'
    
    # 任务默认配置
    JOB_DEFAULTS = {
        'coalesce': True,  # 合并多个相同的任务
        'max_instances': 1,  # 同一时间只运行一个实例
        'misfire_grace_time': 600  # 错过执行时间的容忍度（秒）
    }
    
    # 工作时间配置
    WORK_HOURS = {
        'start': time(9, 0),   # 9:00
        'end': time(18, 0)     # 18:00
    }
    
    # 任务配置
    JOBS = {
        # 智能维护任务
        'smart_maintenance': {
            'name': '智能维护任务',
            'trigger_type': 'interval',
            'trigger_config': {'minutes': 5},
            'enabled': True,
            'work_hours_only': False,  # 是否只在工作时间运行
            'priority': 'medium',
            'description': '根据系统负载智能执行维护任务'
        },
        
        # 轻量级监控
        'light_monitoring': {
            'name': '轻量级监控',
            'trigger_type': 'interval',
            'trigger_config': {'minutes': 10},
            'enabled': True,
            'work_hours_only': False,
            'priority': 'low',
            'description': '监控系统状态和任务执行情况'
        },
        
        # 每日维护
        'daily_maintenance': {
            'name': '每日深度维护',
            'trigger_type': 'cron',
            'trigger_config': {'hour': 2, 'minute': 0},
            'enabled': True,
            'work_hours_only': False,
            'priority': 'high',
            'description': '每日凌晨执行深度维护和清理'
        },
        
        # 每周优化
        'weekly_optimization': {
            'name': '每周系统优化',
            'trigger_type': 'cron',
            'trigger_config': {'day_of_week': 6, 'hour': 3, 'minute': 0},  # 周日凌晨3点
            'enabled': True,
            'work_hours_only': False,
            'priority': 'high',
            'description': '每周执行数据库优化和系统清理'
        },
        
        # 健康检查
        'health_check': {
            'name': '系统健康检查',
            'trigger_type': 'interval',
            'trigger_config': {'hours': 1},
            'enabled': True,
            'work_hours_only': False,
            'priority': 'medium',
            'description': '定期检查系统健康状态'
        },
        
        # 日志清理（可选）
        'log_cleanup': {
            'name': '日志清理',
            'trigger_type': 'cron',
            'trigger_config': {'hour': 1, 'minute': 30},
            'enabled': False,  # 默认禁用，可手动启用
            'work_hours_only': False,
            'priority': 'low',
            'description': '清理过期的日志文件'
        },
        
        # 数据备份（可选）
        'data_backup': {
            'name': '数据备份',
            'trigger_type': 'cron',
            'trigger_config': {'hour': 4, 'minute': 0},
            'enabled': False,  # 默认禁用
            'work_hours_only': False,
            'priority': 'high',
            'description': '备份重要数据'
        }
    }
    
    # 维护配置
    MAINTENANCE_CONFIG = {
        # 日志文件大小阈值（MB）
        'log_size_threshold': 50,
        
        # 日志保留天数
        'log_retention_days': 7,
        
        # 工作时间维护阈值
        'work_hours_threshold': 100,  # MB，工作时间内只有超过此大小才维护
        
        # 备份保留天数
        'backup_retention_days': 30,
        
        # 数据库优化阈值
        'db_optimization_threshold': 1000  # 记录数
    }
    
    # 监控配置
    MONITORING_CONFIG = {
        # 错误率阈值
        'error_rate_threshold': 0.1,  # 10%
        
        # 任务超时阈值（分钟）
        'job_timeout_threshold': 30,
        
        # 内存使用阈值（MB）
        'memory_threshold': 1024,
        
        # 磁盘使用阈值（%）
        'disk_threshold': 85
    }
    
    # 通知配置
    NOTIFICATION_CONFIG = {
        # 是否启用通知
        'enabled': False,
        
        # 通知方式
        'methods': ['log'],  # 可选: log, email, webhook
        
        # 邮件配置
        'email': {
            'smtp_server': '',
            'smtp_port': 587,
            'username': '',
            'password': '',
            'from_addr': '',
            'to_addrs': []
        },
        
        # Webhook配置
        'webhook': {
            'url': '',
            'timeout': 10
        }
    }
    
    @classmethod
    def get_job_config(cls, job_id):
        """获取指定任务的配置"""
        return cls.JOBS.get(job_id, {})
    
    @classmethod
    def get_enabled_jobs(cls):
        """获取启用的任务列表"""
        return {job_id: config for job_id, config in cls.JOBS.items() 
                if config.get('enabled', True)}
    
    @classmethod
    def is_work_hours(cls):
        """检查当前是否为工作时间"""
        from datetime import datetime
        now = datetime.now().time()
        return cls.WORK_HOURS['start'] <= now <= cls.WORK_HOURS['end']
    
    @classmethod
    def should_run_in_work_hours(cls, job_id):
        """检查任务是否应该在工作时间运行"""
        job_config = cls.get_job_config(job_id)
        work_hours_only = job_config.get('work_hours_only', False)
        
        if work_hours_only:
            return cls.is_work_hours()
        return True
    
    @classmethod
    def get_job_priority(cls, job_id):
        """获取任务优先级"""
        job_config = cls.get_job_config(job_id)
        return job_config.get('priority', 'medium')
    
    @classmethod
    def update_job_config(cls, job_id, **kwargs):
        """更新任务配置"""
        if job_id in cls.JOBS:
            cls.JOBS[job_id].update(kwargs)
            return True
        return False
    
    @classmethod
    def enable_job(cls, job_id):
        """启用任务"""
        return cls.update_job_config(job_id, enabled=True)
    
    @classmethod
    def disable_job(cls, job_id):
        """禁用任务"""
        return cls.update_job_config(job_id, enabled=False)


# 开发环境配置
class DevelopmentSchedulerConfig(SchedulerConfig):
    """开发环境调度器配置"""
    
    # 开发环境下减少任务频率
    JOBS = SchedulerConfig.JOBS.copy()
    JOBS.update({
        'smart_maintenance': {
            **SchedulerConfig.JOBS['smart_maintenance'],
            'trigger_config': {'minutes': 10}  # 开发环境10分钟
        },
        'light_monitoring': {
            **SchedulerConfig.JOBS['light_monitoring'],
            'trigger_config': {'minutes': 30}  # 开发环境30分钟
        }
    })


# 生产环境配置
class ProductionSchedulerConfig(SchedulerConfig):
    """生产环境调度器配置"""
    
    # 生产环境启用通知
    NOTIFICATION_CONFIG = {
        **SchedulerConfig.NOTIFICATION_CONFIG,
        'enabled': True,
        'methods': ['log', 'email']
    }


# 根据环境选择配置
def get_scheduler_config():
    """根据环境获取调度器配置"""
    import os
    
    env = os.environ.get('FLASK_ENV', 'development')
    
    if env == 'production':
        return ProductionSchedulerConfig
    else:
        return DevelopmentSchedulerConfig
