from flask import render_template, request, jsonify, flash, redirect, url_for, current_app
from app import db, csrf
from app.admin import bp
from datetime import datetime
import json

# 临时导入，用于演示
try:
    from flask_login import login_required, current_user
    from app.models import User, Role, Permission, Warehouse, UserRole, RolePermission, AuditLog, UserLoginLog
    from app.auth.decorators import check_permission
    from werkzeug.security import generate_password_hash
    FLASK_LOGIN_AVAILABLE = True
except ImportError:
    FLASK_LOGIN_AVAILABLE = False
    # 创建临时的装饰器
    def login_required(f):
        return f
    def check_permission(permission_code):
        def decorator(f):
            return f
        return decorator


@bp.route('/demo')
def demo():
    """多仓库账号管理系统演示页面"""
    return render_template('admin/demo.html')


@bp.route('/fix-identification-codes')
@login_required
@check_permission('ADMIN_MANAGE')
def fix_identification_codes():
    """修复识别编码页面"""
    return render_template('admin/fix_identification_codes.html')





@bp.route('/users')
@login_required
@check_permission('USER_VIEW')
def users():
    """用户管理页面"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # 根据用户权限过滤数据
    query = User.query
    if not current_user.has_permission('USER_VIEW', warehouse_id=None):
        # 只能查看自己仓库的用户
        query = query.filter_by(warehouse_id=current_user.warehouse_id)
    
    users = query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    warehouses = Warehouse.query.filter_by(status='active').all()
    roles = Role.query.filter_by(status='active').all()
    
    return render_template('admin/users.html',
                         users=users,
                         warehouses=warehouses,
                         roles=roles,
                         current_user=current_user)


@bp.route('/api/users', methods=['GET'])
@csrf.exempt
@login_required
@check_permission('USER_VIEW')
def api_users():
    """获取用户列表API"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '')
        warehouse_id = request.args.get('warehouse_id', type=int)
        status = request.args.get('status', '')

        # 使用eager loading优化查询性能
        query = User.query.options(db.joinedload(User.warehouse))

        # 根据用户权限过滤数据
        if not current_user.has_permission('USER_VIEW', warehouse_id=None):
            query = query.filter(User.warehouse_id == current_user.warehouse_id)

        # 搜索过滤
        if search:
            query = query.filter(
                db.or_(
                    User.username.contains(search),
                    User.real_name.contains(search),
                    User.email.contains(search)
                )
            )

        # 仓库过滤
        if warehouse_id:
            query = query.filter(User.warehouse_id == warehouse_id)

        # 状态过滤
        if status:
            query = query.filter(User.status == status)

        users = query.paginate(
            page=page, per_page=per_page, error_out=False
        )

        return jsonify({
            'users': [user.to_dict() for user in users.items],
            'total': users.total,
            'pages': users.pages,
            'current_page': users.page,
            'has_next': users.has_next,
            'has_prev': users.has_prev
        })

    except Exception as e:
        current_app.logger.error(f"获取用户列表失败: {str(e)}")
        return jsonify({'error': f'获取用户列表失败: {str(e)}'}), 500


@bp.route('/api/users/<int:user_id>', methods=['GET'])
@csrf.exempt
@login_required
@check_permission('USER_VIEW')
def api_get_user(user_id):
    """获取单个用户详情API"""
    try:
        # 检查用户是否已登录
        if not current_user.is_authenticated:
            return jsonify({'error': '请先登录'}), 401

        user = User.query.get_or_404(user_id)

        # 检查权限
        if hasattr(current_user, 'has_permission') and not current_user.has_permission('USER_VIEW', warehouse_id=None):
            if hasattr(current_user, 'warehouse_id') and user.warehouse_id != current_user.warehouse_id:
                return jsonify({'error': '权限不足'}), 403

        return jsonify({
            'success': True,
            'data': user.to_dict()
        })

    except Exception as e:
        current_app.logger.error(f"获取用户详情失败: {str(e)}")
        return jsonify({'error': f'获取用户详情失败: {str(e)}'}), 500


@bp.route('/api/users', methods=['POST'])
@csrf.exempt
@login_required
@check_permission('USER_CREATE')
def api_create_user():
    """创建用户API"""
    data = request.get_json()
    
    # 验证必填字段
    required_fields = ['username', 'real_name', 'password']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} 是必填字段'}), 400
    
    # 检查用户名是否已存在
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': '用户名已存在'}), 400
    
    # 检查邮箱是否已存在
    if data.get('email') and User.query.filter_by(email=data['email']).first():
        return jsonify({'error': '邮箱已存在'}), 400
    
    try:
        # 创建用户
        user = User(
            username=data['username'],
            real_name=data['real_name'],
            email=data.get('email'),
            phone=data.get('phone'),
            employee_id=data.get('employee_id'),
            warehouse_id=data.get('warehouse_id'),
            status=data.get('status', 'active')
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.flush()  # 获取用户ID
        
        # 分配角色
        role_ids = data.get('role_ids', [])
        for role_id in role_ids:
            user_role = UserRole(
                user_id=user.id,
                role_id=role_id,
                warehouse_id=data.get('warehouse_id'),
                assigned_by=current_user.id
            )
            db.session.add(user_role)
        
        # 记录审计日志
        audit_log = AuditLog(
            user_id=current_user.id,
            warehouse_id=current_user.warehouse_id,
            module='user_management',
            action='create',
            resource_type='user',
            resource_id=str(user.id),
            new_values=user.to_dict(),
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit_log)
        
        db.session.commit()
        
        return jsonify({
            'message': '用户创建成功',
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'创建用户失败: {str(e)}'}), 500


@bp.route('/api/users/<int:user_id>', methods=['PUT'])
@csrf.exempt
@login_required
@check_permission('USER_EDIT')
def api_update_user(user_id):
    """更新用户API"""
    user = User.query.get_or_404(user_id)
    
    # 检查权限：只能编辑自己仓库的用户
    if not current_user.has_permission('USER_EDIT', warehouse_id=None):
        if user.warehouse_id != current_user.warehouse_id:
            return jsonify({'error': '没有权限编辑此用户'}), 403
    
    data = request.get_json()
    old_values = user.to_dict()
    
    try:
        # 更新用户信息
        if 'username' in data:
            # 只有admin用户才能修改用户名
            if current_user.username != 'admin':
                return jsonify({'error': '只有管理员才能修改用户名'}), 403
            # 检查用户名是否已被其他用户使用
            existing_user = User.query.filter_by(username=data['username']).first()
            if existing_user and existing_user.id != user.id:
                return jsonify({'error': '用户名已被其他用户使用'}), 400
            user.username = data['username']
        if 'real_name' in data:
            user.real_name = data['real_name']
        if 'email' in data:
            # 检查邮箱是否已被其他用户使用
            if data['email']:  # 只有当邮箱不为空时才检查
                existing_user = User.query.filter_by(email=data['email']).first()
                if existing_user and existing_user.id != user.id:
                    return jsonify({'error': '邮箱已被其他用户使用'}), 400
            user.email = data['email']
        if 'phone' in data:
            user.phone = data['phone']
        if 'employee_id' in data:
            user.employee_id = data['employee_id']
        if 'warehouse_id' in data:
            # 处理空值
            user.warehouse_id = data['warehouse_id'] if data['warehouse_id'] else None
        if 'status' in data:
            user.status = data['status']

        # 更新密码
        if data.get('password'):
            user.set_password(data['password'])

        # 更新角色
        if 'role_ids' in data:
            # 删除现有角色
            UserRole.query.filter_by(user_id=user.id).delete()

            # 添加新角色
            for role_id in data['role_ids']:
                user_role = UserRole(
                    user_id=user.id,
                    role_id=role_id,
                    warehouse_id=data.get('warehouse_id'),
                    assigned_by=current_user.id
                )
                db.session.add(user_role)

        # 先提交用户更新
        db.session.commit()

        # 记录审计日志（使用简化的数据避免JSON序列化问题）
        try:
            # 获取新的用户数据
            new_values = {
                'id': user.id,
                'username': user.username,
                'real_name': user.real_name,
                'email': user.email,
                'phone': user.phone,
                'employee_id': user.employee_id,
                'warehouse_id': user.warehouse_id,
                'status': user.status
            }

            audit_log = AuditLog(
                user_id=current_user.id,
                warehouse_id=current_user.warehouse_id,
                module='user_management',
                action='update',
                resource_type='user',
                resource_id=str(user.id),
                old_values=old_values,
                new_values=new_values,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit_log)
            db.session.commit()
        except Exception as audit_error:
            # 审计日志失败不应该影响用户更新
            current_app.logger.warning(f"审计日志记录失败: {str(audit_error)}")

        return jsonify({
            'success': True,
            'message': '用户更新成功',
            'data': user.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更新用户失败: {str(e)}")
        return jsonify({'error': f'更新用户失败: {str(e)}'}), 500


@bp.route('/api/users/<int:user_id>', methods=['DELETE'])
@csrf.exempt
@login_required
@check_permission('USER_DELETE')
def api_delete_user(user_id):
    """删除用户API"""
    user = User.query.get_or_404(user_id)
    
    # 不能删除自己
    if user.id == current_user.id:
        return jsonify({'error': '不能删除自己的账号'}), 400
    
    # 检查权限：只能删除自己仓库的用户
    if not current_user.has_permission('USER_DELETE', warehouse_id=None):
        if user.warehouse_id != current_user.warehouse_id:
            return jsonify({'error': '没有权限删除此用户'}), 403
    
    try:
        old_values = user.to_dict()

        # 记录审计日志
        audit_log = AuditLog(
            user_id=current_user.id,
            warehouse_id=current_user.warehouse_id,
            module='user_management',
            action='delete',
            resource_type='user',
            resource_id=str(user.id),
            old_values=old_values,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit_log)

        # 删除相关记录（避免外键约束错误）
        # 删除用户权限记录
        from app.models import UserMenuPermission, UserPagePermission, UserOperationPermission, UserWarehousePermission
        UserMenuPermission.query.filter_by(user_id=user.id).delete()
        UserPagePermission.query.filter_by(user_id=user.id).delete()
        UserOperationPermission.query.filter_by(user_id=user.id).delete()
        UserWarehousePermission.query.filter_by(user_id=user.id).delete()

        # 删除用户角色关联
        UserRole.query.filter_by(user_id=user.id).delete()
        UserRole.query.filter_by(assigned_by=user.id).delete()

        # 删除登录日志
        UserLoginLog.query.filter_by(user_id=user.id).delete()

        # 删除审计日志（除了刚刚添加的这条）
        AuditLog.query.filter(AuditLog.user_id == user.id, AuditLog.id != audit_log.id).delete()

        # 删除用户
        db.session.delete(user)
        db.session.commit()

        return jsonify({'message': '用户删除成功'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'删除用户失败: {str(e)}'}), 500


@bp.route('/roles')
@login_required
@check_permission('ROLE_VIEW')
def roles():
    """角色管理页面"""
    roles = Role.query.filter_by(status='active').all()
    permissions = Permission.query.all()

    return render_template('admin/roles.html',
                         roles=roles,
                         permissions=permissions)

@bp.route('/roles-fixed')
@login_required
def roles_fixed():
    """角色管理页面 - 修复版（无缓存问题）"""
    if current_user.username != 'admin':
        flash('只有管理员才能访问角色管理', 'error')
        return redirect(url_for('main.index'))

    return render_template('admin/roles_fixed.html')


@bp.route('/warehouses')
@login_required
@check_permission('WAREHOUSE_VIEW')
def warehouses():
    """仓库管理页面"""
    warehouses = Warehouse.query.all()  # 显示所有仓库，包括停用的

    return render_template('admin/warehouses.html',
                         warehouses=warehouses)

@bp.route('/api/warehouses/<int:warehouse_id>')
@login_required
@check_permission('WAREHOUSE_VIEW')
def get_warehouse(warehouse_id):
    """获取单个仓库信息"""
    try:
        warehouse = Warehouse.query.get_or_404(warehouse_id)
        return jsonify({
            'success': True,
            'warehouse': {
                'id': warehouse.id,
                'warehouse_name': warehouse.warehouse_name,
                'warehouse_code': warehouse.warehouse_code,
                'warehouse_type': warehouse.warehouse_type,
                'address': warehouse.address,
                'contact_person': warehouse.contact_person,
                'contact_phone': warehouse.contact_phone,
                'status': warehouse.status
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/api/warehouses/<int:warehouse_id>/details')
@login_required
@check_permission('WAREHOUSE_VIEW')
def get_warehouse_details(warehouse_id):
    """获取仓库详细信息和统计数据"""
    try:
        warehouse = Warehouse.query.get_or_404(warehouse_id)

        # 获取统计信息
        user_count = User.query.filter_by(warehouse_id=warehouse_id).count() if FLASK_LOGIN_AVAILABLE else 0

        # 尝试获取库存、入库、出库统计（如果相关表存在）
        inventory_count = 0
        inbound_count = 0
        outbound_count = 0

        try:
            # 这些统计可能需要根据实际的表结构调整
            from app.models import Inventory, InboundRecord, OutboundRecord
            inventory_count = Inventory.query.filter_by(warehouse_id=warehouse_id).count()
            inbound_count = InboundRecord.query.filter_by(warehouse_id=warehouse_id).count()
            outbound_count = OutboundRecord.query.filter_by(warehouse_id=warehouse_id).count()
        except:
            # 如果表不存在或查询失败，使用默认值
            pass

        return jsonify({
            'success': True,
            'warehouse': {
                'id': warehouse.id,
                'warehouse_name': warehouse.warehouse_name,
                'warehouse_code': warehouse.warehouse_code,
                'warehouse_type': warehouse.warehouse_type,
                'address': warehouse.address,
                'contact_person': warehouse.contact_person,
                'contact_phone': warehouse.contact_phone,
                'status': warehouse.status,
                'created_at': warehouse.created_at.strftime('%Y-%m-%d %H:%M:%S') if warehouse.created_at else '',
                'updated_at': warehouse.updated_at.strftime('%Y-%m-%d %H:%M:%S') if warehouse.updated_at else ''
            },
            'statistics': {
                'user_count': user_count,
                'inventory_count': inventory_count,
                'inbound_count': inbound_count,
                'outbound_count': outbound_count
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/api/warehouses/<int:warehouse_id>', methods=['PUT'])
@login_required
@check_permission('WAREHOUSE_EDIT')
def update_warehouse(warehouse_id):
    """更新仓库信息"""
    try:
        warehouse = Warehouse.query.get_or_404(warehouse_id)
        data = request.get_json()

        # 验证必填字段
        if not data.get('warehouse_name'):
            return jsonify({'success': False, 'error': '仓库名称不能为空'}), 400
        if not data.get('warehouse_code'):
            return jsonify({'success': False, 'error': '仓库代码不能为空'}), 400
        if not data.get('warehouse_type'):
            return jsonify({'success': False, 'error': '仓库类型不能为空'}), 400

        # 检查仓库代码是否重复（排除当前仓库）
        existing_warehouse = Warehouse.query.filter(
            Warehouse.warehouse_code == data['warehouse_code'],
            Warehouse.id != warehouse_id
        ).first()
        if existing_warehouse:
            return jsonify({'success': False, 'error': '仓库代码已存在'}), 400

        # 更新仓库信息
        warehouse.warehouse_name = data['warehouse_name']
        warehouse.warehouse_code = data['warehouse_code']
        warehouse.warehouse_type = data['warehouse_type']
        warehouse.address = data.get('address', '')
        warehouse.contact_person = data.get('contact_person', '')
        warehouse.contact_phone = data.get('contact_phone', '')
        warehouse.status = data.get('status', 'active')

        db.session.commit()

        # 记录审计日志
        if FLASK_LOGIN_AVAILABLE:
            audit_log = AuditLog(
                user_id=current_user.id,
                warehouse_id=current_user.warehouse_id,
                module='admin',
                action='UPDATE_WAREHOUSE',
                resource_type='warehouse',
                resource_id=str(warehouse.id),
                new_values={'warehouse_name': warehouse.warehouse_name},
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit_log)
            db.session.commit()

        return jsonify({
            'success': True,
            'message': '仓库信息更新成功',
            'warehouse': {
                'id': warehouse.id,
                'warehouse_name': warehouse.warehouse_name,
                'warehouse_code': warehouse.warehouse_code,
                'warehouse_type': warehouse.warehouse_type,
                'address': warehouse.address,
                'contact_person': warehouse.contact_person,
                'contact_phone': warehouse.contact_phone,
                'status': warehouse.status
            }
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'更新仓库失败: {str(e)}'}), 500

@bp.route('/api/warehouses', methods=['POST'])
@login_required
@check_permission('WAREHOUSE_EDIT')
def create_warehouse():
    """创建新仓库并自动创建对应账号和权限"""
    try:
        data = request.get_json()

        # 验证必填字段
        if not data.get('warehouse_name'):
            return jsonify({'success': False, 'error': '仓库名称不能为空'}), 400
        if not data.get('warehouse_code'):
            return jsonify({'success': False, 'error': '仓库代码不能为空'}), 400
        if not data.get('warehouse_type'):
            return jsonify({'success': False, 'error': '仓库类型不能为空'}), 400

        # 检查仓库代码是否重复
        existing_warehouse = Warehouse.query.filter_by(warehouse_code=data['warehouse_code']).first()
        if existing_warehouse:
            return jsonify({'success': False, 'error': '仓库代码已存在'}), 400

        # 创建仓库
        warehouse = Warehouse(
            warehouse_name=data['warehouse_name'],
            warehouse_code=data['warehouse_code'],
            warehouse_type=data['warehouse_type'],
            address=data.get('address', ''),
            contact_person=data.get('contact_person', ''),
            contact_phone=data.get('contact_phone', ''),
            status=data.get('status', 'active')
        )

        db.session.add(warehouse)
        db.session.flush()  # 获取warehouse.id

        # 自动创建仓库对应的账号
        created_accounts = create_warehouse_accounts(warehouse)

        db.session.commit()

        # 记录审计日志
        if FLASK_LOGIN_AVAILABLE:
            audit_log = AuditLog(
                user_id=current_user.id,
                warehouse_id=current_user.warehouse_id,
                module='admin',
                action='CREATE_WAREHOUSE',
                resource_type='warehouse',
                resource_id=str(warehouse.id),
                new_values={
                    'warehouse_name': warehouse.warehouse_name,
                    'created_accounts': len(created_accounts)
                },
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit_log)
            db.session.commit()

        return jsonify({
            'success': True,
            'message': f'仓库创建成功，已自动创建{len(created_accounts)}个对应账号',
            'warehouse': {
                'id': warehouse.id,
                'warehouse_name': warehouse.warehouse_name,
                'warehouse_code': warehouse.warehouse_code,
                'warehouse_type': warehouse.warehouse_type,
                'address': warehouse.address,
                'contact_person': warehouse.contact_person,
                'contact_phone': warehouse.contact_phone,
                'status': warehouse.status
            },
            'created_accounts': created_accounts
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'创建仓库失败: {str(e)}'}), 500

def create_warehouse_accounts(warehouse):
    """为新仓库自动创建对应的账号和权限"""
    created_accounts = []

    try:
        # 获取角色
        manager_role = Role.query.filter_by(role_code='MANAGER').first()
        operator_role = Role.query.filter_by(role_code='OPERATOR').first()

        if not manager_role or not operator_role:
            # 如果角色不存在，先创建基本角色
            if not manager_role:
                manager_role = Role(
                    role_name='仓库经理',
                    role_code='MANAGER',
                    description='仓库管理权限',
                    status='active'
                )
                db.session.add(manager_role)

            if not operator_role:
                operator_role = Role(
                    role_name='仓库操作员',
                    role_code='OPERATOR',
                    description='仓库操作权限',
                    status='active'
                )
                db.session.add(operator_role)

            db.session.flush()

        # 根据仓库类型和代码创建账号
        warehouse_code = warehouse.warehouse_code.lower()
        warehouse_name = warehouse.warehouse_name

        # 创建仓库经理账号
        manager_username = f"{warehouse_code}_manager"
        manager_user = User(
            username=manager_username,
            password_hash=generate_password_hash(f"{warehouse_code}123"),  # 默认密码：仓库代码+123
            real_name=f"{warehouse_name}经理",
            warehouse_id=warehouse.id,
            status='active'
        )
        db.session.add(manager_user)
        db.session.flush()

        # 分配经理角色
        manager_user_role = UserRole(
            user_id=manager_user.id,
            role_id=manager_role.id,
            warehouse_id=warehouse.id,
            assigned_by=current_user.id if FLASK_LOGIN_AVAILABLE else None,
            status='active'
        )
        db.session.add(manager_user_role)

        created_accounts.append({
            'username': manager_username,
            'password': f"{warehouse_code}123",
            'role': '仓库经理',
            'real_name': f"{warehouse_name}经理"
        })

        # 创建仓库操作员账号
        operator_username = f"{warehouse_code}_operator"
        operator_user = User(
            username=operator_username,
            password_hash=generate_password_hash(f"{warehouse_code}456"),  # 默认密码：仓库代码+456
            real_name=f"{warehouse_name}操作员",
            warehouse_id=warehouse.id,
            status='active'
        )
        db.session.add(operator_user)
        db.session.flush()

        # 分配操作员角色
        operator_user_role = UserRole(
            user_id=operator_user.id,
            role_id=operator_role.id,
            warehouse_id=warehouse.id,
            assigned_by=current_user.id if FLASK_LOGIN_AVAILABLE else None,
            status='active'
        )
        db.session.add(operator_user_role)

        created_accounts.append({
            'username': operator_username,
            'password': f"{warehouse_code}456",
            'role': '仓库操作员',
            'real_name': f"{warehouse_name}操作员"
        })

        return created_accounts

    except Exception as e:
        print(f"创建仓库账号失败: {str(e)}")
        return created_accounts







@bp.route('/audit_logs')
@login_required
@check_permission('AUDIT_LOG_VIEW')
def audit_logs():
    """审计日志页面"""
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    query = AuditLog.query
    
    # 根据用户权限过滤数据
    if not current_user.has_permission('AUDIT_LOG_VIEW', warehouse_id=None):
        query = query.filter_by(warehouse_id=current_user.warehouse_id)
    
    logs = query.order_by(AuditLog.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/audit_logs.html', logs=logs)


@bp.route('/performance')
@login_required
@check_permission('ADMIN_VIEW')
def performance_monitor():
    """性能监控页面"""
    if current_user.username != 'admin':
        flash('只有管理员才能访问性能监控', 'error')
        return redirect(url_for('main.index'))

    return render_template('admin/performance_monitor.html')


# ==================== 用户权限管理API ====================

@bp.route('/api/users/<int:user_id>/menu-permissions', methods=['GET'])
@csrf.exempt
@login_required
@check_permission('USER_VIEW')
def get_user_menu_permissions(user_id):
    """获取用户菜单权限"""
    try:
        user = User.query.get_or_404(user_id)

        # 获取所有菜单权限
        from app.models import MenuPermission, UserMenuPermission

        # 查询所有菜单权限和用户的权限状态
        menu_permissions = db.session.query(
            MenuPermission.menu_code,
            MenuPermission.menu_name,
            MenuPermission.menu_icon,
            MenuPermission.menu_level,
            MenuPermission.parent_menu_code,
            UserMenuPermission.is_granted
        ).outerjoin(
            UserMenuPermission,
            (UserMenuPermission.menu_code == MenuPermission.menu_code) &
            (UserMenuPermission.user_id == user_id)
        ).filter(
            MenuPermission.is_active == True
        ).order_by(
            MenuPermission.menu_level,
            MenuPermission.menu_order
        ).all()

        permissions = []
        for perm in menu_permissions:
            permissions.append({
                'menu_code': perm.menu_code,
                'menu_name': perm.menu_name,
                'menu_icon': perm.menu_icon,
                'menu_level': perm.menu_level,
                'parent_menu_code': perm.parent_menu_code,
                'granted': bool(perm.is_granted) if perm.is_granted is not None else False
            })

        return jsonify({
            'success': True,
            'permissions': permissions
        })

    except Exception as e:
        current_app.logger.error(f"获取用户菜单权限失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取用户菜单权限失败: {str(e)}'
        }), 500


@bp.route('/api/users/<int:user_id>/permissions', methods=['PUT'])
@csrf.exempt
@login_required
def update_user_permissions(user_id):
    """更新用户权限"""
    try:
        # 权限检查
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': '请先登录'}), 401

        # 检查是否为管理员或有权限的用户
        if not (current_user.username == 'admin' or
                getattr(current_user, 'is_admin', False) or
                (hasattr(current_user, 'has_permission') and current_user.has_permission('USER_EDIT'))):
            current_app.logger.warning(f"用户 {current_user.username} 尝试修改用户权限但没有权限")
            return jsonify({'success': False, 'error': '您没有权限执行此操作'}), 403

        user = User.query.get_or_404(user_id)
        data = request.get_json()

        current_app.logger.info(f"用户 {current_user.username} 正在更新用户 {user.username} 的权限")
        current_app.logger.debug(f"接收到的权限数据: {data}")

        if not data:
            return jsonify({'success': False, 'error': '无效的请求数据'}), 400

        # 更新菜单权限
        if 'menu_permissions' in data:
            # 删除现有菜单权限
            from app.models import UserMenuPermission
            UserMenuPermission.query.filter_by(user_id=user_id).delete()

            # 添加新的菜单权限
            for menu_code in data['menu_permissions']:
                permission = UserMenuPermission(
                    user_id=user_id,
                    menu_code=menu_code,
                    is_granted=True,
                    granted_at=datetime.now()
                )
                db.session.add(permission)

        # 更新页面权限
        if 'page_permissions' in data:
            from app.models import UserPagePermission
            UserPagePermission.query.filter_by(user_id=user_id).delete()

            for page_code in data['page_permissions']:
                permission = UserPagePermission(
                    user_id=user_id,
                    page_code=page_code,
                    is_granted=True,
                    granted_at=datetime.now()
                )
                db.session.add(permission)

        # 更新操作权限
        if 'operation_permissions' in data:
            from app.models import UserOperationPermission
            UserOperationPermission.query.filter_by(user_id=user_id).delete()

            for operation_code in data['operation_permissions']:
                permission = UserOperationPermission(
                    user_id=user_id,
                    operation_code=operation_code,
                    is_granted=True,
                    granted_at=datetime.now()
                )
                db.session.add(permission)

        # 更新仓库权限
        if 'warehouse_permissions' in data:
            from app.models import UserWarehousePermission
            UserWarehousePermission.query.filter_by(user_id=user_id).delete()

            for warehouse_perm in data['warehouse_permissions']:
                permission = UserWarehousePermission(
                    user_id=user_id,
                    warehouse_id=warehouse_perm['warehouse_id'],
                    warehouse_permission_code=warehouse_perm['permission_code'],
                    is_granted=True,
                    granted_at=datetime.now()
                )
                db.session.add(permission)

        db.session.commit()
        current_app.logger.info(f"用户 {user.username} 的权限更新成功")

        # 记录操作日志
        try:
            from app.models import AuditLog
            audit_log = AuditLog(
                user_id=current_user.id,
                warehouse_id=current_user.warehouse_id,
                module='admin',
                action='UPDATE_USER_PERMISSIONS',
                resource_type='User',
                resource_id=str(user_id),
                new_values={
                    'target_user': user.username,
                    'permissions_updated': True,
                    'menu_count': len(data.get('menu_permissions', [])),
                    'page_count': len(data.get('page_permissions', [])),
                    'operation_count': len(data.get('operation_permissions', [])),
                    'warehouse_count': len(data.get('warehouse_permissions', []))
                },
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit_log)
            db.session.commit()
        except Exception as audit_error:
            current_app.logger.warning(f"记录审计日志失败: {str(audit_error)}")

        return jsonify({
            'success': True,
            'message': '权限更新成功'
        })

    except Exception as e:
        db.session.rollback()
        error_msg = str(e)
        current_app.logger.error(f"更新用户权限失败: {error_msg}")
        current_app.logger.error(f"错误详情: {type(e).__name__}: {error_msg}")

        # 返回更友好的错误信息
        if "foreign key constraint" in error_msg.lower():
            error_msg = "权限配置数据有误，请检查权限设置"
        elif "not found" in error_msg.lower():
            error_msg = "用户不存在"
        elif "permission" in error_msg.lower():
            error_msg = "权限验证失败"

        return jsonify({
            'success': False,
            'error': f'权限更新失败: {error_msg}'
        }), 500


# ==================== 调度器管理路由 ====================

@bp.route('/scheduler')
@login_required
@check_permission('ADMIN_VIEW')
def scheduler_monitor():
    """调度器监控页面"""
    return render_template('admin/scheduler_monitor.html', title='调度器监控')


@bp.route('/scheduler/status')
@login_required
@check_permission('ADMIN_VIEW')
def scheduler_status():
    """获取调度器状态"""
    try:
        from app.services.scheduler_service import scheduler_service
        stats = scheduler_service.get_job_status()

        return jsonify({
            'success': True,
            'data': stats
        })

    except Exception as e:
        current_app.logger.error(f"获取调度器状态失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@bp.route('/scheduler/run_job', methods=['POST'])
@login_required
@check_permission('ADMIN_MANAGE')
@csrf.exempt
def run_job_now():
    """立即执行指定任务"""
    try:
        job_id = request.form.get('job_id')
        if not job_id:
            return jsonify({
                'success': False,
                'message': '缺少任务ID'
            }), 400

        from app.services.scheduler_service import scheduler_service
        result = scheduler_service.run_job_now(job_id)

        # 记录操作日志
        if FLASK_LOGIN_AVAILABLE:
            try:
                audit_log = AuditLog(
                    user_id=current_user.id,
                    action='SCHEDULER_RUN_JOB',
                    resource_type='SCHEDULER',
                    resource_id=job_id,
                    details=f'手动执行任务: {job_id}',
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent', '')
                )
                db.session.add(audit_log)
                db.session.commit()
            except Exception as e:
                current_app.logger.warning(f"记录审计日志失败: {e}")

        return jsonify(result)

    except Exception as e:
        current_app.logger.error(f"执行任务失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@bp.route('/scheduler/pause_job', methods=['POST'])
@login_required
@check_permission('ADMIN_MANAGE')
@csrf.exempt
def pause_job():
    """暂停任务"""
    try:
        job_id = request.form.get('job_id')
        if not job_id:
            return jsonify({
                'success': False,
                'message': '缺少任务ID'
            }), 400

        from app.services.scheduler_service import scheduler_service
        result = scheduler_service.pause_job(job_id)

        return jsonify(result)

    except Exception as e:
        current_app.logger.error(f"暂停任务失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@bp.route('/scheduler/resume_job', methods=['POST'])
@login_required
@check_permission('ADMIN_MANAGE')
@csrf.exempt
def resume_job():
    """恢复任务"""
    try:
        job_id = request.form.get('job_id')
        if not job_id:
            return jsonify({
                'success': False,
                'message': '缺少任务ID'
            }), 400

        from app.services.scheduler_service import scheduler_service
        result = scheduler_service.resume_job(job_id)

        return jsonify(result)

    except Exception as e:
        current_app.logger.error(f"恢复任务失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@bp.route('/scheduler/export_stats')
@login_required
@check_permission('ADMIN_VIEW')
def export_scheduler_stats():
    """导出调度器统计信息"""
    try:
        from app.services.scheduler_service import scheduler_service
        stats = scheduler_service.get_job_status()

        # 生成CSV内容
        import io
        import csv

        output = io.StringIO()
        writer = csv.writer(output)

        # 写入标题
        writer.writerow(['任务ID', '任务名称', '下次执行时间', '已执行次数', '错误次数', '错过次数', '上次执行时间'])

        # 写入数据
        for job in stats.get('jobs', []):
            writer.writerow([
                job.get('id', ''),
                job.get('name', ''),
                job.get('next_run_time', ''),
                job.get('executed', 0),
                job.get('errors', 0),
                job.get('missed', 0),
                job.get('last_run', '')
            ])

        output.seek(0)

        # 创建响应
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv; charset=utf-8'
        response.headers['Content-Disposition'] = f'attachment; filename=scheduler_stats_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'

        return response

    except Exception as e:
        current_app.logger.error(f"导出调度器统计失败: {e}")
        flash(f'导出失败: {str(e)}', 'error')
        return redirect(url_for('admin.scheduler_monitor'))


@bp.route('/performance/dashboard')
@login_required
@check_permission('ADMIN_SYSTEM_MONITOR')
def performance_dashboard():
    """性能监控仪表板"""
    try:
        from app.integrated_performance_optimizer import integrated_optimizer
        from app.performance_monitor import perf_dashboard, performance_metrics

        # 获取性能状态
        quick_status = integrated_optimizer.get_quick_status()

        # 获取详细性能摘要
        performance_summary = perf_dashboard.get_performance_summary()

        # 获取慢查询
        slow_queries = performance_metrics.get_slow_queries(20)

        return render_template('admin/performance_dashboard.html',
                             quick_status=quick_status,
                             performance_summary=performance_summary,
                             slow_queries=slow_queries)

    except Exception as e:
        current_app.logger.error(f"性能仪表板加载失败: {e}")
        flash(f'加载失败: {str(e)}', 'error')
        return redirect(url_for('admin.demo'))


@bp.route('/performance/optimize', methods=['POST'])
@csrf.exempt
@login_required
@check_permission('ADMIN_SYSTEM_OPTIMIZE')
def run_performance_optimization():
    """运行性能优化"""
    try:
        from app.integrated_performance_optimizer import integrated_optimizer

        optimization_type = request.json.get('type', 'comprehensive')

        if optimization_type == 'quick':
            # 快速优化：只清理缓存
            from app.cache_config import get_cache_manager
            cache_manager = get_cache_manager()
            cleared = cache_manager.delete_pattern('search_results*')

            result = {
                'success': True,
                'message': f'快速优化完成，清理了 {cleared} 个缓存项',
                'type': 'quick'
            }
        else:
            # 综合优化
            result = integrated_optimizer.run_comprehensive_optimization()
            result['type'] = 'comprehensive'

        return jsonify(result)

    except Exception as e:
        current_app.logger.error(f"性能优化失败: {e}")
        return jsonify({
            'success': False,
            'message': f'优化失败: {str(e)}'
        }), 500


@bp.route('/performance/status')
@csrf.exempt
@login_required
@check_permission('ADMIN_SYSTEM_MONITOR')
def get_performance_status():
    """获取性能状态API"""
    try:
        from app.integrated_performance_optimizer import integrated_optimizer
        status = integrated_optimizer.get_quick_status()
        return jsonify(status)

    except Exception as e:
        current_app.logger.error(f"获取性能状态失败: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/optimization_monitor')
@login_required
@check_permission('ADMIN_VIEW')
def optimization_monitor():
    """系统优化监控页面"""
    return render_template('admin/optimization_monitor.html')
