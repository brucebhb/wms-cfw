#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速性能修复脚本
解决系统卡顿问题
"""

import os
import sys
import time
import subprocess
import psutil
from datetime import datetime

def print_status(message, status="INFO"):
    """打印状态信息"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    symbols = {
        "INFO": "ℹ️",
        "SUCCESS": "✅", 
        "WARNING": "⚠️",
        "ERROR": "❌",
        "FIXING": "🔧"
    }
    print(f"[{timestamp}] {symbols.get(status, 'ℹ️')} {message}")

def kill_python_processes():
    """终止所有Python进程"""
    print_status("正在终止现有Python进程...", "FIXING")
    
    killed_count = 0
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] and 'python' in proc.info['name'].lower():
                cmdline = proc.info['cmdline']
                if cmdline and any('app.py' in arg or 'flask' in arg for arg in cmdline):
                    print_status(f"终止进程 PID {proc.info['pid']}: {' '.join(cmdline[:2])}", "FIXING")
                    proc.terminate()
                    killed_count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    if killed_count > 0:
        print_status(f"已终止 {killed_count} 个Python进程", "SUCCESS")
        time.sleep(2)  # 等待进程完全终止
    else:
        print_status("没有发现需要终止的Python进程", "INFO")

def clear_cache_files():
    """清理缓存文件"""
    print_status("清理缓存文件...", "FIXING")
    
    cache_dirs = [
        '__pycache__',
        'app/__pycache__',
        'app/*/__pycache__',
        'logs/*.log',
        'temp/*'
    ]
    
    for cache_pattern in cache_dirs:
        try:
            if '*' in cache_pattern:
                # 使用shell命令处理通配符
                os.system(f'rm -rf {cache_pattern} 2>/dev/null || del /s /q {cache_pattern} 2>nul')
            else:
                if os.path.exists(cache_pattern):
                    if os.path.isdir(cache_pattern):
                        os.system(f'rm -rf {cache_pattern} 2>/dev/null || rmdir /s /q {cache_pattern} 2>nul')
                    else:
                        os.remove(cache_pattern)
        except Exception as e:
            print_status(f"清理 {cache_pattern} 失败: {e}", "WARNING")
    
    print_status("缓存文件清理完成", "SUCCESS")

def disable_performance_scripts():
    """禁用性能监控脚本"""
    print_status("禁用性能监控脚本...", "FIXING")
    
    # 重命名性能监控相关的JS文件
    js_dir = "app/static/js"
    performance_files = [
        "performance-monitor.js",
        "performance-optimizer.js", 
        "integrated-performance-manager.js",
        "auto-performance-fixer.js",
        "performance-booster.js",
        "performance-dashboard.js",
        "unified-performance-manager.js"
    ]
    
    disabled_count = 0
    for filename in performance_files:
        filepath = os.path.join(js_dir, filename)
        disabled_filepath = os.path.join(js_dir, f"{filename}.disabled")
        
        if os.path.exists(filepath):
            try:
                os.rename(filepath, disabled_filepath)
                disabled_count += 1
                print_status(f"已禁用: {filename}", "SUCCESS")
            except Exception as e:
                print_status(f"禁用 {filename} 失败: {e}", "WARNING")
    
    print_status(f"已禁用 {disabled_count} 个性能监控脚本", "SUCCESS")

def check_system_resources():
    """检查系统资源"""
    print_status("检查系统资源...", "INFO")
    
    # CPU使用率
    cpu_percent = psutil.cpu_percent(interval=1)
    print_status(f"CPU使用率: {cpu_percent}%", "INFO")
    
    # 内存使用率
    memory = psutil.virtual_memory()
    print_status(f"内存使用率: {memory.percent}% ({memory.used // 1024 // 1024}MB / {memory.total // 1024 // 1024}MB)", "INFO")
    
    # 磁盘使用率
    disk = psutil.disk_usage('.')
    print_status(f"磁盘使用率: {disk.percent}%", "INFO")
    
    # 检查是否有资源问题
    if cpu_percent > 80:
        print_status("CPU使用率过高，可能影响性能", "WARNING")
    if memory.percent > 85:
        print_status("内存使用率过高，可能影响性能", "WARNING")

def start_application():
    """启动应用程序"""
    print_status("启动应用程序...", "FIXING")
    
    # 设置环境变量以启用快速模式
    os.environ['FLASK_ENV'] = 'development'
    os.environ['QUICK_START_MODE'] = '1'
    
    try:
        # 启动应用
        if os.name == 'nt':  # Windows
            subprocess.Popen(['python', 'app.py'], creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:  # Linux/Mac
            subprocess.Popen(['python3', 'app.py'])
        
        print_status("应用程序启动命令已执行", "SUCCESS")
        print_status("请等待几秒钟，然后访问 http://127.0.0.1:5000", "INFO")
        
    except Exception as e:
        print_status(f"启动应用程序失败: {e}", "ERROR")
        return False
    
    return True

def main():
    """主函数"""
    print("=" * 60)
    print("🚀 仓储管理系统快速性能修复工具")
    print("=" * 60)
    
    print_status("开始执行快速性能修复...", "INFO")
    
    # 1. 终止现有进程
    kill_python_processes()
    
    # 2. 清理缓存
    clear_cache_files()
    
    # 3. 禁用性能监控脚本
    disable_performance_scripts()
    
    # 4. 检查系统资源
    check_system_resources()
    
    # 5. 启动应用
    if start_application():
        print_status("快速性能修复完成！", "SUCCESS")
        print_status("系统已优化为快速启动模式", "SUCCESS")
        print_status("所有后台任务和性能监控已禁用", "INFO")
        print_status("页面加载速度应该明显提升", "INFO")
    else:
        print_status("修复过程中出现错误", "ERROR")
    
    print("=" * 60)
    print("修复完成！请访问 http://127.0.0.1:5000 测试系统")
    print("如果还有问题，请检查控制台输出的错误信息")
    print("=" * 60)

if __name__ == "__main__":
    main()
