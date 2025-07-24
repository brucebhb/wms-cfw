#!/bin/bash
# 仓储管理系统 - 一键部署脚本（包含数据迁移）

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
BACKUP_DIR="./backups"
VENV_DIR="$PROJECT_DIR/venv"

# 数据库配置（需要根据实际情况修改）
DB_HOST="localhost"
DB_PORT="3306"
DB_NAME="warehouse_production"
DB_USER="warehouse_user"
DB_PASSWORD=""

echo ""
echo "========================================"
echo -e "${BLUE}🚀 仓储管理系统 - 一键部署脚本${NC}"
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
        "BACKUP")
            echo -e "${CYAN}💾 $message${NC}"
            ;;
    esac
}

check_root() {
    if [[ $EUID -eq 0 ]]; then
        print_status "请不要使用root用户运行此脚本" "ERROR"
        exit 1
    fi
}

check_system() {
    print_status "检查系统环境..." "INFO"
    
    # 检查操作系统
    if [[ ! -f /etc/os-release ]]; then
        print_status "无法识别操作系统" "ERROR"
        exit 1
    fi
    
    . /etc/os-release
    if [[ $ID != "ubuntu" ]]; then
        print_status "此脚本仅支持Ubuntu系统" "WARNING"
    fi
    
    print_status "操作系统: $PRETTY_NAME" "SUCCESS"
    
    # 检查Python
    if ! command -v python3 &> /dev/null; then
        print_status "Python3未安装" "ERROR"
        exit 1
    fi
    
    python_version=$(python3 --version | cut -d' ' -f2)
    print_status "Python版本: $python_version" "SUCCESS"
    
    # 检查MySQL
    if ! command -v mysql &> /dev/null; then
        print_status "MySQL客户端未安装" "ERROR"
        exit 1
    fi
    
    print_status "MySQL客户端已安装" "SUCCESS"
}

install_dependencies() {
    print_status "安装系统依赖..." "DEPLOY"
    
    # 更新包列表
    sudo apt-get update -qq
    
    # 安装必要的包
    sudo apt-get install -y \
        python3-pip \
        python3-venv \
        python3-dev \
        libmysqlclient-dev \
        redis-server \
        nginx \
        supervisor \
        git \
        curl \
        unzip
    
    print_status "系统依赖安装完成" "SUCCESS"
}

create_user_and_directories() {
    print_status "创建项目用户和目录..." "DEPLOY"
    
    # 创建用户
    if ! id "$SERVICE_USER" &>/dev/null; then
        sudo useradd -m -s /bin/bash $SERVICE_USER
        print_status "创建用户: $SERVICE_USER" "SUCCESS"
    else
        print_status "用户已存在: $SERVICE_USER" "INFO"
    fi
    
    # 创建项目目录
    sudo mkdir -p $PROJECT_DIR
    sudo chown $SERVICE_USER:$SERVICE_USER $PROJECT_DIR
    print_status "创建项目目录: $PROJECT_DIR" "SUCCESS"
    
    # 创建日志目录
    sudo mkdir -p /var/log/$PROJECT_NAME
    sudo chown $SERVICE_USER:$SERVICE_USER /var/log/$PROJECT_NAME
    print_status "创建日志目录: /var/log/$PROJECT_NAME" "SUCCESS"
}

deploy_application() {
    print_status "部署应用程序..." "DEPLOY"
    
    # 复制项目文件
    sudo cp -r . $PROJECT_DIR/
    sudo chown -R $SERVICE_USER:$SERVICE_USER $PROJECT_DIR
    
    # 切换到项目用户
    sudo -u $SERVICE_USER bash << EOF
cd $PROJECT_DIR

# 创建虚拟环境
python3 -m venv $VENV_DIR
source $VENV_DIR/bin/activate

# 升级pip
pip install --upgrade pip

# 安装依赖
pip install -r requirements.txt

# 设置执行权限
chmod +x *.sh
chmod +x *.py

EOF
    
    print_status "应用程序部署完成" "SUCCESS"
}

setup_database() {
    print_status "配置数据库..." "DEPLOY"
    
    # 检查数据库连接
    if ! mysql -h $DB_HOST -P $DB_PORT -u $DB_USER -p$DB_PASSWORD -e "SELECT 1;" &>/dev/null; then
        print_status "数据库连接失败，请检查配置" "ERROR"
        return 1
    fi
    
    # 创建数据库（如果不存在）
    mysql -h $DB_HOST -P $DB_PORT -u $DB_USER -p$DB_PASSWORD << EOF
CREATE DATABASE IF NOT EXISTS $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EOF
    
    print_status "数据库配置完成" "SUCCESS"
}

backup_local_data() {
    print_status "备份本地数据..." "BACKUP"
    
    # 运行备份脚本
    if [[ -f "backup_essential_data.py" ]]; then
        python3 backup_essential_data.py
        
        # 检查备份文件
        latest_backup=$(ls -t essential_data_backup_*.json 2>/dev/null | head -1)
        if [[ -n "$latest_backup" ]]; then
            print_status "本地数据备份完成: $latest_backup" "SUCCESS"
            
            # 复制备份文件到服务器
            sudo cp $latest_backup $PROJECT_DIR/
            sudo chown $SERVICE_USER:$SERVICE_USER $PROJECT_DIR/$latest_backup
            
            return 0
        else
            print_status "备份文件未找到" "WARNING"
            return 1
        fi
    else
        print_status "备份脚本未找到，跳过数据备份" "WARNING"
        return 1
    fi
}

restore_server_data() {
    print_status "恢复服务器数据..." "DEPLOY"
    
    # 查找备份文件
    backup_file=$(ls -t $PROJECT_DIR/essential_data_backup_*.json 2>/dev/null | head -1)
    
    if [[ -n "$backup_file" ]]; then
        print_status "找到备份文件: $(basename $backup_file)" "INFO"
        
        # 运行恢复脚本
        sudo -u $SERVICE_USER bash << EOF
cd $PROJECT_DIR
source $VENV_DIR/bin/activate

python3 restore_essential_data.py \\
    --host $DB_HOST \\
    --port $DB_PORT \\
    --user $DB_USER \\
    --password $DB_PASSWORD \\
    --database $DB_NAME \\
    --clear \\
    $backup_file
EOF
        
        if [[ $? -eq 0 ]]; then
            print_status "数据恢复完成" "SUCCESS"
            return 0
        else
            print_status "数据恢复失败" "ERROR"
            return 1
        fi
    else
        print_status "未找到备份文件，跳过数据恢复" "WARNING"
        return 1
    fi
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
ExecStart=$VENV_DIR/bin/python app.py
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    # 重新加载systemd
    sudo systemctl daemon-reload
    sudo systemctl enable $PROJECT_NAME
    
    print_status "系统服务创建完成" "SUCCESS"
}

configure_nginx() {
    print_status "配置Nginx..." "DEPLOY"
    
    sudo tee /etc/nginx/sites-available/$PROJECT_NAME > /dev/null << EOF
server {
    listen 80;
    server_name _;
    
    # 静态文件
    location /static/ {
        alias $PROJECT_DIR/app/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # 应用代理
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
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
    echo -e "${BLUE}开始一键部署流程...${NC}"
    echo ""
    
    # 检查权限
    check_root
    
    # 检查系统
    check_system
    echo ""
    
    # 备份本地数据
    backup_local_data
    echo ""
    
    # 安装依赖
    install_dependencies
    echo ""
    
    # 创建用户和目录
    create_user_and_directories
    echo ""
    
    # 部署应用
    deploy_application
    echo ""
    
    # 配置数据库
    setup_database
    echo ""
    
    # 恢复数据
    restore_server_data
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
        echo -e "${GREEN}🎉 部署完成！${NC}"
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
    else
        echo ""
        echo -e "${RED}❌ 部署失败，请检查错误信息${NC}"
        exit 1
    fi
}

# 运行主函数
main "$@"
