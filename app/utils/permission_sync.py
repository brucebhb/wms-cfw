#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
权限同步工具
自动将装饰器注册的权限同步到数据库
"""

from app import db
from app.models import MenuPermission, PagePermission, OperationPermission
from app.auth.decorators import REGISTERED_PERMISSIONS
from datetime import datetime


def sync_permissions_to_database():
    """
    将装饰器注册的权限同步到数据库
    """
    try:
        sync_count = 0
        
        # 同步菜单权限
        for menu_code, menu_data in REGISTERED_PERMISSIONS['menus'].items():
            existing = MenuPermission.query.filter_by(menu_code=menu_code).first()
            if not existing:
                menu_permission = MenuPermission(
                    menu_code=menu_data['menu_code'],
                    menu_name=menu_data['menu_name'],
                    menu_level=menu_data['menu_level'],
                    parent_menu_code=menu_data['parent_menu_code'],
                    menu_order=menu_data['menu_order'],
                    description=menu_data['description'],
                    is_active=menu_data['is_active']
                )
                db.session.add(menu_permission)
                sync_count += 1
                print(f"新增菜单权限: {menu_code} - {menu_data['menu_name']}")
        
        # 同步页面权限
        for page_code, page_data in REGISTERED_PERMISSIONS['pages'].items():
            existing = PagePermission.query.filter_by(page_code=page_code).first()
            if not existing:
                page_permission = PagePermission(
                    page_code=page_data['page_code'],
                    page_name=page_data['page_name'],
                    menu_code=page_data['menu_code'],
                    page_url=page_data['page_url'],
                    description=page_data['description'],
                    is_active=page_data['is_active']
                )
                db.session.add(page_permission)
                sync_count += 1
                print(f"新增页面权限: {page_code} - {page_data['page_name']}")
        
        # 同步操作权限
        for operation_code, operation_data in REGISTERED_PERMISSIONS['operations'].items():
            existing = OperationPermission.query.filter_by(operation_code=operation_code).first()
            if not existing:
                operation_permission = OperationPermission(
                    operation_code=operation_data['operation_code'],
                    operation_name=operation_data['operation_name'],
                    page_code=operation_data['page_code'],
                    operation_type=operation_data['operation_type'],
                    description=operation_data['description'],
                    is_active=operation_data['is_active']
                )
                db.session.add(operation_permission)
                sync_count += 1
                print(f"新增操作权限: {operation_code} - {operation_data['operation_name']}")
        
        db.session.commit()
        print(f"权限同步完成，共同步 {sync_count} 个权限")
        return True, f"成功同步 {sync_count} 个权限"
        
    except Exception as e:
        db.session.rollback()
        print(f"权限同步失败: {str(e)}")
        return False, f"权限同步失败: {str(e)}"


def get_registered_permissions():
    """
    获取所有注册的权限
    """
    return REGISTERED_PERMISSIONS


def clear_registered_permissions():
    """
    清空注册的权限（用于测试）
    """
    REGISTERED_PERMISSIONS['menus'].clear()
    REGISTERED_PERMISSIONS['pages'].clear()
    REGISTERED_PERMISSIONS['operations'].clear()


def register_default_permissions():
    """
    注册默认的系统权限
    """
    # 注册基础菜单权限
    default_menus = [
        {
            'menu_code': 'FRONTEND_INBOUND',
            'menu_name': '前端仓入库',
            'menu_level': 1,
            'parent_menu_code': None,
            'menu_order': 1,
            'description': '前端仓入库管理菜单'
        },
        {
            'menu_code': 'FRONTEND_OUTBOUND',
            'menu_name': '前端仓出库',
            'menu_level': 1,
            'parent_menu_code': None,
            'menu_order': 2,
            'description': '前端仓出库管理菜单'
        },
        {
            'menu_code': 'BACKEND_INBOUND',
            'menu_name': '后端仓入库',
            'menu_level': 1,
            'parent_menu_code': None,
            'menu_order': 3,
            'description': '后端仓入库管理菜单'
        },
        {
            'menu_code': 'BACKEND_OUTBOUND',
            'menu_name': '后端仓出库',
            'menu_level': 1,
            'parent_menu_code': None,
            'menu_order': 4,
            'description': '后端仓出库管理菜单'
        },
        {
            'menu_code': 'INVENTORY_MANAGEMENT',
            'menu_name': '库存管理',
            'menu_level': 1,
            'parent_menu_code': None,
            'menu_order': 5,
            'description': '库存管理菜单'
        },
        {
            'menu_code': 'PRINT_MANAGEMENT',
            'menu_name': '单据打印',
            'menu_level': 1,
            'parent_menu_code': None,
            'menu_order': 6,
            'description': '单据打印菜单'
        },
        {
            'menu_code': 'ADMIN_MANAGEMENT',
            'menu_name': '系统管理',
            'menu_level': 1,
            'parent_menu_code': None,
            'menu_order': 7,
            'description': '系统管理菜单'
        }
    ]
    
    # 注册基础页面权限
    default_pages = [
        {
            'page_code': 'FRONTEND_INBOUND_LIST',
            'page_name': '前端仓入库记录',
            'menu_code': 'FRONTEND_INBOUND',
            'page_url': '/frontend/inbound/list',
            'description': '前端仓入库记录页面'
        },
        {
            'page_code': 'FRONTEND_RECEIVE_LIST',
            'page_name': '前端仓接收记录',
            'menu_code': 'FRONTEND_INBOUND',
            'page_url': '/frontend/receive/list',
            'description': '前端仓接收记录页面'
        },
        {
            'page_code': 'BACKEND_INBOUND_LIST',
            'page_name': '后端仓入库记录',
            'menu_code': 'BACKEND_INBOUND',
            'page_url': '/backend/inbound/list',
            'description': '后端仓入库记录页面'
        },
        {
            'page_code': 'FRONTEND_OUTBOUND_LIST',
            'page_name': '前端仓出库记录',
            'menu_code': 'FRONTEND_OUTBOUND',
            'page_url': '/frontend/outbound/list',
            'description': '前端仓出库记录页面'
        },
        {
            'page_code': 'BACKEND_OUTBOUND_LIST',
            'page_name': '后端仓出库记录',
            'menu_code': 'BACKEND_OUTBOUND',
            'page_url': '/backend/outbound/list',
            'description': '后端仓出库记录页面'
        },
        {
            'page_code': 'RECEIVER_LIST',
            'page_name': '收货人信息管理',
            'menu_code': 'FRONTEND_OUTBOUND',
            'page_url': '/receiver/list',
            'description': '收货人信息管理页面'
        },
        {
            'page_code': 'OPTIMIZATION_MONITOR',
            'page_name': '优化监控',
            'menu_code': 'ADMIN_MANAGEMENT',
            'page_url': '/admin/optimization-monitor',
            'description': '系统优化监控页面'
        },
        {
            'page_code': 'BACKEND_OUTBOUND_PRINT',
            'page_name': '后端仓出库单页面',
            'menu_code': 'BACKEND_OUTBOUND',
            'page_url': '/backend/outbound/print',
            'description': '后端仓出库单打印页面'
        }
    ]
    
    # 将默认权限添加到注册表
    for menu in default_menus:
        REGISTERED_PERMISSIONS['menus'][menu['menu_code']] = menu
    
    for page in default_pages:
        REGISTERED_PERMISSIONS['pages'][page['page_code']] = page
    
    print(f"已注册 {len(default_menus)} 个菜单权限和 {len(default_pages)} 个页面权限")


def auto_sync_permissions():
    """
    自动同步权限（在应用启动时调用）
    """
    try:
        # 先注册默认权限
        register_default_permissions()
        
        # 然后同步到数据库
        success, message = sync_permissions_to_database()
        
        if success:
            print("✅ 权限自动同步完成")
        else:
            print(f"❌ 权限自动同步失败: {message}")
            
        return success, message
        
    except Exception as e:
        print(f"❌ 权限自动同步异常: {str(e)}")
        return False, str(e)
