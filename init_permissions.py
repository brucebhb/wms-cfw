#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
权限系统初始化脚本
用于创建基础的菜单权限、页面权限和用户权限分配
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import (
    MenuPermission, PagePermission, OperationPermission, WarehousePermission,
    UserMenuPermission, UserPagePermission, UserOperationPermission, UserWarehousePermission,
    User, Warehouse
)

def init_menu_permissions():
    """初始化菜单权限"""
    menus = [
        {'menu_code': 'FRONTEND_INBOUND', 'menu_name': '前端仓入库', 'menu_level': 1, 'menu_order': 1},
        {'menu_code': 'BACKEND_INBOUND', 'menu_name': '后端仓入库', 'menu_level': 1, 'menu_order': 2},
        {'menu_code': 'FRONTEND_OUTBOUND', 'menu_name': '前端仓出库', 'menu_level': 1, 'menu_order': 3},
        {'menu_code': 'BACKEND_OUTBOUND', 'menu_name': '后端仓出库', 'menu_level': 1, 'menu_order': 4},
        {'menu_code': 'INVENTORY_MANAGEMENT', 'menu_name': '库存管理', 'menu_level': 1, 'menu_order': 5},
        {'menu_code': 'PRINT_MANAGEMENT', 'menu_name': '单据打印', 'menu_level': 1, 'menu_order': 6},
        {'menu_code': 'ADMIN_MANAGEMENT', 'menu_name': '用户管理', 'menu_level': 1, 'menu_order': 7},
    ]
    
    for menu_data in menus:
        existing = MenuPermission.query.filter_by(menu_code=menu_data['menu_code']).first()
        if not existing:
            menu = MenuPermission(**menu_data)
            db.session.add(menu)
            print(f"创建菜单权限: {menu_data['menu_name']}")
    
    db.session.commit()

def init_page_permissions():
    """初始化页面权限"""
    pages = [
        # 前端仓入库相关页面
        {'page_code': 'FRONTEND_INBOUND_OPERATION', 'page_name': '前端仓入库操作', 'menu_code': 'FRONTEND_INBOUND'},
        {'page_code': 'FRONTEND_INBOUND_LIST', 'page_name': '前端仓入库记录', 'menu_code': 'FRONTEND_INBOUND'},
        {'page_code': 'FRONTEND_RECEIVE_LIST', 'page_name': '前端仓接收记录', 'menu_code': 'FRONTEND_INBOUND'},
        
        # 后端仓入库相关页面
        {'page_code': 'BACKEND_INBOUND_OPERATION', 'page_name': '后端仓入库操作', 'menu_code': 'BACKEND_INBOUND'},
        {'page_code': 'BACKEND_RECEIVE_RECORDS', 'page_name': '后端仓接收记录', 'menu_code': 'BACKEND_INBOUND'},
        {'page_code': 'BACKEND_INBOUND_LIST', 'page_name': '后端仓入库记录', 'menu_code': 'BACKEND_INBOUND'},
        
        # 前端仓出库相关页面
        {'page_code': 'FRONTEND_OUTBOUND_OPERATION', 'page_name': '前端仓出库操作', 'menu_code': 'FRONTEND_OUTBOUND'},
        {'page_code': 'FRONTEND_OUTBOUND_LIST', 'page_name': '前端仓出库记录', 'menu_code': 'FRONTEND_OUTBOUND'},
        
        # 后端仓出库相关页面
        {'page_code': 'BACKEND_OUTBOUND_OPERATION', 'page_name': '后端仓出库操作', 'menu_code': 'BACKEND_OUTBOUND'},
        {'page_code': 'BACKEND_OUTBOUND_LIST', 'page_name': '后端仓出库记录', 'menu_code': 'BACKEND_OUTBOUND'},
        {'page_code': 'BACKEND_OUTBOUND_PRINT', 'page_name': '后端仓出库单页面', 'menu_code': 'BACKEND_OUTBOUND'},
        
        # 库存管理相关页面
        {'page_code': 'FRONTEND_INVENTORY_LIST', 'page_name': '前端仓库存界面', 'menu_code': 'INVENTORY_MANAGEMENT'},
        {'page_code': 'BACKEND_INVENTORY_LIST', 'page_name': '后端仓库存界面', 'menu_code': 'INVENTORY_MANAGEMENT'},
        {'page_code': 'ALL_INVENTORY_LIST', 'page_name': '全仓库存查询', 'menu_code': 'INVENTORY_MANAGEMENT'},
        {'page_code': 'TRANSIT_CARGO_LIST', 'page_name': '在途货物库存', 'menu_code': 'INVENTORY_MANAGEMENT'},
        
        # 其他页面
        {'page_code': 'RECEIVER_LIST', 'page_name': '收货人信息', 'menu_code': 'FRONTEND_OUTBOUND'},
        {'page_code': 'LABEL_PRINT', 'page_name': '标签打印', 'menu_code': 'PRINT_MANAGEMENT'},

        # 管理员页面
        {'page_code': 'USER_MANAGEMENT', 'page_name': '用户管理', 'menu_code': 'ADMIN_MANAGEMENT'},
        {'page_code': 'WAREHOUSE_MANAGEMENT', 'page_name': '仓库管理', 'menu_code': 'ADMIN_MANAGEMENT'},
        {'page_code': 'AUDIT_LOGS', 'page_name': '审计日志', 'menu_code': 'ADMIN_MANAGEMENT'},
        {'page_code': 'OPTIMIZATION_MONITOR', 'page_name': '优化监控', 'menu_code': 'ADMIN_MANAGEMENT'},
    ]
    
    for page_data in pages:
        existing = PagePermission.query.filter_by(page_code=page_data['page_code']).first()
        if not existing:
            page = PagePermission(**page_data)
            db.session.add(page)
            print(f"创建页面权限: {page_data['page_name']}")
    
    db.session.commit()

def assign_admin_permissions():
    """为admin用户分配所有权限"""
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        print("未找到admin用户")
        return
    
    # 分配所有菜单权限
    menus = MenuPermission.query.all()
    for menu in menus:
        existing = UserMenuPermission.query.filter_by(
            user_id=admin_user.id, 
            menu_code=menu.menu_code
        ).first()
        if not existing:
            user_menu = UserMenuPermission(
                user_id=admin_user.id,
                menu_code=menu.menu_code,
                is_granted=True,
                granted_by=admin_user.id
            )
            db.session.add(user_menu)
            print(f"为admin分配菜单权限: {menu.menu_name}")
    
    # 分配所有页面权限
    pages = PagePermission.query.all()
    for page in pages:
        existing = UserPagePermission.query.filter_by(
            user_id=admin_user.id, 
            page_code=page.page_code
        ).first()
        if not existing:
            user_page = UserPagePermission(
                user_id=admin_user.id,
                page_code=page.page_code,
                is_granted=True,
                granted_by=admin_user.id
            )
            db.session.add(user_page)
            print(f"为admin分配页面权限: {page.page_name}")
    
    db.session.commit()

def assign_warehouse_user_permissions():
    """为仓库用户分配基础权限"""
    # 获取所有非admin用户
    users = User.query.filter(User.username != 'admin').all()
    
    for user in users:
        if not user.warehouse_id:
            continue
            
        warehouse = Warehouse.query.get(user.warehouse_id)
        if not warehouse:
            continue
        
        print(f"为用户 {user.username} ({warehouse.warehouse_name}) 分配权限...")
        
        # 根据仓库类型分配权限
        if warehouse.warehouse_type == 'frontend':
            # 前端仓用户权限
            permissions_to_assign = [
                # 菜单权限
                ('menu', 'FRONTEND_INBOUND'),
                ('menu', 'FRONTEND_OUTBOUND'),
                ('menu', 'INVENTORY_MANAGEMENT'),
                ('menu', 'PRINT_MANAGEMENT'),
                # 页面权限
                ('page', 'FRONTEND_INBOUND_OPERATION'),
                ('page', 'FRONTEND_INBOUND_LIST'),
                ('page', 'FRONTEND_RECEIVE_LIST'),
                ('page', 'FRONTEND_OUTBOUND_OPERATION'),
                ('page', 'FRONTEND_OUTBOUND_LIST'),
                ('page', 'FRONTEND_INVENTORY_LIST'),
                ('page', 'RECEIVER_LIST'),
                ('page', 'LABEL_PRINT'),
            ]
        else:
            # 后端仓用户权限
            permissions_to_assign = [
                # 菜单权限
                ('menu', 'BACKEND_INBOUND'),
                ('menu', 'BACKEND_OUTBOUND'),
                ('menu', 'INVENTORY_MANAGEMENT'),
                ('menu', 'PRINT_MANAGEMENT'),
                # 页面权限
                ('page', 'BACKEND_INBOUND_OPERATION'),
                ('page', 'BACKEND_RECEIVE_RECORDS'),
                ('page', 'BACKEND_INBOUND_LIST'),
                ('page', 'BACKEND_OUTBOUND_OPERATION'),
                ('page', 'BACKEND_OUTBOUND_LIST'),
                ('page', 'BACKEND_OUTBOUND_PRINT'),
                ('page', 'BACKEND_INVENTORY_LIST'),
                ('page', 'TRANSIT_CARGO_LIST'),
                ('page', 'LABEL_PRINT'),
            ]
        
        # 分配权限
        for perm_type, perm_code in permissions_to_assign:
            if perm_type == 'menu':
                existing = UserMenuPermission.query.filter_by(
                    user_id=user.id, menu_code=perm_code
                ).first()
                if not existing:
                    user_perm = UserMenuPermission(
                        user_id=user.id,
                        menu_code=perm_code,
                        is_granted=True,
                        granted_by=1  # admin用户ID
                    )
                    db.session.add(user_perm)
            elif perm_type == 'page':
                existing = UserPagePermission.query.filter_by(
                    user_id=user.id, page_code=perm_code
                ).first()
                if not existing:
                    user_perm = UserPagePermission(
                        user_id=user.id,
                        page_code=perm_code,
                        is_granted=True,
                        granted_by=1  # admin用户ID
                    )
                    db.session.add(user_perm)
    
    db.session.commit()

def main():
    """主函数"""
    app = create_app()
    
    with app.app_context():
        print("开始初始化权限系统...")
        
        # 1. 初始化菜单权限
        print("\n1. 初始化菜单权限...")
        init_menu_permissions()
        
        # 2. 初始化页面权限
        print("\n2. 初始化页面权限...")
        init_page_permissions()
        
        # 3. 为admin分配所有权限
        print("\n3. 为admin用户分配权限...")
        assign_admin_permissions()
        
        # 4. 为仓库用户分配基础权限
        print("\n4. 为仓库用户分配权限...")
        assign_warehouse_user_permissions()
        
        print("\n✅ 权限系统初始化完成！")
        print("\n现在用户将只能看到他们有权限访问的菜单和页面。")

if __name__ == '__main__':
    main()
