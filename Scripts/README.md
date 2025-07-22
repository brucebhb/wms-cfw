# 系统维护脚本使用说明

## 概述

这套维护脚本可以帮助您自动化地维护仓储管理系统，避免因为日志堆积、进程冲突等问题导致的系统卡顿。

## 脚本说明

### 1. 性能监控 (`performance_monitor.py`)
- **功能**: 监控系统资源使用情况
- **检查内容**: CPU、内存、磁盘使用率，Python进程状态，日志文件大小
- **使用**: `python scripts/performance_monitor.py`

### 2. 日志清理 (`log_cleaner.py`)
- **功能**: 自动清理过大和过期的日志文件
- **清理规则**: 
  - 单个文件超过50MB
  - 文件超过7天
  - 自动轮转当前日志
- **使用**: `python scripts/log_cleaner.py`

### 3. 数据库优化 (`db_optimizer.py`)
- **功能**: 优化数据库性能
- **操作内容**: 
  - 检查表统计信息
  - 清理测试数据
  - 执行VACUUM和ANALYZE
- **使用**: `python scripts/db_optimizer.py`

### 4. 自动维护 (`auto_maintenance.py`)
- **功能**: 整合所有维护任务
- **包含**: 性能监控 + 日志清理 + 数据库优化
- **生成**: 维护报告
- **使用**: `python scripts/auto_maintenance.py`

### 5. 快速修复 (`quick_fix.py`)
- **功能**: 紧急情况下的快速修复
- **操作**: 
  - 杀死重复进程
  - 紧急日志清理
  - 自动重启应用
- **使用**: `python scripts/quick_fix.py`

## 安装依赖

```bash
pip install psutil
```

## 定期维护建议

### 每日维护 (推荐)
```bash
python scripts/auto_maintenance.py
```

### 每周维护
```bash
python scripts/db_optimizer.py
```

### 紧急情况
```bash
python scripts/quick_fix.py
```

## Windows定时任务设置

1. 打开"任务计划程序"
2. 创建基本任务
3. 设置触发器（如每天凌晨2点）
4. 设置操作：启动程序
   - 程序: `C:\Users\杨\Desktop\pythonProject\scripts\run_maintenance.bat`
5. 完成设置

## 手动维护步骤

### 当系统卡顿时：

1. **立即执行快速修复**:
   ```bash
   python scripts/quick_fix.py
   ```

2. **检查系统状态**:
   ```bash
   python scripts/performance_monitor.py
   ```

3. **如果仍然卡顿，手动清理**:
   ```bash
   # 停止所有Python进程
   taskkill /f /im python.exe
   
   # 清理日志
   python scripts/log_cleaner.py
   
   # 重启应用
   python run.py
   ```

### 预防性维护：

1. **每天运行自动维护**:
   ```bash
   python scripts/auto_maintenance.py
   ```

2. **每周检查维护报告**:
   - 查看 `logs/maintenance_report.txt`
   - 根据建议进行优化

3. **监控关键指标**:
   - 日志文件大小 < 50MB
   - 数据库文件大小 < 500MB
   - 系统内存使用率 < 80%
   - 磁盘使用率 < 90%

## 故障排除

### 常见问题：

1. **"ModuleNotFoundError: No module named 'psutil'"**
   - 解决: `pip install psutil`

2. **"权限被拒绝"**
   - 解决: 以管理员身份运行

3. **"找不到脚本文件"**
   - 解决: 确保在项目根目录执行

4. **数据库锁定错误**
   - 解决: 停止应用后再运行维护脚本

### 性能优化建议：

1. **日志管理**:
   - 设置日志轮转
   - 定期清理旧日志
   - 避免在生产环境开启DEBUG模式

2. **数据库优化**:
   - 定期执行VACUUM
   - 清理测试数据
   - 添加必要的索引

3. **系统资源**:
   - 监控内存使用
   - 避免重复启动进程
   - 定期重启应用

## 自定义配置

可以修改脚本中的参数来适应您的需求：

### 日志清理配置 (`log_cleaner.py`):
```python
cleaner = LogCleaner(
    max_size_mb=50,  # 最大文件大小
    keep_days=7      # 保留天数
)
```

### 数据库优化配置 (`db_optimizer.py`):
```python
max_records = 500  # 查询限制
days_to_keep = 90  # 数据保留天数
```

## 监控指标

### 正常状态指标：
- CPU使用率 < 50%
- 内存使用率 < 70%
- 磁盘使用率 < 80%
- 单个日志文件 < 50MB
- Python进程数 = 1

### 需要关注的指标：
- CPU使用率 > 80%
- 内存使用率 > 85%
- 磁盘使用率 > 90%
- 单个日志文件 > 100MB
- Python进程数 > 2

## 联系支持

如果维护脚本无法解决问题，请：
1. 查看维护报告 (`logs/maintenance_report.txt`)
2. 收集系统信息 (`python scripts/performance_monitor.py`)
3. 提供错误日志和系统状态信息
