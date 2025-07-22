#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试出库记录查询，检查车挂/柜号字段
"""

from app import create_app, db
from app.models import OutboundRecord
from datetime import datetime, timedelta

def test_outbound_query():
    """测试出库记录查询"""
    app = create_app()
    
    with app.app_context():
        try:
            print("=== 测试出库记录查询 ===")
            
            # 1. 查询最近的出库记录
            print("1. 查询最近的出库记录...")
            
            # 模拟出库单打印列表的查询逻辑
            start_date = datetime.now() - timedelta(days=7)  # 最近7天
            end_date = datetime.now()
            
            query = OutboundRecord.query.filter(
                db.and_(
                    # 排除发往春疆的记录
                    db.not_(OutboundRecord.destination.like('%春疆%'))
                )
            )
            
            # 添加日期过滤
            query = query.filter(OutboundRecord.outbound_time.between(start_date, end_date))
            
            # 按时间降序排序
            query = query.order_by(OutboundRecord.outbound_time.desc())
            
            # 限制记录数量
            records = query.limit(10).all()
            
            print(f"找到 {len(records)} 条记录")
            
            # 2. 检查每条记录的车挂/柜号字段
            print("\n2. 检查车挂/柜号字段:")
            print("ID | 客户名称 | 车挂 | 柜号 | 出库时间")
            print("-" * 70)
            
            for record in records:
                trailer = getattr(record, 'trailer', None) or '(空)'
                container_number = getattr(record, 'container_number', None) or '(空)'
                print(f"{record.id} | {record.customer_name} | {trailer} | {container_number} | {record.outbound_time}")
            
            # 3. 测试模板逻辑
            print("\n3. 测试模板逻辑:")
            for i, record in enumerate(records[:3]):  # 只测试前3条
                print(f"\n记录 {i+1} (ID: {record.id}):")
                print(f"  客户名称: {record.customer_name}")
                print(f"  trailer属性: {getattr(record, 'trailer', 'NOT_FOUND')}")
                print(f"  container_number属性: {getattr(record, 'container_number', 'NOT_FOUND')}")
                
                # 模拟模板逻辑
                trailer_container = []
                if hasattr(record, 'trailer') and record.trailer:
                    trailer_container.append(f'车挂: {record.trailer}')
                if hasattr(record, 'container_number') and record.container_number:
                    trailer_container.append(f'柜号: {record.container_number}')
                
                result = '; '.join(trailer_container) if trailer_container else ''
                print(f"  模板输出: '{result}'")
            
            # 4. 查询有车挂/柜号数据的记录
            print("\n4. 查询有车挂/柜号数据的记录:")
            records_with_data = OutboundRecord.query.filter(
                db.or_(
                    db.and_(OutboundRecord.trailer.isnot(None), OutboundRecord.trailer != ''),
                    db.and_(OutboundRecord.container_number.isnot(None), OutboundRecord.container_number != '')
                )
            ).order_by(OutboundRecord.outbound_time.desc()).limit(5).all()
            
            print(f"找到 {len(records_with_data)} 条有车挂/柜号数据的记录")
            for record in records_with_data:
                print(f"  ID {record.id}: {record.customer_name} - 车挂: {record.trailer or '(空)'}, 柜号: {record.container_number or '(空)'}")
            
            # 5. 检查字段是否在模型中正确定义
            print("\n5. 检查模型字段定义:")
            sample_record = records[0] if records else None
            if sample_record:
                print("模型属性:")
                for attr in ['trailer', 'container_number']:
                    if hasattr(sample_record, attr):
                        value = getattr(sample_record, attr)
                        print(f"  {attr}: {value} (类型: {type(value)})")
                    else:
                        print(f"  {attr}: 属性不存在")
            
        except Exception as e:
            print(f"❌ 测试过程中出错: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_outbound_query()
