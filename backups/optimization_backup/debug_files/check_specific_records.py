#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查特定识别码的详细记录
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import InboundRecord, OutboundRecord, Inventory, ReceiveRecord

def check_specific_identification_code():
    """检查特定识别码的详细记录"""
    app = create_app()
    
    with app.app_context():
        target_code = "CD/ACKN/鄂E92711/20250713/001"
        
        print(f"🔍 详细检查识别码: {target_code}")
        print("=" * 80)
        
        # 1. 检查入库记录
        print("📦 入库记录:")
        inbound_records = InboundRecord.query.filter_by(identification_code=target_code).all()
        for record in inbound_records:
            print(f"  ID: {record.id}")
            print(f"  识别码: {record.identification_code}")
            print(f"  客户: {record.customer_name}")
            print(f"  车牌: {record.plate_number}")
            print(f"  仓库: {record.operated_warehouse.warehouse_name}")
            print(f"  数量: {record.package_count}件 {record.pallet_count}板")
            print(f"  时间: {record.inbound_time}")
            print("-" * 40)
        
        # 2. 检查出库记录
        print("\n🚚 出库记录:")
        outbound_records = OutboundRecord.query.filter_by(identification_code=target_code).all()
        for record in outbound_records:
            print(f"  ID: {record.id}")
            print(f"  识别码: {record.identification_code}")
            print(f"  客户: {record.customer_name}")
            print(f"  车牌: {record.plate_number}")
            print(f"  源仓库: {record.operated_warehouse.warehouse_name}")
            print(f"  目标仓库: {record.destination_warehouse.warehouse_name if record.destination_warehouse else '客户'}")
            print(f"  数量: {record.package_count}件 {record.pallet_count}板")
            print(f"  时间: {record.outbound_time}")
            print("-" * 40)
        
        # 3. 检查接收记录
        print("\n📥 接收记录:")
        receive_records = ReceiveRecord.query.filter_by(identification_code=target_code).all()
        for record in receive_records:
            print(f"  ID: {record.id}")
            print(f"  识别码: {record.identification_code}")
            print(f"  客户: {record.customer_name}")
            print(f"  车牌: {record.inbound_plate or record.delivery_plate_number or '无'}")
            print(f"  仓库: {record.operated_warehouse.warehouse_name}")
            print(f"  数量: {record.package_count}件 {record.pallet_count}板")
            print(f"  时间: {record.receive_time}")
            print("-" * 40)
        
        # 4. 检查库存记录
        print("\n📋 库存记录:")
        inventory_records = Inventory.query.filter_by(identification_code=target_code).all()
        for record in inventory_records:
            print(f"  ID: {record.id}")
            print(f"  识别码: {record.identification_code}")
            print(f"  客户: {record.customer_name}")
            print(f"  车牌: {record.plate_number}")
            print(f"  仓库: {record.operated_warehouse.warehouse_name}")
            print(f"  数量: {record.package_count}件 {record.pallet_count}板")
            print(f"  更新时间: {record.last_updated}")
            print("-" * 40)
        
        # 5. 检查是否有相似的识别码
        print("\n🔍 检查相似识别码:")
        similar_codes = db.session.query(InboundRecord.identification_code).filter(
            InboundRecord.identification_code.like('%ACKN%'),
            InboundRecord.identification_code.like('%鄂E92711%'),
            InboundRecord.identification_code.like('%20250713%')
        ).distinct().all()
        
        for code_tuple in similar_codes:
            code = code_tuple[0]
            print(f"  - {code}")
        
        # 6. 检查接收记录表中是否有相关记录
        print("\n📥 检查所有相关接收记录:")
        all_receive_records = ReceiveRecord.query.filter(
            ReceiveRecord.customer_name.like('%ACKN%'),
            db.or_(
                ReceiveRecord.inbound_plate.like('%鄂E92711%'),
                ReceiveRecord.delivery_plate_number.like('%鄂E92711%')
            )
        ).all()
        
        for record in all_receive_records:
            print(f"  ID: {record.id}")
            print(f"  识别码: {record.identification_code}")
            print(f"  客户: {record.customer_name}")
            print(f"  车牌: {record.inbound_plate or record.delivery_plate_number or '无'}")
            print(f"  仓库: {record.operated_warehouse.warehouse_name}")
            print(f"  数量: {record.package_count}件 {record.pallet_count}板")
            print(f"  时间: {record.receive_time}")
            print("-" * 40)

def check_batch_numbers():
    """检查批次号相关的记录"""
    app = create_app()
    
    with app.app_context():
        print("\n🔍 检查批次号相关记录:")
        print("=" * 80)
        
        # 检查CD25071401, CD25071402, CD25071403
        batch_numbers = ["CD25071401", "CD25071402", "CD25071403"]
        
        for batch_num in batch_numbers:
            print(f"\n📋 批次号: {batch_num}")
            print("-" * 40)
            
            # 检查接收记录
            receive_records = ReceiveRecord.query.filter(
                ReceiveRecord.identification_code.like(f'%{batch_num}%')
            ).all()
            
            if not receive_records:
                # 如果没有找到，尝试其他字段
                receive_records = ReceiveRecord.query.filter(
                    db.or_(
                        ReceiveRecord.customer_name.like('%ACKN%'),
                        ReceiveRecord.inbound_plate.like('%鄂E92711%'),
                        ReceiveRecord.delivery_plate_number.like('%鄂E92711%')
                    )
                ).all()
            
            for record in receive_records:
                print(f"  接收记录 ID: {record.id}")
                print(f"  识别码: {record.identification_code}")
                print(f"  客户: {record.customer_name}")
                print(f"  车牌: {record.inbound_plate or record.delivery_plate_number or '无'}")
                print(f"  数量: {record.package_count}件 {record.pallet_count}板")
                print(f"  时间: {record.receive_time}")

if __name__ == '__main__':
    check_specific_identification_code()
    check_batch_numbers()
