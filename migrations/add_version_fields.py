#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移脚本：添加版本字段
为关键表添加版本字段以支持乐观锁
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_version_fields():
    """为关键表添加版本字段"""
    app = create_app()
    
    with app.app_context():
        try:
            # 检查并添加版本字段
            tables_to_update = [
                ('inbound_record', 'version'),
                ('outbound_record', 'version'),
                # inventory 表已经有版本字段了
            ]
            
            for table_name, column_name in tables_to_update:
                try:
                    # 检查字段是否已存在
                    check_sql = f"""
                    SELECT COUNT(*) 
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_SCHEMA = DATABASE() 
                    AND TABLE_NAME = '{table_name}' 
                    AND COLUMN_NAME = '{column_name}'
                    """
                    
                    result = db.session.execute(text(check_sql)).scalar()
                    
                    if result == 0:
                        # 字段不存在，添加它
                        add_sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} INTEGER DEFAULT 1 COMMENT '版本号，用于乐观锁控制'"
                        db.session.execute(text(add_sql))
                        logger.info(f"已为表 {table_name} 添加字段 {column_name}")
                    else:
                        logger.info(f"表 {table_name} 的字段 {column_name} 已存在，跳过")
                
                except Exception as e:
                    logger.error(f"处理表 {table_name} 时出错: {str(e)}")
                    continue
            
            # 提交更改
            db.session.commit()
            logger.info("版本字段添加完成")
            
            # 更新现有记录的版本号
            update_existing_records()
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"添加版本字段失败: {str(e)}")
            raise

def update_existing_records():
    """更新现有记录的版本号"""
    try:
        # 更新入库记录
        update_sql = "UPDATE inbound_record SET version = 1 WHERE version IS NULL OR version = 0"
        result = db.session.execute(text(update_sql))
        logger.info(f"更新了 {result.rowcount} 条入库记录的版本号")
        
        # 更新出库记录
        update_sql = "UPDATE outbound_record SET version = 1 WHERE version IS NULL OR version = 0"
        result = db.session.execute(text(update_sql))
        logger.info(f"更新了 {result.rowcount} 条出库记录的版本号")
        
        # 更新库存记录
        update_sql = "UPDATE inventory SET version = 1 WHERE version IS NULL OR version = 0"
        result = db.session.execute(text(update_sql))
        logger.info(f"更新了 {result.rowcount} 条库存记录的版本号")
        
        db.session.commit()
        logger.info("现有记录版本号更新完成")
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新现有记录版本号失败: {str(e)}")
        raise

def create_security_indexes():
    """创建安全相关的索引"""
    app = create_app()

    with app.app_context():
        try:
            indexes_to_create = [
            ("idx_inbound_customer_time", "CREATE INDEX idx_inbound_customer_time ON inbound_record(customer_name, inbound_time)"),
            ("idx_outbound_customer_time", "CREATE INDEX idx_outbound_customer_time ON outbound_record(customer_name, outbound_time)"),
            ("idx_inventory_customer", "CREATE INDEX idx_inventory_customer ON inventory(customer_name)"),
            ("idx_inbound_identification", "CREATE INDEX idx_inbound_identification ON inbound_record(identification_code)"),
            ("idx_outbound_identification", "CREATE INDEX idx_outbound_identification ON outbound_record(identification_code)"),
            ("idx_inventory_identification", "CREATE INDEX idx_inventory_identification ON inventory(identification_code)"),
            ]

            for index_name, index_sql in indexes_to_create:
                try:
                    # 检查索引是否已存在
                    check_sql = f"""
                    SELECT COUNT(*)
                    FROM INFORMATION_SCHEMA.STATISTICS
                    WHERE TABLE_SCHEMA = DATABASE()
                    AND INDEX_NAME = '{index_name}'
                    """

                    result = db.session.execute(text(check_sql)).scalar()

                    if result == 0:
                        db.session.execute(text(index_sql))
                        logger.info(f"创建索引: {index_name}")
                    else:
                        logger.info(f"索引 {index_name} 已存在，跳过")

                except Exception as e:
                    if 'duplicate key name' not in str(e).lower():
                        logger.warning(f"创建索引 {index_name} 失败: {str(e)}")
        
            db.session.commit()
            logger.info("安全索引创建完成")

        except Exception as e:
            db.session.rollback()
            logger.error(f"创建安全索引失败: {str(e)}")

def verify_migration():
    """验证迁移结果"""
    app = create_app()

    with app.app_context():
        try:
            # 检查版本字段
            tables_to_check = ['inbound_record', 'outbound_record', 'inventory']
        
        for table_name in tables_to_check:
            check_sql = f"""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = '{table_name}' 
            AND COLUMN_NAME = 'version'
            """
            
            result = db.session.execute(text(check_sql)).scalar()
            if result > 0:
                logger.info(f"✅ 表 {table_name} 的版本字段验证通过")
            else:
                logger.error(f"❌ 表 {table_name} 缺少版本字段")
        
        # 检查版本号数据
        for table_name in tables_to_check:
            count_sql = f"SELECT COUNT(*) FROM {table_name} WHERE version IS NULL OR version = 0"
            result = db.session.execute(text(count_sql)).scalar()
            if result == 0:
                logger.info(f"✅ 表 {table_name} 的版本号数据验证通过")
            else:
                logger.warning(f"⚠️ 表 {table_name} 有 {result} 条记录的版本号为空或0")
        
            logger.info("迁移验证完成")

        except Exception as e:
            logger.error(f"迁移验证失败: {str(e)}")

if __name__ == '__main__':
    print("开始数据库迁移：添加版本字段...")
    
    try:
        # 1. 添加版本字段
        add_version_fields()
        
        # 2. 创建安全索引
        create_security_indexes()
        
        # 3. 验证迁移结果
        verify_migration()
        
        print("✅ 数据库迁移完成！")
        print("已添加版本字段以支持乐观锁")
        print("已创建性能优化索引")
        
    except Exception as e:
        print(f"❌ 数据库迁移失败: {str(e)}")
        sys.exit(1)
