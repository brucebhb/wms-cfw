#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from app import create_app, db
from app.models import User

def test_admin_permissions():
    """测试admin用户权限"""
    app = create_app()
    with app.app_context():
        # 获取admin用户
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            print("未找到admin用户")
            return
        
        print(f'Admin用户信息:')
        print(f'  用户名: {admin_user.username}')
        print(f'  是否管理员: {admin_user.is_admin}')
        print(f'  是否超级管理员: {admin_user.is_super_admin()}')
        print(f'  仓库ID: {admin_user.warehouse_id}')
        
        # 测试权限
        permissions_to_test = [
            'OUTBOUND_DELETE',
            'INBOUND_DELETE',
            'INVENTORY_DELETE',
            'ADMIN_MANAGEMENT'
        ]
        
        print('\n权限测试:')
        for perm in permissions_to_test:
            has_perm = admin_user.has_permission(perm)
            print(f'  {perm}: {has_perm}')
        
        # 测试PXC用户（凭祥北投仓用户）
        pxc_user = User.query.filter_by(username='PXC').first()
        if pxc_user:
            print(f'\nPXC用户信息:')
            print(f'  用户名: {pxc_user.username}')
            print(f'  是否管理员: {pxc_user.is_admin}')
            print(f'  是否超级管理员: {pxc_user.is_super_admin()}')
            print(f'  仓库ID: {pxc_user.warehouse_id}')
            
            print('\nPXC权限测试:')
            for perm in permissions_to_test:
                has_perm = pxc_user.has_permission(perm)
                print(f'  {perm}: {has_perm}')

if __name__ == '__main__':
    test_admin_permissions()
