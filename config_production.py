# -*- coding: utf-8 -*-
"""
生产环境配置文件
适用于腾讯云服务器 4核8GB 12Mbps
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env.production'))

class ProductionConfig:
    """生产环境配置"""
    
    # 基础配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(32).hex()
    DEBUG = False
    TESTING = False
    
    # MySQL数据库配置 - 生产环境优化
    MYSQL_HOST = os.environ.get('MYSQL_HOST') or 'localhost'
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT') or 3306)
    MYSQL_USER = os.environ.get('MYSQL_USER') or 'root'
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD') or ''
    MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE') or 'warehouse_db'
    
    # 数据库连接字符串 - 生产环境优化
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4&autocommit=true'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 数据库连接池配置 - 针对4核8GB服务器优化
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 20,              # 连接池大小，适合15用户并发
        'pool_timeout': 30,           # 连接超时
        'pool_recycle': 3600,         # 连接回收时间（1小时）
        'pool_pre_ping': True,        # 连接前ping检查
        'max_overflow': 10,           # 最大溢出连接
        'echo': False,                # 生产环境关闭SQL日志
        'connect_args': {
            'connect_timeout': 10,
            'read_timeout': 30,
            'write_timeout': 30,
            'charset': 'utf8mb4',
            'use_unicode': True,
            'autocommit': True
        }
    }
    
    # 分页配置
    ITEMS_PER_PAGE = 20  # 适合生产环境的分页大小
    
    # 会话配置 - 6小时自动过期
    PERMANENT_SESSION_LIFETIME = timedelta(hours=6)
    SESSION_TIMEOUT_HOURS = 6
    SESSION_COOKIE_SECURE = False  # HTTP环境设为False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # 安全配置
    SECURITY_ENABLED = True
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600
    WTF_CSRF_SSL_STRICT = False  # HTTP环境设为False
    
    # 并发控制配置 - 适合15用户
    CONCURRENT_LOCK_TIMEOUT = 30
    MAX_BATCH_OPERATIONS = 100
    MAX_EXPORT_RECORDS = 10000
    
    # 输入验证配置
    MAX_INPUT_LENGTH = 1000
    ALLOWED_FILE_EXTENSIONS = ['xlsx', 'xls', 'csv']
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    # SQL安全配置
    SQL_INJECTION_CHECK = True
    QUERY_TIMEOUT = 30
    
    # Redis缓存配置 - 生产环境
    REDIS_HOST = os.environ.get('REDIS_HOST') or 'localhost'
    REDIS_PORT = int(os.environ.get('REDIS_PORT') or 6379)
    REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD') or None
    REDIS_DB = int(os.environ.get('REDIS_DB') or 0)
    REDIS_URL = f'redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}' if REDIS_PASSWORD else f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}'
    
    # 缓存配置 - 针对8GB内存优化
    CACHE_TYPE = 'redis'
    CACHE_REDIS_URL = REDIS_URL
    CACHE_DEFAULT_TIMEOUT = 300  # 5分钟默认缓存
    CACHE_KEY_PREFIX = 'warehouse_prod:'
    
    # 日志配置 - 生产环境
    LOG_LEVEL = 'INFO'
    LOG_FILE_MAX_SIZE = 100 * 1024 * 1024  # 100MB
    LOG_FILE_BACKUP_COUNT = 5
    LOG_TO_STDOUT = False
    
    # 性能优化配置
    COMPRESS_MIMETYPES = [
        'text/html', 'text/css', 'text/xml',
        'application/json', 'application/javascript',
        'application/xml+rss', 'application/atom+xml',
        'image/svg+xml'
    ]
    COMPRESS_LEVEL = 6
    COMPRESS_MIN_SIZE = 500
    
    # 文件上传配置
    UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # 备份配置
    BACKUP_ENABLED = True
    BACKUP_INTERVAL_HOURS = 24  # 每24小时备份一次
    BACKUP_RETENTION_DAYS = 30  # 保留30天备份
    BACKUP_PATH = os.path.join(basedir, 'backups')
    
    # 监控配置
    MONITORING_ENABLED = True
    PERFORMANCE_MONITORING = True
    ERROR_MONITORING = True
    
    # 邮件配置（可选）
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    
    # 系统限制配置
    MAX_CONCURRENT_USERS = 20  # 略高于预期15用户
    MAX_DAILY_RECORDS = 500    # 高于预期200条记录
    MAX_WAREHOUSES = 15        # 高于预期10个仓库
    
    # API限流配置
    RATELIMIT_ENABLED = True
    RATELIMIT_DEFAULT = "100 per hour"
    RATELIMIT_STORAGE_URL = REDIS_URL

# 环境检测
def get_config():
    """根据环境变量返回配置类"""
    env = os.environ.get('FLASK_ENV', 'production')
    if env == 'production':
        return ProductionConfig
    else:
        # 开发环境回退
        from config import Config
        return Config
