#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查识别编码 PH/泰塑/粤BR77A0/20250712/001 的库存问题
"""

from app import create_app, db
from app.models import InboundRecord, OutboundRecord, Inventory, TransitCargo

def check_inventory_issue():
    app = create_app()
    with app.app_context():
        identification_code = 'PH/泰塑/粤BR77A0/20250712/001'
        
        print(f"=== 检查识别编码: {identification_code} ===\n")
        
        print("=== 入库记录 ===")
        inbound_records = InboundRecord.query.filter_by(identification_code=identification_code).all()
        if not inbound_records:
            print("未找到入库记录")
        else:
            for record in inbound_records:
                warehouse_name = record.operated_warehouse.warehouse_name if record.operated_warehouse else "未知"
                warehouse_type = record.operated_warehouse.warehouse_type if record.operated_warehouse else "未知"
                print(f"ID: {record.id}")
                print(f"  仓库: {warehouse_name} ({warehouse_type})")
                print(f"  板数: {record.pallet_count}")
                print(f"  件数: {record.package_count}")
                print(f"  类型: {record.record_type}")
                print(f"  入库时间: {record.inbound_time}")
                print()
        
        print("=== 出库记录 ===")
        outbound_records = OutboundRecord.query.filter_by(identification_code=identification_code).all()
        if not outbound_records:
            print("未找到出库记录")
        else:
            for record in outbound_records:
                warehouse_name = record.operated_warehouse.warehouse_name if record.operated_warehouse else "未知"
                warehouse_type = record.operated_warehouse.warehouse_type if record.operated_warehouse else "未知"
                print(f"ID: {record.id}")
                print(f"  仓库: {warehouse_name} ({warehouse_type})")
                print(f"  板数: {record.pallet_count}")
                print(f"  件数: {record.package_count}")
                print(f"  目的地: {record.destination}")
                print(f"  出库时间: {record.outbound_time}")
                print()
        
        print("=== 库存记录 ===")
        inventory_records = Inventory.query.filter_by(identification_code=identification_code).all()
        if not inventory_records:
            print("未找到库存记录")
        else:
            for record in inventory_records:
                warehouse_name = record.operated_warehouse.warehouse_name if record.operated_warehouse else "未知"
                warehouse_type = record.operated_warehouse.warehouse_type if record.operated_warehouse else "未知"
                print(f"ID: {record.id}")
                print(f"  仓库: {warehouse_name} ({warehouse_type})")
                print(f"  板数: {record.pallet_count}")
                print(f"  件数: {record.package_count}")
                print(f"  入库板数: {record.inbound_pallet_count}")
                print(f"  入库件数: {record.inbound_package_count}")
                print(f"  最后更新: {record.last_updated}")
                print()
        
        print("=== 在途货物 ===")
        transit_records = TransitCargo.query.filter_by(identification_code=identification_code).all()
        if not transit_records:
            print("未找到在途货物记录")
        else:
            for record in transit_records:
                source_name = record.source_warehouse.warehouse_name if record.source_warehouse else "未知"
                dest_name = record.destination_warehouse.warehouse_name if record.destination_warehouse else "未知"
                print(f"ID: {record.id}")
                print(f"  起始仓库: {source_name}")
                print(f"  目的仓库: {dest_name}")
                print(f"  板数: {record.pallet_count}")
                print(f"  件数: {record.package_count}")
                print(f"  状态: {record.status}")
                print(f"  出发时间: {record.departure_time}")
                print()
        
        # 分析问题
        print("=== 问题分析 ===")
        total_inbound_pallet = sum(r.pallet_count or 0 for r in inbound_records)
        total_inbound_package = sum(r.package_count or 0 for r in inbound_records)
        total_outbound_pallet = sum(r.pallet_count or 0 for r in outbound_records)
        total_outbound_package = sum(r.package_count or 0 for r in outbound_records)
        total_inventory_pallet = sum(r.pallet_count or 0 for r in inventory_records)
        total_inventory_package = sum(r.package_count or 0 for r in inventory_records)
        
        print(f"总入库板数: {total_inbound_pallet}")
        print(f"总入库件数: {total_inbound_package}")
        print(f"总出库板数: {total_outbound_pallet}")
        print(f"总出库件数: {total_outbound_package}")
        print(f"当前库存板数: {total_inventory_pallet}")
        print(f"当前库存件数: {total_inventory_package}")
        
        # 检查前端仓和后端仓的库存分布
        print("\n=== 库存分布 ===")
        frontend_inventory = [r for r in inventory_records if r.operated_warehouse and r.operated_warehouse.warehouse_type == 'frontend']
        backend_inventory = [r for r in inventory_records if r.operated_warehouse and r.operated_warehouse.warehouse_type == 'backend']
        
        frontend_pallet = sum(r.pallet_count or 0 for r in frontend_inventory)
        frontend_package = sum(r.package_count or 0 for r in frontend_inventory)
        backend_pallet = sum(r.pallet_count or 0 for r in backend_inventory)
        backend_package = sum(r.package_count or 0 for r in backend_inventory)
        
        print(f"前端仓库存: {frontend_pallet}板 {frontend_package}件")
        print(f"后端仓库存: {backend_pallet}板 {backend_package}件")
        
        if frontend_pallet > 0 and backend_pallet > 0:
            print("⚠️ 发现问题: 同一票货物在前端仓和后端仓都有库存!")
        elif frontend_pallet == 0 and backend_pallet > 0:
            print("✅ 正常: 货物已从前端仓转移到后端仓")
        elif frontend_pallet > 0 and backend_pallet == 0:
            print("✅ 正常: 货物仍在前端仓")
        else:
            print("⚠️ 异常: 没有库存记录")

if __name__ == "__main__":
    check_inventory_issue()
