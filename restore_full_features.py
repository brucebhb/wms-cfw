#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
恢复完整功能脚本
恢复所有性能监控和后台服务
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
        "RESTORING": "🔄"
    }
    print(f"[{timestamp}] {symbols.get(status, 'ℹ️')} {message}")

def kill_python_processes():
    """终止所有Python进程"""
    print_status("正在终止现有Python进程...", "RESTORING")
    
    killed_count = 0
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] and 'python' in proc.info['name'].lower():
                cmdline = proc.info['cmdline']
                if cmdline and any('app.py' in arg or 'flask' in arg for arg in cmdline):
                    print_status(f"终止进程 PID {proc.info['pid']}: {' '.join(cmdline[:2])}", "RESTORING")
                    proc.terminate()
                    killed_count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    if killed_count > 0:
        print_status(f"已终止 {killed_count} 个Python进程", "SUCCESS")
        time.sleep(2)  # 等待进程完全终止
    else:
        print_status("没有发现需要终止的Python进程", "INFO")

def restore_performance_scripts():
    """恢复性能监控脚本"""
    print_status("恢复性能监控脚本...", "RESTORING")
    
    js_dir = "app/static/js"
    performance_files = [
        "auto-performance-fixer.js",
        "integrated-performance-manager.js", 
        "performance-booster.js",
        "performance-dashboard.js",
        "performance-monitor.js",
        "performance-optimizer.js",
        "unified-performance-manager.js"
    ]
    
    restored_count = 0
    for filename in performance_files:
        disabled_filepath = os.path.join(js_dir, f"{filename}.disabled")
        filepath = os.path.join(js_dir, filename)
        
        if os.path.exists(disabled_filepath):
            try:
                os.rename(disabled_filepath, filepath)
                restored_count += 1
                print_status(f"已恢复: {filename}", "SUCCESS")
            except Exception as e:
                print_status(f"恢复 {filename} 失败: {e}", "WARNING")
        elif os.path.exists(filepath):
            print_status(f"已存在: {filename}", "INFO")
        else:
            print_status(f"未找到: {filename}", "WARNING")
    
    print_status(f"已恢复 {restored_count} 个性能监控脚本", "SUCCESS")

def remove_quick_start_env():
    """移除快速启动环境变量"""
    print_status("移除快速启动环境变量...", "RESTORING")
    
    # 移除环境变量
    if 'QUICK_START_MODE' in os.environ:
        del os.environ['QUICK_START_MODE']
        print_status("已移除 QUICK_START_MODE 环境变量", "SUCCESS")
    else:
        print_status("QUICK_START_MODE 环境变量不存在", "INFO")

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

def start_full_application():
    """启动完整功能的应用程序"""
    print_status("启动完整功能应用程序...", "RESTORING")
    
    # 设置环境变量为正常模式
    os.environ['FLASK_ENV'] = 'development'
    if 'QUICK_START_MODE' in os.environ:
        del os.environ['QUICK_START_MODE']
    
    try:
        # 启动应用
        if os.name == 'nt':  # Windows
            subprocess.Popen(['python', 'app.py'], creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:  # Linux/Mac
            subprocess.Popen(['python3', 'app.py'])
        
        print_status("完整功能应用程序启动命令已执行", "SUCCESS")
        print_status("请等待几秒钟，然后访问 http://127.0.0.1:5000", "INFO")
        
    except Exception as e:
        print_status(f"启动应用程序失败: {e}", "ERROR")
        return False
    
    return True

def main():
    """主函数"""
    print("=" * 60)
    print("🔄 仓储管理系统完整功能恢复工具")
    print("=" * 60)
    
    print_status("开始恢复完整功能...", "INFO")
    
    # 1. 终止现有进程
    kill_python_processes()
    
    # 2. 恢复性能监控脚本
    restore_performance_scripts()
    
    # 3. 移除快速启动环境变量
    remove_quick_start_env()
    
    # 4. 检查系统资源
    check_system_resources()
    
    # 5. 启动完整功能应用
    if start_full_application():
        print_status("完整功能恢复完成！", "SUCCESS")
        print_status("系统已恢复为完整功能模式", "SUCCESS")
        print_status("所有后台任务和性能监控已启用", "INFO")
        print_status("缓存预热和数据库优化已恢复", "INFO")
    else:
        print_status("恢复过程中出现错误", "ERROR")
    
    print("=" * 60)
    print("恢复完成！请访问 http://127.0.0.1:5000 测试系统")
    print("完整功能包括：")
    print("  ✅ 双层缓存系统")
    print("  ✅ 性能监控和优化")
    print("  ✅ 后台维护任务")
    print("  ✅ 数据库优化")
    print("  ✅ 缓存预热")
    print("  ✅ 持续优化服务")
    print("=" * 60)

if __name__ == "__main__":
    main()
