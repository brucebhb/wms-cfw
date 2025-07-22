@echo off
chcp 65001 >nul
title 仓储管理系统 - 快速启动模式

echo.
echo ========================================
echo 🚀 仓储管理系统 - 快速启动模式
echo ========================================
echo.

REM 设置快速启动环境变量
set FLASK_APP=app.py
set FLASK_ENV=development
set QUICK_START_MODE=1

echo 🚀 快速启动模式已启用
echo   ✅ 跳过后台任务初始化
echo   ✅ 禁用性能监控
echo   ✅ 优化页面加载速度
echo.

echo 🚀 启动应用程序...
echo 📍 访问地址: http://127.0.0.1:5000
echo ⏹️  按 Ctrl+C 停止服务器
echo.

python app.py

echo.
echo 👋 应用程序已停止
pause
