# -*- coding: utf-8 -*-
"""
Gunicorn生产环境配置文件
适用于腾讯云4核8G服务器，15用户并发
"""

import multiprocessing
import os

# 服务器配置
bind = "0.0.0.0:5000"
backlog = 2048

# 工作进程配置 - 针对4核CPU优化
workers = 4  # CPU核心数
worker_class = "gevent"  # 使用gevent异步工作模式
worker_connections = 1000  # 每个worker的连接数
max_requests = 1000  # 每个worker处理的最大请求数
max_requests_jitter = 50  # 随机化重启
preload_app = True  # 预加载应用

# 超时配置
timeout = 30  # worker超时时间
keepalive = 2  # keep-alive连接时间
graceful_timeout = 30  # 优雅关闭超时

# 日志配置
accesslog = "/var/log/warehouse/gunicorn_access.log"
errorlog = "/var/log/warehouse/gunicorn_error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# 进程命名
proc_name = "warehouse_production"

# 用户和组（如果以root启动）
user = "warehouse"
group = "warehouse"

# 临时目录
tmp_upload_dir = "/tmp"

# 环境变量
raw_env = [
    'FLASK_ENV=production',
    'PYTHONPATH=/opt/warehouse',
]

# 性能优化
enable_stdio_inheritance = True
reuse_port = True

# 安全配置
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# SSL配置（如果使用HTTPS）
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"

# 监控配置
statsd_host = None  # 如果使用StatsD监控
statsd_prefix = "warehouse"

# 钩子函数
def on_starting(server):
    """服务器启动时执行"""
    server.log.info("🚀 仓储管理系统正在启动...")

def on_reload(server):
    """重载时执行"""
    server.log.info("🔄 仓储管理系统正在重载...")

def when_ready(server):
    """服务器准备就绪时执行"""
    server.log.info("✅ 仓储管理系统已就绪")
    server.log.info(f"📍 监听地址: {bind}")
    server.log.info(f"👥 工作进程数: {workers}")
    server.log.info(f"🔧 工作模式: {worker_class}")

def on_exit(server):
    """服务器退出时执行"""
    server.log.info("⏹️ 仓储管理系统已停止")

def worker_int(worker):
    """worker收到SIGINT信号时执行"""
    worker.log.info(f"Worker {worker.pid} 收到中断信号")

def pre_fork(server, worker):
    """fork worker前执行"""
    server.log.info(f"Worker {worker.age} 正在启动")

def post_fork(server, worker):
    """fork worker后执行"""
    server.log.info(f"Worker {worker.pid} 已启动")

def post_worker_init(worker):
    """worker初始化后执行"""
    worker.log.info(f"Worker {worker.pid} 初始化完成")

def worker_abort(worker):
    """worker异常退出时执行"""
    worker.log.error(f"Worker {worker.pid} 异常退出")

# 开发环境配置（仅在开发时使用）
if os.environ.get('FLASK_ENV') == 'development':
    reload = True
    reload_extra_files = [
        'config.py',
        'config_production.py',
        '.env',
        '.env.production'
    ]
else:
    reload = False
