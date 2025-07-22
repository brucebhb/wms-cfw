@echo off
echo 启动仓储管理系统...
echo.
echo 正在激活虚拟环境...
call venv\Scripts\activate.bat
echo.
echo 启动Flask应用程序...
echo 访问地址: http://localhost:5000
echo 按 Ctrl+C 停止服务器
echo.
python app.py
pause
