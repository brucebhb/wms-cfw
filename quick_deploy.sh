#!/bin/bash
# 仓储管理系统一键部署脚本
# 适用于腾讯云Ubuntu 22.04服务器

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
MYSQL_ROOT_PASSWORD="warehouse_root_2024"
MYSQL_USER="warehouse_user"
MYSQL_PASSWORD="warehouse_secure_2024"
MYSQL_DATABASE="warehouse_production"

echo -e "${GREEN}🚀 仓储管理系统一键部署开始${NC}"
echo -e "${BLUE}📋 目标配置: 4核8G Ubuntu 22.04, 15用户并发${NC}"
echo ""

# 检查权限
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ 请使用sudo运行此脚本${NC}"
    exit 1
fi

# 获取服务器IP
SERVER_IP=$(curl -s ifconfig.me || hostname -I | awk '{print $1}')
echo -e "${BLUE}🌐 服务器IP: $SERVER_IP${NC}"

# 第一阶段：环境准备
echo -e "${YELLOW}📦 第一阶段：安装基础环境...${NC}"

# 更新系统
apt update && apt upgrade -y

# 安装基础软件
apt install -y software-properties-common curl wget git unzip bc

# 安装Python和开发工具
apt install -y python3.10 python3.10-venv python3.10-dev python3-pip \
    build-essential libssl-dev libffi-dev libxml2-dev libxslt1-dev \
    libjpeg-dev libpng-dev zlib1g-dev pkg-config

# 安装MySQL
apt install -y mysql-server mysql-client libmysqlclient-dev

# 安装Redis
apt install -y redis-server

# 安装Nginx和Supervisor
apt install -y nginx supervisor

# 安装测试工具
apt install -y apache2-utils htop iotop nethogs

echo -e "${GREEN}✅ 基础环境安装完成${NC}"

# 第二阶段：服务配置
echo -e "${YELLOW}🔧 第二阶段：配置服务...${NC}"

# 配置MySQL
systemctl start mysql
systemctl enable mysql

# MySQL安全配置
mysql -e "ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '${MYSQL_ROOT_PASSWORD}';"
mysql -u root -p${MYSQL_ROOT_PASSWORD} -e "DELETE FROM mysql.user WHERE User='';"
mysql -u root -p${MYSQL_ROOT_PASSWORD} -e "DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');"
mysql -u root -p${MYSQL_ROOT_PASSWORD} -e "DROP DATABASE IF EXISTS test;"
mysql -u root -p${MYSQL_ROOT_PASSWORD} -e "FLUSH PRIVILEGES;"

# 创建应用数据库
mysql -u root -p${MYSQL_ROOT_PASSWORD} -e "
CREATE DATABASE IF NOT EXISTS ${MYSQL_DATABASE} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '${MYSQL_USER}'@'localhost' IDENTIFIED BY '${MYSQL_PASSWORD}';
GRANT ALL PRIVILEGES ON ${MYSQL_DATABASE}.* TO '${MYSQL_USER}'@'localhost';
FLUSH PRIVILEGES;
"

# 配置Redis
sed -i 's/^# maxmemory <bytes>/maxmemory 1gb/' /etc/redis/redis.conf
sed -i 's/^# maxmemory-policy noeviction/maxmemory-policy allkeys-lru/' /etc/redis/redis.conf
systemctl restart redis-server
systemctl enable redis-server

# 配置防火墙
ufw --force enable
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp

echo -e "${GREEN}✅ 服务配置完成${NC}"

# 第三阶段：应用部署
echo -e "${YELLOW}📱 第三阶段：部署应用...${NC}"

# 创建应用用户和目录
if ! id "$APP_USER" &>/dev/null; then
    useradd -m -s /bin/bash $APP_USER
fi

mkdir -p $APP_DIR
mkdir -p /var/log/warehouse
mkdir -p /var/backups/warehouse
chown $APP_USER:$APP_USER $APP_DIR
chown $APP_USER:$APP_USER /var/log/warehouse
chown $APP_USER:$APP_USER /var/backups/warehouse

# 检查应用代码
if [ ! -f "$APP_DIR/app.py" ]; then
    echo -e "${YELLOW}⚠️  应用代码不存在，请先上传代码到 $APP_DIR${NC}"
    echo -e "${BLUE}💡 可以使用以下命令上传:${NC}"
    echo -e "   scp -r . root@$SERVER_IP:$APP_DIR/"
    echo -e "   然后重新运行此脚本"
    exit 1
fi

cd $APP_DIR

# 创建Python虚拟环境
sudo -u $APP_USER python3.10 -m venv venv
sudo -u $APP_USER venv/bin/pip install --upgrade pip setuptools wheel

# 安装依赖
sudo -u $APP_USER venv/bin/pip install -r requirements.txt
sudo -u $APP_USER venv/bin/pip install gunicorn gevent eventlet

# 创建环境变量文件
cat > $APP_DIR/.env.production << EOF
FLASK_ENV=production
SECRET_KEY=$(openssl rand -hex 32)
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=${MYSQL_USER}
MYSQL_PASSWORD=${MYSQL_PASSWORD}
MYSQL_DATABASE=${MYSQL_DATABASE}
DATABASE_URL=mysql+pymysql://${MYSQL_USER}:${MYSQL_PASSWORD}@localhost:3306/${MYSQL_DATABASE}?charset=utf8mb4
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_URL=redis://localhost:6379/0
LOG_LEVEL=INFO
EOF

chown $APP_USER:$APP_USER $APP_DIR/.env.production
chmod 600 $APP_DIR/.env.production

# 初始化数据库
sudo -u $APP_USER bash -c "
cd $APP_DIR
source venv/bin/activate
export FLASK_ENV=production
python -c \"
from app import create_app, db
from app.models import User, Warehouse
from config_production import ProductionConfig
app = create_app(ProductionConfig)
with app.app_context():
    db.create_all()
    
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
    
    # 创建管理员
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
    print('✅ 数据库初始化完成')
\"
"

echo -e "${GREEN}✅ 应用部署完成${NC}"

# 第四阶段：服务配置
echo -e "${YELLOW}⚙️ 第四阶段：配置服务...${NC}"

# 创建Gunicorn配置
cat > $APP_DIR/gunicorn_config.py << 'EOF'
import multiprocessing
bind = "127.0.0.1:5000"
workers = 4
worker_class = "gevent"
worker_connections = 1000
max_requests = 1000
timeout = 30
keepalive = 2
preload_app = True
accesslog = "/var/log/warehouse/gunicorn_access.log"
errorlog = "/var/log/warehouse/gunicorn_error.log"
loglevel = "info"
user = "warehouse"
group = "warehouse"
EOF

# 创建Supervisor配置
cat > /etc/supervisor/conf.d/warehouse.conf << EOF
[program:warehouse]
command=$APP_DIR/venv/bin/gunicorn -c $APP_DIR/gunicorn_config.py app:app
directory=$APP_DIR
user=$APP_USER
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/warehouse/supervisor.log
environment=FLASK_ENV=production
EOF

# 创建Nginx配置
cat > /etc/nginx/sites-available/warehouse << 'EOF'
upstream warehouse_app {
    server 127.0.0.1:5000 fail_timeout=0;
}

server {
    listen 80;
    server_name _;
    
    client_max_body_size 16M;
    
    location /static {
        alias /opt/warehouse/app/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    location /health {
        proxy_pass http://warehouse_app/health;
        access_log off;
    }
    
    location / {
        proxy_pass http://warehouse_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
EOF

ln -sf /etc/nginx/sites-available/warehouse /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# 设置权限
chown -R $APP_USER:$APP_USER $APP_DIR
chmod +x $APP_DIR/*.py

echo -e "${GREEN}✅ 服务配置完成${NC}"

# 第五阶段：启动服务
echo -e "${YELLOW}🎯 第五阶段：启动服务...${NC}"

systemctl daemon-reload
supervisorctl reread
supervisorctl update
supervisorctl start warehouse

nginx -t && systemctl restart nginx
systemctl enable nginx supervisor

echo -e "${GREEN}✅ 服务启动完成${NC}"

# 第六阶段：验证部署
echo -e "${YELLOW}✅ 第六阶段：验证部署...${NC}"

sleep 10

# 检查服务状态
echo -e "${BLUE}📊 服务状态检查:${NC}"

if supervisorctl status warehouse | grep -q "RUNNING"; then
    echo -e "${GREEN}   ✅ 应用服务运行正常${NC}"
else
    echo -e "${RED}   ❌ 应用服务异常${NC}"
    supervisorctl status warehouse
fi

if systemctl is-active --quiet nginx; then
    echo -e "${GREEN}   ✅ Nginx运行正常${NC}"
else
    echo -e "${RED}   ❌ Nginx异常${NC}"
fi

if systemctl is-active --quiet mysql; then
    echo -e "${GREEN}   ✅ MySQL运行正常${NC}"
else
    echo -e "${RED}   ❌ MySQL异常${NC}"
fi

if systemctl is-active --quiet redis-server; then
    echo -e "${GREEN}   ✅ Redis运行正常${NC}"
else
    echo -e "${RED}   ❌ Redis异常${NC}"
fi

# 健康检查
echo -e "${BLUE}🏥 应用健康检查:${NC}"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/health || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}   ✅ 应用健康检查通过${NC}"
else
    echo -e "${RED}   ❌ 应用健康检查失败 (HTTP $HTTP_CODE)${NC}"
fi

# 部署完成
echo ""
echo -e "${GREEN}🎉 部署完成！${NC}"
echo -e "${BLUE}📍 访问信息:${NC}"
echo -e "   🌐 访问地址: http://$SERVER_IP"
echo -e "   👤 管理员账号: admin"
echo -e "   🔑 管理员密码: admin123"

echo -e "${BLUE}📊 管理命令:${NC}"
echo -e "   supervisorctl status warehouse  # 查看应用状态"
echo -e "   systemctl status nginx         # 查看Nginx状态"
echo -e "   tail -f /var/log/warehouse/gunicorn_error.log  # 查看应用日志"

echo -e "${YELLOW}📋 下一步建议:${NC}"
echo -e "   1. 访问系统并测试所有功能"
echo -e "   2. 运行性能测试: ./performance_test.sh"
echo -e "   3. 配置监控和备份: ./setup_monitoring.sh"
echo -e "   4. 修改默认密码"

echo -e "${GREEN}✨ 仓储管理系统已成功部署到生产环境！${NC}"
