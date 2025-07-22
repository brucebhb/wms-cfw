# -*- coding: utf-8 -*-
"""
认证和权限装饰器
"""

from functools import wraps
from flask import flash, redirect, url_for, request, jsonify, current_app
from flask_login import current_user

# 全局权限注册表
REGISTERED_PERMISSIONS = {
    'menus': {},
    'pages': {},
    'operations': {}
}


def check_permission(permission_code, warehouse_id=None):
    """
    权限检查装饰器 - 兼容版本
    
    Args:
        permission_code: 权限代码
        warehouse_id: 仓库ID，如果为None则使用当前用户的仓库ID
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 检查用户是否已登录
            if not current_user.is_authenticated:
                if request.is_json:
                    return jsonify({'error': '请先登录'}), 401
                flash('请先登录以访问此页面', 'warning')
                return redirect(url_for('auth.login', next=request.url))
            
            # 超级管理员拥有所有权限，直接通过
            if current_user.username == 'admin' or getattr(current_user, 'is_admin', False):
                return f(*args, **kwargs)

            # 确定要检查的仓库ID
            check_warehouse_id = warehouse_id
            if check_warehouse_id is None:
                check_warehouse_id = getattr(current_user, 'warehouse_id', None)

            # 检查权限
            if hasattr(current_user, 'has_permission'):
                if current_user.has_permission(permission_code, check_warehouse_id):
                    return f(*args, **kwargs)
            else:
                # 如果没有has_permission方法，给仓库用户基本权限
                if getattr(current_user, 'warehouse_id', None):
                    # 仓库用户有基本权限
                    basic_permissions = [
                        'USER_VIEW', 'ROLE_VIEW', 'PERMISSION_VIEW', 'WAREHOUSE_VIEW',
                        'INBOUND_VIEW', 'OUTBOUND_VIEW', 'INVENTORY_VIEW'
                    ]
                    if permission_code in basic_permissions:
                        return f(*args, **kwargs)

            # 权限检查失败
            current_app.logger.warning(
                f"用户 {current_user.username} 尝试访问需要权限 {permission_code} 的功能"
            )
            
            if request.is_json:
                return jsonify({'error': '您没有权限执行此操作'}), 403
            
            flash('您没有权限访问此功能', 'error')
            return redirect(url_for('main.index'))
        
        return decorated_function
    return decorator


def register_menu_permission(menu_code, menu_name, menu_level=1, parent_menu_code=None, menu_order=0, description=None):
    """
    注册菜单权限装饰器

    Args:
        menu_code: 菜单代码
        menu_name: 菜单名称
        menu_level: 菜单层级
        parent_menu_code: 父菜单代码
        menu_order: 菜单排序
        description: 描述
    """
    def decorator(f):
        # 注册菜单权限
        REGISTERED_PERMISSIONS['menus'][menu_code] = {
            'menu_code': menu_code,
            'menu_name': menu_name,
            'menu_level': menu_level,
            'parent_menu_code': parent_menu_code,
            'menu_order': menu_order,
            'description': description or f'{menu_name}菜单权限',
            'is_active': True
        }

        @wraps(f)
        def decorated_function(*args, **kwargs):
            return check_permission(menu_code)(f)(*args, **kwargs)
        return decorated_function
    return decorator


def register_page_permission(page_code, page_name, menu_code=None, page_url=None, description=None):
    """
    注册页面权限装饰器

    Args:
        page_code: 页面代码
        page_name: 页面名称
        menu_code: 所属菜单代码
        page_url: 页面URL
        description: 描述
    """
    def decorator(f):
        # 注册页面权限
        REGISTERED_PERMISSIONS['pages'][page_code] = {
            'page_code': page_code,
            'page_name': page_name,
            'menu_code': menu_code,
            'page_url': page_url,
            'description': description or f'{page_name}页面权限',
            'is_active': True
        }

        @wraps(f)
        def decorated_function(*args, **kwargs):
            return check_permission(page_code)(f)(*args, **kwargs)
        return decorated_function
    return decorator


def register_operation_permission(operation_code, operation_name, page_code=None, operation_type='action', description=None):
    """
    注册操作权限装饰器

    Args:
        operation_code: 操作代码
        operation_name: 操作名称
        page_code: 所属页面代码
        operation_type: 操作类型
        description: 描述
    """
    def decorator(f):
        # 注册操作权限
        REGISTERED_PERMISSIONS['operations'][operation_code] = {
            'operation_code': operation_code,
            'operation_name': operation_name,
            'page_code': page_code,
            'operation_type': operation_type,
            'description': description or f'{operation_name}操作权限',
            'is_active': True
        }

        @wraps(f)
        def decorated_function(*args, **kwargs):
            return check_permission(operation_code)(f)(*args, **kwargs)
        return decorated_function
    return decorator


def require_login(f):
    """
    简单的登录检查装饰器
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            if request.is_json:
                return jsonify({'error': '请先登录'}), 401
            flash('请先登录以访问此页面', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """
    管理员权限检查装饰器
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            if request.is_json:
                return jsonify({'error': '请先登录'}), 401
            flash('请先登录以访问此页面', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        
        if current_user.username != 'admin' and not getattr(current_user, 'is_admin', False):
            if request.is_json:
                return jsonify({'error': '需要管理员权限'}), 403
            flash('只有管理员才能访问此功能', 'error')
            return redirect(url_for('main.index'))
        
        return f(*args, **kwargs)
    return decorated_function


def warehouse_permission(operation_type='view'):
    """
    仓库权限检查装饰器
    
    Args:
        operation_type: 操作类型 ('view', 'create', 'edit', 'delete')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                if request.is_json:
                    return jsonify({'error': '请先登录'}), 401
                flash('请先登录以访问此页面', 'warning')
                return redirect(url_for('auth.login', next=request.url))
            
            # 超级管理员拥有所有权限
            if current_user.username == 'admin' or getattr(current_user, 'is_admin', False):
                return f(*args, **kwargs)
            
            # 检查用户是否属于某个仓库
            if not getattr(current_user, 'warehouse_id', None):
                if request.is_json:
                    return jsonify({'error': '您没有分配到任何仓库'}), 403
                flash('您没有分配到任何仓库，请联系管理员', 'error')
                return redirect(url_for('main.index'))
            
            # 根据操作类型检查权限
            if operation_type in ['create', 'edit', 'delete']:
                # 需要检查是否有编辑权限
                user_roles = getattr(current_user, 'get_roles', lambda: [])()
                role_codes = [role.role_code for role in user_roles] if user_roles else []
                
                if 'MANAGER' not in role_codes and operation_type in ['edit', 'delete']:
                    if request.is_json:
                        return jsonify({'error': '您没有权限执行此操作'}), 403
                    flash('您没有权限执行此操作', 'error')
                    return redirect(url_for('main.index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
