# 🔧 服务器问题修复指南

## 问题现象
- 访问 http://175.178.147.75 出现 "Internal Server Error"
- 页面样式未加载
- 系统无法正常访问

## 🔍 诊断步骤

### 1. 连接服务器
```bash
ssh root@175.178.147.75
```

### 2. 检查应用状态
```bash
cd /opt/warehouse
ps aux | grep python
ps aux | grep gunicorn
```

### 3. 查看错误日志
```bash
# 查看应用日志
tail -50 /var/log/warehouse/app.log
tail -50 app.log

# 查看nginx日志
tail -50 /var/log/nginx/error.log
tail -50 /var/log/nginx/access.log

# 查看系统日志
journalctl -u nginx -n 50
```

### 4. 检查数据库连接
```bash
mysql -u warehouse_user -p warehouse_production
# 密码: warehouse_password_2024
```

## 🛠️ 修复步骤

### 步骤1: 停止所有服务
```bash
# 停止Python应用
pkill -f "python.*app.py"
pkill -f gunicorn

# 停止nginx
systemctl stop nginx
```

### 步骤2: 检查和修复数据库
```bash
# 检查MySQL服务
systemctl status mysql
systemctl start mysql

# 测试数据库连接
mysql -u warehouse_user -p warehouse_production -e "SELECT 1;"
```

### 步骤3: 重新安装Python依赖
```bash
cd /opt/warehouse
source venv/bin/activate

# 安装缺失的包
pip install cryptography
pip install python-dotenv
pip install redis
pip install flask-compress
pip install pymysql

# 重新安装所有依赖
pip install -r requirements.txt
```

### 步骤4: 创建简化启动文件
```bash
cd /opt/warehouse

# 创建简化的启动文件
cat > simple_start.py << 'EOF'
from flask import Flask
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'test_key'

@app.route('/')
def index():
    return '''
    <h1>🏭 仓储管理系统</h1>
    <p>✅ 系统正在运行</p>
    <p>📍 服务器: 175.178.147.75</p>
    <p>🔧 这是简化测试版本</p>
    '''

if __name__ == '__main__':
    print("🚀 启动简化版系统...")
    app.run(host='0.0.0.0', port=5000, debug=True)
EOF

chmod +x simple_start.py
chown warehouse:warehouse simple_start.py
```

### 步骤5: 测试简化版本
```bash
# 切换到warehouse用户
sudo -u warehouse bash
cd /opt/warehouse
source venv/bin/activate

# 启动简化版本
python simple_start.py
```

### 步骤6: 配置nginx
```bash
# 创建nginx配置
cat > /etc/nginx/sites-available/warehouse << 'EOF'
server {
    listen 80;
    server_name 175.178.147.75;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
EOF

# 启用配置
ln -sf /etc/nginx/sites-available/warehouse /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl start nginx
```

### 步骤7: 后台运行
```bash
# 后台运行应用
sudo -u warehouse bash << 'EOF'
cd /opt/warehouse
source venv/bin/activate
nohup python simple_start.py > simple.log 2>&1 &
echo $! > simple.pid
EOF
```

## 🔍 验证修复

### 1. 检查进程
```bash
ps aux | grep python
ps aux | grep nginx
```

### 2. 检查端口
```bash
netstat -tlnp | grep :5000
netstat -tlnp | grep :80
```

### 3. 测试访问
```bash
curl -I http://127.0.0.1:5000
curl -I http://175.178.147.75
```

## 📞 如果仍有问题

### 查看详细错误
```bash
# 查看Python错误
tail -f /opt/warehouse/simple.log

# 查看nginx错误
tail -f /var/log/nginx/error.log
```

### 重启所有服务
```bash
systemctl restart mysql
systemctl restart nginx
pkill -f python
sudo -u warehouse bash -c "cd /opt/warehouse && source venv/bin/activate && nohup python simple_start.py > simple.log 2>&1 &"
```

## 🎯 成功标志

当看到以下内容时表示修复成功：
- ✅ 访问 http://175.178.147.75 显示系统页面
- ✅ 没有 "Internal Server Error"
- ✅ 页面样式正常加载
- ✅ 可以正常登录和使用功能

## 📝 注意事项

1. 所有命令都需要在服务器上执行
2. 确保使用正确的用户权限
3. 修改配置后记得重启相关服务
4. 保留原始文件的备份
5. 逐步测试每个修复步骤
