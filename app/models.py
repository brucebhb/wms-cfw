from datetime import datetime
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy import func
import json

# 导入安全组件（延迟导入避免循环依赖）
def get_optimistic_lock_mixin():
    from app.utils.concurrency_control import OptimisticLockMixin
    return OptimisticLockMixin

class InboundRecord(db.Model):
    """入库记录表"""
    id = db.Column(db.Integer, primary_key=True)
    inbound_time = db.Column(db.DateTime, index=True, default=datetime.now, comment='入库时间')
    delivery_plate_number = db.Column(db.String(20), index=True, comment='送货干线车')
    plate_number = db.Column(db.String(20), index=True, nullable=False, comment='入库车牌')
    customer_name = db.Column(db.String(100), index=True, nullable=False, comment='客户名称')
    identification_code = db.Column(db.String(100), index=True, unique=True, comment='识别编码')
    pallet_count = db.Column(db.Integer, default=0, comment='板数')
    package_count = db.Column(db.Integer, default=0, comment='件数')
    weight = db.Column(db.Float, default=0, comment='重量(kg)')
    volume = db.Column(db.Float, default=0, comment='体积(m³)')
    export_mode = db.Column(db.String(50), comment='出境模式')
    order_type = db.Column(db.String(50), comment='订单类型')
    customs_broker = db.Column(db.String(100), comment='报关行')
    location = db.Column(db.String(50), comment='库位')
    documents = db.Column(db.String(100), comment='单据')
    service_staff = db.Column(db.String(50), comment='跟单客服')
    batch_no = db.Column(db.String(50), index=True, comment='批次号，标识同一车辆的所有货物')
    batch_total = db.Column(db.Integer, default=0, comment='批次总数，该批次包含的票据总数')
    batch_sequence = db.Column(db.Integer, default=0, comment='批次序号，该票据在批次中的序号(1-N)')
    inbound_plate = db.Column(db.String(20), comment='入库车牌')
    document_no = db.Column(db.String(100), comment='单据号')
    document_count = db.Column(db.Integer, comment='单据份数')
    remark1 = db.Column(db.String(200), default='', comment='备注1')
    remark2 = db.Column(db.String(200), default='', comment='备注2')
    # 入库类型字段，用于明确区分记录类型
    record_type = db.Column(db.String(20), index=True, default='direct', comment='入库类型: direct=直接入库, receive=接收记录, pending=待接收')
    # 操作追踪字段
    operated_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), comment='操作用户ID')
    operated_warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse.id'), comment='操作仓库ID')
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # 乐观锁版本字段
    version = db.Column(db.Integer, default=1, comment='版本号，用于乐观锁控制')

    # 关联关系
    operated_by_user = db.relationship('User', foreign_keys=[operated_by_user_id], backref='operated_inbound_records')
    operated_warehouse = db.relationship('Warehouse', foreign_keys=[operated_warehouse_id], backref='inbound_records')

    def __repr__(self):
        return f'<InboundRecord {self.id} {self.plate_number} {self.customer_name}>'

    @property
    def create_time(self):
        """为了兼容模板中的 create_time 访问"""
        return self.created_at
    
    def to_dict(self):
        return {
            'id': self.id,
            'inbound_time': self.inbound_time.strftime('%Y-%m-%d') if self.inbound_time else None,
            'delivery_plate_number': self.delivery_plate_number,
            'plate_number': self.plate_number,
            'customer_name': self.customer_name,
            'identification_code': self.identification_code,
            'pallet_count': self.pallet_count,
            'package_count': self.package_count,
            'weight': self.weight,
            'volume': self.volume,
            'export_mode': self.export_mode,
            'order_type': self.order_type,
            'customs_broker': self.customs_broker,
            'location': self.location,
            'documents': self.documents,
            'service_staff': self.service_staff,
            'batch_no': self.batch_no,
            'batch_total': self.batch_total,
            'batch_sequence': self.batch_sequence,
            'inbound_plate': self.inbound_plate,
            'document_no': self.document_no,
            'document_count': self.document_count,
            'remark1': self.remark1,
            'remark2': self.remark2,
            'record_type': self.record_type,
            'operated_by_user_id': self.operated_by_user_id,
            'operated_by_user_name': self.operated_by_user.username if self.operated_by_user else None,
            'operated_warehouse_id': self.operated_warehouse_id,
            'operated_warehouse_name': self.operated_warehouse.warehouse_name if self.operated_warehouse else None,
            'create_time': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

class OutboundRecord(db.Model):
    """出库记录表"""
    id = db.Column(db.Integer, primary_key=True)
    outbound_time = db.Column(db.DateTime, index=True, default=datetime.now, comment='出库时间')
    delivery_plate_number = db.Column(db.String(20), index=True, comment='送货干线车')
    plate_number = db.Column(db.String(20), index=True, nullable=False, comment='出库车牌')
    customer_name = db.Column(db.String(100), index=True, nullable=False, comment='客户名称')
    identification_code = db.Column(db.String(100), index=True, comment='识别编码')
    pallet_count = db.Column(db.Integer, default=0, comment='板数')
    package_count = db.Column(db.Integer, default=0, comment='件数')
    weight = db.Column(db.Float, default=0, comment='重量(kg)')
    volume = db.Column(db.Float, default=0, comment='体积(m³)')
    destination = db.Column(db.String(100), comment='目的地')
    destination_warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse.id'), comment='目的仓库ID')
    warehouse_address = db.Column(db.String(255), comment='仓库地址')
    transport_company = db.Column(db.String(100), comment='运输公司')
    order_type = db.Column(db.String(50), comment='订单类型')
    service_staff = db.Column(db.String(50), comment='跟单客服')
    receiver_id = db.Column(db.Integer, db.ForeignKey('receiver.id'), nullable=True, comment='收货人ID')
    remarks = db.Column(db.String(200), default='', comment='备注')
    remark1 = db.Column(db.String(200), default='', comment='备注1')
    remark2 = db.Column(db.String(200), default='', comment='备注2')
    documents = db.Column(db.String(100), comment='单据')
    large_layer = db.Column(db.Integer, default=0, comment='大层板')
    small_layer = db.Column(db.Integer, default=0, comment='小层板')
    pallet_board = db.Column(db.Integer, default=0, comment='卡板')
    inbound_plate = db.Column(db.String(20), comment='入库车牌')
    document_no = db.Column(db.String(100), comment='单据号')
    document_count = db.Column(db.Integer, comment='单据份数')
    export_mode = db.Column(db.String(50), comment='出境模式')
    customs_broker = db.Column(db.String(100), comment='报关行')
    location = db.Column(db.String(50), comment='库位')
    batch_no = db.Column(db.String(50), index=True, comment='批次号，标识同一车辆的所有货物')
    batch_total = db.Column(db.Integer, default=0, comment='批次总数，该批次包含的票据总数')
    batch_sequence = db.Column(db.Integer, default=1, comment='分批序号，同一识别编码的分批出库序号(1-N)')  # 用于区分同一票货物的不同批次
    vehicle_type = db.Column(db.String(50), comment='车型')
    driver_name = db.Column(db.String(50), comment='司机姓名')
    driver_phone = db.Column(db.String(50), comment='司机电话')
    arrival_time = db.Column(db.DateTime, comment='集拼车到仓时间')
    loading_start_time = db.Column(db.DateTime, comment='开始装车时间')
    loading_end_time = db.Column(db.DateTime, comment='结束装车时间')
    departure_time = db.Column(db.DateTime, comment='离仓发运时间')
    detailed_address = db.Column(db.String(255), comment='详细地址')
    contact_window = db.Column(db.String(100), comment='联络窗口')
    inbound_date = db.Column(db.DateTime, comment='货物入库日期')
    trailer = db.Column(db.String(50), comment='车挂')
    container_number = db.Column(db.String(50), comment='柜号')
    # 操作追踪字段
    operated_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), comment='操作用户ID')
    operated_warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse.id'), comment='操作仓库ID')
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # 乐观锁版本字段
    version = db.Column(db.Integer, default=1, comment='版本号，用于乐观锁控制')

    # 关联关系
    operated_by_user = db.relationship('User', foreign_keys=[operated_by_user_id], backref='operated_outbound_records')
    operated_warehouse = db.relationship('Warehouse', foreign_keys=[operated_warehouse_id], backref='outbound_records')
    destination_warehouse = db.relationship('Warehouse', foreign_keys=[destination_warehouse_id], backref='destination_outbound_records')
    receiver = db.relationship('Receiver', foreign_keys=[receiver_id], backref='outbound_records')

    # 移除错误的唯一约束 - 同一识别编码应该允许分批出库
    # 业务逻辑：一个识别编码可以分多批出库，每批创建一条出库记录

    def __repr__(self):
        return f'<OutboundRecord {self.id} {self.plate_number} {self.customer_name}>'

    @property
    def create_time(self):
        """为了兼容模板中的 create_time 访问"""
        return self.created_at
    
    def to_dict(self):
        return {
            'id': self.id,
            'outbound_time': self.outbound_time.strftime('%Y-%m-%d') if self.outbound_time else None,
            'delivery_plate_number': self.delivery_plate_number,
            'plate_number': self.plate_number,
            'customer_name': self.customer_name,
            'identification_code': self.identification_code,
            'pallet_count': self.pallet_count,
            'package_count': self.package_count,
            'weight': self.weight,
            'volume': self.volume,
            'destination': self.destination,
            'warehouse_address': self.warehouse_address,
            'transport_company': self.transport_company,
            'order_type': self.order_type,
            'service_staff': self.service_staff,
            'receiver_id': self.receiver_id,
            'remarks': self.remarks,
            'remark1': self.remark1,
            'remark2': self.remark2,
            'document_count': self.document_count,
            'large_layer': self.large_layer,
            'small_layer': self.small_layer,
            'pallet_board': self.pallet_board,
            'inbound_plate': self.inbound_plate,
            'document_no': self.document_no,
            'export_mode': self.export_mode,
            'customs_broker': self.customs_broker,
            'location': self.location,
            'batch_no': self.batch_no,
            'batch_total': self.batch_total,
            'trailer': self.trailer,
            'container_number': self.container_number,
            'batch_sequence': self.batch_sequence,
            'vehicle_type': self.vehicle_type,
            'driver_name': self.driver_name,
            'driver_phone': self.driver_phone,
            'arrival_time': self.arrival_time.strftime('%Y-%m-%d %H:%M:%S') if self.arrival_time else None,
            'loading_start_time': self.loading_start_time.strftime('%Y-%m-%d %H:%M:%S') if self.loading_start_time else None,
            'loading_end_time': self.loading_end_time.strftime('%Y-%m-%d %H:%M:%S') if self.loading_end_time else None,
            'departure_time': self.departure_time.strftime('%Y-%m-%d %H:%M:%S') if self.departure_time else None,
            'detailed_address': self.detailed_address,
            'contact_window': self.contact_window,
            'inbound_date': self.inbound_date.strftime('%Y-%m-%d') if self.inbound_date else None,
            'operated_by_user_id': self.operated_by_user_id,
            'operated_by_user_name': self.operated_by_user.username if self.operated_by_user else None,
            'operated_warehouse_id': self.operated_warehouse_id,
            'operated_warehouse_name': self.operated_warehouse.warehouse_name if self.operated_warehouse else None,
            'create_time': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
        
class Inventory(db.Model):
    """库存模型"""
    __tablename__ = 'inventory'
    
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100))  # 客户名称
    identification_code = db.Column(db.String(100), unique=True)  # 识别编码
    inbound_pallet_count = db.Column(db.Integer)  # 入库板数
    inbound_package_count = db.Column(db.Integer)  # 入库件数
    pallet_count = db.Column(db.Integer)  # 库存板数
    package_count = db.Column(db.Integer)  # 库存件数
    weight = db.Column(db.Float)  # 重量
    volume = db.Column(db.Float)  # 体积
    location = db.Column(db.String(50))  # 库位
    documents = db.Column(db.String(100))  # 单据
    export_mode = db.Column(db.String(50))  # 出口方式
    order_type = db.Column(db.String(50))  # 订单类型
    customs_broker = db.Column(db.String(100))  # 报关行
    inbound_time = db.Column(db.DateTime)  # 入库时间
    plate_number = db.Column(db.String(20))  # 车牌号
    service_staff = db.Column(db.String(50))  # 服务人员
    # 后端仓库合并字段（不显示在界面中）
    original_identification_code = db.Column(db.String(100), comment='原始识别编码，用于后端仓库合并同一票货物')
    # 操作追踪字段
    operated_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), comment='操作用户ID')
    operated_warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse.id'), comment='操作仓库ID')
    last_updated = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)  # 最后更新时间
    version = db.Column(db.Integer, default=1)  # 版本号，用于乐观锁并发控制

    # 关联关系
    operated_by_user = db.relationship('User', foreign_keys=[operated_by_user_id], backref='operated_inventory_records')
    operated_warehouse = db.relationship('Warehouse', foreign_keys=[operated_warehouse_id], backref='inventory_records')
    
    def __repr__(self):
        return f'<Inventory {self.id} {self.customer_name} {self.identification_code}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'customer_name': self.customer_name,
            'identification_code': self.identification_code,
            'inbound_pallet_count': self.inbound_pallet_count,
            'inbound_package_count': self.inbound_package_count,
            'pallet_count': self.pallet_count,
            'package_count': self.package_count,
            'weight': self.weight,
            'volume': self.volume,
            'location': self.location,
            'documents': self.documents,
            'export_mode': self.export_mode,
            'order_type': self.order_type,
            'customs_broker': self.customs_broker,
            'service_staff': self.service_staff,
            'operated_by_user_id': self.operated_by_user_id,
            'operated_by_user_name': self.operated_by_user.username if self.operated_by_user else None,
            'operated_warehouse_id': self.operated_warehouse_id,
            'operated_warehouse_name': self.operated_warehouse.warehouse_name if self.operated_warehouse else None,
            'inbound_time': self.inbound_time.strftime('%Y-%m-%d') if self.inbound_time else None,
            'plate_number': self.plate_number,
            'last_updated': self.last_updated.strftime('%Y-%m-%d %H:%M:%S')
        }

class Receiver(db.Model):
    """收货人信息表"""
    id = db.Column(db.Integer, primary_key=True)
    warehouse_name = db.Column(db.String(100), index=True, nullable=False, unique=True, comment='目的仓')
    address = db.Column(db.String(255), nullable=False, comment='详细地址')
    contact = db.Column(db.String(100), nullable=False, comment='联络窗口')
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f'<Receiver {self.id} {self.warehouse_name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'warehouse_name': self.warehouse_name,
            'address': self.address,
            'contact': self.contact,
            'create_time': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        } 

class LabelCode(db.Model):
    __tablename__ = 'label_codes'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), nullable=False, unique=True)
    plate_number = db.Column(db.String(20), nullable=False)
    customer_name = db.Column(db.String(50), nullable=False)
    pallet_count = db.Column(db.Integer, default=0, comment='板数')
    package_count = db.Column(db.Integer, default=0, comment='件数')
    order_type = db.Column(db.String(20), default='零担')
    created_at = db.Column(db.DateTime, default=datetime.now)
    label_size = db.Column(db.String(20), default='40x60')
    label_format = db.Column(db.String(20), default='standard')
    custom_width = db.Column(db.Integer, default=40)
    custom_height = db.Column(db.Integer, default=60)
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'plate_number': self.plate_number,
            'customer_name': self.customer_name,
            'pallet_count': self.pallet_count,
            'package_count': self.package_count,
            'order_type': self.order_type,
            'create_time': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'label_size': self.label_size,
            'label_format': self.label_format,
            'custom_width': self.custom_width,
            'custom_height': self.custom_height
        }


# ==================== 多仓库账号管理系统模型 ====================

class Warehouse(db.Model):
    """仓库表"""
    __tablename__ = 'warehouse'

    id = db.Column(db.Integer, primary_key=True)
    warehouse_code = db.Column(db.String(20), unique=True, nullable=False, comment='仓库代码')
    warehouse_name = db.Column(db.String(100), nullable=False, comment='仓库名称')
    warehouse_type = db.Column(db.Enum('frontend', 'backend', name='warehouse_type'), nullable=False, comment='仓库类型')
    address = db.Column(db.Text, comment='仓库地址')
    contact_person = db.Column(db.String(50), comment='联系人')
    contact_phone = db.Column(db.String(20), comment='联系电话')
    status = db.Column(db.Enum('active', 'inactive', name='warehouse_status'), default='active', comment='状态')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')

    # 关联关系
    users = db.relationship('User', backref='warehouse', lazy='dynamic')
    user_roles = db.relationship('UserRole', backref='warehouse', lazy='dynamic')
    audit_logs = db.relationship('AuditLog', backref='warehouse', lazy='dynamic')

    def __repr__(self):
        return f'<Warehouse {self.warehouse_name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'warehouse_code': self.warehouse_code,
            'warehouse_name': self.warehouse_name,
            'warehouse_type': self.warehouse_type,
            'address': self.address,
            'contact_person': self.contact_person,
            'contact_phone': self.contact_phone,
            'status': self.status,
            'create_time': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'update_time': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }


class Role(db.Model):
    """角色表"""
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    role_code = db.Column(db.String(50), unique=True, nullable=False, comment='角色代码')
    role_name = db.Column(db.String(100), nullable=False, comment='角色名称')
    role_level = db.Column(db.Integer, nullable=False, comment='角色级别')
    description = db.Column(db.Text, comment='角色描述')
    status = db.Column(db.Enum('active', 'inactive', name='role_status'), default='active', comment='状态')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')

    # 关联关系
    user_roles = db.relationship('UserRole', backref='role', lazy='dynamic')
    role_permissions = db.relationship('RolePermission', backref='role', lazy='dynamic')

    def __repr__(self):
        return f'<Role {self.role_name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'role_code': self.role_code,
            'role_name': self.role_name,
            'role_level': self.role_level,
            'description': self.description,
            'status': self.status,
            'create_time': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'update_time': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }


class Permission(db.Model):
    """权限表"""
    __tablename__ = 'permissions'

    id = db.Column(db.Integer, primary_key=True)
    permission_code = db.Column(db.String(100), unique=True, nullable=False, comment='权限代码')
    permission_name = db.Column(db.String(100), nullable=False, comment='权限名称')
    module = db.Column(db.String(50), nullable=False, comment='所属模块')
    action = db.Column(db.String(50), nullable=False, comment='操作类型')
    description = db.Column(db.Text, comment='权限描述')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')

    # 关联关系
    role_permissions = db.relationship('RolePermission', backref='permission', lazy='dynamic')

    def __repr__(self):
        return f'<Permission {self.permission_name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'permission_code': self.permission_code,
            'permission_name': self.permission_name,
            'module': self.module,
            'action': self.action,
            'description': self.description,
            'create_time': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


class User(UserMixin, db.Model):
    """用户表"""
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, comment='用户名')
    password_hash = db.Column(db.String(255), nullable=False, comment='密码哈希')
    real_name = db.Column(db.String(50), nullable=False, comment='真实姓名')
    email = db.Column(db.String(100), comment='邮箱')
    phone = db.Column(db.String(20), comment='手机号')
    employee_id = db.Column(db.String(50), comment='员工编号')
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse.id'), comment='所属仓库ID')
    user_type = db.Column(db.Enum('admin', 'manager', 'operator', 'customer', name='user_type'), default='operator', comment='用户类型')
    is_admin = db.Column(db.Boolean, default=False, comment='是否为超级管理员')
    status = db.Column(db.Enum('active', 'inactive', 'locked', name='user_status'), default='active', comment='账号状态')
    last_login_at = db.Column(db.DateTime, comment='最后登录时间')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')

    # 关联关系
    user_roles = db.relationship('UserRole', foreign_keys='UserRole.user_id', backref='user', lazy='dynamic')
    assigned_roles = db.relationship('UserRole', foreign_keys='UserRole.assigned_by', backref='assigner', lazy='dynamic')
    login_logs = db.relationship('UserLoginLog', backref='user', lazy='dynamic')
    audit_logs = db.relationship('AuditLog', backref='user', lazy='dynamic')

    def set_password(self, password):
        """设置密码"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)

    def get_roles(self, warehouse_id=None):
        """获取用户角色"""
        query = self.user_roles.filter_by(status='active')
        if warehouse_id:
            query = query.filter_by(warehouse_id=warehouse_id)
        return [ur.role for ur in query.all()]

    def has_role(self, role_code):
        """检查用户是否有指定角色"""
        roles = self.get_roles()
        for role in roles:
            if role.role_code == role_code:
                return True
        return False

    def is_super_admin(self):
        """检查是否为超级管理员"""
        return self.is_admin or self.username == 'admin'

    def has_permission(self, permission_code, warehouse_id=None):
        """检查用户是否有指定权限"""
        # 超级管理员拥有所有权限
        if self.is_super_admin():
            return True

        # 使用新的权限管理器检查权限
        from app.utils.permission_manager import PermissionManager

        # 检查页面权限（新权限系统）
        if PermissionManager.has_page_permission(self.id, permission_code):
            return True

        # 检查菜单权限（新权限系统）
        if PermissionManager.has_menu_permission(self.id, permission_code):
            return True

        # 检查操作权限（新权限系统）
        if PermissionManager.has_operation_permission(self.id, permission_code):
            return True

        # 权限检查严格按照数据库中的权限分配进行
        # 不再提供临时的基本权限，确保权限控制的准确性
        return False

    def __repr__(self):
        return f'<User {self.username}>'

    def to_dict(self):
        try:
            # 安全地获取仓库信息
            warehouse_name = None
            warehouse_type = None
            if self.warehouse_id and self.warehouse:
                warehouse_name = self.warehouse.warehouse_name
                warehouse_type = self.warehouse.warehouse_type

            return {
                'id': self.id,
                'username': self.username,
                'real_name': self.real_name,
                'email': self.email,
                'phone': self.phone,
                'employee_id': self.employee_id,
                'warehouse_id': self.warehouse_id,
                'warehouse_name': warehouse_name,
                'warehouse_type': warehouse_type,
                'user_type': self.user_type,
                'is_admin': self.is_admin,
                'is_super_admin': self.is_super_admin(),
                'status': self.status,
                'last_login_at': self.last_login_at.strftime('%Y-%m-%d %H:%M:%S') if self.last_login_at else None,
                'create_time': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
                'update_time': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
            }
        except Exception as e:
            # 如果出现任何错误，返回基本信息
            return {
                'id': self.id,
                'username': self.username,
                'real_name': self.real_name,
                'email': self.email or '',
                'phone': self.phone or '',
                'employee_id': self.employee_id or '',
                'warehouse_id': self.warehouse_id,
                'warehouse_name': None,
                'warehouse_type': None,
                'is_admin': self.is_admin,
                'is_super_admin': False,
                'status': self.status,
                'last_login_at': None,
                'create_time': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
                'update_time': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
            }


class UserRole(db.Model):
    """用户角色关联表"""
    __tablename__ = 'user_roles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse.id'), comment='仓库范围限制')
    assigned_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='分配人ID')
    assigned_at = db.Column(db.DateTime, default=datetime.now, comment='分配时间')
    expires_at = db.Column(db.DateTime, comment='过期时间')
    status = db.Column(db.Enum('active', 'inactive', name='user_role_status'), default='active', comment='状态')

    __table_args__ = (db.UniqueConstraint('user_id', 'role_id', 'warehouse_id', name='unique_user_role_warehouse'),)

    def __repr__(self):
        return f'<UserRole {self.user_id}-{self.role_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'role_id': self.role_id,
            'warehouse_id': self.warehouse_id,
            'assigned_by': self.assigned_by,
            'assigned_at': self.assigned_at.strftime('%Y-%m-%d %H:%M:%S') if self.assigned_at else None,
            'expires_at': self.expires_at.strftime('%Y-%m-%d %H:%M:%S') if self.expires_at else None,
            'status': self.status
        }


class RolePermission(db.Model):
    """角色权限关联表"""
    __tablename__ = 'role_permissions'

    id = db.Column(db.Integer, primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    permission_id = db.Column(db.Integer, db.ForeignKey('permissions.id'), nullable=False)
    warehouse_scope = db.Column(db.Enum('all', 'own', 'none', name='warehouse_scope'), default='own', comment='仓库范围')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')

    __table_args__ = (db.UniqueConstraint('role_id', 'permission_id', name='unique_role_permission'),)

    def __repr__(self):
        return f'<RolePermission {self.role_id}-{self.permission_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'role_id': self.role_id,
            'permission_id': self.permission_id,
            'warehouse_scope': self.warehouse_scope,
            'create_time': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


class UserLoginLog(db.Model):
    """用户登录日志表"""
    __tablename__ = 'user_login_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    login_ip = db.Column(db.String(45), comment='登录IP')
    user_agent = db.Column(db.Text, comment='用户代理')
    login_time = db.Column(db.DateTime, default=datetime.now, comment='登录时间')
    logout_time = db.Column(db.DateTime, comment='登出时间')
    status = db.Column(db.Enum('success', 'failed', name='login_status'), default='success', comment='登录状态')

    def __repr__(self):
        return f'<UserLoginLog {self.user_id}-{self.login_time}>'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'login_ip': self.login_ip,
            'user_agent': self.user_agent,
            'login_time': self.login_time.strftime('%Y-%m-%d %H:%M:%S') if self.login_time else None,
            'logout_time': self.logout_time.strftime('%Y-%m-%d %H:%M:%S') if self.logout_time else None,
            'status': self.status
        }


class AuditLog(db.Model):
    """操作审计日志表"""
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse.id'), comment='操作的仓库')
    module = db.Column(db.String(50), nullable=False, comment='操作模块')
    action = db.Column(db.String(50), nullable=False, comment='操作类型')
    resource_type = db.Column(db.String(50), comment='资源类型')
    resource_id = db.Column(db.String(50), comment='资源ID')
    old_values = db.Column(db.JSON, comment='修改前的值')
    new_values = db.Column(db.JSON, comment='修改后的值')
    ip_address = db.Column(db.String(45), comment='IP地址')
    user_agent = db.Column(db.Text, comment='用户代理')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')

    def __repr__(self):
        return f'<AuditLog {self.user_id}-{self.action}-{self.created_at}>'

    @property
    def create_time(self):
        """为了兼容模板中的 create_time 访问"""
        return self.created_at

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'warehouse_id': self.warehouse_id,
            'module': self.module,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'old_values': self.old_values,
            'new_values': self.new_values,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'create_time': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


class TransitCargo(db.Model):
    """在途货物表"""
    __tablename__ = 'transit_cargo'

    id = db.Column(db.Integer, primary_key=True)

    # 货物基本信息
    customer_name = db.Column(db.String(100), nullable=False, comment='客户名称')
    identification_code = db.Column(db.String(100), nullable=False, comment='识别编码')
    pallet_count = db.Column(db.Integer, default=0, comment='板数')
    package_count = db.Column(db.Integer, default=0, comment='件数')
    weight = db.Column(db.Float, comment='重量(kg)')
    volume = db.Column(db.Float, comment='体积(m³)')

    # 业务信息
    export_mode = db.Column(db.String(50), comment='出境模式')
    order_type = db.Column(db.String(50), comment='订单类型')
    customs_broker = db.Column(db.String(100), comment='报关行')
    documents = db.Column(db.String(100), comment='单据份数')
    service_staff = db.Column(db.String(50), comment='跟单客服')

    # 运输信息
    batch_no = db.Column(db.String(50), nullable=False, index=True, comment='批次号')
    batch_sequence = db.Column(db.Integer, comment='批次序号')
    batch_total = db.Column(db.Integer, comment='批次总数')
    source_warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse.id'), nullable=False, comment='起始仓库ID')
    destination_warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse.id'), nullable=False, comment='目的仓库ID')
    departure_time = db.Column(db.DateTime, nullable=False, comment='出发时间')
    expected_arrival_time = db.Column(db.DateTime, comment='预计到达时间')
    actual_arrival_time = db.Column(db.DateTime, comment='实际到达时间')

    # 运输详情
    plate_number = db.Column(db.String(20), comment='运输车牌')
    delivery_plate_number = db.Column(db.String(20), comment='送货干线车')
    inbound_plate = db.Column(db.String(20), comment='入库车牌')
    driver_name = db.Column(db.String(50), comment='司机姓名')
    driver_phone = db.Column(db.String(20), comment='司机电话')

    # 状态管理
    status = db.Column(db.String(20), default='in_transit', nullable=False, comment='状态')
    # in_transit: 运输中
    # arrived: 已到达待接收
    # received: 已接收完成
    # cancelled: 已取消

    # 备注信息
    remark1 = db.Column(db.Text, comment='备注1')
    remark2 = db.Column(db.Text, comment='备注2')

    # 操作追踪
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), comment='操作用户ID')
    received_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), comment='接收用户ID')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    received_time = db.Column(db.DateTime, comment='接收时间')
    last_updated = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='最后更新时间')

    # 关联关系
    source_warehouse = db.relationship('Warehouse', foreign_keys=[source_warehouse_id], backref='outbound_transit_cargo')
    destination_warehouse = db.relationship('Warehouse', foreign_keys=[destination_warehouse_id], backref='inbound_transit_cargo')
    created_by_user = db.relationship('User', foreign_keys=[created_by_user_id], backref='created_transit_cargo')
    received_by_user = db.relationship('User', foreign_keys=[received_by_user_id], backref='received_transit_cargo')

    def __repr__(self):
        return f'<TransitCargo {self.id} {self.customer_name} {self.identification_code} {self.status}>'

    def to_dict(self):
        return {
            'id': self.id,
            'customer_name': self.customer_name,
            'identification_code': self.identification_code,
            'pallet_count': self.pallet_count,
            'package_count': self.package_count,
            'weight': self.weight,
            'volume': self.volume,
            'export_mode': self.export_mode,
            'order_type': self.order_type,
            'customs_broker': self.customs_broker,
            'documents': self.documents,
            'service_staff': self.service_staff,
            'batch_no': self.batch_no,
            'batch_sequence': self.batch_sequence,
            'batch_total': self.batch_total,
            'source_warehouse_id': self.source_warehouse_id,
            'source_warehouse_name': self.source_warehouse.warehouse_name if self.source_warehouse else None,
            'destination_warehouse_id': self.destination_warehouse_id,
            'destination_warehouse_name': self.destination_warehouse.warehouse_name if self.destination_warehouse else None,
            'departure_time': self.departure_time.strftime('%Y-%m-%d %H:%M:%S') if self.departure_time else None,
            'expected_arrival_time': self.expected_arrival_time.strftime('%Y-%m-%d %H:%M:%S') if self.expected_arrival_time else None,
            'actual_arrival_time': self.actual_arrival_time.strftime('%Y-%m-%d %H:%M:%S') if self.actual_arrival_time else None,
            'plate_number': self.plate_number,
            'delivery_plate_number': self.delivery_plate_number,
            'inbound_plate': self.inbound_plate,
            'driver_name': self.driver_name,
            'driver_phone': self.driver_phone,
            'status': self.status,
            'status_display': self.get_status_display(),
            'remark1': self.remark1,
            'remark2': self.remark2,
            'operated_by_user_id': self.created_by_user_id,
            'operated_by_user_name': self.created_by_user.username if self.created_by_user else None,
            'received_by_user_id': self.received_by_user_id,
            'received_by_user_name': self.received_by_user.username if self.received_by_user else None,
            'create_time': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'received_time': self.received_time.strftime('%Y-%m-%d %H:%M:%S') if self.received_time else None,
            'last_updated': self.last_updated.strftime('%Y-%m-%d %H:%M:%S') if self.last_updated else None
        }

    def get_status_display(self):
        """获取状态显示名称"""
        status_map = {
            'in_transit': '运输中',
            'arrived': '已到达',
            'received': '已接收',
            'cancelled': '已取消'
        }
        return status_map.get(self.status, self.status)

    def get_route_display(self):
        """获取运输路线显示"""
        source_name = self.source_warehouse.warehouse_name if self.source_warehouse else '未知'
        dest_name = self.destination_warehouse.warehouse_name if self.destination_warehouse else '未知'
        return f"{source_name} → {dest_name}"


class ReceiveRecord(db.Model):
    """接收记录表"""
    __tablename__ = 'receive_records'

    id = db.Column(db.Integer, primary_key=True)
    receive_time = db.Column(db.DateTime, index=True, default=datetime.now, comment='接收时间')
    batch_no = db.Column(db.String(50), index=True, comment='批次号')
    shipping_warehouse = db.Column(db.String(100), comment='发货仓库')
    customer_name = db.Column(db.String(100), index=True, nullable=False, comment='客户名称')
    identification_code = db.Column(db.String(100), index=True, unique=True, comment='识别编码')
    pallet_count = db.Column(db.Integer, default=0, comment='板数')
    package_count = db.Column(db.Integer, default=0, comment='件数')
    weight = db.Column(db.Float, default=0, comment='重量(kg)')
    volume = db.Column(db.Float, default=0, comment='体积(m³)')
    shipping_time = db.Column(db.DateTime, comment='发货时间')
    documents = db.Column(db.String(100), comment='单据')
    service_staff = db.Column(db.String(50), comment='跟单客服')
    # 车牌相关字段
    delivery_plate_number = db.Column(db.String(20), comment='送货干线车')
    inbound_plate = db.Column(db.String(20), comment='入库车牌')
    # 库位字段
    storage_location = db.Column(db.String(50), comment='库位栏')
    # 业务字段
    export_mode = db.Column(db.String(50), comment='出境模式')
    order_type = db.Column(db.String(50), comment='订单类型')
    customs_broker = db.Column(db.String(100), comment='报关行')
    batch_total = db.Column(db.Integer, comment='批次总数')
    batch_sequence = db.Column(db.String(20), comment='批次序号')
    remark1 = db.Column(db.Text, comment='备注1')
    remark2 = db.Column(db.Text, comment='备注2')
    # 状态字段
    receive_status = db.Column(db.String(20), default='已接收', comment='接收状态：已接收/未接收')
    # 操作追踪字段
    operated_warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse.id'), comment='操作仓库ID')
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='操作用户ID')
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # 关联关系
    operated_warehouse = db.relationship('Warehouse', foreign_keys=[operated_warehouse_id], backref='receive_records')
    created_by_user = db.relationship('User', foreign_keys=[created_by], backref='created_receive_records')

    def __repr__(self):
        return f'<ReceiveRecord {self.id} {self.customer_name}>'

    @property
    def create_time(self):
        """为了兼容模板中的 create_time 访问"""
        return self.created_at

    def to_dict(self):
        return {
            'id': self.id,
            'receive_time': self.receive_time.strftime('%Y-%m-%d %H:%M:%S') if self.receive_time else None,
            'batch_no': self.batch_no,
            'shipping_warehouse': self.shipping_warehouse,
            'customer_name': self.customer_name,
            'pallet_count': self.pallet_count,
            'package_count': self.package_count,
            'weight': self.weight,
            'volume': self.volume,
            'shipping_time': self.shipping_time.strftime('%Y-%m-%d %H:%M:%S') if self.shipping_time else None,
            'documents': self.documents,
            'service_staff': self.service_staff,
            'delivery_plate_number': self.delivery_plate_number,
            'inbound_plate': self.inbound_plate,
            'storage_location': self.storage_location,
            'export_mode': self.export_mode,
            'order_type': self.order_type,
            'customs_broker': self.customs_broker,
            'batch_total': self.batch_total,
            'batch_sequence': self.batch_sequence,
            'remark1': self.remark1,
            'remark2': self.remark2,
            'receive_status': self.receive_status,
            'operated_warehouse_id': self.operated_warehouse_id,
            'operated_warehouse_name': self.operated_warehouse.warehouse_name if self.operated_warehouse else None,
            'operated_by_user_id': self.created_by,
            'operated_by_user_name': self.created_by_user.username if self.created_by_user else None,
            'create_time': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


# ==================== 精细化权限管理模型 ====================

class MenuPermission(db.Model):
    """菜单权限定义表"""
    __tablename__ = 'menu_permissions'

    id = db.Column(db.Integer, primary_key=True)
    menu_code = db.Column(db.String(100), unique=True, nullable=False, comment='菜单代码')
    menu_name = db.Column(db.String(100), nullable=False, comment='菜单名称')
    parent_menu_code = db.Column(db.String(100), comment='父菜单代码')
    menu_level = db.Column(db.Integer, default=1, comment='菜单层级 1=一级菜单 2=二级菜单')
    menu_order = db.Column(db.Integer, default=0, comment='菜单排序')
    menu_icon = db.Column(db.String(50), comment='菜单图标')
    menu_url = db.Column(db.String(200), comment='菜单链接')
    description = db.Column(db.Text, comment='菜单描述')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')
    created_at = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f'<MenuPermission {self.menu_code}: {self.menu_name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'menu_code': self.menu_code,
            'menu_name': self.menu_name,
            'parent_menu_code': self.parent_menu_code,
            'menu_level': self.menu_level,
            'menu_order': self.menu_order,
            'menu_icon': self.menu_icon,
            'menu_url': self.menu_url,
            'description': self.description,
            'is_active': self.is_active
        }


class PagePermission(db.Model):
    """页面权限定义表"""
    __tablename__ = 'page_permissions'

    id = db.Column(db.Integer, primary_key=True)
    page_code = db.Column(db.String(100), unique=True, nullable=False, comment='页面代码')
    page_name = db.Column(db.String(100), nullable=False, comment='页面名称')
    menu_code = db.Column(db.String(100), db.ForeignKey('menu_permissions.menu_code'), comment='所属菜单')
    page_url = db.Column(db.String(200), comment='页面URL')
    description = db.Column(db.Text, comment='页面描述')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')
    created_at = db.Column(db.DateTime, default=datetime.now)

    # 关联关系
    menu = db.relationship('MenuPermission', backref='pages')

    def __repr__(self):
        return f'<PagePermission {self.page_code}: {self.page_name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'page_code': self.page_code,
            'page_name': self.page_name,
            'menu_code': self.menu_code,
            'page_url': self.page_url,
            'description': self.description,
            'is_active': self.is_active
        }


class OperationPermission(db.Model):
    """操作权限定义表"""
    __tablename__ = 'operation_permissions'

    id = db.Column(db.Integer, primary_key=True)
    operation_code = db.Column(db.String(100), unique=True, nullable=False, comment='操作代码')
    operation_name = db.Column(db.String(100), nullable=False, comment='操作名称')
    page_code = db.Column(db.String(100), db.ForeignKey('page_permissions.page_code'), comment='所属页面')
    operation_type = db.Column(db.String(50), comment='操作类型: view/create/edit/delete/export/print')
    description = db.Column(db.Text, comment='操作描述')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')
    created_at = db.Column(db.DateTime, default=datetime.now)

    # 关联关系
    page = db.relationship('PagePermission', backref='operations')

    def __repr__(self):
        return f'<OperationPermission {self.operation_code}: {self.operation_name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'operation_code': self.operation_code,
            'operation_name': self.operation_name,
            'page_code': self.page_code,
            'operation_type': self.operation_type,
            'description': self.description,
            'is_active': self.is_active
        }


class WarehousePermission(db.Model):
    """仓库权限定义表"""
    __tablename__ = 'warehouse_permissions'

    id = db.Column(db.Integer, primary_key=True)
    warehouse_permission_code = db.Column(db.String(100), unique=True, nullable=False, comment='仓库权限代码')
    warehouse_permission_name = db.Column(db.String(100), nullable=False, comment='仓库权限名称')
    warehouse_type = db.Column(db.String(50), comment='仓库类型: frontend/backend/all')
    operation_scope = db.Column(db.String(50), comment='操作范围: inbound/outbound/inventory/all')
    description = db.Column(db.Text, comment='权限描述')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')
    created_at = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f'<WarehousePermission {self.warehouse_permission_code}: {self.warehouse_permission_name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'warehouse_permission_code': self.warehouse_permission_code,
            'warehouse_permission_name': self.warehouse_permission_name,
            'warehouse_type': self.warehouse_type,
            'operation_scope': self.operation_scope,
            'description': self.description,
            'is_active': self.is_active
        }


class UserMenuPermission(db.Model):
    """用户菜单权限关联表"""
    __tablename__ = 'user_menu_permissions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, comment='用户ID')
    menu_code = db.Column(db.String(100), db.ForeignKey('menu_permissions.menu_code'), nullable=False, comment='菜单代码')
    is_granted = db.Column(db.Boolean, default=True, comment='是否授权')
    granted_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='授权人ID')
    granted_at = db.Column(db.DateTime, default=datetime.now, comment='授权时间')

    # 关联关系
    user = db.relationship('User', foreign_keys=[user_id], backref='menu_permissions')
    menu = db.relationship('MenuPermission', backref='user_permissions')
    granter = db.relationship('User', foreign_keys=[granted_by])

    __table_args__ = (db.UniqueConstraint('user_id', 'menu_code', name='unique_user_menu'),)

    def __repr__(self):
        return f'<UserMenuPermission {self.user_id}-{self.menu_code}>'


class UserPagePermission(db.Model):
    """用户页面权限关联表"""
    __tablename__ = 'user_page_permissions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, comment='用户ID')
    page_code = db.Column(db.String(100), db.ForeignKey('page_permissions.page_code'), nullable=False, comment='页面代码')
    is_granted = db.Column(db.Boolean, default=True, comment='是否授权')
    granted_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='授权人ID')
    granted_at = db.Column(db.DateTime, default=datetime.now, comment='授权时间')

    # 关联关系
    user = db.relationship('User', foreign_keys=[user_id], backref='page_permissions')
    page = db.relationship('PagePermission', backref='user_permissions')
    granter = db.relationship('User', foreign_keys=[granted_by])

    __table_args__ = (db.UniqueConstraint('user_id', 'page_code', name='unique_user_page'),)

    def __repr__(self):
        return f'<UserPagePermission {self.user_id}-{self.page_code}>'


class UserOperationPermission(db.Model):
    """用户操作权限关联表"""
    __tablename__ = 'user_operation_permissions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, comment='用户ID')
    operation_code = db.Column(db.String(100), db.ForeignKey('operation_permissions.operation_code'), nullable=False, comment='操作代码')
    is_granted = db.Column(db.Boolean, default=True, comment='是否授权')
    granted_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='授权人ID')
    granted_at = db.Column(db.DateTime, default=datetime.now, comment='授权时间')

    # 关联关系
    user = db.relationship('User', foreign_keys=[user_id], backref='operation_permissions')
    operation = db.relationship('OperationPermission', backref='user_permissions')
    granter = db.relationship('User', foreign_keys=[granted_by])

    __table_args__ = (db.UniqueConstraint('user_id', 'operation_code', name='unique_user_operation'),)

    def __repr__(self):
        return f'<UserOperationPermission {self.user_id}-{self.operation_code}>'


class UserWarehousePermission(db.Model):
    """用户仓库权限关联表"""
    __tablename__ = 'user_warehouse_permissions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, comment='用户ID')
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse.id'), nullable=False, comment='仓库ID')
    warehouse_permission_code = db.Column(db.String(100), db.ForeignKey('warehouse_permissions.warehouse_permission_code'), nullable=False, comment='仓库权限代码')
    is_granted = db.Column(db.Boolean, default=True, comment='是否授权')
    granted_by = db.Column(db.Integer, db.ForeignKey('user.id'), comment='授权人ID')
    granted_at = db.Column(db.DateTime, default=datetime.now, comment='授权时间')

    # 关联关系
    user = db.relationship('User', foreign_keys=[user_id], backref='warehouse_permissions')
    warehouse = db.relationship('Warehouse', backref='user_permissions')
    warehouse_permission = db.relationship('WarehousePermission', backref='user_permissions')
    granter = db.relationship('User', foreign_keys=[granted_by])

    __table_args__ = (db.UniqueConstraint('user_id', 'warehouse_id', 'warehouse_permission_code', name='unique_user_warehouse_permission'),)

    def __repr__(self):
        return f'<UserWarehousePermission {self.user_id}-{self.warehouse_id}-{self.warehouse_permission_code}>'


class SystemOptimizationLog(db.Model):
    """系统优化日志"""
    __tablename__ = 'system_optimization_logs'

    id = db.Column(db.Integer, primary_key=True)
    optimization_type = db.Column(db.String(50), nullable=False)  # 优化类型：startup, periodic
    message = db.Column(db.Text)  # 优化消息
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<SystemOptimizationLog {self.optimization_type}: {self.timestamp}>'