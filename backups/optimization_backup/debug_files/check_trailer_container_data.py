#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据库中的车挂/柜号数据
"""

from app import create_app, db
from app.models import OutboundRecord
from sqlalchemy import text

def check_trailer_container_data():
    """检查数据库中的车挂/柜号数据"""
    app = create_app()
    
    with app.app_context():
        try:
            print("=== 检查OutboundRecord表中的车挂/柜号数据 ===")
            
            # 1. 检查字段是否存在
            print("1. 检查字段是否存在...")
            result = db.session.execute(text("""
                SELECT COLUMN_NAME, DATA_TYPE, COLUMN_COMMENT
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'outbound_record' 
                AND COLUMN_NAME IN ('trailer', 'container_number')
                ORDER BY COLUMN_NAME
            """))
            
            columns = result.fetchall()
            if columns:
                print("✅ 字段存在:")
                for col in columns:
                    print(f"  {col[0]}: {col[1]} - {col[2]}")
            else:
                print("❌ 字段不存在")
                return
            
            # 2. 检查有车挂/柜号数据的记录数量
            print("\n2. 检查有车挂/柜号数据的记录...")
            
            # 检查有车挂数据的记录
            result = db.session.execute(text("""
                SELECT COUNT(*) FROM outbound_record 
                WHERE trailer IS NOT NULL AND trailer != ''
            """))
            trailer_count = result.scalar()
            print(f"有车挂数据的记录: {trailer_count} 条")
            
            # 检查有柜号数据的记录
            result = db.session.execute(text("""
                SELECT COUNT(*) FROM outbound_record 
                WHERE container_number IS NOT NULL AND container_number != ''
            """))
            container_count = result.scalar()
            print(f"有柜号数据的记录: {container_count} 条")
            
            # 3. 显示最近的几条有车挂/柜号数据的记录
            print("\n3. 最近的车挂/柜号数据记录:")
            result = db.session.execute(text("""
                SELECT id, customer_name, identification_code, trailer, container_number, outbound_time
                FROM outbound_record 
                WHERE (trailer IS NOT NULL AND trailer != '') 
                   OR (container_number IS NOT NULL AND container_number != '')
                ORDER BY outbound_time DESC
                LIMIT 10
            """))
            
            records = result.fetchall()
            if records:
                print("ID | 客户名称 | 识别编码 | 车挂 | 柜号 | 出库时间")
                print("-" * 80)
                for record in records:
                    print(f"{record[0]} | {record[1]} | {record[2]} | {record[3] or ''} | {record[4] or ''} | {record[5]}")
            else:
                print("❌ 没有找到有车挂/柜号数据的记录")
            
            # 4. 检查最近的出库记录（不管是否有车挂/柜号）
            print("\n4. 最近的出库记录（前10条）:")
            result = db.session.execute(text("""
                SELECT id, customer_name, identification_code, trailer, container_number, outbound_time
                FROM outbound_record 
                ORDER BY outbound_time DESC
                LIMIT 10
            """))
            
            recent_records = result.fetchall()
            if recent_records:
                print("ID | 客户名称 | 识别编码 | 车挂 | 柜号 | 出库时间")
                print("-" * 80)
                for record in recent_records:
                    trailer = record[3] or '(空)'
                    container = record[4] or '(空)'
                    print(f"{record[0]} | {record[1]} | {record[2]} | {trailer} | {container} | {record[5]}")
            
            # 5. 检查备注字段中是否还有车挂/柜号信息
            print("\n5. 检查备注字段中的车挂/柜号信息:")
            result = db.session.execute(text("""
                SELECT id, customer_name, remarks
                FROM outbound_record 
                WHERE remarks LIKE '%车挂:%' OR remarks LIKE '%柜号:%'
                ORDER BY outbound_time DESC
                LIMIT 5
            """))
            
            remark_records = result.fetchall()
            if remark_records:
                print("ID | 客户名称 | 备注")
                print("-" * 60)
                for record in remark_records:
                    print(f"{record[0]} | {record[1]} | {record[2]}")
            else:
                print("✅ 备注字段中没有车挂/柜号信息（已迁移到专用字段）")
            
        except Exception as e:
            print(f"❌ 检查过程中出错: {str(e)}")

if __name__ == "__main__":
    check_trailer_container_data()
