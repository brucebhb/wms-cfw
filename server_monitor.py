#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务器监控脚本
适用于4核8G腾讯云服务器
"""

import psutil
import requests
import time
import json
from datetime import datetime

class ServerMonitor:
    def __init__(self):
        self.server_ip = "175.178.147.75"
        self.app_url = f"http://{self.server_ip}"
        
    def check_system_resources(self):
        """检查系统资源使用情况"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            'timestamp': datetime.now().isoformat(),
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_used_gb': round(memory.used / (1024**3), 2),
            'memory_total_gb': round(memory.total / (1024**3), 2),
            'disk_percent': disk.percent,
            'disk_used_gb': round(disk.used / (1024**3), 2),
            'disk_total_gb': round(disk.total / (1024**3), 2)
        }
    
    def check_application_health(self):
        """检查应用健康状态"""
        try:
            response = requests.get(f"{self.app_url}/health", timeout=10)
            return {
                'status': 'healthy' if response.status_code == 200 else 'unhealthy',
                'response_time': response.elapsed.total_seconds(),
                'status_code': response.status_code
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'response_time': None,
                'status_code': None
            }
    
    def check_database_connections(self):
        """检查数据库连接"""
        try:
            import pymysql
            connection = pymysql.connect(
                host='localhost',
                user='warehouse_user',
                password='your_password',  # 需要配置正确密码
                database='warehouse_production'
            )
            cursor = connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM user")
            user_count = cursor.fetchone()[0]
            connection.close()
            
            return {
                'status': 'connected',
                'user_count': user_count
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def generate_report(self):
        """生成监控报告"""
        report = {
            'server_info': {
                'ip': self.server_ip,
                'check_time': datetime.now().isoformat()
            },
            'system_resources': self.check_system_resources(),
            'application_health': self.check_application_health(),
            'database_status': self.check_database_connections()
        }
        
        return report
    
    def print_report(self):
        """打印监控报告"""
        report = self.generate_report()
        
        print("=" * 60)
        print(f"🖥️  服务器监控报告 - {report['server_info']['check_time']}")
        print("=" * 60)
        
        # 系统资源
        sys = report['system_resources']
        print(f"📊 系统资源:")
        print(f"   CPU使用率: {sys['cpu_percent']:.1f}%")
        print(f"   内存使用: {sys['memory_used_gb']:.1f}GB / {sys['memory_total_gb']:.1f}GB ({sys['memory_percent']:.1f}%)")
        print(f"   磁盘使用: {sys['disk_used_gb']:.1f}GB / {sys['disk_total_gb']:.1f}GB ({sys['disk_percent']:.1f}%)")
        
        # 应用健康
        app = report['application_health']
        status_icon = "✅" if app['status'] == 'healthy' else "❌"
        print(f"\n🌐 应用状态: {status_icon} {app['status']}")
        if app['response_time']:
            print(f"   响应时间: {app['response_time']:.3f}秒")
        if app.get('error'):
            print(f"   错误信息: {app['error']}")
        
        # 数据库状态
        db = report['database_status']
        db_icon = "✅" if db['status'] == 'connected' else "❌"
        print(f"\n🗄️  数据库状态: {db_icon} {db['status']}")
        if db.get('user_count'):
            print(f"   用户数量: {db['user_count']}")
        if db.get('error'):
            print(f"   错误信息: {db['error']}")
        
        # 性能建议
        print(f"\n💡 性能建议:")
        if sys['cpu_percent'] > 80:
            print("   ⚠️  CPU使用率过高，建议检查应用进程")
        if sys['memory_percent'] > 85:
            print("   ⚠️  内存使用率过高，建议重启应用")
        if sys['disk_percent'] > 90:
            print("   ⚠️  磁盘空间不足，建议清理日志文件")
        if app['response_time'] and app['response_time'] > 2:
            print("   ⚠️  应用响应时间过长，建议检查性能")
        
        if (sys['cpu_percent'] < 50 and sys['memory_percent'] < 70 and 
            app['status'] == 'healthy' and app['response_time'] and app['response_time'] < 1):
            print("   ✅ 系统运行良好，性能正常")

if __name__ == "__main__":
    monitor = ServerMonitor()
    monitor.print_report()
