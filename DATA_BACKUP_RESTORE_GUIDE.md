# 📦 数据备份与恢复指南

## 🎯 概述

本指南提供了仓储管理系统核心数据的备份和恢复解决方案，确保在服务器部署时能够一键导入重要数据。

## 📋 备份内容

### 核心数据表
- **收货人信息** (`receivers`) - 客户收货人详细信息
- **仓库信息** (`warehouses`) - 仓库配置和基础信息
- **用户信息** (`users`) - 用户账号和密码信息
- **角色信息** (`roles`) - 系统角色定义
- **权限信息** (`permissions`) - 权限配置
- **用户角色关联** (`user_roles`) - 用户与角色的关联关系
- **角色权限关联** (`role_permissions`) - 角色与权限的关联关系

## 🛠️ 工具脚本

### 1. 数据备份脚本
**文件**: `backup_essential_data.py`

**功能**:
- 自动连接本地数据库
- 备份核心数据表
- 生成JSON格式备份文件
- 创建压缩版本节省空间
- 生成文件校验和确保完整性

**使用方法**:
```bash
# 在本地环境运行
python3 backup_essential_data.py
```

**输出文件**:
- `essential_data_backup_YYYYMMDD_HHMMSS.json` - 原始备份文件
- `essential_data_backup_YYYYMMDD_HHMMSS.json.gz` - 压缩备份文件
- `backup_info_YYYYMMDD_HHMMSS.json` - 备份信息文件

### 2. 数据恢复脚本
**文件**: `restore_essential_data.py`

**功能**:
- 验证备份文件完整性
- 连接目标数据库
- 按正确顺序恢复数据
- 支持事务回滚
- 提供详细的恢复日志

**使用方法**:
```bash
# 基本用法（使用配置文件中的数据库设置）
python3 restore_essential_data.py backup_file.json

# 指定数据库连接参数
python3 restore_essential_data.py backup_file.json \
    --host localhost \
    --port 3306 \
    --user warehouse_user \
    --password your_password \
    --database warehouse_production

# 清空现有数据后恢复（谨慎使用）
python3 restore_essential_data.py backup_file.json --clear
```

### 3. 一键部署脚本
**文件**: `deploy_with_data.sh`

**功能**:
- 自动备份本地数据
- 部署应用到Ubuntu服务器
- 恢复数据到生产数据库
- 配置系统服务
- 验证部署结果

**使用方法**:
```bash
# 设置执行权限
chmod +x deploy_with_data.sh

# 运行部署脚本
./deploy_with_data.sh
```

## 🚀 快速部署流程

### 步骤1: 本地数据备份
```bash
# 在本地开发环境运行
python3 backup_essential_data.py
```

### 步骤2: 上传到服务器
```bash
# 将项目文件和备份文件上传到服务器
scp -r . user@server:/tmp/warehouse/
```

### 步骤3: 服务器部署
```bash
# 在服务器上运行
cd /tmp/warehouse
chmod +x deploy_with_data.sh
./deploy_with_data.sh
```

## 🔧 手动操作流程

### 1. 手动备份数据
```bash
# 在本地环境
python3 backup_essential_data.py

# 检查生成的备份文件
ls -la essential_data_backup_*.json*
```

### 2. 传输备份文件
```bash
# 复制备份文件到服务器
scp essential_data_backup_*.json user@server:/opt/warehouse/
```

### 3. 手动恢复数据
```bash
# 在服务器上
cd /opt/warehouse
source venv/bin/activate

# 恢复数据
python3 restore_essential_data.py \
    --host localhost \
    --user warehouse_user \
    --password your_password \
    --database warehouse_production \
    essential_data_backup_20250724_120000.json
```

## ⚙️ 配置说明

### 数据库配置
脚本会自动从以下配置文件读取数据库连接信息：
1. `config_production.py` (生产环境)
2. `config_local.py` (本地环境)
3. `config.py` (默认配置)

### 环境变量
可以通过环境变量覆盖数据库配置：
```bash
export DB_HOST=localhost
export DB_PORT=3306
export DB_USER=warehouse_user
export DB_PASSWORD=your_password
export DB_NAME=warehouse_production
```

## 🔍 故障排除

### 常见问题

#### 1. 数据库连接失败
**错误**: `数据库连接失败: Access denied`
**解决**: 检查数据库用户名、密码和权限

#### 2. 备份文件损坏
**错误**: `备份文件格式不正确`
**解决**: 重新生成备份文件，检查文件完整性

#### 3. 外键约束错误
**错误**: `Cannot add or update a child row`
**解决**: 使用 `--clear` 参数清空现有数据后恢复

#### 4. 权限不足
**错误**: `Permission denied`
**解决**: 确保数据库用户有足够的权限

### 调试方法

#### 1. 检查备份文件内容
```bash
# 查看备份文件信息
python3 -c "
import json
with open('backup_file.json', 'r') as f:
    data = json.load(f)
    print('备份时间:', data['backup_info']['timestamp'])
    print('表数量:', len(data['tables']))
    for table, info in data['tables'].items():
        print(f'{table}: {info[\"count\"]} 条记录')
"
```

#### 2. 验证数据库连接
```bash
# 测试数据库连接
mysql -h localhost -u warehouse_user -p warehouse_production -e "SELECT 1;"
```

#### 3. 查看详细日志
```bash
# 运行恢复脚本时查看详细输出
python3 restore_essential_data.py backup_file.json -v
```

## 📊 数据验证

### 恢复后验证步骤

#### 1. 检查数据完整性
```sql
-- 检查各表记录数
SELECT 'users' as table_name, COUNT(*) as count FROM users
UNION ALL
SELECT 'warehouses', COUNT(*) FROM warehouses
UNION ALL
SELECT 'receivers', COUNT(*) FROM receivers
UNION ALL
SELECT 'roles', COUNT(*) FROM roles
UNION ALL
SELECT 'permissions', COUNT(*) FROM permissions;
```

#### 2. 验证用户登录
- 使用备份的用户账号尝试登录系统
- 确认密码和权限正确

#### 3. 检查仓库配置
- 验证仓库信息是否正确
- 确认仓库类型和状态

#### 4. 测试权限系统
- 验证不同角色的权限
- 确认菜单和功能访问正常

## 🔒 安全注意事项

1. **备份文件安全**: 备份文件包含用户密码信息，请妥善保管
2. **传输加密**: 使用安全的方式传输备份文件（如SCP、SFTP）
3. **访问控制**: 限制备份文件的访问权限
4. **定期备份**: 建议定期创建数据备份
5. **测试恢复**: 定期测试恢复流程确保可用性

## 📞 技术支持

如遇到问题，请检查：
1. 数据库连接配置
2. 备份文件完整性
3. 系统权限设置
4. 网络连接状态

更多技术支持请参考项目文档或联系系统管理员。
