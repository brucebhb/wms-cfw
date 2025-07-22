#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试全库存查询显示问题
"""

from app import create_app, db
from app.models import Inventory, Warehouse, InboundRecord, TransitCargo, OutboundRecord
from sqlalchemy import func
from datetime import datetime, timedelta
from collections import defaultdict

def debug_inventory_display():
    app = create_app()
    with app.app_context():
        identification_code = 'PH/泰塑/粤BR77A0/20250712/001'
        
        print("=== 调试全库存查询显示问题 ===\n")
        
        # 1. 检查原始库存数据
        print("1. 原始库存数据:")
        inventories = Inventory.query.filter_by(identification_code=identification_code).all()
        for inv in inventories:
            warehouse_name = inv.operated_warehouse.warehouse_name if inv.operated_warehouse else "未知"
            warehouse_type = inv.operated_warehouse.warehouse_type if inv.operated_warehouse else "未知"
            print(f"  ID: {inv.id}")
            print(f"  仓库: {warehouse_name} ({warehouse_type})")
            print(f"  板数: {inv.pallet_count}")
            print(f"  件数: {inv.package_count}")
            print(f"  客户名称: {inv.customer_name}")
            print(f"  车牌号: {inv.plate_number}")
            print()
        
        # 2. 模拟 get_aggregated_inventory_direct() 的完整逻辑
        print("2. 模拟 get_aggregated_inventory_direct() 查询:")
        
        # 查询库存数据，按识别编码+仓库分组
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
            print(f"  识别编码: {item.identification_code}")
            print(f"  客户名称: {item.customer_name}")
            print(f"  仓库: {item.warehouse_name} ({item.warehouse_type})")
            print(f"  板数: {item.total_pallet_count}")
            print(f"  件数: {item.total_package_count}")
            print(f"  仓库ID: {item.operated_warehouse_id}")
            print()
        
        # 3. 检查客户名称匹配问题
        print("3. 检查客户名称匹配:")
        for inv in inventories:
            customer_name = inv.customer_name
            print(f"  库存记录客户名称: '{customer_name}'")
            print(f"  是否包含'泰塑': {'泰塑' in customer_name if customer_name else False}")
            
            # 从识别编码解析客户名称
            try:
                code_parts = identification_code.split('/')
                if len(code_parts) >= 3:
                    parsed_customer = code_parts[1]
                    print(f"  从识别编码解析的客户名称: '{parsed_customer}'")
                    print(f"  解析名称是否包含'泰塑': {'泰塑' in parsed_customer}")
            except:
                pass
            print()
        
        # 4. 模拟筛选逻辑
        print("4. 模拟筛选逻辑:")
        
        # 构建模拟数据
        result = []
        for item in inventory_data:
            # 从识别编码中提取正确的客户名称
            correct_customer_name = item.customer_name
            try:
                code_parts = item.identification_code.split('/')
                if len(code_parts) >= 3:
                    correct_customer_name = code_parts[1]  # 客户名称在第二部分
            except:
                pass
            
            result.append({
                'identification_code': item.identification_code,
                'customer_name': correct_customer_name,
                'plate_number': item.plate_number,
                'pallet_count': int(item.total_pallet_count or 0),
                'package_count': int(item.total_package_count or 0),
                'current_warehouse_id': item.operated_warehouse_id,
                'warehouse_name': item.warehouse_name,
                'warehouse_type': item.warehouse_type,
                'inbound_time': item.latest_inbound_time
            })
        
        print(f"构建的结果数量: {len(result)}")
        for item in result:
            print(f"  客户名称: '{item['customer_name']}'")
            print(f"  仓库: {item['warehouse_name']} ({item['warehouse_type']})")
            print(f"  板数: {item['pallet_count']}")
            print()
        
        # 5. 应用客户名称筛选
        print("5. 应用客户名称筛选 (搜索'泰塑'):")
        search_value = '泰塑'
        search_field = 'customer_name'
        
        filtered_data = [
            item for item in result
            if search_value.lower() in str(item.get(search_field, '')).lower()
        ]
        
        print(f"筛选后结果数量: {len(filtered_data)}")
        for item in filtered_data:
            print(f"  客户名称: '{item['customer_name']}'")
            print(f"  仓库: {item['warehouse_name']} ({item['warehouse_type']})")
            print(f"  板数: {item['pallet_count']}")
            print()
        
        # 6. 检查可能的问题
        print("6. 问题分析:")
        
        if len(inventory_data) == 2 and len(filtered_data) == 1:
            print("  问题：客户名称筛选过滤掉了前端仓记录")
            
            # 检查前端仓记录的客户名称
            frontend_items = [item for item in result if item['warehouse_type'] == 'frontend']
            backend_items = [item for item in result if item['warehouse_type'] == 'backend']
            
            if frontend_items:
                frontend_item = frontend_items[0]
                print(f"  前端仓客户名称: '{frontend_item['customer_name']}'")
                print(f"  是否匹配'泰塑': {'泰塑' in frontend_item['customer_name'].lower()}")
            
            if backend_items:
                backend_item = backend_items[0]
                print(f"  后端仓客户名称: '{backend_item['customer_name']}'")
                print(f"  是否匹配'泰塑': {'泰塑' in backend_item['customer_name'].lower()}")
        
        elif len(inventory_data) == 1:
            print("  问题：数据库查询只返回了一条记录")
            print("  可能原因：前端仓库存为0或查询条件有问题")
        
        else:
            print("  数据查询和筛选都正常")

if __name__ == "__main__":
    debug_inventory_display()
