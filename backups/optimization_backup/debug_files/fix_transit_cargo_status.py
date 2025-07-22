#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复在途货物状态
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import TransitCargo, OutboundRecord, Inventory

def fix_transit_cargo_status():
    """修复在途货物状态"""
    app = create_app()
    
    with app.app_context():
        target_code = "CD/ACKN/鄂E92711/20250713/001"
        
        print(f"🔧 修复在途货物状态: {target_code}")
        print("=" * 80)
        
        try:
            # 1. 查找相关的在途记录
            transit_records = TransitCargo.query.filter_by(identification_code=target_code).all()
            
            print(f"找到 {len(transit_records)} 条在途记录:")
            for record in transit_records:
                print(f"  ID: {record.id}")
                print(f"  状态: {record.status}")
                print(f"  数量: {record.package_count}件 {record.pallet_count}板")
                print(f"  源仓库: {record.source_warehouse.warehouse_name}")
                print(f"  目标仓库: {record.destination_warehouse.warehouse_name}")
                print("-" * 40)
            
            # 2. 检查是否有后续的出库记录（出库给客户）
            outbound_to_customer = OutboundRecord.query.filter(
                OutboundRecord.identification_code == target_code,
                OutboundRecord.destination_warehouse_id.is_(None)  # 出库给客户
            ).all()
            
            print(f"\n找到 {len(outbound_to_customer)} 条出库给客户的记录:")
            total_outbound_to_customer = 0
            for record in outbound_to_customer:
                print(f"  ID: {record.id}")
                print(f"  数量: {record.package_count}件 {record.pallet_count}板")
                print(f"  出库时间: {record.outbound_time}")
                total_outbound_to_customer += record.pallet_count or 0
                print("-" * 40)
            
            print(f"总出库给客户: {total_outbound_to_customer} 板")
            
            # 3. 检查当前库存
            current_inventory = Inventory.query.filter_by(identification_code=target_code).all()
            total_current_inventory = sum(inv.pallet_count or 0 for inv in current_inventory)
            
            print(f"当前库存: {total_current_inventory} 板")
            
            # 4. 决定修复策略
            if total_outbound_to_customer > 0 and total_current_inventory == 0:
                print("\n💡 检测到货物已全部出库给客户，在途记录应该清理")
                
                # 策略1：删除在途记录
                print("\n🗑️ 删除过期的在途记录:")
                for record in transit_records:
                    print(f"  删除在途记录 ID: {record.id}")
                    db.session.delete(record)
                
                db.session.commit()
                print("✅ 在途记录清理完成")
                
            elif total_current_inventory == 0:
                print("\n💡 检测到无库存，但可能有其他原因，建议手动检查")
                
                # 策略2：更新状态为已完成
                print("\n📝 更新在途记录状态为已完成:")
                for record in transit_records:
                    record.status = 'completed'
                    print(f"  更新在途记录 ID: {record.id} 状态为 completed")
                
                db.session.commit()
                print("✅ 在途记录状态更新完成")
                
            else:
                print("\n⚠️ 数据状态复杂，建议手动检查")
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ 修复失败: {e}")
            return False

def check_all_transit_cargo_issues():
    """检查所有在途货物问题"""
    app = create_app()
    
    with app.app_context():
        print("\n🔍 检查所有在途货物问题:")
        print("=" * 80)
        
        try:
            # 查找所有状态为received但没有对应库存的在途记录
            transit_received = TransitCargo.query.filter_by(status='received').all()
            
            problematic_records = []
            
            for transit in transit_received:
                # 检查是否有对应的库存
                inventory = Inventory.query.filter_by(
                    identification_code=transit.identification_code,
                    operated_warehouse_id=transit.destination_warehouse_id
                ).first()
                
                if not inventory:
                    # 检查是否已出库给客户
                    outbound_to_customer = OutboundRecord.query.filter(
                        OutboundRecord.identification_code == transit.identification_code,
                        OutboundRecord.operated_warehouse_id == transit.destination_warehouse_id,
                        OutboundRecord.destination_warehouse_id.is_(None)
                    ).first()
                    
                    if outbound_to_customer:
                        problematic_records.append({
                            'transit': transit,
                            'reason': '已出库给客户但在途状态未更新'
                        })
                    else:
                        problematic_records.append({
                            'transit': transit,
                            'reason': '无对应库存且无出库记录'
                        })
            
            if problematic_records:
                print(f"发现 {len(problematic_records)} 个问题在途记录:")
                for item in problematic_records:
                    transit = item['transit']
                    reason = item['reason']
                    print(f"  ID: {transit.id}")
                    print(f"  识别码: {transit.identification_code}")
                    print(f"  目标仓库: {transit.destination_warehouse.warehouse_name}")
                    print(f"  数量: {transit.pallet_count}板")
                    print(f"  问题: {reason}")
                    print("-" * 40)
                
                # 询问是否批量修复
                print(f"\n🔧 批量修复这些问题记录...")
                fixed_count = 0
                
                for item in problematic_records:
                    transit = item['transit']
                    if item['reason'] == '已出库给客户但在途状态未更新':
                        # 删除这些记录
                        db.session.delete(transit)
                        fixed_count += 1
                        print(f"  删除在途记录 ID: {transit.id}")
                
                if fixed_count > 0:
                    db.session.commit()
                    print(f"✅ 批量修复完成，处理了 {fixed_count} 条记录")
                else:
                    print("ℹ️ 无需修复的记录")
            else:
                print("✅ 未发现问题在途记录")
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ 检查失败: {e}")
            return False

if __name__ == '__main__':
    print("🔧 在途货物状态修复工具")
    print("=" * 80)
    
    # 1. 修复特定识别码
    fix_transit_cargo_status()
    
    print("\n" + "=" * 80)
    
    # 2. 检查所有在途货物问题
    check_all_transit_cargo_issues()
    
    print("\n✅ 修复完成！")
    print("建议重新检查界面显示是否正常。")
