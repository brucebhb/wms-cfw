#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据备份管理器
"""

import os
import shutil
import subprocess
import gzip
import json
from datetime import datetime, timedelta
from flask import current_app
from app import db
from app.models import InboundRecord, Inventory, OutboundRecord, TransitCargo, Warehouse, User
import tempfile
import threading
# import schedule  # 暂时移除schedule依赖
import time

class BackupManager:
    """数据备份管理器"""
    
    def __init__(self):
        self.backup_dir = current_app.config.get('BACKUP_DIR', 'backups')
        self.max_backups = current_app.config.get('MAX_BACKUPS', 30)  # 保留30天的备份
        self.ensure_backup_directory()
    
    def ensure_backup_directory(self):
        """确保备份目录存在"""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
            current_app.logger.info(f"创建备份目录: {self.backup_dir}")
    
    def create_database_backup(self, backup_name=None):
        """创建数据库备份"""
        try:
            if not backup_name:
                backup_name = f"db_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            backup_file = os.path.join(self.backup_dir, f"{backup_name}.sql")
            
            # 获取数据库配置
            db_config = current_app.config.get('SQLALCHEMY_DATABASE_URI')
            
            if db_config.startswith('mysql'):
                success = self._backup_mysql(db_config, backup_file)
            elif db_config.startswith('sqlite'):
                success = self._backup_sqlite(db_config, backup_file)
            else:
                current_app.logger.error(f"不支持的数据库类型: {db_config}")
                return False
            
            if success:
                # 压缩备份文件
                compressed_file = f"{backup_file}.gz"
                with open(backup_file, 'rb') as f_in:
                    with gzip.open(compressed_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                
                # 删除未压缩的文件
                os.remove(backup_file)
                
                current_app.logger.info(f"数据库备份完成: {compressed_file}")
                return compressed_file
            
            return False
            
        except Exception as e:
            current_app.logger.error(f"数据库备份失败: {str(e)}")
            return False
    
    def _backup_mysql(self, db_config, backup_file):
        """备份MySQL数据库"""
        try:
            # 解析数据库连接字符串
            # mysql://username:password@host:port/database
            import re
            match = re.match(r'mysql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', db_config)
            if not match:
                current_app.logger.error("无法解析MySQL连接字符串")
                return False
            
            username, password, host, port, database = match.groups()
            
            # 使用mysqldump命令
            cmd = [
                'mysqldump',
                f'--host={host}',
                f'--port={port}',
                f'--user={username}',
                f'--password={password}',
                '--single-transaction',
                '--routines',
                '--triggers',
                database
            ]
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)
            
            if result.returncode == 0:
                current_app.logger.info(f"MySQL备份成功: {backup_file}")
                return True
            else:
                current_app.logger.error(f"MySQL备份失败: {result.stderr}")
                return False
                
        except Exception as e:
            current_app.logger.error(f"MySQL备份异常: {str(e)}")
            return False
    
    def _backup_sqlite(self, db_config, backup_file):
        """备份SQLite数据库"""
        try:
            # 解析SQLite文件路径
            db_path = db_config.replace('sqlite:///', '')
            
            if os.path.exists(db_path):
                shutil.copy2(db_path, backup_file)
                current_app.logger.info(f"SQLite备份成功: {backup_file}")
                return True
            else:
                current_app.logger.error(f"SQLite数据库文件不存在: {db_path}")
                return False
                
        except Exception as e:
            current_app.logger.error(f"SQLite备份异常: {str(e)}")
            return False
    
    def create_data_export(self, tables=None, backup_name=None):
        """创建数据导出（JSON格式）"""
        try:
            if not backup_name:
                backup_name = f"data_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            if not tables:
                tables = ['inbound_record', 'inventory', 'outbound_record', 'transit_cargo', 'warehouse', 'user']
            
            export_data = {}
            
            # 导出各表数据
            table_models = {
                'inbound_record': InboundRecord,
                'inventory': Inventory,
                'outbound_record': OutboundRecord,
                'transit_cargo': TransitCargo,
                'warehouse': Warehouse,
                'user': User
            }
            
            for table_name in tables:
                if table_name in table_models:
                    model = table_models[table_name]
                    records = model.query.all()
                    
                    table_data = []
                    for record in records:
                        record_dict = {}
                        for column in model.__table__.columns:
                            value = getattr(record, column.name)
                            if isinstance(value, datetime):
                                value = value.isoformat()
                            record_dict[column.name] = value
                        table_data.append(record_dict)
                    
                    export_data[table_name] = table_data
                    current_app.logger.info(f"导出表 {table_name}: {len(table_data)} 条记录")
            
            # 保存到文件
            export_file = os.path.join(self.backup_dir, f"{backup_name}.json")
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            # 压缩文件
            compressed_file = f"{export_file}.gz"
            with open(export_file, 'rb') as f_in:
                with gzip.open(compressed_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            os.remove(export_file)
            
            current_app.logger.info(f"数据导出完成: {compressed_file}")
            return compressed_file
            
        except Exception as e:
            current_app.logger.error(f"数据导出失败: {str(e)}")
            return False
    
    def cleanup_old_backups(self):
        """清理旧备份文件"""
        try:
            if not os.path.exists(self.backup_dir):
                return
            
            cutoff_date = datetime.now() - timedelta(days=self.max_backups)
            deleted_count = 0
            
            for filename in os.listdir(self.backup_dir):
                file_path = os.path.join(self.backup_dir, filename)
                
                if os.path.isfile(file_path):
                    file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                    
                    if file_time < cutoff_date:
                        os.remove(file_path)
                        deleted_count += 1
                        current_app.logger.info(f"删除旧备份文件: {filename}")
            
            current_app.logger.info(f"清理完成，删除了 {deleted_count} 个旧备份文件")
            
        except Exception as e:
            current_app.logger.error(f"清理旧备份失败: {str(e)}")
    
    def restore_from_backup(self, backup_file):
        """从备份恢复数据"""
        try:
            if not os.path.exists(backup_file):
                current_app.logger.error(f"备份文件不存在: {backup_file}")
                return False
            
            # 根据文件扩展名判断备份类型
            if backup_file.endswith('.sql.gz'):
                return self._restore_sql_backup(backup_file)
            elif backup_file.endswith('.json.gz'):
                return self._restore_json_backup(backup_file)
            else:
                current_app.logger.error(f"不支持的备份文件格式: {backup_file}")
                return False
                
        except Exception as e:
            current_app.logger.error(f"恢复备份失败: {str(e)}")
            return False
    
    def _restore_sql_backup(self, backup_file):
        """恢复SQL备份"""
        try:
            # 解压文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as temp_file:
                with gzip.open(backup_file, 'rt', encoding='utf-8') as f:
                    temp_file.write(f.read())
                temp_sql_file = temp_file.name
            
            # 执行SQL文件
            db_config = current_app.config.get('SQLALCHEMY_DATABASE_URI')
            
            if db_config.startswith('mysql'):
                success = self._restore_mysql(db_config, temp_sql_file)
            elif db_config.startswith('sqlite'):
                success = self._restore_sqlite(db_config, temp_sql_file)
            else:
                success = False
            
            # 清理临时文件
            os.unlink(temp_sql_file)
            
            return success
            
        except Exception as e:
            current_app.logger.error(f"恢复SQL备份异常: {str(e)}")
            return False
    
    def _restore_json_backup(self, backup_file):
        """恢复JSON备份"""
        try:
            # 解压并读取数据
            with gzip.open(backup_file, 'rt', encoding='utf-8') as f:
                export_data = json.load(f)
            
            # 清空现有数据（谨慎操作）
            current_app.logger.warning("开始清空现有数据...")
            
            # 按依赖关系顺序删除
            db.session.execute('DELETE FROM outbound_record')
            db.session.execute('DELETE FROM transit_cargo')
            db.session.execute('DELETE FROM inventory')
            db.session.execute('DELETE FROM inbound_record')
            db.session.commit()
            
            # 恢复数据
            table_models = {
                'warehouse': Warehouse,
                'user': User,
                'inbound_record': InboundRecord,
                'inventory': Inventory,
                'outbound_record': OutboundRecord,
                'transit_cargo': TransitCargo
            }
            
            for table_name, model in table_models.items():
                if table_name in export_data:
                    records = export_data[table_name]
                    
                    for record_data in records:
                        # 转换日期字段
                        for column in model.__table__.columns:
                            if column.name in record_data and record_data[column.name]:
                                if 'time' in column.name.lower() or 'date' in column.name.lower():
                                    try:
                                        record_data[column.name] = datetime.fromisoformat(record_data[column.name])
                                    except:
                                        pass
                        
                        record = model(**record_data)
                        db.session.add(record)
                    
                    db.session.commit()
                    current_app.logger.info(f"恢复表 {table_name}: {len(records)} 条记录")
            
            current_app.logger.info("JSON备份恢复完成")
            return True
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"恢复JSON备份异常: {str(e)}")
            return False
    
    def schedule_automatic_backup(self):
        """安排自动备份（简化版本，不使用schedule库）"""
        def run_backup():
            current_app.logger.info("开始自动备份...")

            # 创建数据库备份
            db_backup = self.create_database_backup()
            if db_backup:
                current_app.logger.info(f"自动数据库备份完成: {db_backup}")

            # 创建数据导出
            data_export = self.create_data_export()
            if data_export:
                current_app.logger.info(f"自动数据导出完成: {data_export}")

            # 清理旧备份
            self.cleanup_old_backups()

            current_app.logger.info("自动备份任务完成")

        # 简化版本：立即执行一次备份
        try:
            run_backup()
        except Exception as e:
            current_app.logger.error(f"自动备份失败: {str(e)}")

        current_app.logger.info("备份任务已执行")

# 全局备份管理器实例
backup_manager = None

def get_backup_manager():
    """获取备份管理器实例"""
    global backup_manager
    if backup_manager is None:
        backup_manager = BackupManager()
    return backup_manager
