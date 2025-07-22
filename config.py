import os
from datetime import timedelta
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard-to-guess-string'

    # MySQL数据库配置
    MYSQL_HOST = os.environ.get('MYSQL_HOST') or 'localhost'
    MYSQL_PORT = os.environ.get('MYSQL_PORT') or '3306'
    MYSQL_USER = os.environ.get('MYSQL_USER') or 'root'
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD') or ''
    MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE') or 'warehouse_db'

    # 构建MySQL连接字符串
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4'

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_timeout': 20,
        'max_overflow': 0,
        'echo': False  # 设置为True可以看到SQL语句
    }

    ITEMS_PER_PAGE = 50

    # 会话配置 - 6小时自动掉线
    PERMANENT_SESSION_LIFETIME = timedelta(hours=6)
    SESSION_TIMEOUT_HOURS = 6

    # 安全配置
    SECURITY_ENABLED = True
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # CSRF令牌1小时有效期

    # 并发控制配置
    CONCURRENT_LOCK_TIMEOUT = 30  # 并发锁超时时间（秒）
    MAX_BATCH_OPERATIONS = 100    # 最大批量操作数量
    MAX_EXPORT_RECORDS = 10000    # 最大导出记录数

    # 输入验证配置
    MAX_INPUT_LENGTH = 1000       # 最大输入长度
    ALLOWED_FILE_EXTENSIONS = ['xlsx', 'xls', 'csv']  # 允许的文件扩展名
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 最大文件大小 10MB

    # SQL安全配置
    SQL_INJECTION_CHECK = True    # 启用SQL注入检查
    QUERY_TIMEOUT = 30           # 查询超时时间（秒）

    # 日志安全配置
    SECURITY_LOG_ENABLED = True   # 启用安全日志
    LOG_SENSITIVE_DATA = False    # 不记录敏感数据

# 性能优化配置
COMPRESS_MIMETYPES = [
    'text/html',
    'text/css',
    'text/xml',
    'application/json',
    'application/javascript',
    'application/xml+rss',
    'application/atom+xml',
    'image/svg+xml'
]

# 启用压缩
COMPRESS_LEVEL = 6
COMPRESS_MIN_SIZE = 500
