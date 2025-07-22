#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查用户权限是否影响库存显示
"""

from app import create_app, db
from app.models import User, Warehouse, Inventory

def check_user_permissions():
    app = create_app()
    with app.app_context():
        print("=== 检查用户权限对库存显示的影响 ===\n")
        
        # 1. 检查所有用户
        print("1. 系统中的用户:")
        users = User.query.all()
        for user in users:
            warehouse_name = user.warehouse.warehouse_name if user.warehouse else "无仓库"
            warehouse_type = user.warehouse.warehouse_type if user.warehouse else "N/A"
            print(f"  用户: {user.username}")
            print(f"    真实姓名: {user.real_name}")
            print(f"    用户类型: {user.user_type}")
            print(f"    是否管理员: {user.is_admin}")
            print(f"    是否超级管理员: {user.is_super_admin()}")
            print(f"    所属仓库: {warehouse_name} ({warehouse_type})")
            print()
        
        # 2. 检查仓库信息
        print("2. 系统中的仓库:")
        warehouses = Warehouse.query.all()
        for warehouse in warehouses:
            print(f"  ID: {warehouse.id}")
            print(f"  名称: {warehouse.warehouse_name}")
            print(f"  类型: {warehouse.warehouse_type}")
            print(f"  状态: {warehouse.status}")
            print()
        
        # 3. 检查目标库存记录的详细信息
        print("3. 目标库存记录详细信息:")
        identification_code = 'PH/泰塑/粤BR77A0/20250712/001'
        inventories = Inventory.query.filter_by(identification_code=identification_code).all()
        
        for inv in inventories:
            print(f"  库存ID: {inv.id}")
            print(f"  识别编码: {inv.identification_code}")
            print(f"  客户名称: {inv.customer_name}")
            print(f"  车牌号: {inv.plate_number}")
            print(f"  板数: {inv.pallet_count}")
            print(f"  件数: {inv.package_count}")
            print(f"  操作仓库ID: {inv.operated_warehouse_id}")
            print(f"  操作仓库: {inv.operated_warehouse.warehouse_name if inv.operated_warehouse else '未知'}")
            print(f"  仓库类型: {inv.operated_warehouse.warehouse_type if inv.operated_warehouse else '未知'}")
            print(f"  操作用户ID: {inv.operated_by_user_id}")
            print(f"  操作用户: {inv.operated_by_user.username if inv.operated_by_user else '未知'}")
            print(f"  最后更新: {inv.last_updated}")
            print()
        
        # 4. 模拟不同用户的权限检查
        print("4. 模拟不同用户的权限检查:")
        
        # 检查admin用户
        admin_user = User.query.filter_by(username='admin').first()
        if admin_user:
            print(f"  admin用户:")
            print(f"    是否超级管理员: {admin_user.is_super_admin()}")
            print(f"    所属仓库: {admin_user.warehouse.warehouse_name if admin_user.warehouse else '无'}")
            print()
        
        # 检查平湖仓用户
        ph_user = User.query.filter_by(username='ph_operator').first()
        if ph_user:
            print(f"  ph_operator用户:")
            print(f"    是否超级管理员: {ph_user.is_super_admin()}")
            print(f"    所属仓库: {ph_user.warehouse.warehouse_name if ph_user.warehouse else '无'}")
            print(f"    仓库ID: {ph_user.warehouse_id}")
            print()
        
        # 检查凭祥用户
        px_user = User.query.filter_by(username='px_operator').first()
        if px_user:
            print(f"  px_operator用户:")
            print(f"    是否超级管理员: {px_user.is_super_admin()}")
            print(f"    所属仓库: {px_user.warehouse.warehouse_name if px_user.warehouse else '无'}")
            print(f"    仓库ID: {px_user.warehouse_id}")
            print()
        
        # 5. 检查权限装饰器可能的影响
        print("5. 权限相关分析:")
        print("  如果当前登录用户是px_operator（凭祥仓用户），可能存在以下情况：")
        print("  - 权限限制只能看到自己仓库的数据")
        print("  - 数据过滤逻辑可能过滤掉了前端仓的记录")
        print("  - 需要检查 @warehouse_data_filter 装饰器的影响")
        print()
        
        print("  建议测试步骤：")
        print("  1. 使用admin账号登录测试")
        print("  2. 使用ph_operator账号登录测试")
        print("  3. 检查全库存查询是否有权限限制")

if __name__ == "__main__":
    check_user_permissions()
