#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
精细化权限管理工具类
"""

from flask_login import current_user
from app.models import (
    MenuPermission, PagePermission, OperationPermission, WarehousePermission,
    UserMenuPermission, UserPagePermission, UserOperationPermission, UserWarehousePermission
)
from app.models import User, Warehouse


class PermissionManager:
    """权限管理器"""
    
    @staticmethod
    def has_menu_permission(user_id, menu_code):
        """检查用户是否有菜单权限"""
        if not user_id or not menu_code:
            return False
            
        # 超级管理员拥有所有权限
        user = User.query.get(user_id)
        if user and user.is_super_admin():
            return True
            
        # 检查用户菜单权限
        permission = UserMenuPermission.query.filter_by(
            user_id=user_id,
            menu_code=menu_code,
            is_granted=True
        ).first()
        
        return permission is not None
    
    @staticmethod
    def has_page_permission(user_id, page_code):
        """检查用户是否有页面权限"""
        if not user_id or not page_code:
            return False

        # 超级管理员拥有所有权限
        user = User.query.get(user_id)
        if user and user.is_super_admin():
            return True

        # 如果page_code是列表，检查是否有任何一个权限
        if isinstance(page_code, list):
            for code in page_code:
                permission = UserPagePermission.query.filter_by(
                    user_id=user_id,
                    page_code=code,
                    is_granted=True
                ).first()
                if permission:
                    return True
            return False

        # 检查用户页面权限
        permission = UserPagePermission.query.filter_by(
            user_id=user_id,
            page_code=page_code,
            is_granted=True
        ).first()

        return permission is not None
    
    @staticmethod
    def has_operation_permission(user_id, operation_code):
        """检查用户是否有操作权限"""
        if not user_id or not operation_code:
            return False
            
        # 超级管理员拥有所有权限
        user = User.query.get(user_id)
        if user and user.is_super_admin():
            return True
            
        # 检查用户操作权限
        permission = UserOperationPermission.query.filter_by(
            user_id=user_id,
            operation_code=operation_code,
            is_granted=True
        ).first()
        
        return permission is not None
    
    @staticmethod
    def has_warehouse_permission(user_id, warehouse_id, warehouse_permission_code):
        """检查用户是否有仓库权限"""
        if not user_id or not warehouse_id or not warehouse_permission_code:
            return False
            
        # 超级管理员拥有所有权限
        user = User.query.get(user_id)
        if user and user.is_super_admin():
            return True
            
        # 检查用户仓库权限
        permission = UserWarehousePermission.query.filter_by(
            user_id=user_id,
            warehouse_id=warehouse_id,
            warehouse_permission_code=warehouse_permission_code,
            is_granted=True
        ).first()
        
        return permission is not None
    
    @staticmethod
    def get_user_accessible_menus(user_id):
        """获取用户可访问的菜单列表"""
        if not user_id:
            return []
            
        # 超级管理员可以访问所有菜单
        user = User.query.get(user_id)
        if user and user.is_super_admin():
            return MenuPermission.query.filter_by(is_active=True).order_by(
                MenuPermission.menu_level, MenuPermission.menu_order
            ).all()
        
        # 获取用户有权限的菜单
        user_menu_permissions = UserMenuPermission.query.filter_by(
            user_id=user_id,
            is_granted=True
        ).all()
        
        menu_codes = [perm.menu_code for perm in user_menu_permissions]
        
        menus = MenuPermission.query.filter(
            MenuPermission.menu_code.in_(menu_codes),
            MenuPermission.is_active == True
        ).order_by(
            MenuPermission.menu_level, MenuPermission.menu_order
        ).all()
        
        return menus
    
    @staticmethod
    def get_user_accessible_pages(user_id, menu_code=None):
        """获取用户可访问的页面列表"""
        if not user_id:
            return []
            
        # 超级管理员可以访问所有页面
        user = User.query.get(user_id)
        if user and user.is_super_admin():
            query = PagePermission.query.filter_by(is_active=True)
            if menu_code:
                query = query.filter_by(menu_code=menu_code)
            return query.all()
        
        # 获取用户有权限的页面
        user_page_permissions = UserPagePermission.query.filter_by(
            user_id=user_id,
            is_granted=True
        ).all()
        
        page_codes = [perm.page_code for perm in user_page_permissions]
        
        query = PagePermission.query.filter(
            PagePermission.page_code.in_(page_codes),
            PagePermission.is_active == True
        )
        
        if menu_code:
            query = query.filter_by(menu_code=menu_code)
            
        return query.all()
    
    @staticmethod
    def get_user_accessible_warehouses(user_id):
        """获取用户可访问的仓库列表"""
        if not user_id:
            return []
            
        # 超级管理员可以访问所有仓库
        user = User.query.get(user_id)
        if user and user.is_super_admin():
            return Warehouse.query.filter_by(status='active').all()
        
        # 获取用户有权限的仓库
        user_warehouse_permissions = UserWarehousePermission.query.filter_by(
            user_id=user_id,
            is_granted=True
        ).all()
        
        warehouse_ids = list(set([perm.warehouse_id for perm in user_warehouse_permissions]))
        
        warehouses = Warehouse.query.filter(
            Warehouse.id.in_(warehouse_ids),
            Warehouse.status == 'active'
        ).all()
        
        return warehouses
    
    @staticmethod
    def build_menu_tree(menus):
        """构建菜单树结构"""
        menu_dict = {}
        root_menus = []
        
        # 将菜单转换为字典
        for menu in menus:
            menu_data = menu.to_dict()
            menu_data['children'] = []
            menu_dict[menu.menu_code] = menu_data
        
        # 构建树结构
        for menu in menus:
            if menu.parent_menu_code and menu.parent_menu_code in menu_dict:
                # 添加到父菜单的children中
                menu_dict[menu.parent_menu_code]['children'].append(menu_dict[menu.menu_code])
            else:
                # 根菜单
                root_menus.append(menu_dict[menu.menu_code])
        
        return root_menus
    
    @staticmethod
    def grant_menu_permission(user_id, menu_code, granted_by_user_id):
        """授予用户菜单权限"""
        from app import db
        
        # 检查是否已存在
        existing = UserMenuPermission.query.filter_by(
            user_id=user_id,
            menu_code=menu_code
        ).first()
        
        if existing:
            existing.is_granted = True
            existing.granted_by = granted_by_user_id
            existing.granted_at = datetime.now()
        else:
            permission = UserMenuPermission(
                user_id=user_id,
                menu_code=menu_code,
                is_granted=True,
                granted_by=granted_by_user_id
            )
            db.session.add(permission)
        
        db.session.commit()
    
    @staticmethod
    def revoke_menu_permission(user_id, menu_code):
        """撤销用户菜单权限"""
        from app import db
        
        permission = UserMenuPermission.query.filter_by(
            user_id=user_id,
            menu_code=menu_code
        ).first()
        
        if permission:
            permission.is_granted = False
            db.session.commit()
    
    @staticmethod
    def grant_page_permission(user_id, page_code, granted_by_user_id):
        """授予用户页面权限"""
        from app import db
        
        # 检查是否已存在
        existing = UserPagePermission.query.filter_by(
            user_id=user_id,
            page_code=page_code
        ).first()
        
        if existing:
            existing.is_granted = True
            existing.granted_by = granted_by_user_id
            existing.granted_at = datetime.now()
        else:
            permission = UserPagePermission(
                user_id=user_id,
                page_code=page_code,
                is_granted=True,
                granted_by=granted_by_user_id
            )
            db.session.add(permission)
        
        db.session.commit()
    
    @staticmethod
    def grant_operation_permission(user_id, operation_code, granted_by_user_id):
        """授予用户操作权限"""
        from app import db
        
        # 检查是否已存在
        existing = UserOperationPermission.query.filter_by(
            user_id=user_id,
            operation_code=operation_code
        ).first()
        
        if existing:
            existing.is_granted = True
            existing.granted_by = granted_by_user_id
            existing.granted_at = datetime.now()
        else:
            permission = UserOperationPermission(
                user_id=user_id,
                operation_code=operation_code,
                is_granted=True,
                granted_by=granted_by_user_id
            )
            db.session.add(permission)
        
        db.session.commit()
    
    @staticmethod
    def grant_warehouse_permission(user_id, warehouse_id, warehouse_permission_code, granted_by_user_id):
        """授予用户仓库权限"""
        from app import db
        
        # 检查是否已存在
        existing = UserWarehousePermission.query.filter_by(
            user_id=user_id,
            warehouse_id=warehouse_id,
            warehouse_permission_code=warehouse_permission_code
        ).first()
        
        if existing:
            existing.is_granted = True
            existing.granted_by = granted_by_user_id
            existing.granted_at = datetime.now()
        else:
            permission = UserWarehousePermission(
                user_id=user_id,
                warehouse_id=warehouse_id,
                warehouse_permission_code=warehouse_permission_code,
                is_granted=True,
                granted_by=granted_by_user_id
            )
            db.session.add(permission)
        
        db.session.commit()


# 模板函数，用于在Jinja2模板中检查权限
def has_menu_permission(menu_code):
    """模板函数：检查当前用户是否有菜单权限"""
    if not current_user.is_authenticated:
        return False
    return PermissionManager.has_menu_permission(current_user.id, menu_code)


def has_page_permission(page_code):
    """模板函数：检查当前用户是否有页面权限"""
    if not current_user.is_authenticated:
        return False
    return PermissionManager.has_page_permission(current_user.id, page_code)


def has_operation_permission(operation_code):
    """模板函数：检查当前用户是否有操作权限"""
    if not current_user.is_authenticated:
        return False
    return PermissionManager.has_operation_permission(current_user.id, operation_code)


def has_warehouse_permission(warehouse_id, warehouse_permission_code):
    """模板函数：检查当前用户是否有仓库权限"""
    if not current_user.is_authenticated:
        return False
    return PermissionManager.has_warehouse_permission(current_user.id, warehouse_id, warehouse_permission_code)
