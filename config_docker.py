#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Docker容器化部署配置
"""

import os
from datetime import timedelta


class DockerConfig:
    """Docker容器化配置"""
    
    # 基础配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'docker-warehouse-secret-key-2024'
    
    # 数据库配置
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'mysql')
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT', 3306))
    MYSQL_USER = os.environ.get('MYSQL_USER', 'warehouse_user')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', 'warehouse_pass')
    MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE', 'warehouse_db')
    
    SQLALCHEMY_DATABASE_URI = (
        f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@'
        f'{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4'
    )
    
    # 异步数据库URL
    ASYNC_DATABASE_URI = (
        f'mysql+aiomysql://{MYSQL_USER}:{MYSQL_PASSWORD}@'
        f'{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4'
    )
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 20,
        'pool_timeout': 20,
        'pool_recycle': 3600,
        'max_overflow': 30,
        'pool_pre_ping': True
    }
    
    # Redis配置
    REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')
    REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
    REDIS_DB = int(os.environ.get('REDIS_DB', 0))
    REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', None)
    
    if REDIS_PASSWORD:
        REDIS_URL = f'redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}'
    else:
        REDIS_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}'
    
    # 会话配置
    PERMANENT_SESSION_LIFETIME = timedelta(hours=6)
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # 文件上传
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = '/app/uploads'
    
    # 日志配置
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = '/app/logs/warehouse.log'
    LOG_MAX_SIZE = 100 * 1024 * 1024  # 100MB
    LOG_BACKUP_COUNT = 5
    
    # 性能配置
    ENABLE_ASYNC = os.environ.get('ENABLE_ASYNC', 'True').lower() == 'true'
    ENABLE_CACHE = os.environ.get('ENABLE_CACHE', 'True').lower() == 'true'
    CACHE_DEFAULT_TIMEOUT = int(os.environ.get('CACHE_DEFAULT_TIMEOUT', 300))
    
    # 安全配置
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600
    
    # 调试配置（生产环境关闭）
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    TESTING = False
    
    # 应用配置
    WAREHOUSE_NAMES = {
        1: '平湖仓',
        2: '昆山仓', 
        3: '成都仓',
        4: '凭祥北投仓',
        5: '凭祥保税仓'
    }
    
    # 分页配置
    ITEMS_PER_PAGE = 20
    MAX_ITEMS_PER_PAGE = 100
    
    # 缓存配置
    CACHE_TYPE = 'redis'
    CACHE_REDIS_URL = REDIS_URL
    CACHE_DEFAULT_TIMEOUT = CACHE_DEFAULT_TIMEOUT
    
    # 异步任务配置
    ASYNC_POOL_SIZE = int(os.environ.get('ASYNC_POOL_SIZE', 10))
    ASYNC_TIMEOUT = int(os.environ.get('ASYNC_TIMEOUT', 30))
    
    # 监控配置
    ENABLE_METRICS = os.environ.get('ENABLE_METRICS', 'True').lower() == 'true'
    METRICS_PORT = int(os.environ.get('METRICS_PORT', 9090))
    
    @staticmethod
    def init_app(app):
        """初始化应用配置"""
        
        # 创建必要的目录
        os.makedirs('/app/logs', exist_ok=True)
        os.makedirs('/app/uploads', exist_ok=True)
        
        # 配置日志
        import logging
        from logging.handlers import RotatingFileHandler
        
        if not app.debug and not app.testing:
            # 文件日志
            file_handler = RotatingFileHandler(
                DockerConfig.LOG_FILE,
                maxBytes=DockerConfig.LOG_MAX_SIZE,
                backupCount=DockerConfig.LOG_BACKUP_COUNT
            )
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
            ))
            file_handler.setLevel(getattr(logging, DockerConfig.LOG_LEVEL))
            app.logger.addHandler(file_handler)
            
            # 控制台日志
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s'
            ))
            console_handler.setLevel(logging.INFO)
            app.logger.addHandler(console_handler)
            
            app.logger.setLevel(getattr(logging, DockerConfig.LOG_LEVEL))
            app.logger.info('🐳 仓库管理系统容器化启动')


class DevelopmentDockerConfig(DockerConfig):
    """开发环境Docker配置"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'


class ProductionDockerConfig(DockerConfig):
    """生产环境Docker配置"""
    DEBUG = False
    LOG_LEVEL = 'INFO'
    SESSION_COOKIE_SECURE = True
    
    @classmethod
    def init_app(cls, app):
        DockerConfig.init_app(app)
        
        # 生产环境额外配置
        import logging
        from logging import StreamHandler
        
        # 错误邮件通知（如果配置了）
        mail_handler = None
        if os.environ.get('MAIL_SERVER'):
            mail_handler = SMTPHandler(
                mailhost=(os.environ.get('MAIL_SERVER'), 587),
                fromaddr=os.environ.get('MAIL_FROM'),
                toaddrs=os.environ.get('MAIL_TO', '').split(','),
                subject='仓库管理系统错误',
                credentials=(
                    os.environ.get('MAIL_USERNAME'),
                    os.environ.get('MAIL_PASSWORD')
                ),
                secure=()
            )
            mail_handler.setLevel(logging.ERROR)
            app.logger.addHandler(mail_handler)


# 配置映射
config = {
    'development': DevelopmentDockerConfig,
    'production': ProductionDockerConfig,
    'default': DevelopmentDockerConfig
}
