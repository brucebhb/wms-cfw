#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导出本地数据库的完整数据
"""

import json
from datetime import datetime
from app import create_app, db
from app.models import *
from config import Config

def export_local_data():
    """导出本地数据库的所有基础数据"""
    app = create_app(Config)
    with app.app_context():
        print('🚀 开始导出本地数据库数据...')
        
        export_data = {}
        
        # 1. 导出用户数据
        print('👤 导出用户数据...')
        users = User.query.all()
        export_data['users'] = []
        for user in users:
            user_data = {
                'username': user.username,
                'password_hash': user.password_hash,  # 直接导出密码哈希
                'real_name': user.real_name,
                'email': user.email,
                'phone': user.phone,
                'employee_id': user.employee_id,
                'warehouse_id': user.warehouse_id,
                'user_type': user.user_type,
                'is_admin': user.is_admin,
                'status': user.status,
                'last_login_at': user.last_login_at.isoformat() if user.last_login_at else None,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'updated_at': user.updated_at.isoformat() if user.updated_at else None
            }
            export_data['users'].append(user_data)
            print(f'  - {user.real_name} ({user.username})')
        
        # 2. 导出仓库数据
        print('\n📦 导出仓库数据...')
        warehouses = Warehouse.query.all()
        export_data['warehouses'] = []
        for wh in warehouses:
            wh_data = {
                'warehouse_code': wh.warehouse_code,
                'warehouse_name': wh.warehouse_name,
                'warehouse_type': wh.warehouse_type,
                'address': wh.address,
                'contact_person': wh.contact_person,
                'contact_phone': wh.contact_phone,
                'status': wh.status,
                'created_at': wh.created_at.isoformat() if wh.created_at else None,
                'updated_at': wh.updated_at.isoformat() if wh.updated_at else None
            }
            export_data['warehouses'].append(wh_data)
            print(f'  - {wh.warehouse_name} ({wh.warehouse_code})')
        
        # 3. 导出角色数据
        print('\n🎭 导出角色数据...')
        roles = Role.query.all()
        export_data['roles'] = []
        for role in roles:
            role_data = {
                'role_code': role.role_code,
                'role_name': role.role_name,
                'role_level': role.role_level,
                'description': role.description,
                'status': role.status,
                'created_at': role.created_at.isoformat() if role.created_at else None,
                'updated_at': role.updated_at.isoformat() if role.updated_at else None
            }
            export_data['roles'].append(role_data)
            print(f'  - {role.role_name} ({role.role_code})')
        
        # 4. 导出菜单权限
        print('\n🔐 导出菜单权限...')
        menu_perms = MenuPermission.query.all()
        export_data['menu_permissions'] = []
        for mp in menu_perms:
            mp_data = {
                'menu_code': mp.menu_code,
                'menu_name': mp.menu_name,
                'parent_menu_code': mp.parent_menu_code,
                'menu_level': mp.menu_level,
                'menu_order': mp.menu_order,
                'menu_icon': mp.menu_icon,
                'menu_url': mp.menu_url,
                'description': mp.description,
                'is_active': mp.is_active,
                'created_at': mp.created_at.isoformat() if mp.created_at else None
            }
            export_data['menu_permissions'].append(mp_data)
            print(f'  - {mp.menu_name} ({mp.menu_code})')
        
        # 5. 导出页面权限
        print('\n📄 导出页面权限...')
        page_perms = PagePermission.query.all()
        export_data['page_permissions'] = []
        for pp in page_perms:
            pp_data = {
                'page_code': pp.page_code,
                'page_name': pp.page_name,
                'page_url': pp.page_url,
                'description': pp.description,
                'is_active': pp.is_active,
                'created_at': pp.created_at.isoformat() if pp.created_at else None
            }
            export_data['page_permissions'].append(pp_data)
            print(f'  - {pp.page_name} ({pp.page_code})')
        
        # 6. 导出操作权限（如果存在）
        try:
            print('\n⚡ 导出操作权限...')
            op_perms = OperationPermission.query.all()
            export_data['operation_permissions'] = []
            for op in op_perms:
                op_data = {
                    'operation_code': op.operation_code,
                    'operation_name': op.operation_name,
                    'operation_type': op.operation_type,
                    'description': op.description,
                    'is_active': op.is_active,
                    'created_at': op.created_at.isoformat() if op.created_at else None
                }
                export_data['operation_permissions'].append(op_data)
                print(f'  - {op.operation_name} ({op.operation_code})')
        except Exception as e:
            print(f'  操作权限表不存在或出错: {e}')
            export_data['operation_permissions'] = []
        
        # 7. 导出用户菜单权限关联
        print('\n🔗 导出用户菜单权限关联...')
        user_menu_perms = UserMenuPermission.query.all()
        export_data['user_menu_permissions'] = []
        for ump in user_menu_perms:
            ump_data = {
                'user_id': ump.user_id,
                'menu_code': ump.menu_code,
                'is_granted': ump.is_granted,
                'granted_by': ump.granted_by,
                'granted_at': ump.granted_at.isoformat() if ump.granted_at else None
            }
            export_data['user_menu_permissions'].append(ump_data)
        print(f'  - 用户菜单权限关联: {len(user_menu_perms)} 条')
        
        # 8. 导出用户页面权限关联
        print('\n📄 导出用户页面权限关联...')
        user_page_perms = UserPagePermission.query.all()
        export_data['user_page_permissions'] = []
        for upp in user_page_perms:
            upp_data = {
                'user_id': upp.user_id,
                'page_code': upp.page_code,
                'is_granted': upp.is_granted,
                'granted_by': upp.granted_by,
                'granted_at': upp.granted_at.isoformat() if upp.granted_at else None
            }
            export_data['user_page_permissions'].append(upp_data)
        print(f'  - 用户页面权限关联: {len(user_page_perms)} 条')
        
        # 9. 导出收货人数据
        print('\n📮 导出收货人数据...')
        receivers = Receiver.query.all()
        export_data['receivers'] = []
        for receiver in receivers:
            receiver_data = {
                'warehouse_name': receiver.warehouse_name,
                'address': receiver.address,
                'contact': receiver.contact
            }
            export_data['receivers'].append(receiver_data)
            print(f'  - {receiver.warehouse_name}: {receiver.contact}')
        
        # 10. 导出其他基础数据
        try:
            print('\n🏷️ 导出标签代码...')
            label_codes = LabelCode.query.all()
            export_data['label_codes'] = []
            for lc in label_codes:
                lc_data = {
                    'code': lc.code,
                    'description': lc.description,
                    'is_active': lc.is_active,
                    'created_at': lc.created_at.isoformat() if lc.created_at else None
                }
                export_data['label_codes'].append(lc_data)
            print(f'  - 标签代码: {len(label_codes)} 条')
        except Exception as e:
            print(f'  标签代码表不存在或出错: {e}')
            export_data['label_codes'] = []
        
        # 保存到JSON文件
        export_file = 'local_data_export.json'
        with open(export_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        print(f'\n✅ 数据导出完成！保存到文件: {export_file}')
        print(f'📊 导出统计:')
        print(f'  - 用户: {len(export_data["users"])} 个')
        print(f'  - 仓库: {len(export_data["warehouses"])} 个')
        print(f'  - 角色: {len(export_data["roles"])} 个')
        print(f'  - 菜单权限: {len(export_data["menu_permissions"])} 个')
        print(f'  - 页面权限: {len(export_data["page_permissions"])} 个')
        print(f'  - 操作权限: {len(export_data["operation_permissions"])} 个')
        print(f'  - 用户菜单权限: {len(export_data["user_menu_permissions"])} 条')
        print(f'  - 用户页面权限: {len(export_data["user_page_permissions"])} 条')
        print(f'  - 收货人: {len(export_data["receivers"])} 个')
        print(f'  - 标签代码: {len(export_data["label_codes"])} 个')

if __name__ == '__main__':
    export_local_data()
