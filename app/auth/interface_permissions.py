# -*- coding: utf-8 -*-
"""
界面权限检查工具
用于在模板和视图中检查用户的界面权限
"""

from functools import wraps
from flask import current_app, g
from flask_login import current_user


def has_interface_permission(permission_code, warehouse_id=None):
    """
    检查当前用户是否有指定的界面权限
    
    Args:
        permission_code: 权限代码
        warehouse_id: 仓库ID（可选，用于仓库范围限制）
    
    Returns:
        bool: 是否有权限
    """
    if not current_user.is_authenticated:
        return False
    
    # 超级管理员拥有所有权限
    if getattr(current_user, 'is_admin', False) or current_user.username == 'admin':
        return True
    
    # 这里应该查询数据库中的权限配置
    # 目前先返回基于角色的简单判断
    user_warehouse_id = getattr(current_user, 'warehouse_id', None)
    
    # 权限映射规则（实际应该从数据库获取）
    permission_rules = {
        # 菜单权限
        'MENU_INBOUND': ['MANAGER', 'OPERATOR'],
        'MENU_OUTBOUND': ['MANAGER', 'OPERATOR'],
        'MENU_INVENTORY': ['MANAGER', 'OPERATOR'],
        'MENU_ADMIN': ['ADMIN'],
        
        # 页面权限
        'PAGE_INBOUND_LIST': ['MANAGER', 'OPERATOR'],
        'PAGE_OUTBOUND_LIST': ['MANAGER', 'OPERATOR'],
        'PAGE_INVENTORY_LIST': ['MANAGER', 'OPERATOR'],
        
        # 按钮权限
        'BTN_INBOUND_CREATE': ['MANAGER', 'OPERATOR'],
        'BTN_INBOUND_EDIT': ['MANAGER'],
        'BTN_INBOUND_DELETE': ['MANAGER'],
        'BTN_OUTBOUND_CREATE': ['MANAGER', 'OPERATOR'],
        'BTN_OUTBOUND_DELETE': ['MANAGER'],
        'BTN_INVENTORY_EXPORT': ['MANAGER'],
        
        # 跨仓库查看权限
        'VIEW_FRONTEND_INVENTORY': ['MANAGER'],  # 只有经理可以跨仓库查看
        'VIEW_BACKEND_INVENTORY': ['MANAGER'],
        
        # 字段权限
        'FIELD_COST_PRICE': ['MANAGER'],  # 只有经理可以看成本价格
        'FIELD_PROFIT_MARGIN': ['MANAGER'],
    }
    
    # 获取用户角色
    user_roles = get_user_roles(current_user.id)
    
    # 检查权限
    allowed_roles = permission_rules.get(permission_code, [])
    for role_code in user_roles:
        if role_code in allowed_roles:
            # 检查仓库范围限制
            if warehouse_id and user_warehouse_id and warehouse_id != user_warehouse_id:
                # 跨仓库权限检查
                if permission_code.startswith('VIEW_') and role_code == 'MANAGER':
                    return True  # 经理可以跨仓库查看
                return False
            return True
    
    return False


def get_user_roles(user_id):
    """
    获取用户的角色代码列表
    
    Args:
        user_id: 用户ID
    
    Returns:
        list: 角色代码列表
    """
    try:
        from app.models import UserRole, Role
        
        user_roles = UserRole.query.filter_by(
            user_id=user_id,
            status='active'
        ).join(Role).all()
        
        return [ur.role.role_code for ur in user_roles if ur.role]
    except:
        return []


def can_access_warehouse_data(target_warehouse_id):
    """
    检查用户是否可以访问指定仓库的数据
    
    Args:
        target_warehouse_id: 目标仓库ID
    
    Returns:
        bool: 是否可以访问
    """
    if not current_user.is_authenticated:
        return False
    
    # 超级管理员可以访问所有仓库
    if getattr(current_user, 'is_admin', False) or current_user.username == 'admin':
        return True
    
    user_warehouse_id = getattr(current_user, 'warehouse_id', None)
    
    # 用户可以访问自己的仓库
    if user_warehouse_id == target_warehouse_id:
        return True
    
    # 检查跨仓库查看权限
    user_roles = get_user_roles(current_user.id)
    if 'MANAGER' in user_roles:
        # 经理可以跨仓库查看（但不能操作）
        return True
    
    return False


def get_accessible_warehouses():
    """
    获取用户可以访问的仓库列表
    
    Returns:
        list: 仓库ID列表
    """
    if not current_user.is_authenticated:
        return []
    
    # 超级管理员可以访问所有仓库
    if getattr(current_user, 'is_admin', False) or current_user.username == 'admin':
        try:
            from app.models import Warehouse
            warehouses = Warehouse.query.filter_by(status='active').all()
            return [w.id for w in warehouses]
        except:
            return []
    
    user_warehouse_id = getattr(current_user, 'warehouse_id', None)
    accessible_warehouses = []
    
    if user_warehouse_id:
        accessible_warehouses.append(user_warehouse_id)
    
    # 检查跨仓库查看权限
    user_roles = get_user_roles(current_user.id)
    if 'MANAGER' in user_roles:
        try:
            from app.models import Warehouse
            warehouses = Warehouse.query.filter_by(status='active').all()
            for warehouse in warehouses:
                if warehouse.id not in accessible_warehouses:
                    accessible_warehouses.append(warehouse.id)
        except:
            pass
    
    return accessible_warehouses


def filter_data_by_warehouse_permission(query, warehouse_field='warehouse_id'):
    """
    根据用户的仓库权限过滤查询结果
    
    Args:
        query: SQLAlchemy查询对象
        warehouse_field: 仓库字段名
    
    Returns:
        过滤后的查询对象
    """
    if not current_user.is_authenticated:
        return query.filter(False)  # 返回空结果
    
    # 超级管理员可以查看所有数据
    if getattr(current_user, 'is_admin', False) or current_user.username == 'admin':
        return query
    
    # 获取用户可访问的仓库
    accessible_warehouses = get_accessible_warehouses()
    
    if accessible_warehouses:
        return query.filter(getattr(query.column_descriptions[0]['type'], warehouse_field).in_(accessible_warehouses))
    else:
        return query.filter(False)  # 返回空结果


# 模板上下文处理器，在模板中可以使用权限检查函数
def register_template_functions(app):
    """注册模板函数"""
    
    @app.context_processor
    def inject_permission_functions():
        return {
            'has_interface_permission': has_interface_permission,
            'can_access_warehouse_data': can_access_warehouse_data,
            'get_accessible_warehouses': get_accessible_warehouses
        }


# 视图装饰器
def require_interface_permission(permission_code):
    """
    视图装饰器：要求用户有指定的界面权限
    
    Args:
        permission_code: 权限代码
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not has_interface_permission(permission_code):
                from flask import abort
                abort(403)  # 禁止访问
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# 权限配置示例
INTERFACE_PERMISSION_EXAMPLES = {
    # 前端仓库操作员权限配置
    'frontend_operator': {
        'menus': ['MENU_INBOUND', 'MENU_OUTBOUND', 'MENU_INVENTORY'],
        'pages': ['PAGE_INBOUND_LIST', 'PAGE_OUTBOUND_LIST', 'PAGE_INVENTORY_LIST'],
        'buttons': ['BTN_INBOUND_CREATE', 'BTN_OUTBOUND_CREATE'],
        'cross_warehouse': [],  # 不能跨仓库查看
        'fields': []  # 不能看敏感字段
    },
    
    # 前端仓库经理权限配置
    'frontend_manager': {
        'menus': ['MENU_INBOUND', 'MENU_OUTBOUND', 'MENU_INVENTORY'],
        'pages': ['PAGE_INBOUND_LIST', 'PAGE_OUTBOUND_LIST', 'PAGE_INVENTORY_LIST'],
        'buttons': ['BTN_INBOUND_CREATE', 'BTN_INBOUND_EDIT', 'BTN_OUTBOUND_CREATE', 'BTN_INVENTORY_EXPORT'],
        'cross_warehouse': ['VIEW_BACKEND_INVENTORY'],  # 可以查看后端库存
        'fields': ['FIELD_COST_PRICE', 'FIELD_PROFIT_MARGIN']  # 可以看敏感字段
    },
    
    # 后端仓库操作员权限配置
    'backend_operator': {
        'menus': ['MENU_INBOUND', 'MENU_OUTBOUND', 'MENU_INVENTORY'],
        'pages': ['PAGE_INBOUND_LIST', 'PAGE_OUTBOUND_LIST', 'PAGE_INVENTORY_LIST'],
        'buttons': ['BTN_INBOUND_CREATE', 'BTN_OUTBOUND_CREATE'],
        'cross_warehouse': [],  # 不能跨仓库查看
        'fields': []  # 不能看敏感字段
    },
    
    # 后端仓库经理权限配置
    'backend_manager': {
        'menus': ['MENU_INBOUND', 'MENU_OUTBOUND', 'MENU_INVENTORY'],
        'pages': ['PAGE_INBOUND_LIST', 'PAGE_OUTBOUND_LIST', 'PAGE_INVENTORY_LIST'],
        'buttons': ['BTN_INBOUND_CREATE', 'BTN_INBOUND_EDIT', 'BTN_OUTBOUND_CREATE', 'BTN_INVENTORY_EXPORT'],
        'cross_warehouse': ['VIEW_FRONTEND_INVENTORY'],  # 可以查看前端库存
        'fields': ['FIELD_COST_PRICE', 'FIELD_PROFIT_MARGIN']  # 可以看敏感字段
    }
}
