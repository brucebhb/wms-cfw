@echo off
chcp 65001 >nul
title 仓储管理系统完整功能恢复

echo.
echo ========================================
echo 🔄 仓储管理系统完整功能恢复工具
echo ========================================
echo.

echo [%time%] 🔄 开始恢复完整功能...

REM 1. 终止现有Python进程
echo [%time%] 🔄 终止现有Python进程...
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im pythonw.exe >nul 2>&1
echo [%time%] ✅ Python进程已终止

REM 2. 恢复性能监控脚本
echo [%time%] 🔄 恢复性能监控脚本...
cd app\static\js
if exist auto-performance-fixer.js.disabled ren auto-performance-fixer.js.disabled auto-performance-fixer.js >nul 2>&1
if exist integrated-performance-manager.js.disabled ren integrated-performance-manager.js.disabled integrated-performance-manager.js >nul 2>&1
if exist performance-booster.js.disabled ren performance-booster.js.disabled performance-booster.js >nul 2>&1
if exist performance-dashboard.js.disabled ren performance-dashboard.js.disabled performance-dashboard.js >nul 2>&1
if exist performance-monitor.js.disabled ren performance-monitor.js.disabled performance-monitor.js >nul 2>&1
if exist performance-optimizer.js.disabled ren performance-optimizer.js.disabled performance-optimizer.js >nul 2>&1
if exist unified-performance-manager.js.disabled ren unified-performance-manager.js.disabled unified-performance-manager.js >nul 2>&1
cd ..\..\..
echo [%time%] ✅ 性能监控脚本已恢复

REM 3. 移除快速启动环境变量
echo [%time%] 🔄 移除快速启动模式...
set QUICK_START_MODE=
echo [%time%] ✅ 快速启动模式已移除

REM 4. 设置完整功能环境变量
echo [%time%] 🔄 设置完整功能模式...
set FLASK_ENV=development
echo [%time%] ✅ 完整功能模式已设置

REM 5. 启动完整功能应用程序
echo [%time%] 🚀 启动完整功能应用程序...
echo.
echo ========================================
echo ✅ 完整功能恢复完成！
echo ========================================
echo.
echo 📋 恢复内容：
echo   ✅ 已恢复所有性能监控脚本
echo   ✅ 已启用双层缓存系统
echo   ✅ 已启用后台维护任务
echo   ✅ 已启用数据库优化
echo   ✅ 已启用缓存预热
echo   ✅ 已启用持续优化服务
echo.
echo 🚀 正在启动完整功能系统...
echo 📍 访问地址: http://127.0.0.1:5000
echo.

REM 启动应用
start "仓储管理系统-完整功能" python app.py

echo [%time%] ✅ 完整功能应用程序启动完成
echo.
echo 💡 完整功能包括：
echo   ✅ 双层缓存系统 (L1内存 + L2Redis)
echo   ✅ 性能监控和实时优化
echo   ✅ 后台维护任务 (每3分钟)
echo   ✅ 数据库索引优化
echo   ✅ 缓存预热和调度
echo   ✅ 持续优化服务
echo   ✅ 启动检查器
echo   ✅ 运行时性能管理
echo.
echo ⚠️  注意：
echo   - 完整功能模式启动时间较长 (30-60秒)
echo   - 系统会自动进行后台优化
echo   - 如需快速启动，请使用 quick_fix.bat
echo.
echo 按任意键关闭此窗口...
pause >nul
