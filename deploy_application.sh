#!/bin/bash
# 仓储管理系统应用部署脚本
# 第二阶段：部署Flask应用

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置变量
APP_DIR="/opt/warehouse"
APP_USER="warehouse"
VENV_DIR="$APP_DIR/venv"
SERVICE_NAME="warehouse"

echo -e "${GREEN}🚀 开始部署仓储管理系统应用...${NC}"

# 1. 检查权限
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ 请使用sudo运行此脚本${NC}"
    exit 1
fi

# 2. 检查应用代码是否存在
if [ ! -f "$APP_DIR/app.py" ]; then
    echo -e "${RED}❌ 应用代码不存在，请先上传代码到 $APP_DIR${NC}"
    exit 1
fi

cd $APP_DIR

# 3. 创建Python虚拟环境
echo -e "${YELLOW}🐍 创建Python虚拟环境...${NC}"
sudo -u $APP_USER python3.10 -m venv $VENV_DIR
sudo -u $APP_USER $VENV_DIR/bin/pip install --upgrade pip setuptools wheel

# 4. 安装Python依赖
echo -e "${YELLOW}📚 安装Python依赖...${NC}"
sudo -u $APP_USER $VENV_DIR/bin/pip install -r requirements.txt
sudo -u $APP_USER $VENV_DIR/bin/pip install gunicorn gevent eventlet

# 5. 创建Gunicorn配置文件
echo -e "${YELLOW}⚙️ 创建Gunicorn配置...${NC}"
cat > $APP_DIR/gunicorn_config.py << 'EOF'
# Gunicorn配置文件 - 针对4核8G服务器优化
import multiprocessing
import os

# 服务器配置
bind = "127.0.0.1:5000"
backlog = 2048

# 工作进程配置 - 针对4核CPU优化
workers = 4  # CPU核心数
worker_class = "gevent"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
preload_app = True

# 超时配置
timeout = 30
keepalive = 2
graceful_timeout = 30

# 日志配置
accesslog = "/var/log/warehouse/gunicorn_access.log"
errorlog = "/var/log/warehouse/gunicorn_error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# 进程命名
proc_name = "warehouse_app"

# 用户和组
user = "warehouse"
group = "warehouse"

# 临时目录
tmp_upload_dir = "/tmp"

# 环境变量
raw_env = [
    'FLASK_ENV=production',
]

# 性能优化
enable_stdio_inheritance = True
reuse_port = True

# 安全配置
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190
EOF

chown $APP_USER:$APP_USER $APP_DIR/gunicorn_config.py

# 6. 初始化数据库
echo -e "${YELLOW}🗄️ 初始化数据库...${NC}"
sudo -u $APP_USER bash -c "
cd $APP_DIR
source $VENV_DIR/bin/activate
export FLASK_ENV=production
python -c \"
from app import create_app, db
from config_production import ProductionConfig
app = create_app(ProductionConfig)
with app.app_context():
    db.create_all()
    print('✅ 数据库表创建完成')
\"
"

# 7. 创建初始管理员用户
echo -e "${YELLOW}👑 创建初始管理员用户...${NC}"
sudo -u $APP_USER bash -c "
cd $APP_DIR
source $VENV_DIR/bin/activate
export FLASK_ENV=production
python -c \"
from app import create_app, db
from app.models import User, Warehouse
from config_production import ProductionConfig
app = create_app(ProductionConfig)
with app.app_context():
    # 创建仓库
    warehouses = [
        {'warehouse_code': 'PH', 'warehouse_name': '平湖仓', 'warehouse_type': 'frontend'},
        {'warehouse_code': 'KS', 'warehouse_name': '昆山仓', 'warehouse_type': 'frontend'},
        {'warehouse_code': 'CD', 'warehouse_name': '成都仓', 'warehouse_type': 'frontend'},
        {'warehouse_code': 'PX', 'warehouse_name': '凭祥北投仓', 'warehouse_type': 'backend'}
    ]
    
    for wh_data in warehouses:
        if not Warehouse.query.filter_by(warehouse_code=wh_data['warehouse_code']).first():
            warehouse = Warehouse(**wh_data)
            db.session.add(warehouse)
    
    # 创建管理员用户
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            real_name='系统管理员',
            email='admin@warehouse.com',
            user_type='admin',
            is_admin=True,
            status='active'
        )
        admin.set_password('admin123')
        db.session.add(admin)
    
    db.session.commit()
    print('✅ 初始数据创建完成')
\"
"

# 8. 创建Supervisor配置
echo -e "${YELLOW}👮 配置Supervisor...${NC}"
cat > /etc/supervisor/conf.d/warehouse.conf << EOF
[program:warehouse]
command=$VENV_DIR/bin/gunicorn -c $APP_DIR/gunicorn_config.py app:app
directory=$APP_DIR
user=$APP_USER
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/warehouse/supervisor.log
stdout_logfile_maxbytes=100MB
stdout_logfile_backups=5
environment=FLASK_ENV=production,PYTHONPATH="$APP_DIR"
priority=999
startsecs=10
startretries=3
stopwaitsecs=10
EOF

# 9. 创建Nginx配置
echo -e "${YELLOW}🌐 配置Nginx...${NC}"
cat > /etc/nginx/sites-available/warehouse << 'EOF'
# 仓储管理系统Nginx配置
# 针对4核8G服务器和15用户并发优化

upstream warehouse_app {
    server 127.0.0.1:5000 fail_timeout=0;
}

server {
    listen 80;
    server_name _;  # 接受所有IP访问
    
    # 安全头
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # 隐藏Nginx版本
    server_tokens off;
    
    # 客户端配置
    client_max_body_size 16M;
    client_body_timeout 60s;
    client_header_timeout 60s;
    
    # 静态文件缓存
    location /static {
        alias /opt/warehouse/app/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
        add_header Vary Accept-Encoding;
        
        # 启用gzip压缩
        gzip on;
        gzip_vary on;
        gzip_min_length 1024;
        gzip_types text/css application/javascript application/json image/svg+xml;
    }
    
    # 健康检查
    location /health {
        proxy_pass http://warehouse_app/health;
        access_log off;
        proxy_connect_timeout 5s;
        proxy_send_timeout 5s;
        proxy_read_timeout 5s;
    }
    
    # 主应用代理
    location / {
        proxy_pass http://warehouse_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时配置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # 缓冲配置
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
        proxy_busy_buffers_size 8k;
        
        # 重试配置
        proxy_next_upstream error timeout invalid_header http_500 http_502 http_503;
        proxy_next_upstream_tries 2;
        proxy_next_upstream_timeout 3s;
    }
    
    # 日志配置
    access_log /var/log/nginx/warehouse_access.log;
    error_log /var/log/nginx/warehouse_error.log warn;
}
EOF

# 启用站点
ln -sf /etc/nginx/sites-available/warehouse /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# 10. 优化Nginx全局配置
echo -e "${YELLOW}⚡ 优化Nginx配置...${NC}"
cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.backup

cat > /etc/nginx/nginx.conf << 'EOF'
user www-data;
worker_processes 4;  # 匹配CPU核心数
pid /run/nginx.pid;

events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    # 基础配置
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    # 日志格式
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                   '$status $body_bytes_sent "$http_referer" '
                   '"$http_user_agent" "$http_x_forwarded_for" '
                   'rt=$request_time uct="$upstream_connect_time" '
                   'uht="$upstream_header_time" urt="$upstream_response_time"';
    
    # Gzip压缩
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;
    
    # 包含站点配置
    include /etc/nginx/conf.d/*.conf;
    include /etc/nginx/sites-enabled/*;
}
EOF

# 11. 设置文件权限
echo -e "${YELLOW}🔐 设置文件权限...${NC}"
chown -R $APP_USER:$APP_USER $APP_DIR
chmod -R 755 $APP_DIR
chmod 600 $APP_DIR/.env.production
chmod +x $APP_DIR/*.py

# 12. 启动所有服务
echo -e "${YELLOW}🎯 启动服务...${NC}"
systemctl daemon-reload
supervisorctl reread
supervisorctl update
supervisorctl start warehouse

nginx -t && systemctl restart nginx

echo -e "${GREEN}✅ 应用部署完成！${NC}"
echo -e "${BLUE}📋 服务状态检查:${NC}"

# 检查服务状态
sleep 5

if supervisorctl status warehouse | grep -q "RUNNING"; then
    echo -e "${GREEN}   ✅ 应用服务运行正常${NC}"
else
    echo -e "${RED}   ❌ 应用服务启动失败${NC}"
    supervisorctl status warehouse
fi

if systemctl is-active --quiet nginx; then
    echo -e "${GREEN}   ✅ Nginx运行正常${NC}"
else
    echo -e "${RED}   ❌ Nginx启动失败${NC}"
fi

echo -e "${BLUE}📍 访问信息:${NC}"
echo -e "   🌐 访问地址: http://$(curl -s ifconfig.me)"
echo -e "   👤 管理员账号: admin / admin123"

echo -e "${BLUE}📊 监控命令:${NC}"
echo -e "   supervisorctl status warehouse"
echo -e "   tail -f /var/log/warehouse/gunicorn_error.log"
echo -e "   tail -f /var/log/nginx/warehouse_error.log"

echo -e "${GREEN}🎉 部署完成！系统已就绪！${NC}"
