@echo off
chcp 65001 >nul
title 仓储管理系统 - 智能优化模式

echo.
echo ========================================
echo 🧠 仓储管理系统 - 智能优化模式
echo ========================================
echo.

echo 🎯 智能优化特性：
echo   ✅ 自适应性能调整
echo   ✅ 动态负载监控
echo   ✅ 智能缓存管理
echo   ✅ 后台任务优化
echo   ✅ 实时性能监控
echo   ✅ Web控制面板
echo.

REM 设置环境变量
set FLASK_APP=app.py
set FLASK_ENV=development
set INTELLIGENT_OPTIMIZATION=1

echo 🔧 环境配置：
echo   📍 访问地址: http://127.0.0.1:5000
echo   🎛️  优化面板: http://127.0.0.1:5000/optimization/dashboard
echo   ⏹️  按 Ctrl+C 停止服务器
echo.

echo 🚀 启动智能优化系统...
echo.

REM 启动应用
python app.py

echo.
echo 👋 应用程序已停止
pause
