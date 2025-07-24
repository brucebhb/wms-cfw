#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
仓储管理系统 - 核心数据备份脚本
备份收货人信息、仓库管理信息、用户密码信息等核心数据
"""

import os
import sys
import json
import mysql.connector
from datetime import datetime
import hashlib
import gzip

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def print_status(message, status="INFO"):
    """打印状态信息"""
    colors = {
        "INFO": "\033[0;34m",      # 蓝色
        "SUCCESS": "\033[0;32m",   # 绿色
        "WARNING": "\033[1;33m",   # 黄色
        "ERROR": "\033[0;31m",     # 红色
        "BACKUP": "\033[1;35m"     # 紫色
    }
    reset = "\033[0m"
    
    prefix = {
        "INFO": "ℹ️ ",
        "SUCCESS": "✅",
        "WARNING": "⚠️ ",
        "ERROR": "❌",
        "BACKUP": "💾"
    }
    
    color = colors.get(status, colors["INFO"])
    icon = prefix.get(status, "")
    print(f"{color}{icon} {message}{reset}")

def get_database_config():
    """获取数据库配置"""
    try:
        # 尝试从不同的配置文件读取
        config = None
        if os.path.exists('config_local.py'):
            from config_local import Config
            config = Config()
        elif os.path.exists('config.py'):
            from config import Config
            config = Config()

        if config and hasattr(config, 'SQLALCHEMY_DATABASE_URI'):
            # 解析数据库URL
            db_url = config.SQLALCHEMY_DATABASE_URI
            if db_url.startswith('mysql://'):
                # mysql://username:password@host:port/database
                parts = db_url.replace('mysql://', '').split('/')
                db_name = parts[1] if len(parts) > 1 else 'warehouse_db'

                auth_host = parts[0].split('@')
                host_port = auth_host[1] if len(auth_host) > 1 else 'localhost:3306'
                host = host_port.split(':')[0]
                port = int(host_port.split(':')[1]) if ':' in host_port else 3306

                if len(auth_host) > 1:
                    user_pass = auth_host[0].split(':')
                    user = user_pass[0] if len(user_pass) > 0 else 'root'
                    password = user_pass[1] if len(user_pass) > 1 else ''
                else:
                    user = 'root'
                    password = ''

                return {
                    'host': host,
                    'port': port,
                    'user': user,
                    'password': password,
                    'database': db_name
                }

        # 如果无法从配置文件读取，使用默认配置
        raise Exception("无法从配置文件读取数据库配置")

    except Exception as e:
        print_status(f"读取配置失败，使用默认配置: {e}", "WARNING")
        return {
            'host': 'localhost',
            'port': 3306,
            'user': 'root',
            'password': '',
            'database': 'warehouse_db'
        }

def connect_database(config):
    """连接数据库"""
    try:
        conn = mysql.connector.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password'],
            database=config['database'],
            charset='utf8mb4'
        )
        return conn
    except mysql.connector.Error as e:
        print_status(f"数据库连接失败: {e}", "ERROR")
        return None

def backup_table_data(cursor, table_name, columns=None):
    """备份表数据"""
    try:
        if columns:
            query = f"SELECT {', '.join(columns)} FROM {table_name}"
        else:
            query = f"SELECT * FROM {table_name}"
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        # 获取列名
        if columns:
            column_names = columns
        else:
            cursor.execute(f"DESCRIBE {table_name}")
            column_names = [row[0] for row in cursor.fetchall()]
        
        # 转换为字典列表
        data = []
        for row in rows:
            row_dict = {}
            for i, value in enumerate(row):
                if isinstance(value, datetime):
                    row_dict[column_names[i]] = value.isoformat()
                else:
                    row_dict[column_names[i]] = value
            data.append(row_dict)
        
        return {
            'table': table_name,
            'columns': column_names,
            'data': data,
            'count': len(data)
        }
    except mysql.connector.Error as e:
        print_status(f"备份表 {table_name} 失败: {e}", "ERROR")
        return None

def create_backup():
    """创建数据备份"""
    print_status("开始备份核心数据...", "BACKUP")
    
    # 获取数据库配置
    db_config = get_database_config()
    print_status(f"连接数据库: {db_config['host']}:{db_config['port']}/{db_config['database']}", "INFO")
    
    # 连接数据库
    conn = connect_database(db_config)
    if not conn:
        return False
    
    cursor = conn.cursor()
    
    # 备份数据
    backup_data = {
        'backup_info': {
            'timestamp': datetime.now().isoformat(),
            'version': '1.0',
            'description': '仓储管理系统核心数据备份',
            'database': db_config['database']
        },
        'tables': {}
    }
    
    # 1. 备份收货人信息
    print_status("备份收货人信息...", "BACKUP")
    receivers_data = backup_table_data(cursor, 'receivers')
    if receivers_data:
        backup_data['tables']['receivers'] = receivers_data
        print_status(f"收货人信息备份完成: {receivers_data['count']} 条记录", "SUCCESS")
    
    # 2. 备份仓库信息
    print_status("备份仓库信息...", "BACKUP")
    warehouses_data = backup_table_data(cursor, 'warehouses')
    if warehouses_data:
        backup_data['tables']['warehouses'] = warehouses_data
        print_status(f"仓库信息备份完成: {warehouses_data['count']} 条记录", "SUCCESS")
    
    # 3. 备份用户信息（包含密码）
    print_status("备份用户信息...", "BACKUP")
    users_data = backup_table_data(cursor, 'users')
    if users_data:
        backup_data['tables']['users'] = users_data
        print_status(f"用户信息备份完成: {users_data['count']} 条记录", "SUCCESS")
    
    # 4. 备份角色信息
    print_status("备份角色信息...", "BACKUP")
    roles_data = backup_table_data(cursor, 'roles')
    if roles_data:
        backup_data['tables']['roles'] = roles_data
        print_status(f"角色信息备份完成: {roles_data['count']} 条记录", "SUCCESS")
    
    # 5. 备份权限信息
    print_status("备份权限信息...", "BACKUP")
    permissions_data = backup_table_data(cursor, 'permissions')
    if permissions_data:
        backup_data['tables']['permissions'] = permissions_data
        print_status(f"权限信息备份完成: {permissions_data['count']} 条记录", "SUCCESS")
    
    # 6. 备份用户角色关联
    print_status("备份用户角色关联...", "BACKUP")
    user_roles_data = backup_table_data(cursor, 'user_roles')
    if user_roles_data:
        backup_data['tables']['user_roles'] = user_roles_data
        print_status(f"用户角色关联备份完成: {user_roles_data['count']} 条记录", "SUCCESS")
    
    # 7. 备份角色权限关联
    print_status("备份角色权限关联...", "BACKUP")
    role_permissions_data = backup_table_data(cursor, 'role_permissions')
    if role_permissions_data:
        backup_data['tables']['role_permissions'] = role_permissions_data
        print_status(f"角色权限关联备份完成: {role_permissions_data['count']} 条记录", "SUCCESS")
    
    # 关闭数据库连接
    cursor.close()
    conn.close()
    
    # 保存备份文件
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f'essential_data_backup_{timestamp}.json'
    
    try:
        with open(backup_filename, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
        
        # 创建压缩版本
        compressed_filename = f'essential_data_backup_{timestamp}.json.gz'
        with open(backup_filename, 'rb') as f_in:
            with gzip.open(compressed_filename, 'wb') as f_out:
                f_out.writelines(f_in)
        
        # 计算文件大小和校验和
        file_size = os.path.getsize(backup_filename)
        compressed_size = os.path.getsize(compressed_filename)
        
        with open(backup_filename, 'rb') as f:
            file_hash = hashlib.md5(f.read()).hexdigest()
        
        print_status(f"备份文件已保存: {backup_filename}", "SUCCESS")
        print_status(f"压缩备份文件: {compressed_filename}", "SUCCESS")
        print_status(f"文件大小: {file_size:,} 字节 (压缩后: {compressed_size:,} 字节)", "INFO")
        print_status(f"文件校验和: {file_hash}", "INFO")
        
        # 创建备份信息文件
        backup_info = {
            'backup_file': backup_filename,
            'compressed_file': compressed_filename,
            'timestamp': timestamp,
            'file_size': file_size,
            'compressed_size': compressed_size,
            'md5_hash': file_hash,
            'tables_count': len(backup_data['tables']),
            'total_records': sum(table['count'] for table in backup_data['tables'].values())
        }
        
        info_filename = f'backup_info_{timestamp}.json'
        with open(info_filename, 'w', encoding='utf-8') as f:
            json.dump(backup_info, f, ensure_ascii=False, indent=2)
        
        print_status(f"备份信息文件: {info_filename}", "SUCCESS")
        return True
        
    except Exception as e:
        print_status(f"保存备份文件失败: {e}", "ERROR")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("💾 仓储管理系统 - 核心数据备份工具")
    print("=" * 60)
    print()
    
    print_status("备份内容包括:", "INFO")
    print("  📋 收货人信息 (receivers)")
    print("  🏢 仓库信息 (warehouses)")
    print("  👤 用户信息 (users)")
    print("  🔐 角色信息 (roles)")
    print("  🛡️  权限信息 (permissions)")
    print("  🔗 用户角色关联 (user_roles)")
    print("  🔗 角色权限关联 (role_permissions)")
    print()
    
    success = create_backup()
    
    if success:
        print()
        print_status("数据备份完成！", "SUCCESS")
        print()
        print("📋 使用说明:")
        print("1. 将备份文件复制到服务器")
        print("2. 运行 restore_essential_data.py 脚本导入数据")
        print("3. 验证数据完整性")
    else:
        print_status("数据备份失败！", "ERROR")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
