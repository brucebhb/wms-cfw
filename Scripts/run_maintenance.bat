@echo off
REM 自动维护批处理文件
REM 用于Windows定时任务

echo 开始系统维护...
echo 时间: %date% %time%

REM 切换到项目目录
cd /d "C:\Users\杨\Desktop\pythonProject"

REM 运行维护脚本
python scripts\auto_maintenance.py

echo 维护完成
echo 时间: %date% %time%

REM 可选：暂停以查看结果（调试时使用）
REM pause
