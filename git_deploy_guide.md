# 🚀 Git仓库部署指南

## 📋 部署概述

使用Git仓库部署仓储管理系统到Ubuntu服务器，包含完整的环境和数据迁移。

## 🔧 准备工作

### 1. **确认Git仓库状态**
确保您的Git仓库包含：
- ✅ 所有项目文件
- ✅ 虚拟环境文件 (Scripts/, Lib/, pyvenv.cfg)
- ✅ 数据备份文件 (essential_data_backup_*.json)
- ✅ 部署脚本 (deploy_with_data.sh)
- ✅ 配置文件 (config_*.py)

### 2. **服务器要求**
- Ubuntu 18.04+ 或 Debian 10+
- 至少 2GB RAM
- 至少 10GB 磁盘空间
- 网络连接正常
- sudo权限

## 🚀 部署步骤

### 第一步：连接服务器
```bash
# SSH连接到服务器
ssh username@your-server-ip

# 或者使用密钥
ssh -i /path/to/your-key.pem username@your-server-ip
```

### 第二步：安装基础依赖
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Git和基础工具
sudo apt install -y git curl wget vim

# 安装Python和开发工具
sudo apt install -y python3 python3-pip python3-venv python3-dev

# 安装MySQL
sudo apt install -y mysql-server mysql-client libmysqlclient-dev

# 安装Redis
sudo apt install -y redis-server

# 安装CUPS打印系统
sudo apt install -y cups cups-client

# 安装Nginx (可选)
sudo apt install -y nginx
```

### 第三步：配置MySQL数据库
```bash
# 启动MySQL服务
sudo systemctl start mysql
sudo systemctl enable mysql

# 安全配置MySQL
sudo mysql_secure_installation

# 创建数据库和用户
sudo mysql -u root -p
```

在MySQL中执行：
```sql
CREATE DATABASE warehouse_production CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'warehouse_user'@'localhost' IDENTIFIED BY 'your_secure_password';
GRANT ALL PRIVILEGES ON warehouse_production.* TO 'warehouse_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 第四步：克隆Git仓库
```bash
# 进入部署目录
cd /opt

# 克隆仓库 (替换为您的仓库地址)
sudo git clone https://github.com/your-username/your-repo.git warehouse

# 设置权限
sudo chown -R $USER:$USER /opt/warehouse
cd /opt/warehouse
```

### 第五步：运行部署脚本
```bash
# 设置执行权限
chmod +x *.sh

# 运行Git部署脚本
./git_deploy_to_server.sh
```

## 📝 详细操作命令

### **完整部署命令序列**
```bash
# 1. 连接服务器
ssh username@your-server-ip

# 2. 一键安装所有依赖
curl -fsSL https://raw.githubusercontent.com/your-username/your-repo/main/install_dependencies.sh | bash

# 3. 克隆仓库
sudo git clone https://github.com/your-username/your-repo.git /opt/warehouse
sudo chown -R $USER:$USER /opt/warehouse
cd /opt/warehouse

# 4. 配置数据库
sudo mysql -u root -p < database_setup.sql

# 5. 运行部署脚本
chmod +x git_deploy_to_server.sh
./git_deploy_to_server.sh

# 6. 启动服务
sudo systemctl start warehouse
sudo systemctl enable warehouse
```

## 🔧 配置文件修改

### **数据库配置**
编辑 `config_production.py`：
```python
class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'mysql://warehouse_user:your_secure_password@localhost/warehouse_production'
    REDIS_URL = 'redis://localhost:6379/0'
    SECRET_KEY = 'your-production-secret-key'
```

### **Nginx配置** (可选)
```bash
# 复制Nginx配置
sudo cp nginx_warehouse.conf /etc/nginx/sites-available/warehouse
sudo ln -s /etc/nginx/sites-available/warehouse /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

## 🔍 验证部署

### **检查服务状态**
```bash
# 检查应用服务
sudo systemctl status warehouse

# 检查端口监听
netstat -tlnp | grep :5000

# 检查日志
sudo journalctl -u warehouse -f

# 测试HTTP响应
curl http://localhost:5000
```

### **访问应用**
```bash
# 本地访问
http://localhost

# 外部访问 (替换为您的服务器IP)
http://your-server-ip
```

## 🔄 更新部署

### **更新代码**
```bash
cd /opt/warehouse

# 拉取最新代码
git pull origin main

# 重启服务
sudo systemctl restart warehouse
```

### **更新数据库**
```bash
# 如果有数据库变更
source venv/bin/activate
python -c "from app import db; db.create_all()"
```

## 🛠️ 故障排除

### **常见问题**

#### 1. **Git克隆失败**
```bash
# 检查网络连接
ping github.com

# 使用HTTPS而不是SSH
git clone https://github.com/your-username/your-repo.git

# 如果是私有仓库，配置访问令牌
git clone https://username:token@github.com/your-username/your-repo.git
```

#### 2. **权限问题**
```bash
# 修复文件权限
sudo chown -R warehouse:warehouse /opt/warehouse
chmod +x /opt/warehouse/*.sh
```

#### 3. **数据库连接失败**
```bash
# 检查MySQL服务
sudo systemctl status mysql

# 测试数据库连接
mysql -u warehouse_user -p warehouse_production
```

#### 4. **端口被占用**
```bash
# 查看端口占用
sudo netstat -tlnp | grep :5000

# 杀死占用进程
sudo kill -9 PID
```

## 📊 监控和维护

### **日志查看**
```bash
# 应用日志
sudo journalctl -u warehouse -f

# Nginx日志
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# 系统日志
sudo tail -f /var/log/syslog
```

### **性能监控**
```bash
# 系统资源
htop
df -h
free -h

# 服务状态
sudo systemctl status warehouse mysql redis nginx
```

### **备份数据**
```bash
# 数据库备份
mysqldump -u warehouse_user -p warehouse_production > backup_$(date +%Y%m%d).sql

# 应用备份
tar -czf warehouse_backup_$(date +%Y%m%d).tar.gz /opt/warehouse
```

## 🔒 安全配置

### **防火墙设置**
```bash
# 启用UFW防火墙
sudo ufw enable

# 允许SSH
sudo ufw allow ssh

# 允许HTTP和HTTPS
sudo ufw allow 80
sudo ufw allow 443

# 检查状态
sudo ufw status
```

### **SSL证书** (可选)
```bash
# 安装Certbot
sudo apt install certbot python3-certbot-nginx

# 获取SSL证书
sudo certbot --nginx -d your-domain.com
```

## 📞 技术支持

如遇到部署问题：
1. 检查服务器系统要求
2. 确认网络连接正常
3. 查看详细错误日志
4. 验证数据库配置
5. 确认文件权限设置

部署成功后，您的仓储管理系统将在Ubuntu服务器上稳定运行！
