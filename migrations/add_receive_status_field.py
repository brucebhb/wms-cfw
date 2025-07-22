#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移脚本：为 ReceiveRecord 表添加 receive_status 字段
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import ReceiveRecord
from sqlalchemy import text

def add_receive_status_field():
    """为 ReceiveRecord 表添加 receive_status 字段"""
    app = create_app()
    
    with app.app_context():
        try:
            # 检查字段是否已存在
            with db.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT COUNT(*) as count
                    FROM information_schema.columns
                    WHERE table_name = 'receive_records'
                    AND column_name = 'receive_status'
                    AND table_schema = DATABASE()
                """))

                field_exists = result.fetchone()[0] > 0

                if not field_exists:
                    print("正在添加 receive_status 字段...")

                    # 添加字段
                    conn.execute(text("""
                        ALTER TABLE receive_records
                        ADD COLUMN receive_status VARCHAR(20) DEFAULT '已接收'
                        COMMENT '接收状态：已接收/未接收'
                    """))

                    # 更新现有记录的状态为"已接收"
                    conn.execute(text("""
                        UPDATE receive_records
                        SET receive_status = '已接收'
                        WHERE receive_status IS NULL
                    """))

                    conn.commit()

                    print("✓ receive_status 字段添加成功")
                    print("✓ 现有记录状态已更新为'已接收'")

                else:
                    print("receive_status 字段已存在，跳过添加")
                
        except Exception as e:
            print(f"添加字段时出错: {str(e)}")
            db.session.rollback()
            return False
            
        return True

if __name__ == '__main__':
    print("开始数据库迁移：添加接收状态字段")
    success = add_receive_status_field()
    if success:
        print("数据库迁移完成")
    else:
        print("数据库迁移失败")
        sys.exit(1)
