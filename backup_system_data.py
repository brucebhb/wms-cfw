#!/usr/bin/env python3
"""
系统数据备份脚本
备份用户信息、收货人信息、仓库信息等重要数据
"""

import json
import os
from datetime import datetime
from app import create_app
from app.models import db, User, Receiver, Warehouse, UserMenuPermission, UserPagePermission, UserOperationPermission, UserWarehousePermission

def backup_system_data():
    """备份系统重要数据"""
    app = create_app()
    with app.app_context():
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_dir = 'backups'
            
            # 创建备份目录
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
                print(f"创建备份目录: {backup_dir}")
            
            print(f"开始备份系统数据 - {timestamp}")
            
            # 1. 备份用户信息
            print("\n📋 备份用户信息...")
            users = User.query.all()
            users_data = []
            
            for user in users:
                user_data = {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'password_hash': user.password_hash,
                    'real_name': user.real_name,
                    'phone': getattr(user, 'phone', None),
                    'employee_id': getattr(user, 'employee_id', None),
                    'user_type': user.user_type,
                    'warehouse_id': user.warehouse_id,
                    'is_admin': getattr(user, 'is_admin', False),
                    'status': getattr(user, 'status', 'active'),
                    'created_at': user.created_at.isoformat() if user.created_at else None,
                    'updated_at': user.updated_at.isoformat() if user.updated_at else None,
                    'last_login_at': user.last_login_at.isoformat() if user.last_login_at else None
                }
                users_data.append(user_data)
            
            users_file = os.path.join(backup_dir, f'users_backup_{timestamp}.json')
            with open(users_file, 'w', encoding='utf-8') as f:
                json.dump(users_data, f, ensure_ascii=False, indent=2)
            print(f"✅ 用户信息已备份到: {users_file} ({len(users_data)} 个用户)")
            
            # 2. 备份收货人信息
            print("\n📋 备份收货人信息...")
            receivers = Receiver.query.all()
            receivers_data = []

            for receiver in receivers:
                receiver_data = {
                    'id': receiver.id,
                    'warehouse_name': receiver.warehouse_name,
                    'address': receiver.address,
                    'contact': receiver.contact,
                    'phone': getattr(receiver, 'phone', None),
                    'is_active': getattr(receiver, 'is_active', True),
                    'created_at': receiver.created_at.isoformat() if hasattr(receiver, 'created_at') and receiver.created_at else None,
                    'updated_at': receiver.updated_at.isoformat() if hasattr(receiver, 'updated_at') and receiver.updated_at else None
                }
                receivers_data.append(receiver_data)
            
            receivers_file = os.path.join(backup_dir, f'receivers_backup_{timestamp}.json')
            with open(receivers_file, 'w', encoding='utf-8') as f:
                json.dump(receivers_data, f, ensure_ascii=False, indent=2)
            print(f"✅ 收货人信息已备份到: {receivers_file} ({len(receivers_data)} 个收货人)")
            
            # 3. 备份仓库信息
            print("\n📋 备份仓库信息...")
            warehouses = Warehouse.query.all()
            warehouses_data = []
            
            for warehouse in warehouses:
                warehouse_data = {
                    'id': warehouse.id,
                    'warehouse_name': warehouse.warehouse_name,
                    'warehouse_code': warehouse.warehouse_code,
                    'warehouse_type': warehouse.warehouse_type,
                    'address': warehouse.address,
                    'contact_person': warehouse.contact_person,
                    'contact_phone': warehouse.contact_phone,
                    'status': warehouse.status,
                    'created_at': warehouse.created_at.isoformat() if warehouse.created_at else None,
                    'updated_at': warehouse.updated_at.isoformat() if warehouse.updated_at else None
                }
                warehouses_data.append(warehouse_data)
            
            warehouses_file = os.path.join(backup_dir, f'warehouses_backup_{timestamp}.json')
            with open(warehouses_file, 'w', encoding='utf-8') as f:
                json.dump(warehouses_data, f, ensure_ascii=False, indent=2)
            print(f"✅ 仓库信息已备份到: {warehouses_file} ({len(warehouses_data)} 个仓库)")
            
            # 4. 备份用户权限信息
            print("\n📋 备份用户权限信息...")
            permissions_data = {
                'menu_permissions': [],
                'page_permissions': [],
                'operation_permissions': [],
                'warehouse_permissions': []
            }
            
            # 菜单权限
            menu_perms = UserMenuPermission.query.all()
            for perm in menu_perms:
                permissions_data['menu_permissions'].append({
                    'id': perm.id,
                    'user_id': perm.user_id,
                    'menu_code': perm.menu_code,
                    'is_granted': perm.is_granted,
                    'granted_by': getattr(perm, 'granted_by', None),
                    'granted_at': perm.granted_at.isoformat() if perm.granted_at else None
                })
            
            # 页面权限
            page_perms = UserPagePermission.query.all()
            for perm in page_perms:
                permissions_data['page_permissions'].append({
                    'id': perm.id,
                    'user_id': perm.user_id,
                    'page_code': perm.page_code,
                    'is_granted': perm.is_granted,
                    'granted_by': getattr(perm, 'granted_by', None),
                    'granted_at': perm.granted_at.isoformat() if perm.granted_at else None
                })
            
            # 操作权限
            op_perms = UserOperationPermission.query.all()
            for perm in op_perms:
                permissions_data['operation_permissions'].append({
                    'id': perm.id,
                    'user_id': perm.user_id,
                    'operation_code': perm.operation_code,
                    'is_granted': perm.is_granted,
                    'granted_by': getattr(perm, 'granted_by', None),
                    'granted_at': perm.granted_at.isoformat() if perm.granted_at else None
                })
            
            # 仓库权限
            wh_perms = UserWarehousePermission.query.all()
            for perm in wh_perms:
                permissions_data['warehouse_permissions'].append({
                    'id': perm.id,
                    'user_id': perm.user_id,
                    'warehouse_id': perm.warehouse_id,
                    'warehouse_permission_code': perm.warehouse_permission_code,
                    'is_granted': perm.is_granted,
                    'granted_by': getattr(perm, 'granted_by', None),
                    'granted_at': perm.granted_at.isoformat() if perm.granted_at else None
                })
            
            permissions_file = os.path.join(backup_dir, f'permissions_backup_{timestamp}.json')
            with open(permissions_file, 'w', encoding='utf-8') as f:
                json.dump(permissions_data, f, ensure_ascii=False, indent=2)
            
            total_perms = (len(permissions_data['menu_permissions']) + 
                          len(permissions_data['page_permissions']) + 
                          len(permissions_data['operation_permissions']) + 
                          len(permissions_data['warehouse_permissions']))
            print(f"✅ 用户权限已备份到: {permissions_file} ({total_perms} 个权限记录)")
            
            # 5. 创建备份摘要
            summary = {
                'backup_time': timestamp,
                'backup_files': {
                    'users': users_file,
                    'receivers': receivers_file,
                    'warehouses': warehouses_file,
                    'permissions': permissions_file
                },
                'record_counts': {
                    'users': len(users_data),
                    'receivers': len(receivers_data),
                    'warehouses': len(warehouses_data),
                    'total_permissions': total_perms,
                    'menu_permissions': len(permissions_data['menu_permissions']),
                    'page_permissions': len(permissions_data['page_permissions']),
                    'operation_permissions': len(permissions_data['operation_permissions']),
                    'warehouse_permissions': len(permissions_data['warehouse_permissions'])
                }
            }
            
            summary_file = os.path.join(backup_dir, f'backup_summary_{timestamp}.json')
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            
            print(f"\n🎉 系统数据备份完成!")
            print(f"📁 备份目录: {backup_dir}")
            print(f"📄 备份摘要: {summary_file}")
            print(f"⏰ 备份时间: {timestamp}")
            
            print(f"\n📊 备份统计:")
            print(f"  👥 用户: {len(users_data)} 个")
            print(f"  📮 收货人: {len(receivers_data)} 个")
            print(f"  🏢 仓库: {len(warehouses_data)} 个")
            print(f"  🔐 权限记录: {total_perms} 个")
            
            return True
            
        except Exception as e:
            print(f"❌ 备份失败: {str(e)}")
            return False

if __name__ == '__main__':
    backup_system_data()
