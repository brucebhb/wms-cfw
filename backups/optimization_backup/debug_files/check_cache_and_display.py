#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查缓存和显示数据
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Inventory, TransitCargo

def check_all_related_data():
    """检查所有相关数据"""
    app = create_app()
    
    with app.app_context():
        target_code = "CD/ACKN/鄂E92711/20250713/001"
        
        print(f"🔍 全面检查识别码: {target_code}")
        print("=" * 80)
        
        # 1. 检查库存表
        print("📋 库存表 (Inventory):")
        inventories = Inventory.query.filter_by(identification_code=target_code).all()
        if inventories:
            for inv in inventories:
                print(f"  ID: {inv.id}")
                print(f"  仓库: {inv.operated_warehouse.warehouse_name}")
                print(f"  数量: {inv.package_count}件 {inv.pallet_count}板")
                print(f"  更新时间: {inv.last_updated}")
                print("-" * 40)
        else:
            print("  无库存记录")
        
        # 2. 检查在途货物表
        print("\n🚛 在途货物表 (TransitCargo):")
        transit_records = TransitCargo.query.filter_by(identification_code=target_code).all()
        if transit_records:
            for record in transit_records:
                print(f"  ID: {record.id}")
                print(f"  状态: {record.status}")
                print(f"  源仓库: {record.source_warehouse.warehouse_name}")
                print(f"  目标仓库: {record.destination_warehouse.warehouse_name}")
                print(f"  数量: {record.package_count}件 {record.pallet_count}板")
                print(f"  创建时间: {record.created_at}")
                print("-" * 40)
        else:
            print("  无在途记录")
        
        # 3. 检查是否有相似的识别码
        print("\n🔍 检查相似识别码:")
        similar_inventories = Inventory.query.filter(
            Inventory.identification_code.like('%ACKN%'),
            Inventory.identification_code.like('%鄂E92711%')
        ).all()
        
        if similar_inventories:
            for inv in similar_inventories:
                print(f"  识别码: {inv.identification_code}")
                print(f"  仓库: {inv.operated_warehouse.warehouse_name}")
                print(f"  数量: {inv.package_count}件 {inv.pallet_count}板")
                print("-" * 40)
        else:
            print("  无相似库存记录")
        
        # 4. 检查所有包含"鄂E92711"的库存
        print("\n🔍 检查所有包含'鄂E92711'的库存:")
        all_related = Inventory.query.filter(
            db.or_(
                Inventory.identification_code.like('%鄂E92711%'),
                Inventory.plate_number.like('%鄂E92711%')
            )
        ).all()
        
        if all_related:
            for inv in all_related:
                print(f"  识别码: {inv.identification_code}")
                print(f"  车牌: {inv.plate_number}")
                print(f"  仓库: {inv.operated_warehouse.warehouse_name}")
                print(f"  数量: {inv.package_count}件 {inv.pallet_count}板")
                print("-" * 40)
        else:
            print("  无相关库存记录")

def test_inventory_query_function():
    """测试库存查询函数"""
    app = create_app()
    
    with app.app_context():
        print("\n🧪 测试库存查询函数:")
        print("=" * 80)
        
        # 导入查询函数
        sys.path.append(os.path.join(os.path.dirname(__file__), 'app', 'main'))
        
        try:
            # 直接调用库存查询函数
            from app.main.routes import get_aggregated_inventory_direct
            
            print("调用 get_aggregated_inventory_direct()...")
            inventory_data = get_aggregated_inventory_direct()
            
            # 查找包含"鄂E92711"的记录
            related_records = []
            for item in inventory_data:
                if 'identification_code' in item and item['identification_code']:
                    if '鄂E92711' in item['identification_code']:
                        related_records.append(item)
            
            if related_records:
                print(f"找到 {len(related_records)} 条相关记录:")
                for item in related_records:
                    print(f"  识别码: {item.get('identification_code', 'N/A')}")
                    print(f"  客户: {item.get('customer_name', 'N/A')}")
                    print(f"  仓库: {item.get('current_warehouse', {}).get('warehouse_name', 'N/A')}")
                    print(f"  数量: {item.get('package_count', 0)}件 {item.get('pallet_count', 0)}板")
                    print(f"  状态: {item.get('current_status', 'N/A')}")
                    print("-" * 40)
            else:
                print("  查询函数中无相关记录")
                
        except Exception as e:
            print(f"  ❌ 调用查询函数失败: {e}")

def check_api_response():
    """检查API响应"""
    app = create_app()
    
    with app.app_context():
        print("\n🌐 检查API响应:")
        print("=" * 80)
        
        try:
            # 模拟API调用
            from app.main.routes import api_inventory_list
            from flask import request
            
            # 这里我们直接查询数据库，模拟API逻辑
            from app.models import Inventory
            
            # 查询所有包含"鄂E92711"的库存
            api_results = Inventory.query.filter(
                db.or_(
                    Inventory.identification_code.like('%鄂E92711%'),
                    Inventory.plate_number.like('%鄂E92711%')
                )
            ).all()
            
            if api_results:
                print(f"API查询到 {len(api_results)} 条记录:")
                for inv in api_results:
                    print(f"  ID: {inv.id}")
                    print(f"  识别码: {inv.identification_code}")
                    print(f"  仓库: {inv.operated_warehouse.warehouse_name}")
                    print(f"  数量: {inv.package_count}件 {inv.pallet_count}板")
                    print("-" * 40)
            else:
                print("  API查询无相关记录")
                
        except Exception as e:
            print(f"  ❌ API查询失败: {e}")

if __name__ == '__main__':
    check_all_related_data()
    test_inventory_query_function()
    check_api_response()
