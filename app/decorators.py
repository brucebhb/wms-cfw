#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
权限控制装饰器
"""

from functools import wraps
from flask import flash, redirect, url_for, request, jsonify, current_app
from flask_login import current_user

def require_permission(permission_code, warehouse_id=None):
    """
    权限检查装饰器
    
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
            
            # 系统管理员拥有所有权限，直接通过
            if hasattr(current_user, 'has_role') and current_user.has_role('SYSTEM_ADMIN'):
                return f(*args, **kwargs)

            # 确定要检查的仓库ID
            check_warehouse_id = warehouse_id
            if check_warehouse_id is None:
                check_warehouse_id = current_user.warehouse_id

            # 检查权限
            if not current_user.has_permission(permission_code, check_warehouse_id):
                current_app.logger.warning(
                    f"用户 {current_user.username} 尝试访问需要权限 {permission_code} 的功能"
                )
                
                if request.is_json:
                    return jsonify({'error': '您没有权限执行此操作'}), 403
                
                flash('您没有权限访问此功能', 'error')
                return redirect(url_for('main.index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_any_permission(*permission_codes, warehouse_id=None):
    """
    检查用户是否拥有任意一个权限
    
    Args:
        permission_codes: 权限代码列表
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
            
            # 系统管理员拥有所有权限，直接通过
            if hasattr(current_user, 'has_role') and current_user.has_role('SYSTEM_ADMIN'):
                return f(*args, **kwargs)

            # 确定要检查的仓库ID
            check_warehouse_id = warehouse_id
            if check_warehouse_id is None:
                check_warehouse_id = current_user.warehouse_id

            # 检查是否拥有任意一个权限
            has_permission = False
            for permission_code in permission_codes:
                if current_user.has_permission(permission_code, check_warehouse_id):
                    has_permission = True
                    break

            if not has_permission:
                current_app.logger.warning(
                    f"用户 {current_user.username} 尝试访问需要权限 {permission_codes} 中任意一个的功能"
                )
                
                if request.is_json:
                    return jsonify({'error': '您没有权限执行此操作'}), 403
                
                flash('您没有权限访问此功能', 'error')
                return redirect(url_for('main.index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_all_permissions(*permission_codes, warehouse_id=None):
    """
    检查用户是否拥有所有权限
    
    Args:
        permission_codes: 权限代码列表
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
            
            # 系统管理员拥有所有权限，直接通过
            if hasattr(current_user, 'has_role') and current_user.has_role('SYSTEM_ADMIN'):
                return f(*args, **kwargs)

            # 确定要检查的仓库ID
            check_warehouse_id = warehouse_id
            if check_warehouse_id is None:
                check_warehouse_id = current_user.warehouse_id

            # 检查是否拥有所有权限
            missing_permissions = []
            for permission_code in permission_codes:
                if not current_user.has_permission(permission_code, check_warehouse_id):
                    missing_permissions.append(permission_code)

            if missing_permissions:
                current_app.logger.warning(
                    f"用户 {current_user.username} 缺少权限: {missing_permissions}"
                )
                
                if request.is_json:
                    return jsonify({'error': f'您缺少以下权限: {", ".join(missing_permissions)}'}), 403
                
                flash('您没有足够的权限访问此功能', 'error')
                return redirect(url_for('main.index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def warehouse_data_filter(query, model_class, warehouse_field='warehouse_id', operation_type='view'):
    """
    根据用户权限过滤仓库数据

    Args:
        query: SQLAlchemy查询对象
        model_class: 模型类
        warehouse_field: 仓库字段名，默认为'warehouse_id'
        operation_type: 操作类型，'view'(查看) 或 'edit'(编辑)

    Returns:
        过滤后的查询对象
    """
    if not current_user.is_authenticated:
        # 未登录用户返回空查询
        return query.filter(False)

    # 检查用户是否有系统管理员权限
    if hasattr(current_user, 'has_permission') and current_user.has_permission('SYSTEM_CONFIG'):
        # 系统管理员可以查看和操作所有数据
        return query

    # 获取用户仓库信息
    if hasattr(current_user, 'warehouse') and current_user.warehouse:
        user_warehouse_type = current_user.warehouse.warehouse_type
        user_warehouse_id = current_user.warehouse_id

        warehouse_attr = getattr(model_class, warehouse_field, None)
        if warehouse_attr:
            if operation_type == 'edit':
                # 编辑操作：只能操作自己仓库的数据
                return query.filter(warehouse_attr == user_warehouse_id)
            else:
                # 查看操作：可以查看所有仓库的数据，但有不同的显示权限
                return query

    # 没有仓库权限，返回空查询
    return query.filter(False)


def check_warehouse_operation_permission(target_warehouse_id, operation_type='view'):
    """
    检查用户对特定仓库的操作权限

    Args:
        target_warehouse_id: 目标仓库ID
        operation_type: 操作类型，'view'(查看) 或 'edit'(编辑)

    Returns:
        bool: 是否有权限
    """
    if not current_user.is_authenticated:
        return False

    # 系统管理员有所有权限
    if hasattr(current_user, 'has_permission') and current_user.has_permission('SYSTEM_CONFIG'):
        return True

    # 获取用户仓库信息
    if hasattr(current_user, 'warehouse') and current_user.warehouse:
        user_warehouse_id = current_user.warehouse_id

        if operation_type in ['create', 'edit', 'delete']:
            # 创建、编辑、删除操作：只能操作自己仓库的数据
            return user_warehouse_id == target_warehouse_id
        else:
            # 查看操作：可以查看所有仓库的数据
            return True

    return False


def log_operation(module, action, resource_type=None, resource_id=None, old_values=None, new_values=None):
    """
    记录操作审计日志的装饰器
    
    Args:
        module: 模块名称
        action: 操作类型
        resource_type: 资源类型
        resource_id: 资源ID
        old_values: 修改前的值
        new_values: 修改后的值
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 执行原函数
            result = f(*args, **kwargs)
            
            # 记录审计日志
            if current_user.is_authenticated:
                try:
                    from app.models import AuditLog
                    from app import db
                    
                    audit_log = AuditLog(
                        user_id=current_user.id,
                        warehouse_id=current_user.warehouse_id,
                        module=module,
                        action=action,
                        resource_type=resource_type,
                        resource_id=str(resource_id) if resource_id else None,
                        old_values=old_values,
                        new_values=new_values,
                        ip_address=request.remote_addr,
                        user_agent=request.headers.get('User-Agent')
                    )
                    
                    db.session.add(audit_log)
                    db.session.commit()
                    
                except Exception as e:
                    current_app.logger.error(f"记录审计日志失败: {e}")
            
            return result
        return decorated_function
    return decorator
