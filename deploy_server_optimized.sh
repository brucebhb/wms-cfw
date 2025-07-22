#!/bin/bash
# 仓储管理系统腾讯云服务器优化部署脚本
# 适用于: Ubuntu 22.04 LTS, 4核8G, 15用户并发, 200条/日记录

set -e  # 遇到错误立即退出

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置变量
APP_DIR="/opt/warehouse"
APP_USER="warehouse"
VENV_DIR="$APP_DIR/venv"
SERVICE_NAME="warehouse"
MYSQL_ROOT_PASSWORD="warehouse_root_2024"
MYSQL_USER="warehouse_user"
MYSQL_PASSWORD="warehouse_secure_2024"
MYSQL_DATABASE="warehouse_production"

echo -e "${GREEN}🚀 开始部署仓储管理系统到腾讯云服务器...${NC}"
echo -e "${BLUE}📋 服务器配置: Ubuntu 22.04 LTS, 4核8G, 12Mbps${NC}"
echo -e "${BLUE}👥 预期负载: 15用户并发, 200条/日记录${NC}"

# 1. 检查用户权限
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ 请使用sudo运行此脚本${NC}"
    exit 1
fi

# 2. 系统更新和基础软件安装
echo -e "${YELLOW}📦 更新系统并安装基础软件...${NC}"
apt update && apt upgrade -y
apt install -y software-properties-common curl wget git unzip

# 3. 安装Python 3.10和开发工具
echo -e "${YELLOW}🐍 安装Python 3.10和开发工具...${NC}"
apt install -y python3.10 python3.10-venv python3.10-dev python3-pip \
    build-essential libssl-dev libffi-dev libxml2-dev libxslt1-dev \
    libjpeg-dev libpng-dev zlib1g-dev pkg-config

# 4. 安装MySQL 8.0
echo -e "${YELLOW}🗄️ 安装MySQL 8.0...${NC}"
apt install -y mysql-server mysql-client libmysqlclient-dev

# 启动MySQL服务
systemctl start mysql
systemctl enable mysql

# 配置MySQL安全设置
mysql -e "ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '${MYSQL_ROOT_PASSWORD}';"
mysql -u root -p${MYSQL_ROOT_PASSWORD} -e "DELETE FROM mysql.user WHERE User='';"
mysql -u root -p${MYSQL_ROOT_PASSWORD} -e "DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');"
mysql -u root -p${MYSQL_ROOT_PASSWORD} -e "DROP DATABASE IF EXISTS test;"
mysql -u root -p${MYSQL_ROOT_PASSWORD} -e "DELETE FROM mysql.db WHERE Db='test' OR Db='test\\_%';"
mysql -u root -p${MYSQL_ROOT_PASSWORD} -e "FLUSH PRIVILEGES;"

# 创建应用数据库和用户
echo -e "${YELLOW}🔧 创建应用数据库和用户...${NC}"
mysql -u root -p${MYSQL_ROOT_PASSWORD} -e "
CREATE DATABASE IF NOT EXISTS ${MYSQL_DATABASE} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '${MYSQL_USER}'@'localhost' IDENTIFIED BY '${MYSQL_PASSWORD}';
GRANT ALL PRIVILEGES ON ${MYSQL_DATABASE}.* TO '${MYSQL_USER}'@'localhost';
FLUSH PRIVILEGES;
"

# 5. 安装Redis
echo -e "${YELLOW}🔴 安装Redis...${NC}"
apt install -y redis-server

# 配置Redis
sed -i 's/^# maxmemory <bytes>/maxmemory 1gb/' /etc/redis/redis.conf
sed -i 's/^# maxmemory-policy noeviction/maxmemory-policy allkeys-lru/' /etc/redis/redis.conf
systemctl restart redis-server
systemctl enable redis-server

# 6. 安装Nginx
echo -e "${YELLOW}🌐 安装Nginx...${NC}"
apt install -y nginx

# 7. 安装Supervisor
echo -e "${YELLOW}👮 安装Supervisor...${NC}"
apt install -y supervisor

# 8. 创建应用用户和目录
echo -e "${YELLOW}👤 创建应用用户和目录...${NC}"
if ! id "$APP_USER" &>/dev/null; then
    useradd -m -s /bin/bash $APP_USER
    echo -e "${GREEN}✅ 创建用户: $APP_USER${NC}"
fi

mkdir -p $APP_DIR
mkdir -p /var/log/warehouse
mkdir -p /var/backups/warehouse
chown $APP_USER:$APP_USER $APP_DIR
chown $APP_USER:$APP_USER /var/log/warehouse
chown $APP_USER:$APP_USER /var/backups/warehouse

# 9. 配置防火墙
echo -e "${YELLOW}🔥 配置防火墙...${NC}"
ufw --force enable
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow from 127.0.0.1 to any port 3306  # MySQL本地访问
ufw allow from 127.0.0.1 to any port 6379  # Redis本地访问
ufw allow from 127.0.0.1 to any port 5000  # Flask本地访问

# 10. 优化系统参数
echo -e "${YELLOW}⚡ 优化系统参数...${NC}"

# 优化内核参数
cat >> /etc/sysctl.conf << EOF
# 网络优化
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216
net.core.netdev_max_backlog = 5000
net.ipv4.tcp_congestion_control = bbr

# 文件描述符限制
fs.file-max = 65536

# 虚拟内存优化
vm.swappiness = 10
vm.dirty_ratio = 15
vm.dirty_background_ratio = 5
EOF

# 应用系统参数
sysctl -p

# 设置用户限制
cat >> /etc/security/limits.conf << EOF
$APP_USER soft nofile 65536
$APP_USER hard nofile 65536
$APP_USER soft nproc 32768
$APP_USER hard nproc 32768
EOF

# 11. 创建环境变量模板
echo -e "${YELLOW}⚙️ 创建环境变量模板...${NC}"
cat > $APP_DIR/.env.production << EOF
# 生产环境配置
FLASK_ENV=production
SECRET_KEY=$(openssl rand -hex 32)

# 数据库配置
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=${MYSQL_USER}
MYSQL_PASSWORD=${MYSQL_PASSWORD}
MYSQL_DATABASE=${MYSQL_DATABASE}
DATABASE_URL=mysql+pymysql://${MYSQL_USER}:${MYSQL_PASSWORD}@localhost:3306/${MYSQL_DATABASE}?charset=utf8mb4

# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_URL=redis://localhost:6379/0

# 日志配置
LOG_LEVEL=INFO
LOG_FILE_MAX_SIZE=104857600
LOG_FILE_BACKUP_COUNT=5

# 邮件配置（可选）
MAIL_SERVER=
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_DEFAULT_SENDER=
EOF

chown $APP_USER:$APP_USER $APP_DIR/.env.production
chmod 600 $APP_DIR/.env.production

echo -e "${GREEN}✅ 服务器环境配置完成！${NC}"
echo -e "${BLUE}📋 已安装组件:${NC}"
echo -e "   ✅ Python 3.10"
echo -e "   ✅ MySQL 8.0 (数据库: ${MYSQL_DATABASE})"
echo -e "   ✅ Redis (内存限制: 1GB)"
echo -e "   ✅ Nginx"
echo -e "   ✅ Supervisor"
echo -e "   ✅ 防火墙配置"
echo -e "   ✅ 系统优化"

echo -e "${YELLOW}📝 下一步操作:${NC}"
echo -e "   1. 上传应用代码到 ${APP_DIR}"
echo -e "   2. 运行应用部署脚本"
echo -e "   3. 配置SSL证书（可选）"
echo -e "   4. 设置监控和备份"

echo -e "${GREEN}🎉 环境配置完成！准备部署应用...${NC}"
