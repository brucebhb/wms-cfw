#!/bin/bash
# 基于Git仓库的仓储管理系统部署脚本
# 支持GitHub、GitLab、Gitee等Git平台

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

# Git仓库配置（需要用户提供）
GIT_REPO_URL=""
GIT_BRANCH="main"
GIT_USERNAME=""
GIT_TOKEN=""

echo -e "${GREEN}🚀 基于Git仓库的仓储管理系统部署${NC}"
echo -e "${BLUE}📋 支持GitHub、GitLab、Gitee等平台${NC}"
echo ""

# 检查权限
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ 请使用sudo运行此脚本${NC}"
    exit 1
fi

# 获取Git仓库信息
if [ -z "$GIT_REPO_URL" ]; then
    echo -e "${YELLOW}📝 请输入Git仓库信息:${NC}"
    read -p "Git仓库URL (https://github.com/username/repo.git): " GIT_REPO_URL
    read -p "分支名称 (默认: main): " input_branch
    GIT_BRANCH=${input_branch:-main}
    
    echo -e "${BLUE}💡 如果是私有仓库，请提供访问凭据:${NC}"
    read -p "Git用户名 (可选): " GIT_USERNAME
    read -s -p "Git访问令牌/密码 (可选): " GIT_TOKEN
    echo ""
fi

# 验证Git仓库URL
if [ -z "$GIT_REPO_URL" ]; then
    echo -e "${RED}❌ Git仓库URL不能为空${NC}"
    exit 1
fi

echo -e "${BLUE}📍 部署配置:${NC}"
echo -e "   仓库: $GIT_REPO_URL"
echo -e "   分支: $GIT_BRANCH"
echo -e "   目标目录: $APP_DIR"
echo ""

# 第一阶段：环境准备
echo -e "${YELLOW}📦 第一阶段：安装基础环境...${NC}"

# 更新系统
apt update && apt upgrade -y

# 安装Git
apt install -y git

# 安装基础软件
apt install -y software-properties-common curl wget unzip bc

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

# 第三阶段：从Git克隆代码
echo -e "${YELLOW}📱 第三阶段：从Git仓库获取代码...${NC}"

# 创建应用用户和目录
if ! id "$APP_USER" &>/dev/null; then
    useradd -m -s /bin/bash $APP_USER
fi

mkdir -p /opt
mkdir -p /var/log/warehouse
mkdir -p /var/backups/warehouse
chown $APP_USER:$APP_USER /var/log/warehouse
chown $APP_USER:$APP_USER /var/backups/warehouse

# 删除现有目录（如果存在）
if [ -d "$APP_DIR" ]; then
    echo -e "${YELLOW}⚠️  删除现有应用目录...${NC}"
    rm -rf $APP_DIR
fi

# 克隆Git仓库
echo -e "${BLUE}📥 克隆Git仓库...${NC}"
cd /opt

if [ -n "$GIT_USERNAME" ] && [ -n "$GIT_TOKEN" ]; then
    # 使用认证信息克隆私有仓库
    GIT_URL_WITH_AUTH=$(echo $GIT_REPO_URL | sed "s|https://|https://${GIT_USERNAME}:${GIT_TOKEN}@|")
    sudo -u $APP_USER git clone -b $GIT_BRANCH $GIT_URL_WITH_AUTH warehouse
else
    # 克隆公共仓库
    sudo -u $APP_USER git clone -b $GIT_BRANCH $GIT_REPO_URL warehouse
fi

# 设置目录权限
chown -R $APP_USER:$APP_USER $APP_DIR

cd $APP_DIR

# 配置Git（用于后续更新）
sudo -u $APP_USER git config pull.rebase false

echo -e "${GREEN}✅ 代码获取完成${NC}"

# 第四阶段：应用部署
echo -e "${YELLOW}⚙️ 第四阶段：部署应用...${NC}"

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

# 第五阶段：服务配置
echo -e "${YELLOW}⚙️ 第五阶段：配置服务...${NC}"

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

# 第六阶段：启动服务
echo -e "${YELLOW}🎯 第六阶段：启动服务...${NC}"

systemctl daemon-reload
supervisorctl reread
supervisorctl update
supervisorctl start warehouse

nginx -t && systemctl restart nginx
systemctl enable nginx supervisor

echo -e "${GREEN}✅ 服务启动完成${NC}"

# 创建更新脚本
echo -e "${YELLOW}🔄 创建更新脚本...${NC}"
cat > /usr/local/bin/warehouse_update.sh << 'EOF'
#!/bin/bash
# 仓储管理系统更新脚本

APP_DIR="/opt/warehouse"
APP_USER="warehouse"

echo "🔄 开始更新仓储管理系统..."

cd $APP_DIR

# 备份当前版本
echo "📦 备份当前版本..."
sudo -u $APP_USER git stash
sudo -u $APP_USER git stash drop || true

# 拉取最新代码
echo "📥 拉取最新代码..."
sudo -u $APP_USER git pull origin main

# 更新依赖
echo "📚 更新依赖..."
sudo -u $APP_USER venv/bin/pip install -r requirements.txt

# 数据库迁移（如果有）
echo "🗄️ 数据库迁移..."
sudo -u $APP_USER bash -c "
cd $APP_DIR
source venv/bin/activate
export FLASK_ENV=production
python -c \"
from app import create_app, db
from config_production import ProductionConfig
app = create_app(ProductionConfig)
with app.app_context():
    db.create_all()
    print('✅ 数据库更新完成')
\"
"

# 重启服务
echo "🔄 重启服务..."
supervisorctl restart warehouse

echo "✅ 更新完成！"
EOF

chmod +x /usr/local/bin/warehouse_update.sh

# 验证部署
echo -e "${YELLOW}✅ 第七阶段：验证部署...${NC}"

sleep 10

# 获取服务器IP
SERVER_IP=$(curl -s ifconfig.me || hostname -I | awk '{print $1}')

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
echo -e "${GREEN}🎉 Git部署完成！${NC}"
echo -e "${BLUE}📍 访问信息:${NC}"
echo -e "   🌐 访问地址: http://$SERVER_IP"
echo -e "   👤 管理员账号: admin"
echo -e "   🔑 管理员密码: admin123"

echo -e "${BLUE}📊 Git管理命令:${NC}"
echo -e "   warehouse_update.sh           # 更新系统"
echo -e "   cd $APP_DIR && git status     # 查看Git状态"
echo -e "   cd $APP_DIR && git log --oneline -10  # 查看提交历史"

echo -e "${BLUE}📊 系统管理命令:${NC}"
echo -e "   supervisorctl status warehouse  # 查看应用状态"
echo -e "   systemctl status nginx         # 查看Nginx状态"

echo -e "${GREEN}✨ 基于Git的仓储管理系统部署完成！${NC}"
