# -*- coding: utf-8 -*-
"""
界面权限管理模型
用于控制用户可以访问哪些界面和功能
"""

from app import db
from datetime import datetime


class InterfacePermission(db.Model):
    """界面权限表 - 控制用户可以看到哪些界面元素"""
    __tablename__ = 'interface_permissions'

    id = db.Column(db.Integer, primary_key=True)
    permission_code = db.Column(db.String(100), unique=True, nullable=False, comment='权限代码')
    permission_name = db.Column(db.String(100), nullable=False, comment='权限名称')
    interface_type = db.Column(db.Enum('menu', 'page', 'button', 'section', 'field', name='interface_type'), 
                              nullable=False, comment='界面类型')
    module = db.Column(db.String(50), nullable=False, comment='所属模块')
    parent_code = db.Column(db.String(100), comment='父级权限代码')
    warehouse_scope = db.Column(db.Enum('all', 'frontend', 'backend', 'own', name='warehouse_scope'), 
                               default='own', comment='仓库范围限制')
    data_scope = db.Column(db.Enum('all', 'warehouse', 'own', name='data_scope'), 
                          default='warehouse', comment='数据范围限制')
    operation_type = db.Column(db.Enum('view', 'create', 'edit', 'delete', 'export', 'print', name='operation_type'), 
                              default='view', comment='操作类型')
    description = db.Column(db.Text, comment='权限描述')
    sort_order = db.Column(db.Integer, default=0, comment='排序')
    status = db.Column(db.Enum('active', 'inactive', name='interface_permission_status'), 
                      default='active', comment='状态')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')

    def __repr__(self):
        return f'<InterfacePermission {self.permission_name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'permission_code': self.permission_code,
            'permission_name': self.permission_name,
            'interface_type': self.interface_type,
            'module': self.module,
            'parent_code': self.parent_code,
            'warehouse_scope': self.warehouse_scope,
            'data_scope': self.data_scope,
            'operation_type': self.operation_type,
            'description': self.description,
            'sort_order': self.sort_order,
            'status': self.status
        }


class RoleInterfacePermission(db.Model):
    """角色界面权限关联表"""
    __tablename__ = 'role_interface_permissions'

    id = db.Column(db.Integer, primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    interface_permission_id = db.Column(db.Integer, db.ForeignKey('interface_permissions.id'), nullable=False)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'), comment='仓库限制')
    granted = db.Column(db.Boolean, default=True, comment='是否授权')
    granted_by = db.Column(db.Integer, db.ForeignKey('users.id'), comment='授权人')
    granted_at = db.Column(db.DateTime, default=datetime.now, comment='授权时间')
    expires_at = db.Column(db.DateTime, comment='过期时间')
    status = db.Column(db.Enum('active', 'inactive', name='role_interface_permission_status'), 
                      default='active', comment='状态')

    __table_args__ = (
        db.UniqueConstraint('role_id', 'interface_permission_id', 'warehouse_id', 
                           name='unique_role_interface_permission'),
    )

    def __repr__(self):
        return f'<RoleInterfacePermission {self.role_id}-{self.interface_permission_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'role_id': self.role_id,
            'interface_permission_id': self.interface_permission_id,
            'warehouse_id': self.warehouse_id,
            'granted': self.granted,
            'granted_by': self.granted_by,
            'granted_at': self.granted_at.isoformat() if self.granted_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'status': self.status
        }


# 预定义的界面权限配置
INTERFACE_PERMISSIONS_CONFIG = {
    # 主导航菜单权限
    'MENU_INBOUND': {
        'permission_name': '入库管理菜单',
        'interface_type': 'menu',
        'module': 'inbound',
        'warehouse_scope': 'own',
        'description': '显示入库管理菜单项'
    },
    'MENU_OUTBOUND': {
        'permission_name': '出库管理菜单',
        'interface_type': 'menu',
        'module': 'outbound',
        'warehouse_scope': 'own',
        'description': '显示出库管理菜单项'
    },
    'MENU_INVENTORY': {
        'permission_name': '库存管理菜单',
        'interface_type': 'menu',
        'module': 'inventory',
        'warehouse_scope': 'own',
        'description': '显示库存管理菜单项'
    },
    'MENU_ADMIN': {
        'permission_name': '系统管理菜单',
        'interface_type': 'menu',
        'module': 'admin',
        'warehouse_scope': 'all',
        'description': '显示系统管理菜单项'
    },

    # 页面访问权限
    'PAGE_INBOUND_LIST': {
        'permission_name': '入库记录页面',
        'interface_type': 'page',
        'module': 'inbound',
        'parent_code': 'MENU_INBOUND',
        'warehouse_scope': 'own',
        'description': '访问入库记录列表页面'
    },
    'PAGE_OUTBOUND_LIST': {
        'permission_name': '出库记录页面',
        'interface_type': 'page',
        'module': 'outbound',
        'parent_code': 'MENU_OUTBOUND',
        'warehouse_scope': 'own',
        'description': '访问出库记录列表页面'
    },
    'PAGE_INVENTORY_LIST': {
        'permission_name': '库存查询页面',
        'interface_type': 'page',
        'module': 'inventory',
        'parent_code': 'MENU_INVENTORY',
        'warehouse_scope': 'own',
        'description': '访问库存查询页面'
    },

    # 跨仓库查看权限
    'VIEW_FRONTEND_INVENTORY': {
        'permission_name': '查看前端仓库库存',
        'interface_type': 'section',
        'module': 'inventory',
        'warehouse_scope': 'frontend',
        'data_scope': 'all',
        'operation_type': 'view',
        'description': '可以查看所有前端仓库的库存信息'
    },
    'VIEW_BACKEND_INVENTORY': {
        'permission_name': '查看后端仓库库存',
        'interface_type': 'section',
        'module': 'inventory',
        'warehouse_scope': 'backend',
        'data_scope': 'all',
        'operation_type': 'view',
        'description': '可以查看后端仓库的库存信息'
    },

    # 操作按钮权限
    'BTN_INBOUND_CREATE': {
        'permission_name': '新增入库按钮',
        'interface_type': 'button',
        'module': 'inbound',
        'warehouse_scope': 'own',
        'operation_type': 'create',
        'description': '显示新增入库按钮'
    },
    'BTN_INBOUND_EDIT': {
        'permission_name': '编辑入库按钮',
        'interface_type': 'button',
        'module': 'inbound',
        'warehouse_scope': 'own',
        'operation_type': 'edit',
        'description': '显示编辑入库按钮'
    },
    'BTN_OUTBOUND_CREATE': {
        'permission_name': '新增出库按钮',
        'interface_type': 'button',
        'module': 'outbound',
        'warehouse_scope': 'own',
        'operation_type': 'create',
        'description': '显示新增出库按钮'
    },
    'BTN_INVENTORY_EXPORT': {
        'permission_name': '导出库存按钮',
        'interface_type': 'button',
        'module': 'inventory',
        'warehouse_scope': 'own',
        'operation_type': 'export',
        'description': '显示导出库存按钮'
    },

    # 字段显示权限
    'FIELD_COST_PRICE': {
        'permission_name': '成本价格字段',
        'interface_type': 'field',
        'module': 'inventory',
        'warehouse_scope': 'own',
        'description': '显示商品成本价格字段'
    },
    'FIELD_PROFIT_MARGIN': {
        'permission_name': '利润率字段',
        'interface_type': 'field',
        'module': 'inventory',
        'warehouse_scope': 'own',
        'description': '显示利润率字段'
    }
}
