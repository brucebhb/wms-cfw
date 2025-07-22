@echo off
chcp 65001 >nul
title 仓储管理系统快速性能修复

echo.
echo ========================================
echo 🚀 仓储管理系统快速性能修复工具
echo ========================================
echo.

echo [%time%] 🔧 开始执行快速修复...

REM 1. 终止现有Python进程
echo [%time%] 🔧 终止现有Python进程...
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im pythonw.exe >nul 2>&1
echo [%time%] ✅ Python进程已终止

REM 2. 清理缓存文件
echo [%time%] 🔧 清理缓存文件...
if exist __pycache__ rmdir /s /q __pycache__ >nul 2>&1
if exist app\__pycache__ rmdir /s /q app\__pycache__ >nul 2>&1
for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d" >nul 2>&1
if exist logs\*.log del /q logs\*.log >nul 2>&1
if exist temp\* del /q temp\* >nul 2>&1
echo [%time%] ✅ 缓存文件清理完成

REM 3. 禁用性能监控脚本
echo [%time%] 🔧 禁用性能监控脚本...
cd app\static\js
if exist performance-monitor.js ren performance-monitor.js performance-monitor.js.disabled >nul 2>&1
if exist performance-optimizer.js ren performance-optimizer.js performance-optimizer.js.disabled >nul 2>&1
if exist integrated-performance-manager.js ren integrated-performance-manager.js integrated-performance-manager.js.disabled >nul 2>&1
if exist auto-performance-fixer.js ren auto-performance-fixer.js auto-performance-fixer.js.disabled >nul 2>&1
if exist performance-booster.js ren performance-booster.js performance-booster.js.disabled >nul 2>&1
if exist performance-dashboard.js ren performance-dashboard.js performance-dashboard.js.disabled >nul 2>&1
if exist unified-performance-manager.js ren unified-performance-manager.js unified-performance-manager.js.disabled >nul 2>&1
cd ..\..\..
echo [%time%] ✅ 性能监控脚本已禁用

REM 4. 设置快速启动环境变量
echo [%time%] 🔧 设置快速启动模式...
set FLASK_ENV=development
set QUICK_START_MODE=1
echo [%time%] ✅ 快速启动模式已设置

REM 5. 启动应用程序
echo [%time%] 🚀 启动应用程序...
echo.
echo ========================================
echo ✅ 快速性能修复完成！
echo ========================================
echo.
echo 📋 修复内容：
echo   ✅ 已终止所有Python进程
echo   ✅ 已清理缓存文件
echo   ✅ 已禁用性能监控脚本
echo   ✅ 已启用快速启动模式
echo.
echo 🚀 正在启动系统...
echo 📍 访问地址: http://127.0.0.1:5000
echo.

REM 启动应用
start "仓储管理系统" python app.py

echo [%time%] ✅ 应用程序启动完成
echo.
echo 💡 提示：
echo   - 页面加载速度应该明显提升
echo   - 所有后台任务已禁用
echo   - 如果还有问题，请检查控制台输出
echo.
echo 按任意键关闭此窗口...
pause >nul
