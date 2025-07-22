#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试全库存查询功能，检查为什么只显示后端仓的2板
"""

from app import create_app, db
from app.models import Inventory, Warehouse, InboundRecord, TransitCargo, OutboundRecord
from sqlalchemy import func
from datetime import datetime

def test_global_inventory_query():
    app = create_app()
    with app.app_context():
        identification_code = 'PH/泰塑/粤BR77A0/20250712/001'
        
        print(f"=== 测试全库存查询逻辑 ===")
        print(f"识别编码: {identification_code}\n")
        
        # 1. 测试直接库存查询（模拟 get_aggregated_inventory_direct 的查询）
        print("=== 1. 直接库存查询 ===")
        inventory_data = db.session.query(
            Inventory.identification_code,
            func.max(Inventory.customer_name).label('customer_name'),
            func.max(Inventory.plate_number).label('plate_number'),
            func.sum(Inventory.pallet_count).label('total_pallet_count'),
            func.sum(Inventory.package_count).label('total_package_count'),
            func.sum(Inventory.weight).label('total_weight'),
            func.sum(Inventory.volume).label('total_volume'),
            Inventory.operated_warehouse_id,
            Warehouse.warehouse_name,
            Warehouse.warehouse_type,
            func.max(Inventory.inbound_time).label('latest_inbound_time')
        ).join(
            Warehouse, Inventory.operated_warehouse_id == Warehouse.id
        ).filter(
            Inventory.identification_code == identification_code,
            # 只查询有库存的记录
            db.or_(
                Inventory.pallet_count > 0,
                Inventory.package_count > 0
            )
        ).group_by(
            Inventory.identification_code,
            Inventory.operated_warehouse_id,
            Warehouse.warehouse_name,
            Warehouse.warehouse_type
        ).order_by(
            Inventory.identification_code,
            Warehouse.warehouse_type.desc(),  # 前端仓优先显示
            Warehouse.warehouse_name
        ).all()
        
        print(f"查询结果数量: {len(inventory_data)}")
        for item in inventory_data:
            print(f"  仓库: {item.warehouse_name} ({item.warehouse_type})")
            print(f"  板数: {item.total_pallet_count}")
            print(f"  件数: {item.total_package_count}")
            print(f"  仓库ID: {item.operated_warehouse_id}")
            print()
        
        # 2. 测试在途货物查询
        print("=== 2. 在途货物查询 ===")
        transit_data = db.session.query(
            TransitCargo.identification_code,
            TransitCargo.customer_name,
            func.sum(TransitCargo.pallet_count).label('total_pallet_count'),
            func.sum(TransitCargo.package_count).label('total_package_count'),
            TransitCargo.status
        ).filter(
            TransitCargo.identification_code == identification_code,
            TransitCargo.status == 'in_transit'  # 只查询真正在途的货物
        ).group_by(
            TransitCargo.identification_code,
            TransitCargo.customer_name,
            TransitCargo.status
        ).all()
        
        print(f"在途货物数量: {len(transit_data)}")
        for item in transit_data:
            print(f"  状态: {item.status}")
            print(f"  板数: {item.total_pallet_count}")
            print(f"  件数: {item.total_package_count}")
            print()
        
        # 3. 检查所有在途记录（包括已接收的）
        print("=== 3. 所有在途记录 ===")
        all_transit = TransitCargo.query.filter_by(identification_code=identification_code).all()
        for record in all_transit:
            print(f"  状态: {record.status}")
            print(f"  板数: {record.pallet_count}")
            print(f"  件数: {record.package_count}")
            print(f"  起始仓库: {record.source_warehouse.warehouse_name if record.source_warehouse else '未知'}")
            print(f"  目的仓库: {record.destination_warehouse.warehouse_name if record.destination_warehouse else '未知'}")
            print()
        
        # 4. 模拟全库存查询的完整逻辑
        print("=== 4. 模拟完整全库存查询逻辑 ===")
        
        # 获取所有库存记录，按identification_code分组
        from collections import defaultdict
        all_inventories = Inventory.query.filter_by(identification_code=identification_code).all()
        inventory_groups = defaultdict(list)
        
        for inv in all_inventories:
            if inv.identification_code:
                inventory_groups[inv.identification_code].append(inv)
        
        aggregated_results = []
        
        for identification_code_key, inventories in inventory_groups.items():
            if not inventories:
                continue
            
            print(f"处理识别编码: {identification_code_key}")
            print(f"库存记录数量: {len(inventories)}")
            
            # 获取基础信息
            base_inventory = min(inventories, key=lambda x: x.inbound_time or datetime.min)
            
            # 基础信息模板
            base_info = {
                'identification_code': identification_code_key,
                'customer_name': base_inventory.customer_name,
                'plate_number': base_inventory.plate_number or '',
                'weight': base_inventory.weight or 0,
                'volume': base_inventory.volume or 0,
                'inbound_time': base_inventory.inbound_time,
            }
            
            # 处理前端仓状态
            frontend_inventories = [inv for inv in inventories
                                   if inv.operated_warehouse and inv.operated_warehouse.warehouse_type == 'frontend']
            
            print(f"前端仓库存记录数量: {len(frontend_inventories)}")
            
            # 按仓库分组前端库存（只包含有库存的记录）
            frontend_warehouse_groups = defaultdict(list)
            for inv in frontend_inventories:
                if (inv.pallet_count or 0) > 0 or (inv.package_count or 0) > 0:
                    frontend_warehouse_groups[inv.operated_warehouse_id].append(inv)
            
            print(f"有库存的前端仓库数量: {len(frontend_warehouse_groups)}")
            
            for warehouse_id, warehouse_inventories in frontend_warehouse_groups.items():
                total_pallet = sum(inv.pallet_count or 0 for inv in warehouse_inventories)
                total_package = sum(inv.package_count or 0 for inv in warehouse_inventories)
                
                if total_pallet > 0 or total_package > 0:
                    warehouse = warehouse_inventories[0].operated_warehouse
                    
                    frontend_item = base_info.copy()
                    frontend_item.update({
                        'current_status': 'frontend',
                        'current_warehouse_id': warehouse_id,
                        'current_warehouse': warehouse,
                        'pallet_count': total_pallet,
                        'package_count': total_package,
                    })
                    aggregated_results.append(frontend_item)
                    print(f"  添加前端仓记录: {warehouse.warehouse_name}, {total_pallet}板")
            
            # 处理后端仓状态
            backend_inventories = [inv for inv in inventories
                                  if inv.operated_warehouse and inv.operated_warehouse.warehouse_type == 'backend']
            
            print(f"后端仓库存记录数量: {len(backend_inventories)}")
            
            # 按仓库分组后端库存（只包含有库存的记录）
            backend_warehouse_groups = defaultdict(list)
            for inv in backend_inventories:
                if (inv.pallet_count or 0) > 0 or (inv.package_count or 0) > 0:
                    backend_warehouse_groups[inv.operated_warehouse_id].append(inv)
            
            print(f"有库存的后端仓库数量: {len(backend_warehouse_groups)}")
            
            for warehouse_id, warehouse_inventories in backend_warehouse_groups.items():
                total_pallet = sum(inv.pallet_count or 0 for inv in warehouse_inventories)
                total_package = sum(inv.package_count or 0 for inv in warehouse_inventories)
                
                if total_pallet > 0 or total_package > 0:
                    warehouse = warehouse_inventories[0].operated_warehouse
                    
                    backend_item = base_info.copy()
                    backend_item.update({
                        'current_status': 'backend',
                        'current_warehouse_id': warehouse_id,
                        'current_warehouse': warehouse,
                        'pallet_count': total_pallet,
                        'package_count': total_package,
                    })
                    aggregated_results.append(backend_item)
                    print(f"  添加后端仓记录: {warehouse.warehouse_name}, {total_pallet}板")
        
        print(f"\n最终聚合结果数量: {len(aggregated_results)}")
        for result in aggregated_results:
            warehouse_name = result['current_warehouse'].warehouse_name if result['current_warehouse'] else '未知'
            print(f"  {result['current_status']}: {warehouse_name}, {result['pallet_count']}板")

if __name__ == "__main__":
    test_global_inventory_query()
