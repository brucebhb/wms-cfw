#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
仓储管理系统 - 核心数据恢复脚本
从备份文件恢复收货人信息、仓库管理信息、用户密码信息等核心数据
"""

import os
import sys
import json
import mysql.connector
from datetime import datetime
import gzip
import hashlib
import argparse

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def print_status(message, status="INFO"):
    """打印状态信息"""
    colors = {
        "INFO": "\033[0;34m",      # 蓝色
        "SUCCESS": "\033[0;32m",   # 绿色
        "WARNING": "\033[1;33m",   # 黄色
        "ERROR": "\033[0;31m",     # 红色
        "RESTORE": "\033[1;36m"    # 青色
    }
    reset = "\033[0m"
    
    prefix = {
        "INFO": "ℹ️ ",
        "SUCCESS": "✅",
        "WARNING": "⚠️ ",
        "ERROR": "❌",
        "RESTORE": "🔄"
    }
    
    color = colors.get(status, colors["INFO"])
    icon = prefix.get(status, "")
    print(f"{color}{icon} {message}{reset}")

def get_database_config(host=None, port=None, user=None, password=None, database=None):
    """获取数据库配置"""
    if all([host, user, database]):
        return {
            'host': host,
            'port': port or 3306,
            'user': user,
            'password': password or '',
            'database': database
        }
    
    try:
        # 尝试从配置文件读取
        if os.path.exists('config_production.py'):
            from config_production import Config
        elif os.path.exists('config_local.py'):
            from config_local import Config
        else:
            from config import Config
        
        config = Config()
        
        # 解析数据库URL
        db_url = config.SQLALCHEMY_DATABASE_URI
        if db_url.startswith('mysql://'):
            # mysql://username:password@host:port/database
            parts = db_url.replace('mysql://', '').split('/')
            db_name = parts[1] if len(parts) > 1 else 'warehouse_production'
            
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
        else:
            # 默认生产环境配置
            host = 'localhost'
            port = 3306
            user = 'warehouse_user'
            password = ''
            db_name = 'warehouse_production'
        
        return {
            'host': host,
            'port': port,
            'user': user,
            'password': password,
            'database': db_name
        }
    except Exception as e:
        print_status(f"读取配置失败，使用默认配置: {e}", "WARNING")
        return {
            'host': 'localhost',
            'port': 3306,
            'user': 'warehouse_user',
            'password': '',
            'database': 'warehouse_production'
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
            charset='utf8mb4',
            autocommit=False
        )
        return conn
    except mysql.connector.Error as e:
        print_status(f"数据库连接失败: {e}", "ERROR")
        return None

def load_backup_file(backup_file):
    """加载备份文件"""
    try:
        if backup_file.endswith('.gz'):
            with gzip.open(backup_file, 'rt', encoding='utf-8') as f:
                data = json.load(f)
        else:
            with open(backup_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        
        # 验证备份文件格式
        if 'backup_info' not in data or 'tables' not in data:
            raise ValueError("备份文件格式不正确")
        
        return data
    except Exception as e:
        print_status(f"加载备份文件失败: {e}", "ERROR")
        return None

def verify_backup_integrity(backup_file):
    """验证备份文件完整性"""
    if backup_file.endswith('.gz'):
        # 对于压缩文件，先解压再验证
        try:
            with gzip.open(backup_file, 'rb') as f:
                content = f.read()
            file_hash = hashlib.md5(content).hexdigest()
        except Exception as e:
            print_status(f"读取压缩文件失败: {e}", "ERROR")
            return False
    else:
        try:
            with open(backup_file, 'rb') as f:
                content = f.read()
            file_hash = hashlib.md5(content).hexdigest()
        except Exception as e:
            print_status(f"读取备份文件失败: {e}", "ERROR")
            return False
    
    print_status(f"文件校验和: {file_hash}", "INFO")
    return True

def clear_existing_data(cursor, table_name):
    """清空现有数据"""
    try:
        cursor.execute(f"DELETE FROM {table_name}")
        print_status(f"已清空表 {table_name} 的现有数据", "WARNING")
        return True
    except mysql.connector.Error as e:
        print_status(f"清空表 {table_name} 失败: {e}", "ERROR")
        return False

def restore_table_data(cursor, table_data, clear_existing=False):
    """恢复表数据"""
    table_name = table_data['table']
    columns = table_data['columns']
    data = table_data['data']

    print_status(f"恢复表 {table_name} 数据...", "RESTORE")

    if clear_existing:
        if not clear_existing_data(cursor, table_name):
            return False

    if not data:
        print_status(f"表 {table_name} 无数据需要恢复", "INFO")
        return True

    try:
        # 构建插入语句
        placeholders = ', '.join(['%s'] * len(columns))
        insert_query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"

        # 准备数据
        values_list = []
        for row in data:
            values = []
            for col in columns:
                value = row.get(col)
                # 处理日期时间字符串
                if isinstance(value, str) and 'T' in value and ':' in value:
                    try:
                        value = datetime.fromisoformat(value.replace('Z', '+00:00'))
                    except:
                        pass
                values.append(value)
            values_list.append(values)

        # 批量插入
        cursor.executemany(insert_query, values_list)

        print_status(f"表 {table_name} 恢复完成: {len(values_list)} 条记录", "SUCCESS")
        return True

    except mysql.connector.Error as e:
        print_status(f"恢复表 {table_name} 失败: {e}", "ERROR")
        return False

def restore_data(backup_file, db_config, clear_existing=False):
    """恢复数据"""
    print_status("开始恢复核心数据...", "RESTORE")

    # 验证备份文件
    if not verify_backup_integrity(backup_file):
        return False

    # 加载备份数据
    backup_data = load_backup_file(backup_file)
    if not backup_data:
        return False

    print_status(f"备份时间: {backup_data['backup_info']['timestamp']}", "INFO")
    print_status(f"备份描述: {backup_data['backup_info']['description']}", "INFO")

    # 连接数据库
    conn = connect_database(db_config)
    if not conn:
        return False

    cursor = conn.cursor()

    try:
        # 开始事务
        conn.start_transaction()

        # 按顺序恢复数据（考虑外键约束）
        restore_order = [
            'warehouses',      # 仓库信息（基础数据）
            'receivers',       # 收货人信息
            'roles',          # 角色信息
            'permissions',    # 权限信息
            'users',          # 用户信息
            'user_roles',     # 用户角色关联
            'role_permissions' # 角色权限关联
        ]

        success_count = 0
        total_records = 0

        for table_name in restore_order:
            if table_name in backup_data['tables']:
                table_data = backup_data['tables'][table_name]
                if restore_table_data(cursor, table_data, clear_existing):
                    success_count += 1
                    total_records += table_data['count']
                else:
                    raise Exception(f"恢复表 {table_name} 失败")

        # 提交事务
        conn.commit()

        print_status(f"数据恢复完成: {success_count} 个表，共 {total_records} 条记录", "SUCCESS")
        return True

    except Exception as e:
        # 回滚事务
        conn.rollback()
        print_status(f"数据恢复失败，已回滚: {e}", "ERROR")
        return False
    finally:
        cursor.close()
        conn.close()

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='仓储管理系统核心数据恢复工具')
    parser.add_argument('backup_file', help='备份文件路径')
    parser.add_argument('--host', help='数据库主机地址', default=None)
    parser.add_argument('--port', type=int, help='数据库端口', default=None)
    parser.add_argument('--user', help='数据库用户名', default=None)
    parser.add_argument('--password', help='数据库密码', default=None)
    parser.add_argument('--database', help='数据库名称', default=None)
    parser.add_argument('--clear', action='store_true', help='清空现有数据后恢复')

    args = parser.parse_args()

    print("=" * 60)
    print("🔄 仓储管理系统 - 核心数据恢复工具")
    print("=" * 60)
    print()

    # 检查备份文件
    if not os.path.exists(args.backup_file):
        print_status(f"备份文件不存在: {args.backup_file}", "ERROR")
        return 1

    print_status(f"备份文件: {args.backup_file}", "INFO")

    # 获取数据库配置
    db_config = get_database_config(
        args.host, args.port, args.user, args.password, args.database
    )

    print_status(f"目标数据库: {db_config['host']}:{db_config['port']}/{db_config['database']}", "INFO")

    if args.clear:
        print_status("警告: 将清空现有数据！", "WARNING")
        confirm = input("确认继续？(y/N): ")
        if confirm.lower() != 'y':
            print_status("操作已取消", "INFO")
            return 0

    # 恢复数据
    success = restore_data(args.backup_file, db_config, args.clear)

    if success:
        print()
        print_status("数据恢复完成！", "SUCCESS")
        print()
        print("📋 后续步骤:")
        print("1. 验证用户登录功能")
        print("2. 检查收货人信息")
        print("3. 确认仓库配置")
        print("4. 测试权限系统")
    else:
        print_status("数据恢复失败！", "ERROR")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
