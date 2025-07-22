#!/bin/bash
# 仓储管理系统生产环境部署脚本

set -e  # 遇到错误立即退出

echo "🚀 开始部署仓储管理系统到生产环境..."

# 配置变量
APP_DIR="/opt/warehouse"
APP_USER="warehouse"
VENV_DIR="$APP_DIR/venv"
SERVICE_NAME="warehouse"

# 1. 检查用户权限
if [ "$EUID" -ne 0 ]; then
    echo "❌ 请使用sudo运行此脚本"
    exit 1
fi

# 2. 安装Python和依赖
echo "📦 安装Python和系统依赖..."
apt update
apt install -y python3 python3-pip python3-venv python3-dev build-essential \
    libmysqlclient-dev pkg-config supervisor nginx redis-server mysql-server

# 3. 创建应用目录和用户
echo "👤 设置应用环境..."
if ! id "$APP_USER" &>/dev/null; then
    useradd -m -s /bin/bash $APP_USER
fi

mkdir -p $APP_DIR
chown $APP_USER:$APP_USER $APP_DIR

# 4. 复制应用代码
echo "📁 复制应用代码..."
sudo -u $APP_USER cp -r . $APP_DIR/
cd $APP_DIR

# 5. 创建Python虚拟环境
echo "🐍 创建Python虚拟环境..."
sudo -u $APP_USER python3 -m venv $VENV_DIR
sudo -u $APP_USER $VENV_DIR/bin/pip install --upgrade pip

# 6. 安装Python依赖
echo "📚 安装Python依赖..."
sudo -u $APP_USER $VENV_DIR/bin/pip install -r requirements.txt
sudo -u $APP_USER $VENV_DIR/bin/pip install gunicorn gevent

# 7. 配置环境变量
echo "⚙️ 配置环境变量..."
if [ ! -f "$APP_DIR/.env.production" ]; then
    echo "⚠️  请配置 .env.production 文件"
    sudo -u $APP_USER cp .env.production.template .env.production
    echo "📝 请编辑 $APP_DIR/.env.production 文件并填入正确的配置"
    read -p "配置完成后按回车继续..."
fi

# 8. 初始化数据库
echo "🗄️ 初始化数据库..."
sudo -u $APP_USER $VENV_DIR/bin/python -c "
import os
os.environ['FLASK_ENV'] = 'production'
from app import create_app, db
app = create_app()
with app.app_context():
    db.create_all()
    print('数据库表创建完成')
"

# 9. 创建Supervisor配置
echo "👮 配置Supervisor..."
tee /etc/supervisor/conf.d/warehouse.conf > /dev/null <<EOF
[program:warehouse]
command=$VENV_DIR/bin/gunicorn -c $APP_DIR/gunicorn_config.py app:app
directory=$APP_DIR
user=$APP_USER
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/warehouse/gunicorn.log
stdout_logfile_maxbytes=100MB
stdout_logfile_backups=5
environment=FLASK_ENV=production
EOF

# 10. 创建Nginx配置
echo "🌐 配置Nginx..."
tee /etc/nginx/sites-available/warehouse > /dev/null <<EOF
server {
    listen 80;
    server_name _;  # 接受所有域名/IP
    
    # 安全头
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    # 静态文件
    location /static {
        alias $APP_DIR/app/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # 应用代理
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        proxy_buffering off;
    }
    
    # 健康检查
    location /health {
        proxy_pass http://127.0.0.1:5000/health;
        access_log off;
    }
    
    # 限制请求大小
    client_max_body_size 16M;
    
    # 日志
    access_log /var/log/nginx/warehouse_access.log;
    error_log /var/log/nginx/warehouse_error.log;
}
EOF

# 启用站点
ln -sf /etc/nginx/sites-available/warehouse /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# 11. 创建日志目录
echo "📝 创建日志目录..."
mkdir -p /var/log/warehouse
chown $APP_USER:$APP_USER /var/log/warehouse

# 12. 设置权限
echo "🔐 设置文件权限..."
chown -R $APP_USER:$APP_USER $APP_DIR
chmod -R 755 $APP_DIR
chmod 600 $APP_DIR/.env.production

# 13. 启动服务
echo "🎯 启动服务..."
systemctl enable supervisor
systemctl start supervisor
supervisorctl reread
supervisorctl update
supervisorctl start warehouse

systemctl enable nginx
systemctl restart nginx

systemctl enable redis-server
systemctl start redis-server

systemctl enable mysql
systemctl start mysql

# 14. 验证部署
echo "✅ 验证部署..."
sleep 5

if supervisorctl status warehouse | grep -q "RUNNING"; then
    echo "✅ 应用服务运行正常"
else
    echo "❌ 应用服务启动失败"
    supervisorctl status warehouse
fi

if systemctl is-active --quiet nginx; then
    echo "✅ Nginx运行正常"
else
    echo "❌ Nginx启动失败"
fi

if systemctl is-active --quiet redis-server; then
    echo "✅ Redis运行正常"
else
    echo "❌ Redis启动失败"
fi

if systemctl is-active --quiet mysql; then
    echo "✅ MySQL运行正常"
else
    echo "❌ MySQL启动失败"
fi

echo ""
echo "🎉 部署完成！"
echo "📍 访问地址: http://your_server_ip"
echo "📊 监控命令:"
echo "   supervisorctl status warehouse  # 查看应用状态"
echo "   tail -f /var/log/warehouse/gunicorn.log  # 查看应用日志"
echo "   tail -f /var/log/nginx/warehouse_error.log  # 查看Nginx错误日志"
echo ""
echo "⚠️  下一步:"
echo "   1. 配置 .env.production 文件"
echo "   2. 创建管理员用户"
echo "   3. 配置防火墙规则"
echo "   4. 设置定期备份"
