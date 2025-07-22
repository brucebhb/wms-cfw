#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from app import create_app, db
from app.models import User, Permission, Warehouse, UserRole, Role

def check_user_permissions():
    """检查用户权限"""
    app = create_app()
    with app.app_context():
        print('检查用户权限')
        print('=' * 60)
        
        # 查看所有用户
        users = User.query.all()
        print(f'系统中的用户数量: {len(users)}')
        
        for user in users:
            print(f'\n用户: {user.username}')
            print(f'  ID: {user.id}')
            print(f'  仓库ID: {user.warehouse_id}')
            if user.warehouse:
                print(f'  仓库名称: {user.warehouse.warehouse_name}')
            print(f'  状态: {user.status}')
            print(f'  用户类型: {user.user_type}')
            print(f'  是否管理员: {user.is_admin}')

            # 检查用户角色
            user_roles = UserRole.query.filter_by(user_id=user.id, status='active').all()
            print(f'  角色数量: {len(user_roles)}')

            for user_role in user_roles:
                role = Role.query.get(user_role.role_id)
                if role:
                    print(f'    角色: {role.name}')
                    print(f'    角色描述: {role.description}')

                    # 检查角色权限
                    if hasattr(role, 'permissions'):
                        permissions = [p.name for p in role.permissions]
                        print(f'    权限: {permissions}')

                        # 检查是否有OUTBOUND_DELETE权限
                        has_outbound_delete = any(p.name == 'OUTBOUND_DELETE' for p in role.permissions)
                        print(f'    有出库删除权限: {has_outbound_delete}')
                    else:
                        print(f'    权限: 无权限关联')

            if len(user_roles) == 0:
                print(f'  无角色分配')
        
        print('\n' + '=' * 60)
        print('仓库信息:')
        warehouses = Warehouse.query.all()
        for warehouse in warehouses:
            print(f'  ID: {warehouse.id}, 名称: {warehouse.warehouse_name}, 类型: {warehouse.warehouse_type}')

if __name__ == '__main__':
    check_user_permissions()
