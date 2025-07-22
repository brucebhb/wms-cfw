#!/bin/bash
# 仓储管理系统生产环境启动脚本
# 适用于腾讯云Ubuntu服务器

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

echo -e "${GREEN}🏭 仓储管理系统生产环境启动器${NC}"
echo -e "${BLUE}===============================================${NC}"

# 检查是否在正确的目录
if [ ! -f "app.py" ]; then
    echo -e "${RED}❌ 请在项目根目录运行此脚本${NC}"
    exit 1
fi

# 设置生产环境变量
export FLASK_ENV=production
export PYTHONPATH=$(pwd)

echo -e "${YELLOW}🔍 检查生产环境配置...${NC}"

# 检查环境变量文件
if [ ! -f ".env.production" ]; then
    echo -e "${RED}❌ 缺少环境变量文件: .env.production${NC}"
    echo -e "${BLUE}💡 请复制 .env.example 为 .env.production 并配置正确的值${NC}"
    exit 1
fi

# 检查生产配置文件
if [ ! -f "config_production.py" ]; then
    echo -e "${RED}❌ 缺少生产环境配置文件: config_production.py${NC}"
    exit 1
fi

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}📦 创建Python虚拟环境...${NC}"
    python3.10 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
else
    echo -e "${GREEN}✅ 虚拟环境已存在${NC}"
    source venv/bin/activate
fi

# 检查依赖
echo -e "${YELLOW}📚 检查Python依赖...${NC}"
if ! pip check > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️ 发现依赖问题，尝试修复...${NC}"
    pip install -r requirements.txt
fi

# 创建必要的目录
echo -e "${YELLOW}📁 创建必要目录...${NC}"
mkdir -p logs
mkdir -p backups
mkdir -p uploads

# 测试数据库连接
echo -e "${YELLOW}🗄️ 测试数据库连接...${NC}"
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv('.env.production')

try:
    from config_production import ProductionConfig
    from app import create_app, db
    
    app = create_app(ProductionConfig)
    with app.app_context():
        with db.engine.connect() as conn:
            conn.execute(db.text('SELECT 1'))
    print('✅ 数据库连接正常')
except Exception as e:
    print(f'❌ 数据库连接失败: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ 数据库连接失败，请检查配置${NC}"
    exit 1
fi

# 测试Redis连接
echo -e "${YELLOW}🔴 测试Redis连接...${NC}"
python3 -c "
import os
import redis
from dotenv import load_dotenv

load_dotenv('.env.production')

try:
    redis_host = os.environ.get('REDIS_HOST', 'localhost')
    redis_port = int(os.environ.get('REDIS_PORT', 6379))
    redis_db = int(os.environ.get('REDIS_DB', 0))
    
    r = redis.Redis(host=redis_host, port=redis_port, db=redis_db)
    r.ping()
    print('✅ Redis连接正常')
except Exception as e:
    print(f'⚠️ Redis连接失败: {e}')
    print('💡 Redis不可用时系统将使用内存缓存')
"

# 初始化数据库
echo -e "${YELLOW}🔧 初始化数据库...${NC}"
python3 -c "
from config_production import ProductionConfig
from app import create_app, db
from app.models import User, Warehouse

app = create_app(ProductionConfig)
with app.app_context():
    # 创建所有表
    db.create_all()
    
    # 创建初始仓库数据
    if Warehouse.query.count() == 0:
        print('📦 创建初始仓库数据...')
        warehouses = [
            {'warehouse_code': 'PH', 'warehouse_name': '平湖仓', 'warehouse_type': 'frontend'},
            {'warehouse_code': 'KS', 'warehouse_name': '昆山仓', 'warehouse_type': 'frontend'},
            {'warehouse_code': 'CD', 'warehouse_name': '成都仓', 'warehouse_type': 'frontend'},
            {'warehouse_code': 'PX', 'warehouse_name': '凭祥北投仓', 'warehouse_type': 'backend'}
        ]
        
        for wh_data in warehouses:
            warehouse = Warehouse(**wh_data)
            db.session.add(warehouse)
        
        db.session.commit()
        print('✅ 初始仓库数据创建完成')
    
    # 创建管理员用户
    if not User.query.filter_by(username='admin').first():
        print('👑 创建管理员用户...')
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
        print('✅ 管理员用户创建完成 (admin/admin123)')

print('✅ 数据库初始化完成')
"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ 数据库初始化失败${NC}"
    exit 1
fi

# 显示启动信息
echo -e "${GREEN}✅ 所有检查通过，准备启动应用...${NC}"
echo -e "${BLUE}===============================================${NC}"
echo -e "${BLUE}🕐 启动时间: $(date '+%Y-%m-%d %H:%M:%S')${NC}"
echo -e "${BLUE}🌐 环境模式: 生产环境${NC}"
echo -e "${BLUE}📍 访问地址: http://$(curl -s ifconfig.me || hostname -I | awk '{print $1}')${NC}"
echo -e "${BLUE}👤 管理员账号: admin / admin123${NC}"
echo -e "${BLUE}===============================================${NC}"

echo -e "${YELLOW}💡 生产环境建议使用 Gunicorn 启动:${NC}"
echo -e "${BLUE}   gunicorn -c gunicorn_config.py app:app${NC}"
echo -e "${YELLOW}💡 当前使用 Flask 内置服务器（仅用于测试）${NC}"

# 询问是否继续
echo ""
read -p "是否继续启动？(y/N): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}⏹️ 启动已取消${NC}"
    exit 0
fi

# 启动应用
echo -e "${GREEN}🚀 启动仓储管理系统...${NC}"

# 使用Python启动脚本
python3 start_production.py
