# 数据完整性预防措施指南

## 概述

为了预防类似"客户名称与识别编码不一致"的数据问题，我们实施了一套完整的数据完整性管理系统。

## 🛡️ 已实施的预防措施

### 1. 事务管理 (Transaction Management)
- **文件**: `app/utils/transaction_manager.py`
- **功能**: 确保所有数据库操作的原子性
- **特点**:
  - 原子事务上下文管理器
  - 出库操作专用事务管理
  - 死锁重试机制
  - 详细的事务日志记录

### 2. 数据一致性检查 (Data Consistency Checker)
- **文件**: `app/utils/data_consistency_checker.py`
- **功能**: 定期检查和修复数据不一致问题
- **检查项目**:
  - 识别编码一致性
  - 库存平衡性
  - 业务字段一致性
  - 在途货物一致性
- **自动修复**: 客户名称不一致问题

### 3. 操作日志记录 (Operation Logger)
- **文件**: `app/utils/operation_logger.py`
- **功能**: 记录详细的库存变更日志
- **记录内容**:
  - 操作前后状态对比
  - 用户信息和IP地址
  - 操作时间和耗时
  - 错误详情和堆栈信息

### 4. 数据备份管理 (Backup Manager)
- **文件**: `app/utils/backup_manager.py`
- **功能**: 自动备份和恢复数据
- **备份类型**:
  - MySQL/SQLite数据库备份
  - JSON格式数据导出
  - 压缩存储节省空间
  - 自动清理旧备份

### 5. 数据完整性管理器 (Data Integrity Manager)
- **文件**: `app/utils/data_integrity_manager.py`
- **功能**: 集成所有完整性功能的统一管理器
- **特点**:
  - 安全操作上下文管理
  - 状态快照和对比
  - 操作后一致性验证
  - 自动备份触发

### 6. 定期维护任务 (Maintenance Tasks)
- **文件**: `scripts/maintenance_tasks.py`
- **功能**: 每3分钟自动执行维护任务
- **任务内容**:
  - 数据一致性检查
  - 备份状态检查
  - 数据库优化
  - 系统健康检查

## 🚀 使用方法

### 启动维护任务
```bash
# Windows
start_maintenance.bat

# 或直接运行Python脚本
python scripts/maintenance_tasks.py
```

### 在代码中使用安全操作
```python
from app.utils.data_integrity_manager import data_integrity_manager

# 安全出库操作
outbound_data = {
    'identification_code': 'PH/裕同/沪A12345/20250712/001',
    'operated_warehouse_id': 1,
    'pallet_count': 2,
    'package_count': 0,
    'destination': '凭祥北投仓',
    'outbound_time': datetime.now()
}

outbound_record = data_integrity_manager.safe_outbound_operation(
    identification_code='PH/裕同/沪A12345/20250712/001',
    outbound_data=outbound_data
)
```

### 手动运行一致性检查
```python
from app.utils.data_consistency_checker import DataConsistencyChecker

# 运行完整检查
results = DataConsistencyChecker.run_full_consistency_check()

# 自动修复客户名称问题
fixed_count = DataConsistencyChecker.fix_customer_name_issues()
```

## 📊 监控和报告

### 日志文件位置
- **应用日志**: `logs/app.log`
- **维护历史**: `logs/maintenance_history.json`
- **一致性报告**: `reports/consistency_check_*.json`

### 备份文件位置
- **备份目录**: `backups/`
- **数据库备份**: `*.sql.gz`
- **数据导出**: `*.json.gz`

## ⚠️ 重要提醒

### 1. 维护任务必须运行
- 维护任务每3分钟运行一次，确保数据完整性
- 如果停止维护任务，数据问题可能会累积

### 2. 备份策略
- 系统每天自动创建备份
- 保留30天的备份文件
- 重要操作会触发额外备份

### 3. 问题处理流程
1. **发现问题**: 维护任务会自动检测
2. **自动修复**: 系统会尝试自动修复常见问题
3. **人工干预**: 严重问题需要人工处理
4. **备份恢复**: 必要时可从备份恢复数据

## 🔧 配置选项

### 环境变量配置
```python
# config.py 中的相关配置
BACKUP_DIR = 'backups'          # 备份目录
MAX_BACKUPS = 30                # 保留备份天数
LOG_FILE_SIZE = 100 * 1024 * 1024  # 日志文件大小 (100MB)
```

### 维护任务间隔
- 当前设置: 每3分钟
- 可在 `scripts/maintenance_tasks.py` 中修改

## 📈 性能影响

### 资源消耗
- **CPU**: 维护任务占用很少CPU资源
- **内存**: 约增加50-100MB内存使用
- **磁盘**: 备份文件会占用额外磁盘空间
- **网络**: 无额外网络消耗

### 性能优化
- 维护任务在后台运行，不影响用户操作
- 使用索引优化一致性检查查询
- 压缩备份文件节省空间

## 🆘 故障排除

### 常见问题

1. **维护任务启动失败**
   - 检查Python环境
   - 确认数据库连接正常
   - 查看错误日志

2. **一致性检查发现问题**
   - 查看详细报告
   - 运行自动修复
   - 必要时手动处理

3. **备份失败**
   - 检查磁盘空间
   - 确认备份目录权限
   - 查看备份日志

### 紧急恢复
```python
# 从备份恢复数据
from app.utils.backup_manager import get_backup_manager

backup_manager = get_backup_manager()
success = backup_manager.restore_from_backup('backups/backup_file.json.gz')
```

## 📞 技术支持

如果遇到问题，请：
1. 查看日志文件
2. 运行诊断脚本
3. 联系技术支持并提供日志信息

---

**注意**: 这套预防措施系统已经集成到现有代码中，会自动运行并保护数据完整性。建议定期查看维护报告，确保系统正常运行。
