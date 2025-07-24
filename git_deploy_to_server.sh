#!/bin/bash
# 仓储管理系统 - Git仓库部署脚本

# 设置颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 配置变量
PROJECT_NAME="warehouse"
PROJECT_DIR="/opt/warehouse"
SERVICE_USER="warehouse"
VENV_DIR="$PROJECT_DIR/venv"

# 数据库配置
DB_HOST="localhost"
DB_PORT="3306"
DB_NAME="warehouse_production"
DB_USER="warehouse_user"
DB_PASSWORD=""

echo ""
echo "========================================"
echo -e "${BLUE}🚀 Git仓库部署脚本${NC}"
echo "========================================"
echo ""

print_status() {
    local message=$1
    local status=${2:-"INFO"}
    
    case $status in
        "SUCCESS")
            echo -e "${GREEN}✅ $message${NC}"
            ;;
        "ERROR")
            echo -e "${RED}❌ $message${NC}"
            ;;
        "WARNING")
            echo -e "${YELLOW}⚠️  $message${NC}"
            ;;
        "INFO")
            echo -e "${BLUE}ℹ️  $message${NC}"
            ;;
        "DEPLOY")
            echo -e "${PURPLE}🚀 $message${NC}"
            ;;
        "GIT")
            echo -e "${CYAN}📦 $message${NC}"
            ;;
    esac
}

check_git_repo() {
    print_status "检查Git仓库状态..." "GIT"
    
    if [ ! -d ".git" ]; then
        print_status "当前目录不是Git仓库" "ERROR"
        exit 1
    fi
    
    # 检查是否有未提交的更改
    if ! git diff-index --quiet HEAD --; then
        print_status "检测到未提交的更改" "WARNING"
        git status --porcelain
    fi
    
    # 获取当前分支和提交信息
    current_branch=$(git branch --show-current)
    current_commit=$(git rev-parse --short HEAD)
    
    print_status "当前分支: $current_branch" "INFO"
    print_status "当前提交: $current_commit" "INFO"
    
    # 检查关键文件
    required_files=(
        "app.py"
        "requirements.txt"
        "config.py"
        "backup_essential_data.py"
        "restore_essential_data.py"
    )
    
    for file in "${required_files[@]}"; do
        if [ -f "$file" ]; then
            print_status "找到文件: $file" "SUCCESS"
        else
            print_status "缺少文件: $file" "ERROR"
            exit 1
        fi
    done
}

check_system() {
    print_status "检查系统环境..." "INFO"
    
    # 检查操作系统
    if [[ ! -f /etc/os-release ]]; then
        print_status "无法识别操作系统" "ERROR"
        exit 1
    fi
    
    . /etc/os-release
    print_status "操作系统: $PRETTY_NAME" "SUCCESS"
    
    # 检查是否为root用户
    if [[ $EUID -eq 0 ]]; then
        print_status "请不要使用root用户运行此脚本" "ERROR"
        exit 1
    fi
    
    # 检查sudo权限
    if ! sudo -n true 2>/dev/null; then
        print_status "需要sudo权限，请确保当前用户在sudo组中" "ERROR"
        exit 1
    fi
    
    print_status "系统环境检查通过" "SUCCESS"
}

install_system_dependencies() {
    print_status "安装系统依赖..." "DEPLOY"
    
    # 更新包列表
    sudo apt-get update -qq
    
    # 安装基础依赖
    sudo apt-get install -y \
        python3 \
        python3-pip \
        python3-venv \
        python3-dev \
        libmysqlclient-dev \
        mysql-client \
        redis-server \
        cups \
        cups-client \
        nginx \
        supervisor \
        git \
        curl \
        unzip \
        htop \
        net-tools
    
    print_status "系统依赖安装完成" "SUCCESS"
}

setup_project_user() {
    print_status "设置项目用户..." "DEPLOY"
    
    # 创建项目用户
    if ! id "$SERVICE_USER" &>/dev/null; then
        sudo useradd -m -s /bin/bash $SERVICE_USER
        print_status "创建用户: $SERVICE_USER" "SUCCESS"
    else
        print_status "用户已存在: $SERVICE_USER" "INFO"
    fi
    
    # 将当前用户添加到项目用户组
    sudo usermod -a -G $SERVICE_USER $USER
    
    # 确保项目目录权限正确
    if [ "$PWD" != "$PROJECT_DIR" ]; then
        print_status "当前不在项目目录，需要移动文件..." "WARNING"
        
        # 创建项目目录
        sudo mkdir -p $PROJECT_DIR
        
        # 复制文件到项目目录
        sudo cp -r . $PROJECT_DIR/
        
        # 设置权限
        sudo chown -R $SERVICE_USER:$SERVICE_USER $PROJECT_DIR
        
        print_status "文件已移动到: $PROJECT_DIR" "SUCCESS"
    else
        # 设置当前目录权限
        sudo chown -R $SERVICE_USER:$SERVICE_USER $PROJECT_DIR
        print_status "项目目录权限已设置" "SUCCESS"
    fi
}

setup_python_environment() {
    print_status "设置Python环境..." "DEPLOY"
    
    cd $PROJECT_DIR
    
    # 检查是否已有虚拟环境
    if [ -d "venv" ] || [ -d "Scripts" ]; then
        print_status "检测到现有虚拟环境，重新创建..." "WARNING"
        sudo -u $SERVICE_USER rm -rf venv Scripts Lib pyvenv.cfg
    fi
    
    # 创建新的虚拟环境
    sudo -u $SERVICE_USER python3 -m venv venv
    
    # 激活虚拟环境并安装依赖
    sudo -u $SERVICE_USER bash << 'EOF'
cd /opt/warehouse
source venv/bin/activate

# 升级pip
pip install --upgrade pip

# 安装依赖
pip install -r requirements.txt

# 设置执行权限
chmod +x *.sh *.py
EOF
    
    print_status "Python环境设置完成" "SUCCESS"
}

configure_database() {
    print_status "配置数据库..." "DEPLOY"
    
    # 检查MySQL是否运行
    if ! systemctl is-active --quiet mysql; then
        sudo systemctl start mysql
        sudo systemctl enable mysql
        print_status "MySQL服务已启动" "SUCCESS"
    fi
    
    # 提示用户输入数据库密码
    echo ""
    print_status "请输入数据库配置信息:" "INFO"
    read -p "数据库密码 (warehouse_user): " -s DB_PASSWORD
    echo ""
    
    if [ -z "$DB_PASSWORD" ]; then
        print_status "数据库密码不能为空" "ERROR"
        exit 1
    fi
    
    # 测试数据库连接
    if mysql -h $DB_HOST -P $DB_PORT -u $DB_USER -p$DB_PASSWORD -e "SELECT 1;" &>/dev/null; then
        print_status "数据库连接成功" "SUCCESS"
    else
        print_status "数据库连接失败，请检查配置" "ERROR"
        print_status "请确保已创建数据库和用户:" "INFO"
        echo "  CREATE DATABASE warehouse_production CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
        echo "  CREATE USER 'warehouse_user'@'localhost' IDENTIFIED BY 'password';"
        echo "  GRANT ALL PRIVILEGES ON warehouse_production.* TO 'warehouse_user'@'localhost';"
        exit 1
    fi
}

restore_data() {
    print_status "恢复数据..." "DEPLOY"
    
    cd $PROJECT_DIR
    
    # 查找备份文件
    backup_file=$(ls -t essential_data_backup_*.json 2>/dev/null | head -1)
    
    if [ -n "$backup_file" ]; then
        print_status "找到备份文件: $backup_file" "SUCCESS"
        
        # 恢复数据
        sudo -u $SERVICE_USER bash << EOF
cd $PROJECT_DIR
source venv/bin/activate

python3 restore_essential_data.py \\
    --host $DB_HOST \\
    --port $DB_PORT \\
    --user $DB_USER \\
    --password $DB_PASSWORD \\
    --database $DB_NAME \\
    --clear \\
    $backup_file
EOF
        
        if [ $? -eq 0 ]; then
            print_status "数据恢复成功" "SUCCESS"
        else
            print_status "数据恢复失败" "ERROR"
            exit 1
        fi
    else
        print_status "未找到备份文件，跳过数据恢复" "WARNING"
    fi
}

create_production_config() {
    print_status "创建生产环境配置..." "DEPLOY"
    
    cd $PROJECT_DIR
    
    # 创建生产环境配置文件
    sudo -u $SERVICE_USER tee config_production.py > /dev/null << EOF
import os
from config import Config

class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'mysql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME'
    REDIS_URL = 'redis://localhost:6379/0'
    SECRET_KEY = os.environ.get('SECRET_KEY') or '$(openssl rand -hex 32)'
    
    # 生产环境设置
    DEBUG = False
    TESTING = False
    
    # 日志配置
    LOG_LEVEL = 'INFO'
    LOG_FILE = '/var/log/warehouse/app.log'
    
    # 缓存配置
    CACHE_TYPE = 'redis'
    CACHE_REDIS_URL = 'redis://localhost:6379/1'
    
    # 会话配置
    SESSION_PERMANENT = False
    PERMANENT_SESSION_LIFETIME = 21600  # 6小时
    
    # 安全配置
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600
EOF
    
    print_status "生产环境配置创建完成" "SUCCESS"
}

create_systemd_service() {
    print_status "创建系统服务..." "DEPLOY"
    
    sudo tee /etc/systemd/system/$PROJECT_NAME.service > /dev/null << EOF
[Unit]
Description=仓储管理系统
After=network.target mysql.service redis.service

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$PROJECT_DIR
Environment=FLASK_ENV=production
Environment=PYTHONPATH=$PROJECT_DIR
ExecStart=$PROJECT_DIR/venv/bin/python app.py
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
    
    # 创建日志目录
    sudo mkdir -p /var/log/$PROJECT_NAME
    sudo chown $SERVICE_USER:$SERVICE_USER /var/log/$PROJECT_NAME
    
    # 重新加载systemd
    sudo systemctl daemon-reload
    sudo systemctl enable $PROJECT_NAME
    
    print_status "系统服务创建完成" "SUCCESS"
}

configure_nginx() {
    print_status "配置Nginx..." "DEPLOY"
    
    sudo tee /etc/nginx/sites-available/$PROJECT_NAME > /dev/null << 'EOF'
server {
    listen 80;
    server_name _;
    
    # 静态文件
    location /static/ {
        alias /opt/warehouse/app/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # 应用代理
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # 缓冲设置
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }
    
    # 健康检查
    location /health {
        proxy_pass http://127.0.0.1:5000/health;
        access_log off;
    }
}
EOF
    
    # 启用站点
    sudo ln -sf /etc/nginx/sites-available/$PROJECT_NAME /etc/nginx/sites-enabled/
    sudo rm -f /etc/nginx/sites-enabled/default
    
    # 测试配置
    sudo nginx -t
    
    print_status "Nginx配置完成" "SUCCESS"
}

start_services() {
    print_status "启动服务..." "DEPLOY"
    
    # 启动Redis
    sudo systemctl start redis-server
    sudo systemctl enable redis-server
    
    # 启动应用
    sudo systemctl start $PROJECT_NAME
    
    # 启动Nginx
    sudo systemctl restart nginx
    
    print_status "服务启动完成" "SUCCESS"
}

verify_deployment() {
    print_status "验证部署..." "INFO"
    
    sleep 5  # 等待服务启动
    
    # 检查服务状态
    if sudo systemctl is-active --quiet $PROJECT_NAME; then
        print_status "应用服务运行正常" "SUCCESS"
    else
        print_status "应用服务启动失败" "ERROR"
        sudo systemctl status $PROJECT_NAME
        return 1
    fi
    
    # 检查端口
    if netstat -tlnp | grep -q ":5000"; then
        print_status "应用端口5000监听正常" "SUCCESS"
    else
        print_status "应用端口5000未监听" "ERROR"
        return 1
    fi
    
    # 检查HTTP响应
    if curl -s http://localhost/ > /dev/null; then
        print_status "HTTP服务响应正常" "SUCCESS"
    else
        print_status "HTTP服务无响应" "ERROR"
        return 1
    fi
    
    print_status "部署验证完成" "SUCCESS"
    return 0
}

main() {
    echo -e "${BLUE}开始Git仓库部署流程...${NC}"
    echo ""
    
    # 检查Git仓库
    check_git_repo
    echo ""
    
    # 检查系统
    check_system
    echo ""
    
    # 安装系统依赖
    install_system_dependencies
    echo ""
    
    # 设置项目用户
    setup_project_user
    echo ""
    
    # 设置Python环境
    setup_python_environment
    echo ""
    
    # 配置数据库
    configure_database
    echo ""
    
    # 恢复数据
    restore_data
    echo ""
    
    # 创建生产配置
    create_production_config
    echo ""
    
    # 创建系统服务
    create_systemd_service
    echo ""
    
    # 配置Nginx
    configure_nginx
    echo ""
    
    # 启动服务
    start_services
    echo ""
    
    # 验证部署
    if verify_deployment; then
        echo ""
        echo "========================================"
        echo -e "${GREEN}🎉 Git部署完成！${NC}"
        echo "========================================"
        echo ""
        echo -e "${BLUE}📋 部署信息:${NC}"
        echo -e "  🌐 访问地址: http://$(hostname -I | awk '{print $1}')/"
        echo -e "  📁 项目目录: $PROJECT_DIR"
        echo -e "  👤 运行用户: $SERVICE_USER"
        echo -e "  🗄️  数据库: $DB_NAME"
        echo ""
        echo -e "${BLUE}📋 管理命令:${NC}"
        echo -e "  启动服务: sudo systemctl start $PROJECT_NAME"
        echo -e "  停止服务: sudo systemctl stop $PROJECT_NAME"
        echo -e "  重启服务: sudo systemctl restart $PROJECT_NAME"
        echo -e "  查看状态: sudo systemctl status $PROJECT_NAME"
        echo -e "  查看日志: sudo journalctl -u $PROJECT_NAME -f"
        echo ""
        echo -e "${BLUE}📋 更新命令:${NC}"
        echo -e "  cd $PROJECT_DIR"
        echo -e "  git pull origin main"
        echo -e "  sudo systemctl restart $PROJECT_NAME"
        echo ""
    else
        echo ""
        echo -e "${RED}❌ 部署失败，请检查错误信息${NC}"
        exit 1
    fi
}

# 运行主函数
main "$@"
