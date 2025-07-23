#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
权限管理路由
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models import (
    User, MenuPermission, PagePermission, OperationPermission, WarehousePermission,
    UserMenuPermission, UserPagePermission, UserOperationPermission, UserWarehousePermission,
    Warehouse
)
from app.decorators import require_permission

# 使用主admin蓝图
from app.admin import bp as permission_bp

@permission_bp.route('/permissions')
@login_required
@require_permission('ADMIN_MANAGEMENT')
def permission_management():
    """权限管理主页面"""
    users = User.query.filter(User.username != 'admin').all()
    menus = MenuPermission.query.all()
    pages = PagePermission.query.all()
    warehouses = Warehouse.query.all()
    
    return render_template('admin/permission_management.html',
                         users=users, menus=menus, pages=pages, warehouses=warehouses)

@permission_bp.route('/user/<int:user_id>/permissions')
@login_required
@require_permission('ADMIN_MANAGEMENT')
def get_user_permissions_legacy(user_id):
    """获取用户权限"""
    user = User.query.get_or_404(user_id)
    
    # 获取用户的菜单权限
    menu_permissions = UserMenuPermission.query.filter_by(user_id=user_id, is_granted=True).all()
    menu_codes = [mp.menu_code for mp in menu_permissions]
    
    # 获取用户的页面权限
    page_permissions = UserPagePermission.query.filter_by(user_id=user_id, is_granted=True).all()
    page_codes = [pp.page_code for pp in page_permissions]
    
    return jsonify({
        'user_id': user_id,
        'username': user.username,
        'warehouse_name': user.warehouse.warehouse_name if user.warehouse else None,
        'menu_permissions': menu_codes,
        'page_permissions': page_codes
    })

@permission_bp.route('/user/<int:user_id>/permissions', methods=['POST'])
@login_required
@require_permission('ADMIN_MANAGEMENT')
def update_user_permissions_legacy(user_id):
    """更新用户权限"""
    try:
        user = User.query.get_or_404(user_id)
        data = request.get_json()
        
        menu_permissions = data.get('menu_permissions', [])
        page_permissions = data.get('page_permissions', [])
        
        # 删除现有的菜单权限
        UserMenuPermission.query.filter_by(user_id=user_id).delete()
        
        # 添加新的菜单权限
        for menu_code in menu_permissions:
            user_menu = UserMenuPermission(
                user_id=user_id,
                menu_code=menu_code,
                is_granted=True,
                granted_by=current_user.id
            )
            db.session.add(user_menu)
        
        # 删除现有的页面权限
        UserPagePermission.query.filter_by(user_id=user_id).delete()
        
        # 添加新的页面权限
        for page_code in page_permissions:
            user_page = UserPagePermission(
                user_id=user_id,
                page_code=page_code,
                is_granted=True,
                granted_by=current_user.id
            )
            db.session.add(user_page)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'用户 {user.username} 的权限已更新'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'更新权限失败: {str(e)}'
        }), 500

@permission_bp.route('/permissions/batch-assign', methods=['POST'])
@login_required
@require_permission('ADMIN_MANAGEMENT')
def batch_assign_permissions():
    """批量分配权限"""
    try:
        data = request.get_json()
        warehouse_type = data.get('warehouse_type')  # 'frontend' 或 'backend'
        permission_template = data.get('permission_template')  # 'basic' 或 'full'
        
        # 根据仓库类型获取用户
        if warehouse_type == 'frontend':
            warehouses = Warehouse.query.filter_by(warehouse_type='frontend').all()
        elif warehouse_type == 'backend':
            warehouses = Warehouse.query.filter_by(warehouse_type='backend').all()
        else:
            return jsonify({'success': False, 'message': '无效的仓库类型'}), 400
        
        warehouse_ids = [w.id for w in warehouses]
        users = User.query.filter(User.warehouse_id.in_(warehouse_ids)).all()
        
        # 定义权限模板
        if warehouse_type == 'frontend':
            if permission_template == 'basic':
                menu_permissions = ['FRONTEND_INBOUND', 'FRONTEND_OUTBOUND']
                page_permissions = ['FRONTEND_INBOUND_OPERATION', 'FRONTEND_INBOUND_LIST', 
                                  'FRONTEND_OUTBOUND_OPERATION', 'FRONTEND_OUTBOUND_LIST']
            else:  # full
                menu_permissions = ['FRONTEND_INBOUND', 'FRONTEND_OUTBOUND', 'INVENTORY_MANAGEMENT', 'PRINT_MANAGEMENT']
                page_permissions = ['FRONTEND_INBOUND_OPERATION', 'FRONTEND_INBOUND_LIST', 'FRONTEND_RECEIVE_LIST',
                                  'FRONTEND_OUTBOUND_OPERATION', 'FRONTEND_OUTBOUND_LIST', 'FRONTEND_INVENTORY_LIST',
                                  'RECEIVER_LIST', 'LABEL_PRINT', 'OUTBOUND_PRINT_LIST', 'OUTBOUND_EXIT_PLAN']
        else:  # backend
            if permission_template == 'basic':
                menu_permissions = ['BACKEND_INBOUND', 'BACKEND_OUTBOUND']
                page_permissions = ['BACKEND_INBOUND_OPERATION', 'BACKEND_RECEIVE_RECORDS',
                                  'BACKEND_OUTBOUND_OPERATION', 'BACKEND_OUTBOUND_LIST']
            else:  # full
                menu_permissions = ['BACKEND_INBOUND', 'BACKEND_OUTBOUND', 'INVENTORY_MANAGEMENT', 'PRINT_MANAGEMENT']
                page_permissions = ['BACKEND_INBOUND_OPERATION', 'BACKEND_RECEIVE_RECORDS', 'BACKEND_INBOUND_LIST',
                                  'BACKEND_OUTBOUND_OPERATION', 'BACKEND_OUTBOUND_LIST', 'BACKEND_INVENTORY_LIST',
                                  'TRANSIT_CARGO_LIST', 'LABEL_PRINT', 'BACKEND_OUTBOUND_PRINT', 'OUTBOUND_PRINT_LIST', 'OUTBOUND_EXIT_PLAN']
        
        # 为每个用户分配权限
        updated_count = 0
        for user in users:
            # 删除现有权限
            UserMenuPermission.query.filter_by(user_id=user.id).delete()
            UserPagePermission.query.filter_by(user_id=user.id).delete()
            
            # 分配菜单权限
            for menu_code in menu_permissions:
                user_menu = UserMenuPermission(
                    user_id=user.id,
                    menu_code=menu_code,
                    is_granted=True,
                    granted_by=current_user.id
                )
                db.session.add(user_menu)
            
            # 分配页面权限
            for page_code in page_permissions:
                user_page = UserPagePermission(
                    user_id=user.id,
                    page_code=page_code,
                    is_granted=True,
                    granted_by=current_user.id
                )
                db.session.add(user_page)
            
            updated_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'已为 {updated_count} 个{warehouse_type}仓库用户分配{permission_template}权限'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'批量分配权限失败: {str(e)}'
        }), 500

@permission_bp.route('/permissions/reset/<int:user_id>', methods=['POST'])
@login_required
@require_permission('ADMIN_MANAGEMENT')
def reset_user_permissions(user_id):
    """重置用户权限"""
    try:
        user = User.query.get_or_404(user_id)
        
        # 删除所有权限
        UserMenuPermission.query.filter_by(user_id=user_id).delete()
        UserPagePermission.query.filter_by(user_id=user_id).delete()
        UserOperationPermission.query.filter_by(user_id=user_id).delete()
        UserWarehousePermission.query.filter_by(user_id=user_id).delete()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'用户 {user.username} 的权限已重置'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'重置权限失败: {str(e)}'
        }), 500

@permission_bp.route('/permissions/init-receiver-permission', methods=['POST'])
@login_required
@require_permission('ADMIN_MANAGEMENT')
def init_receiver_permission():
    """初始化收货人信息管理权限"""
    try:
        # 检查是否已存在收货人信息管理权限
        existing_permission = PagePermission.query.filter_by(page_code='RECEIVER_LIST').first()
        if existing_permission:
            return jsonify({
                'success': True,
                'message': '收货人信息管理权限已存在'
            })

        # 创建收货人信息管理页面权限
        receiver_permission = PagePermission(
            page_code='RECEIVER_LIST',
            page_name='收货人信息管理',
            page_category='数据管理',
            description='管理收货人信息，包括查看、添加、编辑、删除收货人信息',
            is_active=True
        )

        db.session.add(receiver_permission)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '收货人信息管理权限已成功添加到系统中'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'初始化权限失败: {str(e)}'
        }), 500

@permission_bp.route('/permissions/sync-from-decorators', methods=['POST'])
@login_required
@require_permission('ADMIN_MANAGEMENT')
def sync_permissions_from_decorators():
    """从装饰器同步权限到数据库"""
    try:
        from app.utils.permission_sync import sync_permissions_to_database
        success, message = sync_permissions_to_database()

        return jsonify({
            'success': success,
            'message': message
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'同步权限失败: {str(e)}'
        }), 500

@permission_bp.route('/permissions/registered-list', methods=['GET'])
@login_required
@require_permission('ADMIN_MANAGEMENT')
def get_registered_permissions():
    """获取装饰器注册的权限列表"""
    try:
        from app.utils.permission_sync import get_registered_permissions
        registered = get_registered_permissions()

        return jsonify({
            'success': True,
            'data': {
                'menus': list(registered['menus'].values()),
                'pages': list(registered['pages'].values()),
                'operations': list(registered['operations'].values())
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取注册权限失败: {str(e)}'
        }), 500

@permission_bp.route('/permissions/decorator-guide')
@login_required
@require_permission('ADMIN_MANAGEMENT')
def permission_decorator_guide():
    """权限装饰器使用指南"""
    return render_template('admin/permission_decorator_guide.html')

@permission_bp.route('/permissions/sync-navigation', methods=['POST'])
@login_required
@require_permission('ADMIN_MANAGEMENT')
def sync_navigation_permissions():
    """同步导航菜单中的权限"""
    try:
        from app.models import PagePermission

        # 从导航菜单中提取的实际权限代码
        actual_permissions = [
            # 前端仓入库
            ('FRONTEND_INBOUND_OPERATION', '前端仓入库操作', 'FRONTEND_INBOUND'),
            ('FRONTEND_INBOUND_LIST', '前端仓入库记录', 'FRONTEND_INBOUND'),
            ('FRONTEND_RECEIVE_LIST', '前端仓接收记录', 'FRONTEND_INBOUND'),

            # 后端仓入库
            ('BACKEND_INBOUND_OPERATION', '后端仓入库操作', 'BACKEND_INBOUND'),
            ('BACKEND_RECEIVE_RECORDS', '后端仓接收记录', 'BACKEND_INBOUND'),
            ('BACKEND_INBOUND_LIST', '后端仓入库记录', 'BACKEND_INBOUND'),

            # 前端仓出库
            ('FRONTEND_OUTBOUND_OPERATION', '前端仓出库操作', 'FRONTEND_OUTBOUND'),
            ('FRONTEND_OUTBOUND_LIST', '前端仓出库记录', 'FRONTEND_OUTBOUND'),

            # 后端仓出库
            ('BACKEND_OUTBOUND_OPERATION', '后端仓出库操作', 'BACKEND_OUTBOUND'),
            ('BACKEND_OUTBOUND_LIST', '后端仓出库记录', 'BACKEND_OUTBOUND'),
            ('BACKEND_OUTBOUND_PRINT', '后端仓出库单页面', 'BACKEND_OUTBOUND'),

            # 库存管理
            ('FRONTEND_INVENTORY_LIST', '前端仓库存界面', 'INVENTORY_MANAGEMENT'),
            ('BACKEND_INVENTORY_LIST', '后端仓库存界面', 'INVENTORY_MANAGEMENT'),
            ('ALL_INVENTORY_LIST', '全仓库存查询', 'INVENTORY_MANAGEMENT'),
            ('TRANSIT_CARGO_LIST', '在途货物库存', 'INVENTORY_MANAGEMENT'),

            # 收货人管理
            ('RECEIVER_LIST', '收货人信息', 'FRONTEND_OUTBOUND'),

            # 统计报表
            ('CARGO_VOLUME_DASHBOARD', '货量报表仪表板', 'REPORTS'),
            ('WAREHOUSE_OPERATIONS', '仓库运营分析', 'REPORTS'),
            ('CUSTOMER_ANALYSIS', '客户业务分析', 'REPORTS'),
            ('TREND_ANALYSIS', '趋势预测分析', 'REPORTS'),

            # 单据打印
            ('OUTBOUND_PRINT_LIST', '出库单打印', 'PRINT_MANAGEMENT'),
            ('OUTBOUND_EXIT_PLAN', '出境计划单', 'PRINT_MANAGEMENT'),
            ('BACKEND_OUTBOUND_PRINT', '后端仓出库单页面', 'PRINT_MANAGEMENT'),

            # 用户管理
            ('USER_MANAGEMENT', '用户管理', 'ADMIN_MANAGEMENT'),
            ('WAREHOUSE_MANAGEMENT', '仓库管理', 'ADMIN_MANAGEMENT'),
            ('AUDIT_LOGS', '审计日志', 'ADMIN_MANAGEMENT'),
            ('OPTIMIZATION_MONITOR', '优化监控', 'ADMIN_MANAGEMENT'),
        ]

        added_count = 0
        updated_count = 0

        for page_code, page_name, menu_code in actual_permissions:
            existing = PagePermission.query.filter_by(page_code=page_code).first()
            if not existing:
                permission = PagePermission(
                    page_code=page_code,
                    page_name=page_name,
                    menu_code=menu_code,
                    is_active=True
                )
                db.session.add(permission)
                added_count += 1
            else:
                # 更新现有权限的菜单归属
                if existing.menu_code != menu_code or existing.page_name != page_name:
                    existing.menu_code = menu_code
                    existing.page_name = page_name
                    updated_count += 1

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'导航权限同步完成！新增 {added_count} 个权限，更新 {updated_count} 个权限。',
            'added': added_count,
            'updated': updated_count
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"同步导航权限失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'同步导航权限失败: {str(e)}'
        }), 500
