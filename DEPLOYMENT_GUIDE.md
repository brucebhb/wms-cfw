# 🚀 仓储管理系统腾讯云服务器完整部署指南

## 📋 服务器配置
- **云服务商**: 腾讯云
- **配置**: 4核8G内存，12Mbps带宽
- **系统**: Ubuntu 22.04 LTS
- **预期负载**: 15人并发，每日200条记录
- **访问方式**: IP地址访问（无域名）

## 🎯 部署概览

本部署方案分为4个阶段：
1. **服务器环境配置** - 安装基础软件和优化系统
2. **应用程序部署** - 部署Flask应用和配置服务
3. **监控维护配置** - 设置监控、备份和维护
4. **性能测试验证** - 验证系统性能和功能

## 📦 第一阶段：服务器环境配置

### 1.1 连接服务器
```bash
# 使用SSH连接到腾讯云服务器
ssh root@your_server_ip
```

### 1.2 上传部署脚本
```bash
# 在本地项目目录执行
scp deploy_server_optimized.sh root@your_server_ip:/root/
scp deploy_application.sh root@your_server_ip:/root/
scp setup_monitoring.sh root@your_server_ip:/root/
```

### 1.3 执行环境配置
```bash
# 在服务器上执行
chmod +x deploy_server_optimized.sh
./deploy_server_optimized.sh
```

**此阶段完成后将安装：**
- ✅ Python 3.10 + 开发工具
- ✅ MySQL 8.0 (数据库: warehouse_production)
- ✅ Redis (内存限制: 1GB)
- ✅ Nginx + Supervisor
- ✅ 防火墙配置
- ✅ 系统性能优化

## 📁 第二阶段：应用程序部署

### 2.1 上传应用代码
```bash
# 方法1: 使用scp上传整个项目
tar -czf warehouse_app.tar.gz --exclude=venv --exclude=__pycache__ .
scp warehouse_app.tar.gz root@your_server_ip:/opt/warehouse/
ssh root@your_server_ip "cd /opt/warehouse && tar -xzf warehouse_app.tar.gz"

# 方法2: 使用git克隆（如果代码在git仓库）
ssh root@your_server_ip "cd /opt && git clone your_repo_url warehouse"
```

### 2.2 执行应用部署
```bash
# 在服务器上执行
chmod +x deploy_application.sh
./deploy_application.sh
```

**此阶段完成后将配置：**
- ✅ Python虚拟环境和依赖
- ✅ Gunicorn应用服务器 (4进程)
- ✅ 数据库初始化和初始数据
- ✅ Nginx反向代理配置
- ✅ Supervisor进程管理
- ✅ 系统服务自启动

### 2.3 验证部署
```bash
# 检查服务状态
supervisorctl status warehouse
systemctl status nginx mysql redis-server

# 测试应用访问
curl http://localhost/health
curl http://your_server_ip
```

## 🔧 第三阶段：监控维护配置

### 3.1 配置监控系统
```bash
# 在服务器上执行
chmod +x setup_monitoring.sh
./setup_monitoring.sh
```

**此阶段完成后将配置：**
- ✅ 系统监控脚本 (每5分钟检查)
- ✅ 自动备份脚本 (每日2点备份)
- ✅ 日志轮转配置
- ✅ 性能优化脚本
- ✅ 定时维护任务

### 3.2 验证监控功能
```bash
# 手动执行监控检查
/usr/local/bin/warehouse_status.sh

# 手动执行备份
/usr/local/bin/warehouse_backup.sh

# 查看定时任务
crontab -l
```

## 🎯 第四阶段：性能测试验证

### 4.1 功能测试清单

**基础功能测试：**
- [ ] 用户登录 (admin/admin123)
- [ ] 仓库管理界面
- [ ] 入库记录创建
- [ ] 出库记录创建
- [ ] 库存查询
- [ ] 标签打印功能
- [ ] 用户权限控制

**性能测试：**
```bash
# 安装压力测试工具
apt install -y apache2-utils

# 并发测试 (模拟15用户)
ab -n 1000 -c 15 http://your_server_ip/

# 数据库压力测试
ab -n 500 -c 10 -p post_data.json -T application/json http://your_server_ip/api/inbound
```

### 4.2 监控指标验证
```bash
# 检查系统资源使用
htop
iotop
nethogs

# 检查应用性能
tail -f /var/log/warehouse/gunicorn_error.log
tail -f /var/log/nginx/warehouse_access.log
```

## 🔐 安全配置

### 5.1 防火墙规则
```bash
# 查看当前规则
ufw status

# 只允许必要端口
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
```

### 5.2 SSL证书配置（可选）
```bash
# 安装Let's Encrypt（如果有域名）
apt install -y certbot python3-certbot-nginx
certbot --nginx -d your_domain.com

# 或创建自签名证书
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/ssl/private/warehouse.key \
    -out /etc/ssl/certs/warehouse.crt
```

## 📊 系统管理命令

### 日常管理命令
```bash
# 查看系统状态
warehouse_status.sh

# 重启应用
supervisorctl restart warehouse

# 查看日志
tail -f /var/log/warehouse/gunicorn_error.log
tail -f /var/log/nginx/warehouse_error.log

# 手动备份
warehouse_backup.sh

# 性能优化
warehouse_optimize.sh
```

### 故障排除
```bash
# 应用无法启动
supervisorctl status warehouse
cat /var/log/warehouse/supervisor.log

# 数据库连接问题
systemctl status mysql
mysql -u warehouse_user -p warehouse_production

# Nginx配置问题
nginx -t
systemctl status nginx
```

## 📈 性能优化建议

### 针对15用户并发优化
1. **Gunicorn配置**: 4个worker进程
2. **MySQL连接池**: 20个连接
3. **Redis缓存**: 1GB内存限制
4. **Nginx缓存**: 静态文件30天缓存

### 针对200条/日记录优化
1. **数据库索引**: 已优化关键字段索引
2. **分页查询**: 每页20条记录
3. **定期清理**: 自动清理30天前日志
4. **备份策略**: 每日备份，保留30天

## 🚨 监控告警

### 自动监控项目
- ✅ 应用服务状态 (每5分钟)
- ✅ 数据库连接状态
- ✅ 磁盘空间使用率
- ✅ 内存使用率
- ✅ 应用健康检查

### 告警阈值
- 磁盘使用率 > 85%
- 内存使用率 > 90%
- 应用响应时间 > 5秒
- 服务异常自动重启

## 📞 技术支持

### 常用端口
- **HTTP**: 80
- **HTTPS**: 443 (如配置SSL)
- **MySQL**: 3306 (仅本地)
- **Redis**: 6379 (仅本地)
- **应用**: 5000 (仅本地)

### 重要文件路径
- **应用目录**: `/opt/warehouse`
- **日志目录**: `/var/log/warehouse`
- **备份目录**: `/var/backups/warehouse`
- **配置文件**: `/opt/warehouse/.env.production`

### 联系方式
如遇问题，请提供以下信息：
1. 错误日志内容
2. 系统状态报告 (`warehouse_status.sh`)
3. 具体操作步骤

---

**🎉 部署完成后，您的仓储管理系统将具备：**
- ✅ 高可用性 (自动重启和故障恢复)
- ✅ 高性能 (针对15用户并发优化)
- ✅ 数据安全 (每日自动备份)
- ✅ 系统监控 (实时状态监控)
- ✅ 维护便利 (自动化运维脚本)

**访问地址**: `http://your_server_ip`  
**管理员账号**: `admin / admin123`
