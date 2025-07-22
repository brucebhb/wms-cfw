#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户权限管理API路由
"""

from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db, csrf
from app.models import User, Warehouse
from app.models import (
    MenuPermission, PagePermission, OperationPermission, WarehousePermission,
    UserMenuPermission, UserPagePermission, UserOperationPermission, UserWarehousePermission
)
from app.utils.permission_manager import PermissionManager
from app.auth.decorators import check_permission
from datetime import datetime
import json

bp = Blueprint('user_permissions', __name__)


@bp.route('/admin/user-permissions')
@login_required
@check_permission('ADMIN_VIEW')
def user_permissions_index():
    """用户权限管理主页"""
    users = User.query.filter_by(status='active').all()
    return render_template('admin/user_permissions.html', users=users)


@bp.route('/admin/api/user-permissions/<int:user_id>')
@csrf.exempt
@login_required
@check_permission('ADMIN_VIEW')
def get_user_permissions(user_id):
    """获取用户的所有权限"""
    try:
        user = User.query.get_or_404(user_id)
        
        # 获取用户菜单权限
        menu_permissions = db.session.query(
            UserMenuPermission.menu_code,
            UserMenuPermission.is_granted,
            MenuPermission.menu_name,
            MenuPermission.menu_level,
            MenuPermission.parent_menu_code
        ).join(
            MenuPermission, UserMenuPermission.menu_code == MenuPermission.menu_code
        ).filter(
            UserMenuPermission.user_id == user_id
        ).all()
        
        # 获取用户页面权限
        page_permissions = db.session.query(
            UserPagePermission.page_code,
            UserPagePermission.is_granted,
            PagePermission.page_name,
            PagePermission.menu_code
        ).join(
            PagePermission, UserPagePermission.page_code == PagePermission.page_code
        ).filter(
            UserPagePermission.user_id == user_id
        ).all()
        
        # 获取用户操作权限
        operation_permissions = db.session.query(
            UserOperationPermission.operation_code,
            UserOperationPermission.is_granted,
            OperationPermission.operation_name,
            OperationPermission.page_code,
            OperationPermission.operation_type
        ).join(
            OperationPermission, UserOperationPermission.operation_code == OperationPermission.operation_code
        ).filter(
            UserOperationPermission.user_id == user_id
        ).all()
        
        # 获取用户仓库权限
        warehouse_permissions = db.session.query(
            UserWarehousePermission.warehouse_id,
            UserWarehousePermission.warehouse_permission_code,
            UserWarehousePermission.is_granted,
            Warehouse.warehouse_name,
            WarehousePermission.warehouse_permission_name
        ).join(
            Warehouse, UserWarehousePermission.warehouse_id == Warehouse.id
        ).join(
            WarehousePermission, UserWarehousePermission.warehouse_permission_code == WarehousePermission.warehouse_permission_code
        ).filter(
            UserWarehousePermission.user_id == user_id
        ).all()
        
        return jsonify({
            'success': True,
            'data': {
                'user': user.to_dict(),
                'menu_permissions': [
                    {
                        'menu_code': mp.menu_code,
                        'menu_name': mp.menu_name,
                        'menu_level': mp.menu_level,
                        'parent_menu_code': mp.parent_menu_code,
                        'is_granted': mp.is_granted
                    } for mp in menu_permissions
                ],
                'page_permissions': [
                    {
                        'page_code': pp.page_code,
                        'page_name': pp.page_name,
                        'menu_code': pp.menu_code,
                        'is_granted': pp.is_granted
                    } for pp in page_permissions
                ],
                'operation_permissions': [
                    {
                        'operation_code': op.operation_code,
                        'operation_name': op.operation_name,
                        'page_code': op.page_code,
                        'operation_type': op.operation_type,
                        'is_granted': op.is_granted
                    } for op in operation_permissions
                ],
                'warehouse_permissions': [
                    {
                        'warehouse_id': wp.warehouse_id,
                        'warehouse_name': wp.warehouse_name,
                        'warehouse_permission_code': wp.warehouse_permission_code,
                        'warehouse_permission_name': wp.warehouse_permission_name,
                        'is_granted': wp.is_granted
                    } for wp in warehouse_permissions
                ]
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/admin/api/user-permissions/<int:user_id>/menu', methods=['POST'])
@csrf.exempt
@login_required
@check_permission('ADMIN_EDIT')
def update_user_menu_permissions(user_id):
    """更新用户菜单权限"""
    try:
        data = request.get_json()
        menu_permissions = data.get('menu_permissions', [])
        
        # 删除现有权限
        UserMenuPermission.query.filter_by(user_id=user_id).delete()
        
        # 添加新权限
        for perm in menu_permissions:
            if perm.get('is_granted', False):
                permission = UserMenuPermission(
                    user_id=user_id,
                    menu_code=perm['menu_code'],
                    is_granted=True,
                    granted_by=current_user.id
                )
                db.session.add(permission)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '菜单权限更新成功'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/admin/api/user-permissions/<int:user_id>/page', methods=['POST'])
@csrf.exempt
@login_required
@check_permission('ADMIN_EDIT')
def update_user_page_permissions(user_id):
    """更新用户页面权限"""
    try:
        data = request.get_json()
        page_permissions = data.get('page_permissions', [])
        
        # 删除现有权限
        UserPagePermission.query.filter_by(user_id=user_id).delete()
        
        # 添加新权限
        for perm in page_permissions:
            if perm.get('is_granted', False):
                permission = UserPagePermission(
                    user_id=user_id,
                    page_code=perm['page_code'],
                    is_granted=True,
                    granted_by=current_user.id
                )
                db.session.add(permission)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '页面权限更新成功'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/admin/api/user-permissions/<int:user_id>/operation', methods=['POST'])
@csrf.exempt
@login_required
@check_permission('ADMIN_EDIT')
def update_user_operation_permissions(user_id):
    """更新用户操作权限"""
    try:
        data = request.get_json()
        operation_permissions = data.get('operation_permissions', [])
        
        # 删除现有权限
        UserOperationPermission.query.filter_by(user_id=user_id).delete()
        
        # 添加新权限
        for perm in operation_permissions:
            if perm.get('is_granted', False):
                permission = UserOperationPermission(
                    user_id=user_id,
                    operation_code=perm['operation_code'],
                    is_granted=True,
                    granted_by=current_user.id
                )
                db.session.add(permission)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '操作权限更新成功'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/admin/api/user-permissions/<int:user_id>/warehouse', methods=['POST'])
@csrf.exempt
@login_required
@check_permission('ADMIN_EDIT')
def update_user_warehouse_permissions(user_id):
    """更新用户仓库权限"""
    try:
        data = request.get_json()
        warehouse_permissions = data.get('warehouse_permissions', [])
        
        # 删除现有权限
        UserWarehousePermission.query.filter_by(user_id=user_id).delete()
        
        # 添加新权限
        for perm in warehouse_permissions:
            if perm.get('is_granted', False):
                permission = UserWarehousePermission(
                    user_id=user_id,
                    warehouse_id=perm['warehouse_id'],
                    warehouse_permission_code=perm['warehouse_permission_code'],
                    is_granted=True,
                    granted_by=current_user.id
                )
                db.session.add(permission)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '仓库权限更新成功'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/admin/api/user-permissions/<int:user_id>/batch', methods=['POST'])
@csrf.exempt
@login_required
@check_permission('ADMIN_EDIT')
def update_user_all_permissions(user_id):
    """批量更新用户所有权限"""
    try:
        data = request.get_json()
        
        # 删除现有权限
        UserMenuPermission.query.filter_by(user_id=user_id).delete()
        UserPagePermission.query.filter_by(user_id=user_id).delete()
        UserOperationPermission.query.filter_by(user_id=user_id).delete()
        UserWarehousePermission.query.filter_by(user_id=user_id).delete()
        
        # 添加菜单权限
        for perm in data.get('menu_permissions', []):
            if perm.get('is_granted', False):
                permission = UserMenuPermission(
                    user_id=user_id,
                    menu_code=perm['menu_code'],
                    is_granted=True,
                    granted_by=current_user.id
                )
                db.session.add(permission)
        
        # 添加页面权限
        for perm in data.get('page_permissions', []):
            if perm.get('is_granted', False):
                permission = UserPagePermission(
                    user_id=user_id,
                    page_code=perm['page_code'],
                    is_granted=True,
                    granted_by=current_user.id
                )
                db.session.add(permission)
        
        # 添加操作权限
        for perm in data.get('operation_permissions', []):
            if perm.get('is_granted', False):
                permission = UserOperationPermission(
                    user_id=user_id,
                    operation_code=perm['operation_code'],
                    is_granted=True,
                    granted_by=current_user.id
                )
                db.session.add(permission)
        
        # 添加仓库权限
        for perm in data.get('warehouse_permissions', []):
            if perm.get('is_granted', False):
                permission = UserWarehousePermission(
                    user_id=user_id,
                    warehouse_id=perm['warehouse_id'],
                    warehouse_permission_code=perm['warehouse_permission_code'],
                    is_granted=True,
                    granted_by=current_user.id
                )
                db.session.add(permission)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '用户权限更新成功'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/admin/api/permissions/definitions')
@csrf.exempt
@login_required
@check_permission('ADMIN_VIEW')
def get_permission_definitions():
    """获取所有权限定义"""
    try:
        # 获取所有菜单权限定义
        menus = MenuPermission.query.filter_by(is_active=True).order_by(
            MenuPermission.menu_level, MenuPermission.menu_order
        ).all()
        
        # 获取所有页面权限定义
        pages = PagePermission.query.filter_by(is_active=True).all()
        
        # 获取所有操作权限定义
        operations = OperationPermission.query.filter_by(is_active=True).all()
        
        # 获取所有仓库权限定义
        warehouse_permissions = WarehousePermission.query.filter_by(is_active=True).all()
        
        # 获取所有仓库
        warehouses = Warehouse.query.filter_by(status='active').all()
        
        return jsonify({
            'success': True,
            'data': {
                'menus': [menu.to_dict() for menu in menus],
                'pages': [page.to_dict() for page in pages],
                'operations': [op.to_dict() for op in operations],
                'warehouse_permissions': [wp.to_dict() for wp in warehouse_permissions],
                'warehouses': [w.to_dict() for w in warehouses]
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
