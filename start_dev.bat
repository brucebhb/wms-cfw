@echo off
echo 🚀 启动仓储管理系统开发环境...

REM 激活虚拟环境
call .venv\Scripts\activate.bat

REM 设置环境变量
set FLASK_ENV=development
set PYTHONPATH=%CD%

REM 检查依赖
echo 📦 检查依赖...
python -c "import flask, pymysql, redis; print('✅ 依赖检查通过')" 2>nul
if errorlevel 1 (
    echo ❌ 依赖缺失，正在安装...
    pip install -r requirements.txt
)

REM 启动应用
echo 🎯 启动应用...
python app.py

pause
