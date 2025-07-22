#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复特定识别码的库存问题
专门修复 CD/ACKN/鄂E92711/20250713/001 的库存不一致
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import InboundRecord, OutboundRecord, Inventory, ReceiveRecord, TransitCargo
from datetime import datetime

def fix_specific_inventory_issue():
    """修复特定识别码的库存问题"""
    app = create_app()
    
    with app.app_context():
        target_code = "CD/ACKN/鄂E92711/20250713/001"
        
        print(f"🔧 修复识别码: {target_code}")
        print("=" * 80)
        
        try:
            # 1. 查找相关记录
            inbound_records = InboundRecord.query.filter_by(identification_code=target_code).all()
            outbound_records = OutboundRecord.query.filter_by(identification_code=target_code).all()
            receive_records = ReceiveRecord.query.filter_by(identification_code=target_code).all()
            inventory_records = Inventory.query.filter_by(identification_code=target_code).all()
            transit_records = TransitCargo.query.filter_by(identification_code=target_code).all()
            
            print("📋 当前状态:")
            print(f"  入库记录: {len(inbound_records)} 条")
            print(f"  出库记录: {len(outbound_records)} 条") 
            print(f"  接收记录: {len(receive_records)} 条")
            print(f"  库存记录: {len(inventory_records)} 条")
            print(f"  在途记录: {len(transit_records)} 条")
            
            # 2. 分析问题
            print("\n🔍 问题分析:")
            
            # 入库情况
            total_inbound = sum(r.pallet_count or 0 for r in inbound_records)
            print(f"  总入库: {total_inbound} 板")
            
            # 出库情况  
            total_outbound = sum(r.pallet_count or 0 for r in outbound_records)
            print(f"  总出库: {total_outbound} 板")
            
            # 接收情况
            total_received = sum(r.pallet_count or 0 for r in receive_records)
            print(f"  总接收: {total_received} 板")
            
            # 当前库存
            total_inventory = sum(r.pallet_count or 0 for r in inventory_records)
            print(f"  当前库存: {total_inventory} 板")
            
            # 3. 确定修复方案
            print("\n💡 修复方案:")
            
            if len(outbound_records) > 0 and len(receive_records) == 0:
                # 情况：有出库到后端仓，但没有接收记录
                outbound = outbound_records[0]
                if outbound.destination_warehouse_id:
                    print(f"  检测到前端仓出库到后端仓，但缺少接收记录")
                    print(f"  出库数量: {outbound.pallet_count} 板")
                    print(f"  目标仓库: {outbound.destination_warehouse.warehouse_name}")
                    
                    # 方案1：重新创建接收记录
                    print(f"  方案1: 重新创建接收记录")
                    
                    # 方案2：调整库存到正确状态
                    print(f"  方案2: 直接调整库存到正确状态")
                    
                    # 执行修复
                    print("\n🔧 执行修复...")
                    
                    # 删除现有库存记录
                    for inv in inventory_records:
                        print(f"  删除库存记录: {inv.operated_warehouse.warehouse_name} - {inv.pallet_count} 板")
                        db.session.delete(inv)
                    
                    # 重新计算正确的库存
                    # 成都仓：入库21板 - 出库21板 = 0板
                    # 凭祥北投仓：接收21板 = 21板 (但实际应该是21板，不是16板)
                    
                    # 为凭祥北投仓创建正确的库存记录
                    base_record = inbound_records[0]
                    correct_inventory = Inventory(
                        identification_code=target_code,
                        operated_warehouse_id=outbound.destination_warehouse_id,
                        customer_name=base_record.customer_name,
                        plate_number=base_record.plate_number,
                        package_count=outbound.package_count or 0,
                        pallet_count=outbound.pallet_count or 0,
                        weight=base_record.weight,
                        volume=base_record.volume,
                        inbound_time=base_record.inbound_time,
                        last_updated=datetime.now()
                    )
                    db.session.add(correct_inventory)
                    
                    print(f"  ✅ 创建正确库存: {outbound.destination_warehouse.warehouse_name} - {outbound.pallet_count} 板")
                    
                    # 提交更改
                    db.session.commit()
                    print("  ✅ 修复完成")
                    
                    return True
            
            print("  ❌ 未找到明确的修复方案")
            return False
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ 修复失败: {e}")
            return False

def fix_all_inconsistent_inventory():
    """修复所有不一致的库存"""
    app = create_app()
    
    with app.app_context():
        print("🔧 批量修复所有不一致的库存...")
        print("=" * 80)
        
        # 不一致的识别码列表（从检查结果中获取）
        inconsistent_codes = [
            "CD/ACKN/鄂E92711/20250713/001",
            "PH/丁乙恒/跨越/20250712/001", 
            "PH/佛山震雄/粤BHW989/20250712/001",
            "PH/华顶/粤BR3505/20250712/002",
            "PH/富士康/粤BKZ658/20250712/001",
            "PH/捷联达/川AKK808/20250712/001",
            "PH/裕同/川AT3006/20250712/002",
            "PH/首镭激光/粤BM3284/20250712/002"
        ]
        
        fixed_count = 0
        
        for code in inconsistent_codes:
            print(f"\n🔧 修复: {code}")
            print("-" * 60)
            
            try:
                # 获取相关记录
                inbound_records = InboundRecord.query.filter_by(identification_code=code).all()
                outbound_records = OutboundRecord.query.filter_by(identification_code=code).all()
                receive_records = ReceiveRecord.query.filter_by(identification_code=code).all()
                inventory_records = Inventory.query.filter_by(identification_code=code).all()
                
                # 计算正确的库存分布
                warehouse_inventory = {}
                
                # 处理入库
                for record in inbound_records:
                    warehouse_id = record.operated_warehouse_id
                    if warehouse_id not in warehouse_inventory:
                        warehouse_inventory[warehouse_id] = {
                            'warehouse': record.operated_warehouse,
                            'packages': 0,
                            'pallets': 0
                        }
                    warehouse_inventory[warehouse_id]['packages'] += record.package_count or 0
                    warehouse_inventory[warehouse_id]['pallets'] += record.pallet_count or 0
                
                # 处理接收
                for record in receive_records:
                    warehouse_id = record.operated_warehouse_id
                    if warehouse_id not in warehouse_inventory:
                        warehouse_inventory[warehouse_id] = {
                            'warehouse': record.operated_warehouse,
                            'packages': 0,
                            'pallets': 0
                        }
                    warehouse_inventory[warehouse_id]['packages'] += record.package_count or 0
                    warehouse_inventory[warehouse_id]['pallets'] += record.pallet_count or 0
                
                # 处理出库
                for record in outbound_records:
                    warehouse_id = record.operated_warehouse_id
                    if warehouse_id in warehouse_inventory:
                        warehouse_inventory[warehouse_id]['packages'] -= record.package_count or 0
                        warehouse_inventory[warehouse_id]['pallets'] -= record.pallet_count or 0
                
                # 删除现有库存记录
                for inv in inventory_records:
                    db.session.delete(inv)
                
                # 创建正确的库存记录
                for warehouse_id, data in warehouse_inventory.items():
                    if data['pallets'] > 0:  # 只创建有库存的记录
                        base_record = inbound_records[0] if inbound_records else None
                        if base_record:
                            new_inventory = Inventory(
                                identification_code=code,
                                operated_warehouse_id=warehouse_id,
                                customer_name=base_record.customer_name,
                                plate_number=base_record.plate_number,
                                package_count=data['packages'],
                                pallet_count=data['pallets'],
                                weight=base_record.weight,
                                volume=base_record.volume,
                                inbound_time=base_record.inbound_time,
                                last_updated=datetime.now()
                            )
                            db.session.add(new_inventory)
                            print(f"  ✅ 创建库存: {data['warehouse'].warehouse_name} - {data['pallets']} 板")
                
                db.session.commit()
                fixed_count += 1
                print(f"  ✅ {code} 修复完成")
                
            except Exception as e:
                db.session.rollback()
                print(f"  ❌ {code} 修复失败: {e}")
        
        print(f"\n✅ 批量修复完成，成功修复 {fixed_count}/{len(inconsistent_codes)} 个识别码")
        return fixed_count

if __name__ == '__main__':
    print("🔧 库存数据修复工具")
    print("=" * 80)
    
    # 1. 修复特定识别码
    print("1. 修复特定识别码 CD/ACKN/鄂E92711/20250713/001")
    fix_specific_inventory_issue()
    
    print("\n" + "=" * 80)
    
    # 2. 批量修复所有不一致的库存
    print("2. 批量修复所有不一致的库存")
    fix_all_inconsistent_inventory()
    
    print("\n" + "=" * 80)
    print("✅ 所有修复完成！")
    print("建议重新运行库存一致性检查来验证修复结果。")
