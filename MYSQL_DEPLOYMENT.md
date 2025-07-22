# 🚀 MySQL服务器部署指南

## 📋 概述

您的仓储管理系统现在完全支持MySQL数据库，并且维护任务已调整为**每3小时自动执行一次**。

## ✅ MySQL兼容性特性

### 🔧 数据库优化
- ✅ **MySQL专用优化**: 使用 `OPTIMIZE TABLE` 和 `ANALYZE TABLE`
- ✅ **SQLite兼容**: 继续支持开发环境的SQLite
- ✅ **PostgreSQL支持**: 基本支持PostgreSQL
- ✅ **自动检测**: 根据数据库类型自动选择优化策略

### 📊 数据库监控
- ✅ **MySQL大小检测**: 查询 `information_schema.tables` 获取准确大小
- ✅ **表统计信息**: 自动更新MySQL表统计
- ✅ **连接池管理**: 优化的连接池配置
- ✅ **性能监控**: 实时监控数据库性能

### ⏰ 维护计划（已调整为每3小时）
- 🕐 **每3小时**: 完整维护（日志清理 + 数据库优化 + 健康检查）
- 🕐 **每1小时**: 轻量级清理（清理>20MB日志文件）
- 🌙 **每日凌晨2点**: 深度维护（清理60天前数据）
- 📅 **每周日凌晨3点**: 数据库深度优化

## 🛠️ 部署步骤

### 1. 准备MySQL数据库

```sql
-- 创建数据库
CREATE DATABASE warehouse_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建用户
CREATE USER 'warehouse_user'@'%' IDENTIFIED BY 'your_strong_password';

-- 授权
GRANT ALL PRIVILEGES ON warehouse_db.* TO 'warehouse_user'@'%';
FLUSH PRIVILEGES;
```

### 2. 安装依赖

```bash
# 安装Python依赖
pip install -r requirements.txt

# 安装MySQL驱动
pip install PyMySQL

# 安装维护相关依赖
pip install APScheduler psutil
```

### 3. 配置环境变量

```bash
# 数据库配置
export MYSQL_HOST=your_mysql_host
export MYSQL_PORT=3306
export MYSQL_USER=warehouse_user
export MYSQL_PASSWORD=your_strong_password
export MYSQL_DATABASE=warehouse_db

# 应用配置
export FLASK_CONFIG=production
export SECRET_KEY=your_secret_key
```

### 4. 使用自动部署脚本

```bash
# 给脚本执行权限
chmod +x deploy_mysql.sh

# 执行部署
./deploy_mysql.sh
```

### 5. 手动部署（可选）

```bash
# 初始化数据库
python -c "
from app import create_app, db
app = create_app()
with app.app_context():
    db.create_all()
    print('数据库初始化完成')
"

# 启动应用
python run.py
```

## 📊 维护任务详情

### 每3小时维护任务
```python
# 执行内容：
1. 系统健康检查
2. 清理超过50MB的日志文件
3. MySQL表优化 (OPTIMIZE TABLE)
4. 清理90天前的测试数据
5. 生成维护报告
```

### 每小时轻量清理
```python
# 执行内容：
1. 清理超过20MB的日志文件
2. 清理3天前的旧日志
3. 快速健康检查
```

### 每日深度维护
```python
# 执行内容：
1. 完整维护任务
2. 清理60天前的数据
3. 深度数据库分析
4. 详细性能报告
```

## 🔧 配置文件示例

### config.py (生产环境)
```python
import os

class ProductionConfig:
    # MySQL配置
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{os.environ['MYSQL_USER']}:"
        f"{os.environ['MYSQL_PASSWORD']}@"
        f"{os.environ['MYSQL_HOST']}:"
        f"{os.environ['MYSQL_PORT']}/"
        f"{os.environ['MYSQL_DATABASE']}"
        f"?charset=utf8mb4"
    )
    
    # 维护配置
    MAINTENANCE_INTERVAL_HOURS = 3  # 每3小时
    LOG_CLEANUP_SIZE_MB = 50
    LOG_KEEP_DAYS = 7
    DB_CLEANUP_DAYS = 90
```

## 🌐 Nginx配置

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /static {
        alias /path/to/your/app/static;
        expires 1y;
    }
}
```

## 📈 监控和管理

### Web管理界面
- 访问: `http://your-domain.com/maintenance/`
- 功能: 实时监控、手动维护、任务管理

### 系统服务管理
```bash
# 查看状态
sudo systemctl status warehouse-system

# 重启服务
sudo systemctl restart warehouse-system

# 查看日志
sudo journalctl -u warehouse-system -f
```

### 数据库监控
```sql
-- 查看数据库大小
SELECT 
    table_schema as '数据库',
    ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) as '大小(MB)'
FROM information_schema.tables 
WHERE table_schema = 'warehouse_db';

-- 查看表大小
SELECT 
    table_name as '表名',
    ROUND(((data_length + index_length) / 1024 / 1024), 2) as '大小(MB)'
FROM information_schema.tables 
WHERE table_schema = 'warehouse_db'
ORDER BY (data_length + index_length) DESC;
```

## 🚨 故障排除

### 常见问题

1. **MySQL连接失败**
   ```bash
   # 检查连接
   mysql -h$MYSQL_HOST -u$MYSQL_USER -p$MYSQL_PASSWORD -e "SELECT 1;"
   ```

2. **维护任务不执行**
   ```bash
   # 检查调度器状态
   curl http://localhost:5000/maintenance/scheduler/status
   ```

3. **数据库性能问题**
   ```sql
   -- 检查慢查询
   SHOW VARIABLES LIKE 'slow_query_log';
   SHOW VARIABLES LIKE 'long_query_time';
   ```

### 性能优化建议

1. **MySQL配置优化**
   ```ini
   [mysqld]
   innodb_buffer_pool_size = 1G
   innodb_log_file_size = 256M
   max_connections = 200
   query_cache_size = 64M
   ```

2. **应用配置优化**
   ```python
   SQLALCHEMY_ENGINE_OPTIONS = {
       'pool_size': 20,
       'pool_timeout': 20,
       'pool_recycle': 3600,
       'max_overflow': 10,
       'pool_pre_ping': True
   }
   ```

## ✅ 验证部署

### 1. 检查服务状态
```bash
curl http://localhost:5000/
curl http://localhost:5000/maintenance/
```

### 2. 检查维护任务
```bash
# 查看调度器状态
curl http://localhost:5000/maintenance/scheduler/status

# 手动执行维护
curl -X POST http://localhost:5000/maintenance/run_maintenance
```

### 3. 检查数据库
```sql
-- 验证表结构
SHOW TABLES;
DESCRIBE users;
DESCRIBE warehouses;
```

## 🎉 部署完成

现在您的系统具备：
- ✅ **MySQL生产数据库**: 高性能、可扩展
- ✅ **每3小时自动维护**: 保持系统最佳状态
- ✅ **Web管理界面**: 方便的监控和管理
- ✅ **自动优化**: MySQL专用的优化策略
- ✅ **故障恢复**: 完善的错误处理和恢复机制

**您的仓储管理系统现在可以在生产环境稳定运行！** 🚀
