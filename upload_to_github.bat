@echo off
echo 🚀 上传仓储管理系统到GitHub仓库
echo ========================================

REM 检查Git是否安装
git --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Git未安装，请先安装Git
    echo 💡 访问: https://git-scm.com/download/win
    pause
    exit /b 1
)

echo ✅ Git已安装

REM 检查是否在正确目录
if not exist "app.py" (
    echo ❌ 请在项目根目录运行此脚本
    echo 💡 当前目录应包含app.py文件
    pause
    exit /b 1
)

echo ✅ 在正确的项目目录

REM 初始化Git仓库
echo 📁 初始化Git仓库...
git init

REM 设置默认分支
echo 🌿 设置默认分支为main...
git branch -M main

REM 添加远程仓库
echo 🔗 添加远程仓库...
git remote add origin https://github.com/brucebhb/WMS.git 2>nul
git remote set-url origin https://github.com/brucebhb/WMS.git

REM 添加所有文件
echo 📦 添加所有文件...
git add .

REM 检查状态
echo 📋 检查文件状态...
git status

REM 创建提交
echo 💾 创建提交...
git commit -m "初始提交：仓储管理系统完整代码

- 完整的Flask应用架构
- 多仓库管理功能
- 用户权限系统
- 入库出库管理
- 库存管理
- 标签打印功能
- 生产环境配置
- 部署脚本和文档
- 所有项目文件和配置"

REM 推送到GitHub
echo 🚀 推送到GitHub...
echo 💡 如果需要认证，请输入您的GitHub用户名和密码/令牌
git push -u origin main

if errorlevel 1 (
    echo ❌ 推送失败
    echo 💡 可能需要配置认证信息
    echo 💡 请访问: https://github.com/settings/tokens 创建个人访问令牌
    echo 💡 然后运行: git remote set-url origin https://brucebhb:YOUR_TOKEN@github.com/brucebhb/WMS.git
    pause
    exit /b 1
)

echo ✅ 上传成功！
echo 🌐 访问您的仓库: https://github.com/brucebhb/WMS
echo 📊 检查文件是否完整上传

pause
