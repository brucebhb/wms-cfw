#!/usr/bin/env python3
"""
MySQL数据库备份工具
支持完整备份、增量备份、数据恢复等功能
使用Python直接连接MySQL进行备份
"""

import os
import sys
import json
import gzip
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from config import Config
import pymysql
import pymysql.cursors

class MySQLBackup:
    def __init__(self):
        self.config = Config()
        self.backup_dir = Path('mysql_backups')
        self.backup_dir.mkdir(exist_ok=True)
        
        # MySQL连接参数
        self.host = self.config.MYSQL_HOST
        self.port = self.config.MYSQL_PORT
        self.user = self.config.MYSQL_USER
        self.password = self.config.MYSQL_PASSWORD
        self.database = self.config.MYSQL_DATABASE
        
    def get_timestamp(self):
        """获取时间戳"""
        return datetime.now().strftime('%Y%m%d_%H%M%S')
    
    def format_size(self, size_bytes):
        """格式化文件大小"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
    
    def get_connection(self):
        """获取数据库连接"""
        try:
            connection = pymysql.connect(
                host=self.host,
                port=int(self.port),
                user=self.user,
                password=self.password,
                database=self.database,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            return connection
        except Exception as e:
            print(f"❌ 数据库连接失败: {str(e)}")
            return None
    
    def test_connection(self):
        """测试数据库连接"""
        connection = self.get_connection()
        if connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
                    if result:
                        print("✅ 数据库连接测试成功")
                        return True
            except Exception as e:
                print(f"❌ 数据库查询失败: {str(e)}")
            finally:
                connection.close()

        return False
    
    def get_database_info(self):
        """获取数据库信息"""
        connection = self.get_connection()
        if not connection:
            return {'table_count': 0, 'total_rows': 0}

        try:
            with connection.cursor() as cursor:
                # 获取表信息
                cursor.execute("SHOW TABLE STATUS")
                tables = cursor.fetchall()

                table_count = len(tables)
                total_rows = sum(table.get('Rows', 0) or 0 for table in tables)

                return {
                    'table_count': table_count,
                    'total_rows': total_rows,
                    'tables': [table['Name'] for table in tables]
                }

        except Exception as e:
            print(f"⚠️ 获取数据库信息失败: {str(e)}")
            return {'table_count': 0, 'total_rows': 0}
        finally:
            connection.close()
    
    def create_backup(self, compress=True):
        """创建数据库备份"""
        if not self.test_connection():
            return False

        timestamp = self.get_timestamp()
        backup_filename = f'warehouse_db_backup_{timestamp}.sql'

        if compress:
            backup_filename += '.gz'

        backup_path = self.backup_dir / backup_filename

        print(f"🔄 开始备份数据库: {self.database}")
        print(f"📁 备份文件: {backup_path}")

        connection = self.get_connection()
        if not connection:
            return False

        try:
            # 获取数据库信息
            db_info = self.get_database_info()

            # 创建SQL备份内容
            sql_content = self.generate_sql_backup(connection, db_info)

            # 写入备份文件
            if compress:
                with gzip.open(backup_path, 'wt', encoding='utf-8') as f:
                    f.write(sql_content)
            else:
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(sql_content)

            # 获取文件大小
            file_size = backup_path.stat().st_size

            # 创建备份信息文件
            backup_info = {
                'timestamp': timestamp,
                'database': self.database,
                'backup_file': str(backup_path),
                'compressed': compress,
                'file_size': file_size,
                'table_count': db_info['table_count'],
                'total_rows': db_info['total_rows'],
                'backup_time': datetime.now().isoformat(),
                'tables': db_info.get('tables', [])
            }

            info_file = self.backup_dir / f'backup_info_{timestamp}.json'
            with open(info_file, 'w', encoding='utf-8') as f:
                json.dump(backup_info, f, indent=2, ensure_ascii=False)

            print(f"✅ 备份完成!")
            print(f"📊 文件大小: {self.format_size(file_size)}")
            print(f"📋 表数量: {db_info['table_count']}")
            print(f"📊 总记录数: {db_info['total_rows']}")
            print(f"📄 备份信息: {info_file}")

            return True

        except Exception as e:
            print(f"❌ 备份过程中出现异常: {str(e)}")
            return False
        finally:
            connection.close()
    
    def generate_sql_backup(self, connection, db_info):
        """生成SQL备份内容"""
        sql_lines = []

        # 添加备份头信息
        sql_lines.append("-- MySQL数据库备份")
        sql_lines.append(f"-- 数据库: {self.database}")
        sql_lines.append(f"-- 备份时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        sql_lines.append(f"-- 表数量: {db_info['table_count']}")
        sql_lines.append(f"-- 总记录数: {db_info['total_rows']}")
        sql_lines.append("")
        sql_lines.append("SET FOREIGN_KEY_CHECKS=0;")
        sql_lines.append("SET SQL_MODE='NO_AUTO_VALUE_ON_ZERO';")
        sql_lines.append("")

        try:
            with connection.cursor() as cursor:
                # 获取所有表
                cursor.execute("SHOW TABLES")
                tables = [row[f'Tables_in_{self.database}'] for row in cursor.fetchall()]

                for table_name in tables:
                    print(f"  📋 备份表: {table_name}")

                    # 获取表结构
                    cursor.execute(f"SHOW CREATE TABLE `{table_name}`")
                    create_table = cursor.fetchone()

                    sql_lines.append(f"-- 表结构: {table_name}")
                    sql_lines.append(f"DROP TABLE IF EXISTS `{table_name}`;")
                    sql_lines.append(create_table['Create Table'] + ";")
                    sql_lines.append("")

                    # 获取表数据
                    cursor.execute(f"SELECT * FROM `{table_name}`")
                    rows = cursor.fetchall()

                    if rows:
                        sql_lines.append(f"-- 表数据: {table_name}")

                        # 获取列名
                        cursor.execute(f"DESCRIBE `{table_name}`")
                        columns = [col['Field'] for col in cursor.fetchall()]

                        # 分批插入数据
                        batch_size = 1000
                        for i in range(0, len(rows), batch_size):
                            batch = rows[i:i + batch_size]

                            values_list = []
                            for row in batch:
                                values = []
                                for col in columns:
                                    value = row[col]
                                    if value is None:
                                        values.append('NULL')
                                    elif isinstance(value, str):
                                        # 转义字符串
                                        escaped = value.replace('\\', '\\\\').replace("'", "\\'").replace('\n', '\\n').replace('\r', '\\r')
                                        values.append(f"'{escaped}'")
                                    elif isinstance(value, (int, float)):
                                        values.append(str(value))
                                    elif isinstance(value, datetime):
                                        values.append(f"'{value.strftime('%Y-%m-%d %H:%M:%S')}'")
                                    else:
                                        values.append(f"'{str(value)}'")

                                values_list.append(f"({','.join(values)})")

                            column_names = ','.join(f'`{col}`' for col in columns)
                            sql_lines.append(f"INSERT INTO `{table_name}` ({column_names}) VALUES")
                            sql_lines.append(',\n'.join(values_list) + ";")

                        sql_lines.append("")

                    sql_lines.append("")

        except Exception as e:
            print(f"⚠️ 生成备份SQL时出错: {str(e)}")
            raise

        sql_lines.append("SET FOREIGN_KEY_CHECKS=1;")
        return '\n'.join(sql_lines)
    
    def list_backups(self):
        """列出所有备份"""
        backups = []
        
        for info_file in self.backup_dir.glob('backup_info_*.json'):
            try:
                with open(info_file, 'r', encoding='utf-8') as f:
                    backup_info = json.load(f)
                    
                # 检查备份文件是否存在
                backup_file = Path(backup_info['backup_file'])
                if backup_file.exists():
                    backup_info['file_exists'] = True
                    backup_info['current_size'] = backup_file.stat().st_size
                else:
                    backup_info['file_exists'] = False
                    backup_info['current_size'] = 0
                
                backups.append(backup_info)
                
            except Exception as e:
                print(f"⚠️ 读取备份信息失败 {info_file}: {str(e)}")
        
        return sorted(backups, key=lambda x: x['timestamp'], reverse=True)
    
    def clean_old_backups(self, keep_days=7):
        """清理旧备份"""
        cutoff_date = datetime.now() - timedelta(days=keep_days)
        deleted_count = 0
        
        print(f"🧹 清理 {keep_days} 天前的备份文件...")
        
        for info_file in self.backup_dir.glob('backup_info_*.json'):
            try:
                with open(info_file, 'r', encoding='utf-8') as f:
                    backup_info = json.load(f)
                
                backup_time = datetime.fromisoformat(backup_info['backup_time'])
                
                if backup_time < cutoff_date:
                    # 删除备份文件
                    backup_file = Path(backup_info['backup_file'])
                    if backup_file.exists():
                        backup_file.unlink()
                        print(f"  🗑️ 删除备份文件: {backup_file.name}")
                    
                    # 删除信息文件
                    info_file.unlink()
                    print(f"  🗑️ 删除信息文件: {info_file.name}")
                    
                    deleted_count += 1
                    
            except Exception as e:
                print(f"⚠️ 处理文件失败 {info_file}: {str(e)}")
        
        if deleted_count > 0:
            print(f"✅ 清理完成，删除了 {deleted_count} 个旧备份")
        else:
            print("✅ 没有需要清理的旧备份")

def main():
    """主函数"""
    backup_tool = MySQLBackup()
    
    if len(sys.argv) < 2:
        print("🗄️ MySQL数据库备份工具")
        print("=" * 50)
        print("用法:")
        print("  python mysql_backup.py create     - 创建数据库备份")
        print("  python mysql_backup.py list       - 列出所有备份")
        print("  python mysql_backup.py clean      - 清理7天前的备份")
        print("  python mysql_backup.py clean <天数> - 清理指定天数前的备份")
        print("  python mysql_backup.py test       - 测试数据库连接")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'create':
        backup_tool.create_backup()
    
    elif command == 'list':
        backups = backup_tool.list_backups()
        if not backups:
            print("❌ 没有找到备份文件")
            return
        
        print("📋 MySQL备份列表")
        print("=" * 90)
        print(f"{'序号':<4} {'备份时间':<20} {'表数量':<8} {'记录数':<10} {'文件大小':<12} {'状态':<8}")
        print("-" * 90)

        for i, backup in enumerate(backups, 1):
            backup_time = datetime.fromisoformat(backup['backup_time']).strftime('%Y-%m-%d %H:%M:%S')
            size_str = backup_tool.format_size(backup['current_size'])
            status = "✅ 正常" if backup['file_exists'] else "❌ 丢失"
            total_rows = backup.get('total_rows', 0)

            print(f"{i:<4} {backup_time:<20} {backup['table_count']:<8} {total_rows:<10} {size_str:<12} {status:<8}")
    
    elif command == 'clean':
        keep_days = 7
        if len(sys.argv) >= 3:
            try:
                keep_days = int(sys.argv[2])
            except ValueError:
                print("❌ 请输入有效的天数")
                return
        
        backup_tool.clean_old_backups(keep_days)
    
    elif command == 'test':
        backup_tool.test_connection()
    
    else:
        print(f"❌ 未知命令: {command}")
        print("使用 'python mysql_backup.py' 查看帮助")

if __name__ == '__main__':
    main()
