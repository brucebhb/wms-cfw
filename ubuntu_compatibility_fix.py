#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ubuntu部署兼容性修复脚本
修复Windows特定代码，确保在Ubuntu环境下正常运行
"""

import os
import sys
import shutil
import platform
from pathlib import Path

def print_status(message, status="INFO"):
    """打印状态信息"""
    colors = {
        "INFO": "\033[0;34m",      # 蓝色
        "SUCCESS": "\033[0;32m",   # 绿色
        "WARNING": "\033[1;33m",   # 黄色
        "ERROR": "\033[0;31m",     # 红色
        "FIXING": "\033[1;35m"     # 紫色
    }
    reset = "\033[0m"
    
    prefix = {
        "INFO": "ℹ️ ",
        "SUCCESS": "✅",
        "WARNING": "⚠️ ",
        "ERROR": "❌",
        "FIXING": "🔧"
    }
    
    color = colors.get(status, colors["INFO"])
    icon = prefix.get(status, "")
    print(f"{color}{icon} {message}{reset}")

def check_system():
    """检查系统环境"""
    print_status("检查系统环境...", "INFO")
    
    system = platform.system()
    if system != "Linux":
        print_status(f"当前系统: {system}", "WARNING")
        print_status("此脚本专为Linux/Ubuntu环境设计", "WARNING")
    else:
        print_status(f"当前系统: {system} ✓", "SUCCESS")
    
    # 检查Python版本
    python_version = sys.version_info
    if python_version.major >= 3 and python_version.minor >= 8:
        print_status(f"Python版本: {python_version.major}.{python_version.minor} ✓", "SUCCESS")
    else:
        print_status(f"Python版本: {python_version.major}.{python_version.minor} (建议3.8+)", "WARNING")

def fix_file_permissions():
    """修复文件权限"""
    print_status("修复文件权限...", "FIXING")
    
    # 需要执行权限的脚本文件
    script_files = [
        "start.sh",
        "quick_fix.sh",
        "deploy.sh",
        "setup_linux_printing.sh",
        "quick_deploy.sh",
        "quick_git_deploy.sh",
        "quick_git_update.sh",
        "quick_start.sh",
        "quick_update.sh"
    ]
    
    for script in script_files:
        if os.path.exists(script):
            try:
                os.chmod(script, 0o755)
                print_status(f"已设置执行权限: {script}", "SUCCESS")
            except Exception as e:
                print_status(f"设置权限失败 {script}: {e}", "ERROR")

def check_dependencies():
    """检查依赖包"""
    print_status("检查依赖包...", "INFO")
    
    # Linux特定依赖
    linux_deps = {
        "cups-python": "Linux打印支持",
        "reportlab": "PDF生成",
        "psutil": "系统监控"
    }
    
    missing_deps = []
    for dep, desc in linux_deps.items():
        try:
            __import__(dep.replace('-', '_'))
            print_status(f"{dep} ({desc}) ✓", "SUCCESS")
        except ImportError:
            missing_deps.append((dep, desc))
            print_status(f"{dep} ({desc}) - 未安装", "WARNING")
    
    if missing_deps:
        print_status("需要安装以下依赖:", "WARNING")
        for dep, desc in missing_deps:
            print(f"  pip install {dep}  # {desc}")

def check_printing_system():
    """检查打印系统"""
    print_status("检查打印系统...", "INFO")
    
    # 检查CUPS是否安装
    cups_commands = ["lpstat", "lpr", "lpadmin"]
    cups_available = True
    
    for cmd in cups_commands:
        if shutil.which(cmd) is None:
            print_status(f"CUPS命令未找到: {cmd}", "WARNING")
            cups_available = False
        else:
            print_status(f"CUPS命令可用: {cmd} ✓", "SUCCESS")
    
    if not cups_available:
        print_status("建议安装CUPS打印系统:", "WARNING")
        print("  sudo apt-get update")
        print("  sudo apt-get install cups cups-client")

def create_systemd_service():
    """创建systemd服务文件"""
    print_status("创建systemd服务文件...", "FIXING")
    
    service_content = """[Unit]
Description=仓储管理系统
After=network.target mysql.service redis.service

[Service]
Type=simple
User=warehouse
Group=warehouse
WorkingDirectory=/opt/warehouse
Environment=FLASK_ENV=production
Environment=PYTHONPATH=/opt/warehouse
ExecStart=/opt/warehouse/venv/bin/python app.py
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
    
    try:
        with open("warehouse.service", "w", encoding="utf-8") as f:
            f.write(service_content)
        print_status("已创建 warehouse.service 文件", "SUCCESS")
        print_status("部署时需要复制到 /etc/systemd/system/", "INFO")
    except Exception as e:
        print_status(f"创建服务文件失败: {e}", "ERROR")

def create_nginx_config():
    """创建Nginx配置文件"""
    print_status("创建Nginx配置文件...", "FIXING")
    
    nginx_content = """server {
    listen 80;
    server_name _;
    
    # 静态文件
    location /static/ {
        alias /opt/warehouse/app/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # 应用代理
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # 缓冲设置
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }
    
    # 健康检查
    location /health {
        proxy_pass http://127.0.0.1:5000/health;
        access_log off;
    }
}
"""
    
    try:
        with open("nginx_warehouse.conf", "w", encoding="utf-8") as f:
            f.write(nginx_content)
        print_status("已创建 nginx_warehouse.conf 文件", "SUCCESS")
        print_status("部署时需要复制到 /etc/nginx/sites-available/", "INFO")
    except Exception as e:
        print_status(f"创建Nginx配置失败: {e}", "ERROR")

def main():
    """主函数"""
    print("=" * 60)
    print("🐧 Ubuntu部署兼容性修复脚本")
    print("=" * 60)
    print()
    
    # 检查系统环境
    check_system()
    print()
    
    # 修复文件权限
    fix_file_permissions()
    print()
    
    # 检查依赖
    check_dependencies()
    print()
    
    # 检查打印系统
    check_printing_system()
    print()
    
    # 创建服务文件
    create_systemd_service()
    print()
    
    # 创建Nginx配置
    create_nginx_config()
    print()
    
    print_status("Ubuntu兼容性修复完成！", "SUCCESS")
    print()
    print("📋 后续部署步骤:")
    print("1. 安装缺失的依赖包")
    print("2. 配置CUPS打印系统（如需要）")
    print("3. 复制服务文件到systemd目录")
    print("4. 配置Nginx反向代理")
    print("5. 启动服务")

if __name__ == "__main__":
    main()
