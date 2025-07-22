#!/usr/bin/env python3
"""
备份管理工具
提供备份创建、查看、清理等功能
"""

import json
import os
import sys
from datetime import datetime, timedelta
from backup_system_data import backup_system_data

def list_backups():
    """列出所有备份"""
    backup_dir = 'backups'
    if not os.path.exists(backup_dir):
        print("❌ 备份目录不存在")
        return []
    
    summaries = []
    for file in os.listdir(backup_dir):
        if file.startswith('backup_summary_') and file.endswith('.json'):
            summary_path = os.path.join(backup_dir, file)
            try:
                with open(summary_path, 'r', encoding='utf-8') as f:
                    summary = json.load(f)
                    # 计算文件大小
                    total_size = 0
                    for backup_file in summary['backup_files'].values():
                        if os.path.exists(backup_file):
                            total_size += os.path.getsize(backup_file)
                    summary['total_size'] = total_size
                    summaries.append((file, summary))
            except Exception as e:
                print(f"⚠️ 读取备份摘要失败 {file}: {str(e)}")
    
    return sorted(summaries, key=lambda x: x[1]['backup_time'], reverse=True)

def format_size(size_bytes):
    """格式化文件大小"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"

def format_time(time_str):
    """格式化时间显示"""
    try:
        dt = datetime.strptime(time_str, '%Y%m%d_%H%M%S')
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return time_str

def show_backup_details(backup_summary):
    """显示备份详细信息"""
    print(f"\n📋 备份详情")
    print("=" * 50)
    print(f"⏰ 备份时间: {format_time(backup_summary['backup_time'])}")
    print(f"📁 备份文件:")
    
    total_size = 0
    for name, path in backup_summary['backup_files'].items():
        if os.path.exists(path):
            size = os.path.getsize(path)
            total_size += size
            print(f"   {name}: {os.path.basename(path)} ({format_size(size)})")
        else:
            print(f"   {name}: {os.path.basename(path)} (❌ 文件不存在)")
    
    print(f"📊 总大小: {format_size(total_size)}")
    print(f"\n📈 数据统计:")
    counts = backup_summary['record_counts']
    print(f"   👥 用户: {counts['users']} 个")
    print(f"   📮 收货人: {counts['receivers']} 个")
    print(f"   🏢 仓库: {counts['warehouses']} 个")
    print(f"   🔐 权限记录: {counts['total_permissions']} 个")
    print(f"      ├─ 菜单权限: {counts['menu_permissions']} 个")
    print(f"      ├─ 页面权限: {counts['page_permissions']} 个")
    print(f"      ├─ 操作权限: {counts['operation_permissions']} 个")
    print(f"      └─ 仓库权限: {counts['warehouse_permissions']} 个")

def clean_old_backups(keep_days=30):
    """清理旧备份文件"""
    backup_dir = 'backups'
    if not os.path.exists(backup_dir):
        print("❌ 备份目录不存在")
        return
    
    cutoff_date = datetime.now() - timedelta(days=keep_days)
    deleted_count = 0
    
    print(f"🧹 清理 {keep_days} 天前的备份文件...")
    
    for file in os.listdir(backup_dir):
        if file.startswith('backup_summary_') and file.endswith('.json'):
            try:
                time_str = file.replace('backup_summary_', '').replace('.json', '')
                backup_time = datetime.strptime(time_str, '%Y%m%d_%H%M%S')
                
                if backup_time < cutoff_date:
                    # 删除相关的所有备份文件
                    files_to_delete = [
                        f'backup_summary_{time_str}.json',
                        f'users_backup_{time_str}.json',
                        f'receivers_backup_{time_str}.json',
                        f'warehouses_backup_{time_str}.json',
                        f'permissions_backup_{time_str}.json'
                    ]
                    
                    for del_file in files_to_delete:
                        del_path = os.path.join(backup_dir, del_file)
                        if os.path.exists(del_path):
                            os.remove(del_path)
                            print(f"  🗑️ 删除: {del_file}")
                    
                    deleted_count += 1
                    
            except Exception as e:
                print(f"⚠️ 处理文件失败 {file}: {str(e)}")
    
    if deleted_count > 0:
        print(f"✅ 清理完成，删除了 {deleted_count} 个旧备份")
    else:
        print("✅ 没有需要清理的旧备份")

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("🔧 备份管理工具")
        print("=" * 50)
        print("用法:")
        print("  python backup_manager.py create    - 创建新备份")
        print("  python backup_manager.py list      - 列出所有备份")
        print("  python backup_manager.py show <N>  - 显示第N个备份的详情")
        print("  python backup_manager.py clean     - 清理30天前的备份")
        print("  python backup_manager.py clean <天数> - 清理指定天数前的备份")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'create':
        print("🔄 创建系统数据备份...")
        if backup_system_data():
            print("✅ 备份创建成功！")
        else:
            print("❌ 备份创建失败！")
    
    elif command == 'list':
        backups = list_backups()
        if not backups:
            print("❌ 没有找到备份文件")
            return
        
        print("📋 备份列表")
        print("=" * 80)
        print(f"{'序号':<4} {'备份时间':<20} {'用户':<6} {'收货人':<8} {'仓库':<6} {'权限':<8} {'大小':<10}")
        print("-" * 80)
        
        for i, (filename, summary) in enumerate(backups, 1):
            time_str = format_time(summary['backup_time'])
            counts = summary['record_counts']
            size_str = format_size(summary.get('total_size', 0))
            
            print(f"{i:<4} {time_str:<20} {counts['users']:<6} {counts['receivers']:<8} "
                  f"{counts['warehouses']:<6} {counts['total_permissions']:<8} {size_str:<10}")
    
    elif command == 'show':
        if len(sys.argv) < 3:
            print("❌ 请指定要显示的备份序号")
            return
        
        try:
            index = int(sys.argv[2]) - 1
            backups = list_backups()
            
            if index < 0 or index >= len(backups):
                print("❌ 无效的备份序号")
                return
            
            show_backup_details(backups[index][1])
            
        except ValueError:
            print("❌ 请输入有效的数字")
    
    elif command == 'clean':
        keep_days = 30
        if len(sys.argv) >= 3:
            try:
                keep_days = int(sys.argv[2])
            except ValueError:
                print("❌ 请输入有效的天数")
                return
        
        clean_old_backups(keep_days)
    
    else:
        print(f"❌ 未知命令: {command}")
        print("使用 'python backup_manager.py' 查看帮助")

if __name__ == '__main__':
    main()
