#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试库存筛选条件，验证为什么只显示后端仓的记录
"""

from app import create_app, db
from app.models import Warehouse

def test_inventory_filters():
    app = create_app()
    with app.app_context():
        # 模拟查询结果（基于之前的测试）
        mock_inventory_data = [
            {
                'identification_code': 'PH/泰塑/粤BR77A0/20250712/001',
                'customer_name': '泰塑',
                'current_warehouse_id': 1,  # 平湖仓
                'current_status': 'frontend',
                'pallet_count': 2,
                'package_count': 0,
                'inbound_time': '2025-07-12 00:00:00'
            },
            {
                'identification_code': 'PH/泰塑/粤BR77A0/20250712/001',
                'customer_name': '泰塑',
                'current_warehouse_id': 4,  # 凭祥北投仓
                'current_status': 'backend',
                'pallet_count': 2,
                'package_count': 0,
                'inbound_time': '2025-07-12 00:00:00'
            }
        ]
        
        # 获取仓库信息
        warehouses = Warehouse.query.all()
        warehouse_map = {w.id: w.warehouse_name for w in warehouses}
        
        print("=== 仓库信息 ===")
        for w in warehouses:
            print(f"ID: {w.id}, 名称: {w.warehouse_name}, 类型: {w.warehouse_type}")
        print()
        
        print("=== 模拟筛选测试 ===")
        print("原始数据:")
        for item in mock_inventory_data:
            warehouse_name = warehouse_map.get(item['current_warehouse_id'], '未知')
            print(f"  {item['identification_code']} - {warehouse_name}: {item['pallet_count']}板")
        print()
        
        # 测试不同的仓库筛选条件
        test_cases = [
            {'warehouse_id': '', 'description': '无筛选（显示全部）'},
            {'warehouse_id': '1', 'description': '只显示平湖仓'},
            {'warehouse_id': '4', 'description': '只显示凭祥北投仓'},
        ]
        
        for test_case in test_cases:
            warehouse_id = test_case['warehouse_id']
            description = test_case['description']
            
            print(f"测试条件: {description}")
            
            # 应用仓库筛选
            if warehouse_id:
                filtered_data = [
                    item for item in mock_inventory_data
                    if item.get('current_warehouse_id') == int(warehouse_id)
                ]
            else:
                filtered_data = mock_inventory_data
            
            print(f"筛选结果 ({len(filtered_data)} 条):")
            if filtered_data:
                for item in filtered_data:
                    warehouse_name = warehouse_map.get(item['current_warehouse_id'], '未知')
                    print(f"  {item['identification_code']} - {warehouse_name}: {item['pallet_count']}板")
            else:
                print("  无结果")
            print()
        
        print("=== 结论 ===")
        print("如果您在全库存查询页面只看到后端仓的2板，很可能是因为：")
        print("1. 仓库筛选下拉框选择了'凭祥北投仓'")
        print("2. 或者其他筛选条件过滤掉了前端仓的记录")
        print()
        print("解决方法：")
        print("1. 将仓库筛选设置为'全部仓库'或留空")
        print("2. 清除其他筛选条件")
        print("3. 点击查询或刷新页面")

if __name__ == "__main__":
    test_inventory_filters()
