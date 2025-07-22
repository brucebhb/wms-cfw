# 🏭 仓储管理系统生产环境配置指南

## 📋 概述

本指南将帮助您将仓储管理系统从开发环境切换到生产环境配置，确保系统在腾讯云服务器上稳定运行。

## 🔧 已完成的生产环境配置

### 1. 配置文件更新

#### ✅ 应用配置 (`app/__init__.py`)
- 自动检测环境变量 `FLASK_ENV`
- 生产环境默认使用 `ProductionConfig`
- 开发环境回退到 `Config`

#### ✅ 主应用文件 (`app.py`)
- 根据环境变量选择配置类
- 生产环境关闭debug模式
- 监听所有接口 (0.0.0.0)

#### ✅ 生产环境配置 (`config_production.py`)
- 针对4核8G服务器优化
- MySQL连接池配置 (20个连接)
- Redis缓存配置
- 安全设置优化
- 性能参数调优

### 2. 依赖管理

#### ✅ 更新的依赖列表 (`requirements.txt`)
- 添加生产环境服务器 (Gunicorn, gevent)
- 移除Windows特定依赖到条件安装
- 添加安全相关包 (cryptography, bcrypt)
- 分类组织依赖项

### 3. 生产环境启动脚本

#### ✅ Python启动脚本 (`start_production.py`)
- 环境检查和验证
- 数据库连接测试
- Redis连接测试
- 自动初始化数据库
- 创建管理员用户

#### ✅ Shell启动脚本 (`start_production.sh`)
- 完整的环境检查
- 虚拟环境管理
- 依赖安装验证
- 交互式启动确认

### 4. 服务器配置

#### ✅ Gunicorn配置 (`gunicorn_production.py`)
- 4个worker进程 (匹配CPU核心)
- gevent异步模式
- 完整的日志配置
- 性能优化参数
- 安全限制设置

#### ✅ Systemd服务文件 (`warehouse.service`)
- 自动启动配置
- 依赖服务管理
- 安全沙箱设置
- 资源限制配置

### 5. 检查和验证工具

#### ✅ 生产就绪检查 (`check_production_ready.py`)
- 文件完整性检查
- 依赖模块验证
- 数据库连接测试
- 系统要求检查
- 安全配置验证

## 🚀 生产环境部署步骤

### 第一步：环境准备

```bash
# 1. 设置环境变量
export FLASK_ENV=production

# 2. 复制环境变量模板
cp .env.example .env.production

# 3. 编辑生产环境配置
nano .env.production
```

#### 必须配置的环境变量：
```bash
# 应用配置
SECRET_KEY=your-very-secure-secret-key-here
FLASK_ENV=production

# 数据库配置
MYSQL_HOST=localhost
MYSQL_USER=warehouse_user
MYSQL_PASSWORD=your-secure-password
MYSQL_DATABASE=warehouse_production

# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

### 第二步：依赖安装

```bash
# 1. 创建虚拟环境
python3.10 -m venv venv
source venv/bin/activate

# 2. 安装依赖
pip install --upgrade pip
pip install -r requirements.txt
```

### 第三步：系统检查

```bash
# 运行生产就绪检查
python3 check_production_ready.py
```

### 第四步：启动应用

#### 方式一：使用启动脚本（推荐）
```bash
# 设置执行权限
chmod +x start_production.sh

# 启动应用
./start_production.sh
```

#### 方式二：直接使用Python
```bash
python3 start_production.py
```

#### 方式三：使用Gunicorn（生产推荐）
```bash
# 前台运行
gunicorn -c gunicorn_production.py app:app

# 后台运行
nohup gunicorn -c gunicorn_production.py app:app &
```

### 第五步：系统服务配置（可选）

```bash
# 1. 复制服务文件
sudo cp warehouse.service /etc/systemd/system/

# 2. 重载systemd
sudo systemctl daemon-reload

# 3. 启用服务
sudo systemctl enable warehouse

# 4. 启动服务
sudo systemctl start warehouse

# 5. 检查状态
sudo systemctl status warehouse
```

## 🔍 验证部署

### 1. 健康检查
```bash
curl http://localhost:5000/health
```

### 2. 访问测试
- 浏览器访问: `http://your_server_ip:5000`
- 管理员登录: `admin / admin123`

### 3. 功能测试
- [ ] 用户登录
- [ ] 仓库管理
- [ ] 入库操作
- [ ] 出库操作
- [ ] 库存查询
- [ ] 权限控制

## 📊 性能监控

### 查看应用状态
```bash
# Gunicorn进程
ps aux | grep gunicorn

# 系统资源
htop

# 日志监控
tail -f /var/log/warehouse/gunicorn_error.log
```

### 性能指标
- **响应时间**: < 1秒
- **并发用户**: 15人
- **内存使用**: < 4GB
- **CPU使用**: < 80%

## 🔒 安全配置

### 1. 文件权限
```bash
# 设置敏感文件权限
chmod 600 .env.production
chown warehouse:warehouse .env.production
```

### 2. 防火墙配置
```bash
# 只开放必要端口
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow ssh
```

### 3. 定期更新
```bash
# 更新系统包
sudo apt update && sudo apt upgrade

# 更新Python依赖
pip install --upgrade -r requirements.txt
```

## 🛠️ 故障排除

### 常见问题

#### 1. 数据库连接失败
```bash
# 检查MySQL服务
sudo systemctl status mysql

# 检查连接配置
mysql -u warehouse_user -p warehouse_production
```

#### 2. Redis连接失败
```bash
# 检查Redis服务
sudo systemctl status redis-server

# 测试连接
redis-cli ping
```

#### 3. 权限问题
```bash
# 检查文件所有者
ls -la .env.production

# 修复权限
sudo chown warehouse:warehouse /opt/warehouse -R
```

#### 4. 端口占用
```bash
# 检查端口使用
sudo netstat -tlnp | grep :5000

# 杀死占用进程
sudo kill -9 <PID>
```

## 📝 维护建议

### 日常维护
- 每日检查日志文件
- 每周重启服务
- 每月更新依赖

### 备份策略
- 数据库每日备份
- 代码定期推送到Git
- 配置文件单独备份

### 监控告警
- 设置资源使用告警
- 配置错误日志监控
- 建立健康检查机制

## 🎯 性能优化建议

### 1. 数据库优化
- 定期执行 `OPTIMIZE TABLE`
- 监控慢查询日志
- 适当增加索引

### 2. 缓存优化
- 启用Redis持久化
- 设置合理的过期时间
- 监控缓存命中率

### 3. 应用优化
- 使用连接池
- 启用gzip压缩
- 优化静态文件缓存

---

**🎉 恭喜！您的仓储管理系统已成功配置为生产环境！**

如有问题，请检查日志文件或运行诊断脚本进行排查。
