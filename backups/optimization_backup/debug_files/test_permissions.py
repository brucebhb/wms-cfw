#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
权限系统测试脚本
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User
from app.utils.permission_manager import PermissionManager

def test_user_permissions():
    """测试用户权限"""
    app = create_app()
    
    with app.app_context():
        print("🔍 权限系统测试")
        print("=" * 50)
        
        # 测试admin用户
        admin_user = User.query.filter_by(username='admin').first()
        if admin_user:
            print(f"\n👑 Admin用户 ({admin_user.username}):")
            print(f"  - 是否为超级管理员: {admin_user.is_super_admin()}")
            print(f"  - 菜单权限 FRONTEND_INBOUND: {PermissionManager.has_menu_permission(admin_user.id, 'FRONTEND_INBOUND')}")
            print(f"  - 菜单权限 ADMIN_MANAGEMENT: {PermissionManager.has_menu_permission(admin_user.id, 'ADMIN_MANAGEMENT')}")
            print(f"  - 页面权限 USER_MANAGEMENT: {PermissionManager.has_page_permission(admin_user.id, 'USER_MANAGEMENT')}")
        
        # 测试前端仓用户
        frontend_users = User.query.join(User.warehouse).filter_by(warehouse_type='frontend').limit(2).all()
        for user in frontend_users:
            print(f"\n🏭 前端仓用户 ({user.username} - {user.warehouse.warehouse_name}):")
            print(f"  - 菜单权限 FRONTEND_INBOUND: {PermissionManager.has_menu_permission(user.id, 'FRONTEND_INBOUND')}")
            print(f"  - 菜单权限 BACKEND_INBOUND: {PermissionManager.has_menu_permission(user.id, 'BACKEND_INBOUND')}")
            print(f"  - 菜单权限 ADMIN_MANAGEMENT: {PermissionManager.has_menu_permission(user.id, 'ADMIN_MANAGEMENT')}")
            print(f"  - 页面权限 FRONTEND_INBOUND_OPERATION: {PermissionManager.has_page_permission(user.id, 'FRONTEND_INBOUND_OPERATION')}")
            print(f"  - 页面权限 BACKEND_INBOUND_OPERATION: {PermissionManager.has_page_permission(user.id, 'BACKEND_INBOUND_OPERATION')}")
        
        # 测试后端仓用户
        backend_users = User.query.join(User.warehouse).filter_by(warehouse_type='backend').limit(2).all()
        for user in backend_users:
            print(f"\n🚛 后端仓用户 ({user.username} - {user.warehouse.warehouse_name}):")
            print(f"  - 菜单权限 FRONTEND_INBOUND: {PermissionManager.has_menu_permission(user.id, 'FRONTEND_INBOUND')}")
            print(f"  - 菜单权限 BACKEND_INBOUND: {PermissionManager.has_menu_permission(user.id, 'BACKEND_INBOUND')}")
            print(f"  - 菜单权限 ADMIN_MANAGEMENT: {PermissionManager.has_menu_permission(user.id, 'ADMIN_MANAGEMENT')}")
            print(f"  - 页面权限 FRONTEND_INBOUND_OPERATION: {PermissionManager.has_page_permission(user.id, 'FRONTEND_INBOUND_OPERATION')}")
            print(f"  - 页面权限 BACKEND_INBOUND_OPERATION: {PermissionManager.has_page_permission(user.id, 'BACKEND_INBOUND_OPERATION')}")
        
        print("\n" + "=" * 50)
        print("✅ 权限测试完成")
        
        # 统计信息
        from app.models import UserMenuPermission, UserPagePermission
        total_menu_perms = UserMenuPermission.query.filter_by(is_granted=True).count()
        total_page_perms = UserPagePermission.query.filter_by(is_granted=True).count()
        total_users = User.query.filter(User.username != 'admin').count()
        
        print(f"\n📊 权限统计:")
        print(f"  - 总用户数: {total_users + 1} (包含admin)")
        print(f"  - 菜单权限分配: {total_menu_perms} 条")
        print(f"  - 页面权限分配: {total_page_perms} 条")

if __name__ == '__main__':
    test_user_permissions()
