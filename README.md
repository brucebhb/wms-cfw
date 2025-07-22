# 仓储管理系统

## 项目概述

这是一个基于Flask的多仓库仓储管理系统，支持前后端仓库分离管理，具备完整的权限控制和用户管理功能。

## 功能特性

### 核心功能
- 🏭 **多仓库管理** - 支持前端仓（平湖、昆山、成都）和后端仓（凭祥北投）
- 📦 **入库管理** - 前端仓入库操作和后端仓接收操作
- 🚚 **出库管理** - 支持拆票分装、批量出库等功能
- 📊 **库存管理** - 实时库存查询和管理
- 🏷️ **标签打印** - 支持货物标签打印功能

### 权限系统
- 👑 **系统管理员** - 最高权限，用户管理、系统配置
- 👔 **总经理** - 业务管理权限，查看所有仓库数据
- 👷 **仓库操作员** - 各仓库的入库、出库操作权限
- 👤 **客户** - 查看自己的货物信息

### 用户界面
- 📱 **响应式设计** - 支持桌面和移动设备
- 🎨 **现代化UI** - 基于Bootstrap的美观界面
- 🔄 **动态菜单** - 根据用户权限显示不同菜单
- 📈 **数据可视化** - 图表和统计信息展示

## 技术栈

- **后端**: Python Flask
- **数据库**: SQLite
- **前端**: HTML5, CSS3, JavaScript, Bootstrap 5
- **权限**: 基于角色的访问控制(RBAC)
- **安全**: CSRF保护, 密码加密, 权限验证
- **备份**: 自动化数据备份与恢复系统

## 🔄 数据备份与恢复

### 备份管理工具

系统提供了完整的数据备份和恢复功能，确保重要数据的安全性。

#### 创建备份
```bash
# 手动创建备份
python backup_system_data.py

# 或使用备份管理工具
python backup_manager.py create
```

#### 查看备份列表
```bash
python backup_manager.py list
```

#### 查看备份详情
```bash
python backup_manager.py show 1  # 查看第1个备份的详情
```

#### 清理旧备份
```bash
python backup_manager.py clean     # 清理30天前的备份
python backup_manager.py clean 7   # 清理7天前的备份
```

#### 恢复数据
```bash
python restore_system_data.py
```

### 备份内容

系统会备份以下重要数据：
- 👥 **用户信息**: 用户账号、密码、权限等
- 📮 **收货人信息**: 收货地址、联系方式等
- 🏢 **仓库信息**: 仓库配置、联系信息等
- 🔐 **权限配置**: 用户权限分配记录

### 备份文件结构

```
backups/
├── backup_summary_20250708_113759.json     # 备份摘要
├── users_backup_20250708_113759.json       # 用户数据
├── receivers_backup_20250708_113759.json   # 收货人数据
├── warehouses_backup_20250708_113759.json  # 仓库数据
└── permissions_backup_20250708_113759.json # 权限数据
```

## 账号信息

系统包含7个核心账号：

| 用户名 | 密码 | 角色 | 权限范围 |
|--------|------|------|----------|
| admin | admin123 | 系统管理员 | 最高权限 |
| general_manager | gm123456 | 总经理 | 业务管理权限 |
| ph_operator | ph123 | 平湖仓操作员 | 平湖仓操作 |
| ks_operator | ks123 | 昆山仓操作员 | 昆山仓操作 |
| cd_operator | cd123 | 成都仓操作员 | 成都仓操作 |
| px_operator | px123 | 凭祥北投仓操作员 | 后端仓操作 |
| customer001 | customer123 | 客户 | 查看自己数据 |

## 快速开始

### 环境要求
- Python 3.8+
- Flask 2.0+
- SQLite 3

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd pythonProject
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **启动应用**
```bash
python app.py
```

或者在Windows上使用：
```bash
start.bat
```

4. **访问系统**
打开浏览器访问: http://localhost:5000

## 项目结构

```
pythonProject/
├── app/                    # 应用主目录
│   ├── __init__.py        # 应用工厂
│   ├── models.py          # 数据模型
│   ├── forms.py           # 表单定义
│   ├── decorators.py      # 权限装饰器
│   ├── utils.py           # 工具函数
│   ├── admin/             # 管理员模块
│   ├── api/               # API接口
│   ├── auth/              # 认证模块
│   ├── customer/          # 客户模块
│   ├── main/              # 主要业务模块
│   ├── printing/          # 打印模块
│   ├── static/            # 静态文件
│   └── templates/         # 模板文件
├── migrations/            # 数据库迁移
├── logs/                  # 日志文件
├── backups/               # 数据备份文件
├── instance/              # 实例配置
├── app.py                 # 应用入口
├── config.py              # 配置文件
├── backup_manager.py      # 备份管理工具
├── backup_system_data.py  # 系统数据备份
├── restore_system_data.py # 系统数据恢复
├── start.bat              # Windows启动脚本
└── requirements.txt       # 依赖列表
```

## 使用说明

### 管理员操作
1. 使用admin账号登录
2. 在用户管理中创建和管理用户
3. 分配角色和权限
4. 查看系统运行状态

### 仓库操作员
1. 使用对应仓库操作员账号登录
2. 进行入库、出库操作
3. 查看库存状态
4. 打印货物标签

### 客户使用
1. 使用客户账号登录
2. 查看自己的入库记录
3. 查看自己的出库记录
4. 查看当前库存状态
5. 查看数据报表

## 安全特性

- ✅ 基于角色的权限控制
- ✅ 密码加密存储
- ✅ CSRF攻击防护
- ✅ 操作日志记录
- ✅ 数据访问隔离
- ✅ 登录状态验证

## 维护说明

### 日志管理
- 应用日志存储在 `logs/` 目录
- 支持日志轮转，自动清理旧日志

### 数据备份
- 定期备份 `app.db` 数据库文件
- 重要操作前建议手动备份

### 性能优化
- 定期清理过期日志
- 监控数据库大小
- 优化查询性能

## 技术支持

如有问题或需要技术支持，请联系系统管理员。

---

**版本**: 1.0.0  
**最后更新**: 2025年7月  
**开发团队**: 仓储管理系统开发组
