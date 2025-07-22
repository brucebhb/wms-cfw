#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查所有库存记录，包括无效的
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import Inventory, Warehouse

def check_all_inventory():
    """检查所有库存记录"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🔍 检查所有库存记录...")
            print("=" * 60)
            
            # 获取前端仓库
            frontend_warehouses = Warehouse.query.filter(
                Warehouse.warehouse_name.in_(['平湖仓', '昆山仓', '成都仓'])
            ).all()
            warehouse_ids = [w.id for w in frontend_warehouses]
            
            # 获取所有前端仓库存记录（包括无效的）
            all_frontend_inventory = Inventory.query.filter(
                Inventory.operated_warehouse_id.in_(warehouse_ids)
            ).all()
            
            print(f"前端仓库总库存记录数: {len(all_frontend_inventory)}")
            print()
            
            for i, item in enumerate(all_frontend_inventory, 1):
                warehouse_name = item.operated_warehouse.warehouse_name if item.operated_warehouse else "未知仓库"
                is_active = (item.pallet_count and item.pallet_count > 0) or (item.package_count and item.package_count > 0)
                status = "✅ 有效" if is_active else "❌ 无效"
                
                print(f"记录 {i}: {status}")
                print(f"  ID: {item.id}")
                print(f"  仓库: {warehouse_name}")
                print(f"  客户: {item.customer_name}")
                print(f"  识别编码: {item.identification_code}")
                print(f"  板数: {item.pallet_count}, 件数: {item.package_count}")
                print(f"  入库车牌: {item.plate_number}")
                print(f"  创建时间: {item.last_updated}")
                print(f"  入库时间: {item.inbound_time}")
                print()
            
            # 统计有效和无效记录
            active_count = sum(1 for item in all_frontend_inventory 
                             if (item.pallet_count and item.pallet_count > 0) or (item.package_count and item.package_count > 0))
            inactive_count = len(all_frontend_inventory) - active_count
            
            print("=" * 60)
            print(f"统计结果:")
            print(f"  总记录数: {len(all_frontend_inventory)}")
            print(f"  有效记录数: {active_count}")
            print(f"  无效记录数: {inactive_count}")
            
            return True
            
        except Exception as e:
            print(f"❌ 检查过程中出现错误: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    check_all_inventory()
