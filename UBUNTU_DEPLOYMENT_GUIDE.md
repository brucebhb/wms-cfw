# 🐧 Ubuntu部署指南 - Windows兼容性处理

## 📋 概述

本指南专门解决将仓储管理系统从Windows环境迁移到Ubuntu环境时的兼容性问题。

## 🔍 Windows兼容性问题清单

### 1. **pywin32依赖问题**
- **问题**: Windows特定的打印机API
- **解决方案**: 已在`requirements.txt`中配置条件安装
- **状态**: ✅ 已解决

### 2. **打印机功能**
- **问题**: 使用了`win32print`模块
- **解决方案**: 使用跨平台打印机管理器
- **文件**: `app/utils/cross_platform_printer.py`
- **状态**: ✅ 已解决

### 3. **启动脚本**
- **问题**: 只有Windows批处理文件
- **解决方案**: 创建了Linux shell脚本
- **文件**: `start.sh`, `quick_fix.sh`
- **状态**: ✅ 已解决

## 🚀 Ubuntu部署步骤

### 第一步：运行兼容性修复脚本

```bash
# 在项目根目录执行
python3 ubuntu_compatibility_fix.py
```

**修复内容：**
- ✅ 检查系统环境
- ✅ 修复文件权限
- ✅ 检查依赖包
- ✅ 检查打印系统
- ✅ 创建systemd服务文件
- ✅ 创建Nginx配置文件

### 第二步：安装系统依赖

```bash
# 更新包管理器
sudo apt-get update

# 安装Python开发环境
sudo apt-get install python3 python3-pip python3-venv python3-dev

# 安装MySQL客户端和开发库
sudo apt-get install mysql-client libmysqlclient-dev

# 安装Redis
sudo apt-get install redis-server

# 安装CUPS打印系统（如需要打印功能）
sudo apt-get install cups cups-client

# 安装Nginx（如需要反向代理）
sudo apt-get install nginx

# 安装其他系统工具
sudo apt-get install supervisor git curl
```

### 第三步：创建项目环境

```bash
# 创建项目用户
sudo useradd -m -s /bin/bash warehouse

# 创建项目目录
sudo mkdir -p /opt/warehouse
sudo chown warehouse:warehouse /opt/warehouse

# 切换到项目用户
sudo su - warehouse

# 进入项目目录
cd /opt/warehouse

# 克隆项目（或上传项目文件）
git clone <your-repo-url> .
# 或者从Windows环境复制文件
```

### 第四步：配置Python环境

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 升级pip
pip install --upgrade pip

# 安装依赖
pip install -r requirements.txt
```

### 第五步：配置数据库

```bash
# 创建MySQL数据库
mysql -u root -p << EOF
CREATE DATABASE warehouse_production CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'warehouse_user'@'localhost' IDENTIFIED BY 'your_secure_password';
GRANT ALL PRIVILEGES ON warehouse_production.* TO 'warehouse_user'@'localhost';
FLUSH PRIVILEGES;
EOF

# 初始化数据库
python app.py init-db
```

### 第六步：配置服务

```bash
# 复制systemd服务文件
sudo cp warehouse.service /etc/systemd/system/

# 重新加载systemd
sudo systemctl daemon-reload

# 启用服务
sudo systemctl enable warehouse

# 启动服务
sudo systemctl start warehouse

# 检查服务状态
sudo systemctl status warehouse
```

### 第七步：配置Nginx（可选）

```bash
# 复制Nginx配置
sudo cp nginx_warehouse.conf /etc/nginx/sites-available/warehouse

# 启用站点
sudo ln -s /etc/nginx/sites-available/warehouse /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重启Nginx
sudo systemctl restart nginx
```

## 🔧 兼容性修复详情

### 1. 打印机功能修复

**原问题：**
```python
import win32print  # Windows特定
```

**修复方案：**
```python
# 跨平台打印机支持
try:
    import win32print
    WINDOWS_PRINT_AVAILABLE = True
except ImportError:
    WINDOWS_PRINT_AVAILABLE = False

# 使用跨平台打印机管理器
from app.utils.cross_platform_printer import get_system_printers
```

### 2. 路径处理修复

**原问题：**
- 硬编码的Windows路径分隔符

**修复方案：**
- 使用`os.path.join()`
- 使用`pathlib.Path`
- 相对路径处理

### 3. 启动脚本修复

**Windows版本：**
```batch
@echo off
python app.py
```

**Linux版本：**
```bash
#!/bin/bash
python3 app.py
```

## 🧪 测试验证

### 1. 基本功能测试

```bash
# 测试应用启动
./start.sh

# 测试API接口
curl http://localhost:5000/health

# 测试数据库连接
python3 -c "from app import db; print('数据库连接正常')"
```

### 2. 打印功能测试

```bash
# 检查打印机
lpstat -p

# 测试打印功能
python3 -c "
from app.utils.cross_platform_printer import get_system_printers
print('可用打印机:', get_system_printers())
"
```

## 🔍 故障排除

### 1. 权限问题

```bash
# 检查文件权限
ls -la *.sh

# 修复权限
chmod +x *.sh
```

### 2. 依赖问题

```bash
# 检查Python包
pip list | grep -E "(mysql|redis|cups)"

# 重新安装问题包
pip install --force-reinstall package_name
```

### 3. 服务问题

```bash
# 查看服务日志
sudo journalctl -u warehouse -f

# 查看应用日志
tail -f logs/app.log
```

## 📝 注意事项

1. **数据库配置**: 确保MySQL配置正确
2. **文件权限**: 确保warehouse用户有适当权限
3. **防火墙**: 开放必要端口（80, 5000）
4. **SSL证书**: 生产环境建议配置HTTPS
5. **备份策略**: 配置定期数据备份

## 🎯 性能优化

1. **使用Gunicorn**: 生产环境推荐
2. **配置Redis**: 启用缓存功能
3. **Nginx优化**: 静态文件缓存
4. **数据库优化**: 索引和查询优化

## 📞 技术支持

如遇到部署问题，请检查：
1. 系统日志：`/var/log/syslog`
2. 应用日志：`logs/app.log`
3. Nginx日志：`/var/log/nginx/error.log`
4. 服务状态：`systemctl status warehouse`
