#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from app import create_app, db
from sqlalchemy import text
import sys

app = create_app()
with app.app_context():
    print('=== 检查inventory表字段 ===')
    
    try:
        # 检查inventory_type字段是否存在
        result = db.session.execute(text("""
            SELECT COUNT(*) as has_inventory_type
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'inventory' 
                AND TABLE_SCHEMA = DATABASE()
                AND COLUMN_NAME = 'inventory_type'
        """)).fetchone()
        
        has_inventory_type = result[0] if result else 0
        print(f'inventory_type字段存在: {has_inventory_type > 0}')
        
        if has_inventory_type == 0:
            print('❌ inventory_type字段不存在，需要添加')
            
            # 添加inventory_type字段
            try:
                db.session.execute(text("""
                    ALTER TABLE inventory 
                    ADD COLUMN inventory_type VARCHAR(20) DEFAULT 'normal' 
                    COMMENT '库存类型'
                """))
                db.session.commit()
                print('✅ 成功添加inventory_type字段')
            except Exception as e:
                print(f'❌ 添加inventory_type字段失败: {e}')
                db.session.rollback()
        else:
            print('✅ inventory_type字段已存在')
        
        # 检查所有inventory表的字段
        print('\n=== inventory表所有字段 ===')
        result = db.session.execute(text("""
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'inventory' 
                AND TABLE_SCHEMA = DATABASE()
            ORDER BY ORDINAL_POSITION
        """)).fetchall()
        
        for row in result:
            column_name, data_type, is_nullable, column_default = row
            print(f'{column_name}: {data_type} (nullable: {is_nullable}, default: {column_default})')
            
    except Exception as e:
        print(f'❌ 检查失败: {e}')
        sys.exit(1)
    
    print('\n=== 检查完成 ===')
