# 🚀 基于Git仓库的部署指南

## 📋 为什么推荐使用Git部署？

### ✅ Git部署的优势
- **版本控制**: 完整的代码版本历史
- **团队协作**: 多人开发，分支管理
- **快速更新**: 一键拉取最新代码
- **回滚支持**: 快速回退到任意版本
- **代码备份**: 云端安全存储
- **CI/CD集成**: 支持自动化部署

### ❌ 直接文件上传的问题
- 无版本控制，难以追踪变更
- 团队协作困难
- 更新部署繁琐
- 无法快速回滚
- 代码容易丢失

## 🛠️ Git仓库准备步骤

### 第一步：选择Git平台

#### 推荐平台对比

| 平台 | 优势 | 适用场景 |
|------|------|----------|
| **GitHub** | 全球最大，生态丰富 | 开源项目，国际团队 |
| **GitLab** | 功能完整，CI/CD强大 | 企业级项目 |
| **Gitee** | 国内访问快，中文友好 | 国内团队，私有项目 |
| **自建Git** | 完全控制，数据安全 | 高安全要求 |

### 第二步：创建Git仓库

#### 方案A：使用GitHub（推荐）

1. **注册GitHub账号**
   - 访问 https://github.com
   - 注册账号并验证邮箱

2. **创建新仓库**
   ```bash
   # 在GitHub网站上点击 "New repository"
   # 仓库名称: warehouse-management-system
   # 描述: 仓储管理系统
   # 选择: Private（私有仓库）
   ```

3. **获取仓库地址**
   ```
   https://github.com/your-username/warehouse-management-system.git
   ```

#### 方案B：使用Gitee（国内推荐）

1. **注册Gitee账号**
   - 访问 https://gitee.com
   - 注册账号并实名认证

2. **创建新仓库**
   ```bash
   # 在Gitee网站上点击 "新建仓库"
   # 仓库名称: warehouse-management-system
   # 仓库介绍: 仓储管理系统
   # 选择: 私有
   ```

3. **获取仓库地址**
   ```
   https://gitee.com/your-username/warehouse-management-system.git
   ```

### 第三步：上传项目代码

#### 在本地项目目录执行：

```bash
# 1. 初始化Git仓库
git init

# 2. 创建.gitignore文件
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/

# 实例文件
instance/
.env
.env.production
.env.local

# 日志文件
logs/
*.log

# 数据库
*.db
*.sqlite

# 临时文件
temp/
tmp/
.tmp/

# IDE文件
.vscode/
.idea/
*.swp
*.swo

# 系统文件
.DS_Store
Thumbs.db

# 备份文件（可选，建议保留）
# backups/
# mysql_backups/
EOF

# 3. 添加所有文件
git add .

# 4. 提交代码
git commit -m "初始提交：仓储管理系统完整代码"

# 5. 添加远程仓库
git remote add origin https://github.com/your-username/warehouse-management-system.git

# 6. 推送代码
git push -u origin main
```

### 第四步：配置访问权限

#### 公开仓库（不推荐）
- 任何人都可以访问代码
- 部署时不需要认证

#### 私有仓库（推荐）
- 只有授权用户可以访问
- 需要配置访问令牌

#### 配置访问令牌

**GitHub令牌配置：**
1. 进入 Settings → Developer settings → Personal access tokens
2. 点击 "Generate new token"
3. 选择权限：repo（完整仓库访问）
4. 复制生成的令牌

**Gitee令牌配置：**
1. 进入 设置 → 私人令牌
2. 点击 "生成新令牌"
3. 选择权限：projects（项目权限）
4. 复制生成的令牌

## 🚀 Git部署执行

### 方式一：使用Git部署脚本

```bash
# 1. 上传Git部署脚本到服务器
scp git_deploy.sh root@your_server_ip:/root/

# 2. 在服务器上执行
ssh root@your_server_ip
chmod +x git_deploy.sh
./git_deploy.sh

# 3. 按提示输入Git仓库信息
# Git仓库URL: https://github.com/your-username/warehouse-management-system.git
# 分支名称: main
# Git用户名: your-username
# Git访问令牌: your-token
```

### 方式二：手动Git部署

```bash
# 1. 连接服务器
ssh root@your_server_ip

# 2. 安装Git
apt update && apt install -y git

# 3. 克隆仓库
cd /opt
git clone https://github.com/your-username/warehouse-management-system.git warehouse

# 4. 执行其他部署脚本
cd warehouse
chmod +x deploy_application.sh
./deploy_application.sh
```

## 🔄 日常更新流程

### 本地开发更新

```bash
# 1. 修改代码后提交
git add .
git commit -m "功能更新：添加新的库存管理功能"
git push origin main
```

### 服务器更新

```bash
# 方式一：使用更新脚本（推荐）
warehouse_update.sh

# 方式二：手动更新
cd /opt/warehouse
sudo -u warehouse git pull origin main
supervisorctl restart warehouse
```

## 🔒 安全配置建议

### 1. 敏感信息处理

**创建环境变量模板：**
```bash
# 在仓库中创建 .env.example
cat > .env.example << 'EOF'
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
MYSQL_HOST=localhost
MYSQL_USER=your-mysql-user
MYSQL_PASSWORD=your-mysql-password
MYSQL_DATABASE=your-database-name
REDIS_URL=redis://localhost:6379/0
EOF
```

**服务器上创建实际配置：**
```bash
# 复制模板并填入真实值
cp .env.example .env.production
# 编辑 .env.production 填入真实配置
```

### 2. 分支管理策略

```bash
# 开发分支
git checkout -b develop

# 功能分支
git checkout -b feature/new-inventory-system

# 生产分支
git checkout main  # 只用于生产部署
```

### 3. 部署密钥管理

```bash
# 在服务器上配置SSH密钥（推荐）
ssh-keygen -t rsa -b 4096 -C "server@warehouse.com"
# 将公钥添加到Git平台的Deploy Keys
```

## 📊 Git部署vs文件上传对比

| 特性 | Git部署 | 文件上传 |
|------|---------|----------|
| **版本控制** | ✅ 完整历史 | ❌ 无版本控制 |
| **团队协作** | ✅ 多人开发 | ❌ 协作困难 |
| **更新便利** | ✅ 一键更新 | ❌ 手动上传 |
| **回滚支持** | ✅ 快速回滚 | ❌ 无法回滚 |
| **代码备份** | ✅ 云端备份 | ❌ 本地备份 |
| **部署复杂度** | 🟡 中等 | 🟢 简单 |
| **安全性** | ✅ 访问控制 | 🟡 依赖服务器 |
| **CI/CD集成** | ✅ 支持 | ❌ 不支持 |

## 🎯 推荐的完整部署流程

### 1. 准备阶段
- [ ] 选择Git平台（推荐GitHub或Gitee）
- [ ] 创建私有仓库
- [ ] 配置访问令牌
- [ ] 上传项目代码

### 2. 部署阶段
- [ ] 使用 `git_deploy.sh` 一键部署
- [ ] 验证所有功能正常
- [ ] 配置监控和备份

### 3. 维护阶段
- [ ] 使用 `warehouse_update.sh` 定期更新
- [ ] 定期备份数据库
- [ ] 监控系统性能

## 💡 最佳实践建议

1. **使用私有仓库**：保护商业代码安全
2. **配置.gitignore**：避免上传敏感文件
3. **分支管理**：main分支用于生产，develop分支用于开发
4. **定期备份**：除了Git备份，还要备份数据库
5. **监控更新**：设置自动化监控，及时发现问题
6. **文档维护**：保持README和部署文档更新

---

**🎉 使用Git部署，您将获得：**
- ✅ 专业的版本控制
- ✅ 便捷的团队协作
- ✅ 快速的更新部署
- ✅ 安全的代码管理
- ✅ 完整的操作历史

**推荐使用Git部署方式，这是现代软件开发的标准做法！**
