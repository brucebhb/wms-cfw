#!/bin/bash

# 修复服务器部署脚本
echo "🔧 开始修复服务器部署问题..."

# 服务器信息
SERVER_IP="175.178.147.75"
SERVER_USER="root"
APP_DIR="/opt/warehouse"

# 1. 停止当前服务
echo "1. 停止当前服务..."
ssh $SERVER_USER@$SERVER_IP << 'EOF'
# 停止所有相关服务
pkill -f "python.*app.py"
pkill -f "gunicorn"
systemctl stop nginx
EOF

# 2. 重新上传核心文件
echo "2. 重新上传核心文件..."
scp app.py $SERVER_USER@$SERVER_IP:$APP_DIR/
scp config_production.py $SERVER_USER@$SERVER_IP:$APP_DIR/
scp -r app/ $SERVER_USER@$SERVER_IP:$APP_DIR/

# 3. 创建简化的环境配置
echo "3. 创建环境配置..."
ssh $SERVER_USER@$SERVER_IP << 'EOF'
cd /opt/warehouse

# 创建简化的环境配置文件
cat > .env.production << 'ENVEOF'
SECRET_KEY=your_super_secret_key_here_change_in_production
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=warehouse_user
MYSQL_PASSWORD=warehouse_password_2024
MYSQL_DATABASE=warehouse_production
FLASK_ENV=production
ENVEOF

# 设置权限
chown -R warehouse:warehouse /opt/warehouse
chmod 644 .env.production
EOF

# 4. 重新安装依赖
echo "4. 重新安装依赖..."
ssh $SERVER_USER@$SERVER_IP << 'EOF'
cd /opt/warehouse
source venv/bin/activate

# 安装缺失的包
pip install cryptography
pip install python-dotenv
pip install redis
pip install flask-compress

# 确保所有依赖都已安装
pip install -r requirements.txt
EOF

# 5. 重新初始化数据库
echo "5. 重新初始化数据库..."
ssh $SERVER_USER@$SERVER_IP << 'EOF'
cd /opt/warehouse
source venv/bin/activate

# 设置环境变量
export FLASK_ENV=production
export FLASK_APP=app.py

# 初始化数据库
python -c "
from app import create_app, db
from config_production import ProductionConfig
import os

# 设置环境
os.environ['FLASK_ENV'] = 'production'

# 创建应用
app = create_app(ProductionConfig)

with app.app_context():
    try:
        # 创建所有表
        db.create_all()
        print('✅ 数据库表创建成功')
        
        # 初始化权限数据
        from app.auth.utils import init_permissions
        init_permissions()
        print('✅ 权限数据初始化成功')
        
        # 创建默认用户
        from app.models import User, Role, UserRole
        from werkzeug.security import generate_password_hash
        
        # 检查是否已有admin用户
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            # 创建admin用户
            admin_user = User(
                username='admin',
                password_hash=generate_password_hash('admin123'),
                is_active=True
            )
            db.session.add(admin_user)
            
            # 创建管理员角色
            admin_role = Role.query.filter_by(name='管理员').first()
            if not admin_role:
                admin_role = Role(name='管理员', description='系统管理员')
                db.session.add(admin_role)
                db.session.flush()
            
            # 分配角色
            user_role = UserRole(user_id=admin_user.id, role_id=admin_role.id)
            db.session.add(user_role)
            
            db.session.commit()
            print('✅ 管理员用户创建成功')
        else:
            print('✅ 管理员用户已存在')
            
    except Exception as e:
        print(f'❌ 数据库初始化失败: {e}')
        import traceback
        traceback.print_exc()
"
EOF

# 6. 创建简化的启动脚本
echo "6. 创建启动脚本..."
ssh $SERVER_USER@$SERVER_IP << 'EOF'
cd /opt/warehouse

# 创建简化的启动脚本
cat > start_app.py << 'STARTEOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from app import create_app, db
from config_production import ProductionConfig

# 设置环境变量
os.environ['FLASK_ENV'] = 'production'

# 创建应用
app = create_app(ProductionConfig)

if __name__ == '__main__':
    print("🚀 启动仓储管理系统 (生产环境)...")
    print("📍 访问地址: http://0.0.0.0:5000")
    
    with app.app_context():
        try:
            # 确保数据库连接正常
            db.engine.execute('SELECT 1')
            print("✅ 数据库连接正常")
        except Exception as e:
            print(f"❌ 数据库连接失败: {e}")
            sys.exit(1)
    
    # 启动应用
    app.run(host='0.0.0.0', port=5000, debug=False)
STARTEOF

chmod +x start_app.py
chown warehouse:warehouse start_app.py
EOF

# 7. 重新配置nginx
echo "7. 重新配置nginx..."
ssh $SERVER_USER@$SERVER_IP << 'EOF'
# 创建nginx配置
cat > /etc/nginx/sites-available/warehouse << 'NGINXEOF'
server {
    listen 80;
    server_name 175.178.147.75;

    # 静态文件配置
    location /static/ {
        alias /opt/warehouse/app/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # 主应用代理
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
NGINXEOF

# 启用配置
ln -sf /etc/nginx/sites-available/warehouse /etc/nginx/sites-enabled/
nginx -t
systemctl start nginx
systemctl enable nginx
EOF

# 8. 启动应用
echo "8. 启动应用..."
ssh $SERVER_USER@$SERVER_IP << 'EOF'
cd /opt/warehouse

# 切换到warehouse用户启动应用
sudo -u warehouse bash << 'USEREOF'
cd /opt/warehouse
source venv/bin/activate
export FLASK_ENV=production
nohup python start_app.py > app.log 2>&1 &
echo $! > app.pid
USEREOF

# 等待启动
sleep 5

# 检查进程
if pgrep -f "python.*start_app.py" > /dev/null; then
    echo "✅ 应用启动成功"
    echo "📍 访问地址: http://175.178.147.75"
else
    echo "❌ 应用启动失败"
    echo "查看日志:"
    tail -20 app.log
fi
EOF

echo "🎉 修复完成！请访问 http://175.178.147.75 测试"
