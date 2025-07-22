#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
定期维护任务脚本
每3分钟运行一次，执行数据完整性检查和维护任务
"""

import os
import sys
import time
import threading
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.utils.data_integrity_manager import DataIntegrityManager
from app.utils.backup_manager import get_backup_manager
from app.utils.data_consistency_checker import DataConsistencyChecker
import json

class MaintenanceTaskRunner:
    """维护任务运行器"""
    
    def __init__(self):
        self.app = create_app()
        self.data_integrity_manager = DataIntegrityManager()
        self.backup_manager = get_backup_manager()
        self.last_run_time = None
        self.task_history = []
        self.running = False
    
    def run_data_consistency_check(self):
        """运行数据一致性检查"""
        with self.app.app_context():
            try:
                print(f"[{datetime.now()}] 开始数据一致性检查...")
                
                # 运行完整的一致性检查
                results = DataConsistencyChecker.run_full_consistency_check()
                
                # 记录检查结果
                task_result = {
                    'task': 'data_consistency_check',
                    'timestamp': datetime.now().isoformat(),
                    'status': 'success',
                    'results': results
                }
                
                print(f"数据一致性检查完成:")
                print(f"  总问题数: {results['total_issues']}")
                print(f"  高严重性: {results['high_severity']}")
                print(f"  中严重性: {results['medium_severity']}")
                print(f"  低严重性: {results['low_severity']}")
                
                # 自动修复客户名称问题
                if results['high_severity'] > 0:
                    print("检测到高严重性问题，尝试自动修复...")
                    fixed_count = DataConsistencyChecker.fix_customer_name_issues()
                    print(f"自动修复了 {fixed_count} 条记录")
                    task_result['auto_fix_count'] = fixed_count
                
                self.task_history.append(task_result)
                return task_result
                
            except Exception as e:
                error_result = {
                    'task': 'data_consistency_check',
                    'timestamp': datetime.now().isoformat(),
                    'status': 'error',
                    'error': str(e)
                }
                print(f"数据一致性检查失败: {str(e)}")
                self.task_history.append(error_result)
                return error_result
    
    def run_backup_maintenance(self):
        """运行备份维护"""
        with self.app.app_context():
            try:
                print(f"[{datetime.now()}] 开始备份维护...")
                
                # 清理旧备份
                self.backup_manager.cleanup_old_backups()
                
                # 检查备份状态
                backup_dir = self.backup_manager.backup_dir
                backup_count = 0
                if os.path.exists(backup_dir):
                    backup_count = len([f for f in os.listdir(backup_dir) if os.path.isfile(os.path.join(backup_dir, f))])
                
                task_result = {
                    'task': 'backup_maintenance',
                    'timestamp': datetime.now().isoformat(),
                    'status': 'success',
                    'backup_count': backup_count
                }
                
                print(f"备份维护完成，当前备份文件数: {backup_count}")
                self.task_history.append(task_result)
                return task_result
                
            except Exception as e:
                error_result = {
                    'task': 'backup_maintenance',
                    'timestamp': datetime.now().isoformat(),
                    'status': 'error',
                    'error': str(e)
                }
                print(f"备份维护失败: {str(e)}")
                self.task_history.append(error_result)
                return error_result
    
    def run_database_optimization(self):
        """运行数据库优化"""
        with self.app.app_context():
            try:
                print(f"[{datetime.now()}] 开始数据库优化...")
                
                # 统计表信息
                from app.models import InboundRecord, Inventory, OutboundRecord, TransitCargo
                
                table_stats = {}
                tables = [
                    ('入库记录', InboundRecord),
                    ('库存记录', Inventory),
                    ('出库记录', OutboundRecord),
                    ('在途记录', TransitCargo)
                ]
                
                for table_name, model in tables:
                    count = model.query.count()
                    table_stats[table_name] = count
                    print(f"  {table_name}: {count} 条记录")
                
                # 检查是否有需要清理的数据
                # 例如：清理超过6个月的已完成在途记录
                six_months_ago = datetime.now() - timedelta(days=180)
                old_transit_count = TransitCargo.query.filter(
                    TransitCargo.status == 'received',
                    TransitCargo.arrival_time < six_months_ago
                ).count()
                
                if old_transit_count > 0:
                    print(f"  发现 {old_transit_count} 条可清理的旧在途记录")
                
                task_result = {
                    'task': 'database_optimization',
                    'timestamp': datetime.now().isoformat(),
                    'status': 'success',
                    'table_stats': table_stats,
                    'old_transit_count': old_transit_count
                }
                
                print("数据库优化完成")
                self.task_history.append(task_result)
                return task_result
                
            except Exception as e:
                error_result = {
                    'task': 'database_optimization',
                    'timestamp': datetime.now().isoformat(),
                    'status': 'error',
                    'error': str(e)
                }
                print(f"数据库优化失败: {str(e)}")
                self.task_history.append(error_result)
                return error_result
    
    def run_system_health_check(self):
        """运行系统健康检查"""
        with self.app.app_context():
            try:
                print(f"[{datetime.now()}] 开始系统健康检查...")
                
                health_status = {
                    'database_connection': False,
                    'disk_space': None,
                    'memory_usage': None,
                    'active_sessions': 0
                }
                
                # 检查数据库连接
                try:
                    db.session.execute('SELECT 1')
                    health_status['database_connection'] = True
                    print("  ✓ 数据库连接正常")
                except Exception as e:
                    print(f"  ✗ 数据库连接失败: {str(e)}")
                
                # 检查磁盘空间
                try:
                    import shutil
                    total, used, free = shutil.disk_usage('.')
                    free_gb = free // (1024**3)
                    health_status['disk_space'] = free_gb
                    print(f"  ✓ 可用磁盘空间: {free_gb} GB")
                    
                    if free_gb < 1:  # 少于1GB发出警告
                        print(f"  ⚠ 磁盘空间不足: {free_gb} GB")
                except Exception as e:
                    print(f"  ✗ 磁盘空间检查失败: {str(e)}")
                
                # 检查内存使用情况
                try:
                    import psutil
                    memory = psutil.virtual_memory()
                    memory_percent = memory.percent
                    health_status['memory_usage'] = memory_percent
                    print(f"  ✓ 内存使用率: {memory_percent:.1f}%")
                    
                    if memory_percent > 90:
                        print(f"  ⚠ 内存使用率过高: {memory_percent:.1f}%")
                except ImportError:
                    print("  - psutil未安装，跳过内存检查")
                except Exception as e:
                    print(f"  ✗ 内存检查失败: {str(e)}")
                
                task_result = {
                    'task': 'system_health_check',
                    'timestamp': datetime.now().isoformat(),
                    'status': 'success',
                    'health_status': health_status
                }
                
                print("系统健康检查完成")
                self.task_history.append(task_result)
                return task_result
                
            except Exception as e:
                error_result = {
                    'task': 'system_health_check',
                    'timestamp': datetime.now().isoformat(),
                    'status': 'error',
                    'error': str(e)
                }
                print(f"系统健康检查失败: {str(e)}")
                self.task_history.append(error_result)
                return error_result
    
    def run_all_maintenance_tasks(self):
        """运行所有维护任务"""
        print(f"\n{'='*60}")
        print(f"开始维护任务 - {datetime.now()}")
        print(f"{'='*60}")
        
        tasks = [
            self.run_data_consistency_check,
            self.run_backup_maintenance,
            self.run_database_optimization,
            self.run_system_health_check
        ]
        
        results = []
        for task in tasks:
            try:
                result = task()
                results.append(result)
            except Exception as e:
                print(f"任务执行失败: {str(e)}")
                results.append({
                    'task': 'unknown',
                    'timestamp': datetime.now().isoformat(),
                    'status': 'error',
                    'error': str(e)
                })
        
        # 保存任务历史（只保留最近50次）
        if len(self.task_history) > 50:
            self.task_history = self.task_history[-50:]
        
        self.last_run_time = datetime.now()
        
        print(f"\n维护任务完成 - {self.last_run_time}")
        print(f"{'='*60}\n")
        
        return results
    
    def save_task_history(self):
        """保存任务历史到文件"""
        try:
            history_dir = 'logs'
            if not os.path.exists(history_dir):
                os.makedirs(history_dir)
            
            history_file = os.path.join(history_dir, 'maintenance_history.json')
            
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(self.task_history, f, ensure_ascii=False, indent=2)
            
            print(f"任务历史已保存: {history_file}")
            
        except Exception as e:
            print(f"保存任务历史失败: {str(e)}")
    
    def start_maintenance_loop(self):
        """启动维护循环"""
        self.running = True
        print("维护任务调度器启动中...")
        print("任务间隔: 3分钟")
        print("按 Ctrl+C 停止\n")
        
        # 立即运行一次
        self.run_all_maintenance_tasks()
        
        try:
            while self.running:
                # 等待3分钟
                for i in range(180):  # 180秒 = 3分钟
                    if not self.running:
                        break
                    time.sleep(1)
                
                if self.running:
                    self.run_all_maintenance_tasks()
                    self.save_task_history()
                    
        except KeyboardInterrupt:
            print("\n收到停止信号，正在关闭维护任务调度器...")
            self.running = False
        
        print("维护任务调度器已停止")
    
    def stop(self):
        """停止维护循环"""
        self.running = False

def main():
    """主函数"""
    runner = MaintenanceTaskRunner()
    
    try:
        runner.start_maintenance_loop()
    except Exception as e:
        print(f"维护任务运行失败: {str(e)}")
        import traceback
        print(f"错误堆栈: {traceback.format_exc()}")
    finally:
        runner.save_task_history()

if __name__ == '__main__':
    main()
