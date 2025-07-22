from flask import jsonify, request, current_app
from app import db, csrf
from app.api.bp import bp
from app.models import Inventory, Warehouse, Receiver
import traceback

# 确保API路由被正确注册到蓝图
__all__ = ['get_inventory', 'get_frontend_inventory', 'get_backend_inventory']

@bp.route('/inventory', methods=['GET'])
@csrf.exempt  # 豁免CSRF保护，提高API响应速度
def get_inventory():
    """获取库存列表API - 管理员专用"""
    try:
        from flask_login import current_user
        current_app.logger.info("开始处理库存API请求")

        # 权限检查 - 只有管理员可以访问所有库存
        if not current_user.is_authenticated or not current_user.is_super_admin():
            return jsonify({
                'success': False,
                'message': '权限不足，只有管理员可以访问所有库存'
            }), 403

        # 获取查询参数
        customer_name = request.args.get('customer_name', '')
        identification_code = request.args.get('identification_code', '')
        location = request.args.get('location', '')

        # 构建查询 - 修复：根据用户权限显示库存
        from app.models import Warehouse

        # 获取前端仓库ID列表
        frontend_warehouses = Warehouse.query.filter_by(warehouse_type='frontend').all()
        frontend_warehouse_ids = [w.id for w in frontend_warehouses]

        # 根据用户权限过滤仓库
        # 超级管理员：不分配仓库，可以查看所有前端仓的库存
        # 普通用户：分配到具体仓库，只能查看自己仓库的库存
        if current_user.is_super_admin():
            # 超级管理员可以查看所有前端仓库存
            current_app.logger.info(f"超级管理员 {current_user.username} 可以查看所有前端仓库存")
        elif hasattr(current_user, 'warehouse') and current_user.warehouse:
            if current_user.warehouse.warehouse_type == 'frontend':
                # 前端仓用户只能查看自己仓库的库存
                frontend_warehouse_ids = [current_user.warehouse_id]
                current_app.logger.info(f"前端仓用户 {current_user.username} 只能查看仓库 {current_user.warehouse_id} 的库存")
            else:
                # 后端仓用户也可以查看所有前端仓库存（用于转移等操作）
                current_app.logger.info(f"后端仓用户 {current_user.username} 可以查看所有前端仓库存")
        else:
            # 未分配仓库的普通用户，不应该有权限访问
            current_app.logger.warning(f"用户 {current_user.username} 未分配仓库且非管理员，拒绝访问")
            return jsonify({
                'success': False,
                'message': '您未分配仓库，无法查看库存'
            }), 403

        query = Inventory.query

        # 只查询前端仓库的库存（出库选择应该只能选择前端仓库的库存）
        if frontend_warehouse_ids:
            query = query.filter(Inventory.operated_warehouse_id.in_(frontend_warehouse_ids))

        # 只显示库存不为0的记录
        query = query.filter((Inventory.pallet_count > 0) | (Inventory.package_count > 0))

        # 按客户名称筛选
        if customer_name:
            query = query.filter(Inventory.customer_name.like(f'%{customer_name}%'))
            current_app.logger.info(f"按客户名称筛选: {customer_name}")

        # 按识别编码筛选
        if identification_code:
            query = query.filter(Inventory.identification_code.like(f'%{identification_code}%'))
            current_app.logger.info(f"按识别编码筛选: {identification_code}")

        # 按库位筛选
        if location:
            query = query.filter(Inventory.location == location)
            current_app.logger.info(f"按库位筛选: {location}")

        # 执行查询
        inventory_items = query.all()
        current_app.logger.info(f"查询到 {len(inventory_items)} 条库存记录")
        
        # 检查第一条记录的属性
        if inventory_items:
            first_item = inventory_items[0]
            current_app.logger.info(f"第一条记录ID: {first_item.id}, 客户: {first_item.customer_name}")
            current_app.logger.info(f"第一条记录属性: {dir(first_item)}")
        
        # 转换为字典列表
        items = []
        for item in inventory_items:
            try:
                # 基本字典，包含模型中确定存在的字段
                # 处理识别编码，如果过长则截断
                identification_code = item.identification_code or ''
                if len(identification_code) > 50:
                    identification_code = identification_code[:50] + '...'
                    current_app.logger.warning(f"识别编码过长已截断: {item.identification_code[:20]}...")

                # 获取对应的入库记录以获取单据信息
                document_count = None
                document_no = None
                if item.identification_code:
                    from app.models import InboundRecord
                    inbound_record = InboundRecord.query.filter_by(
                        identification_code=item.identification_code
                    ).first()
                    if inbound_record:
                        document_count = inbound_record.document_count
                        document_no = inbound_record.document_no

                item_dict = {
                    'id': item.id,
                    'customer_name': item.customer_name,
                    'identification_code': identification_code,
                    'inbound_pallet_count': item.inbound_pallet_count,
                    'inbound_package_count': item.inbound_package_count,
                    'pallet_count': item.pallet_count,
                    'package_count': item.package_count,
                    'weight': item.weight,
                    'volume': item.volume,
                    'location': item.location,
                    'documents': item.documents,
                    'document_count': document_count,  # 从入库记录获取单据份数
                    'document_no': document_no,        # 从入库记录获取单据号
                    'export_mode': item.export_mode,
                    'order_type': item.order_type,
                    'customs_broker': item.customs_broker,
                    'plate_number': item.plate_number,
                    'service_staff': item.service_staff,
                    'remark1': '',  # 添加空备注字段
                    'remark2': ''   # 添加空备注字段
                }
                
                # 处理日期时间字段
                if item.inbound_time:
                    item_dict['inbound_time'] = item.inbound_time.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    item_dict['inbound_time'] = ''
                    
                if item.last_updated:
                    item_dict['last_updated'] = item.last_updated.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    item_dict['last_updated'] = ''
                
                items.append(item_dict)
            except Exception as e:
                current_app.logger.error(f"处理库存项 {item.id} 时出错: {str(e)}")
                current_app.logger.error(traceback.format_exc())
                # 继续处理下一项
        
        current_app.logger.info(f"成功处理 {len(items)} 条库存记录")
        
        return jsonify({
            'success': True,
            'inventory': items,
            'items': items  # 兼容前端可能使用的两种字段名
        })
    except Exception as e:
        current_app.logger.error(f"获取库存列表出错: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f"获取库存列表出错: {str(e)}"
        }), 500


@bp.route('/inventory/frontend', methods=['GET'])
@csrf.exempt
def get_frontend_inventory():
    """获取前端仓库存列表API - 支持权限控制"""
    try:
        from flask_login import current_user
        current_app.logger.info("开始处理前端仓库存API请求")

        # 权限检查
        if not current_user.is_authenticated:
            return jsonify({
                'success': False,
                'message': '用户未认证'
            }), 401

        # 根据用户权限确定可访问的仓库
        if current_user.is_super_admin():
            # 管理员可以看到所有前端仓库
            frontend_warehouses = Warehouse.query.filter(
                Warehouse.warehouse_name.in_(['平湖仓', '昆山仓', '成都仓'])
            ).all()
        else:
            # 普通用户只能看到自己所属仓库的库存
            if current_user.warehouse and current_user.warehouse.warehouse_type == 'frontend':
                frontend_warehouses = [current_user.warehouse]
            else:
                current_app.logger.warning(f"用户 {current_user.username} 没有前端仓库权限")
                return jsonify({
                    'success': True,
                    'inventory': [],
                    'message': '您没有权限访问前端仓库存'
                })

        if not frontend_warehouses:
            current_app.logger.warning("未找到前端仓库")
            return jsonify({
                'success': True,
                'inventory': [],
                'message': '未找到前端仓库'
            })

        warehouse_ids = [w.id for w in frontend_warehouses]
        current_app.logger.info(f"前端仓库IDs: {warehouse_ids}")

        # 获取查询参数
        customer_name = request.args.get('customer_name', '')
        identification_code = request.args.get('identification_code', '')
        location = request.args.get('location', '')

        # 构建查询 - 只查询前端仓库的库存
        query = Inventory.query.filter(Inventory.operated_warehouse_id.in_(warehouse_ids))

        # 只显示库存不为0的记录 - 加强过滤条件
        query = query.filter(
            db.and_(
                db.or_(
                    Inventory.pallet_count > 0,
                    Inventory.package_count > 0
                ),
                Inventory.customer_name.isnot(None),
                Inventory.customer_name != '',
                Inventory.identification_code.isnot(None),
                Inventory.identification_code != ''
            )
        )

        # 按客户名称筛选
        if customer_name:
            query = query.filter(Inventory.customer_name.like(f'%{customer_name}%'))

        # 按识别编码筛选
        if identification_code:
            query = query.filter(Inventory.identification_code.like(f'%{identification_code}%'))

        # 按库位筛选
        if location:
            query = query.filter(Inventory.location == location)

        # 执行查询
        inventory_items = query.all()
        current_app.logger.info(f"查询到前端仓 {len(inventory_items)} 条库存记录")

        # 记录详细的查询结果
        for item in inventory_items:
            current_app.logger.info(f"库存记录 {item.id}: 客户={item.customer_name}, 板数={item.pallet_count}, 件数={item.package_count}")

        # 转换为字典列表
        items = []
        for item in inventory_items:
            try:
                # 验证必要字段
                if not item.customer_name or not item.identification_code:
                    current_app.logger.warning(f"跳过无效记录 {item.id}: 缺少客户名称或识别编码")
                    continue

                # 验证库存数量
                pallet_count = item.pallet_count or 0
                package_count = item.package_count or 0
                if pallet_count <= 0 and package_count <= 0:
                    current_app.logger.warning(f"跳过无效记录 {item.id}: 库存数量为0")
                    continue

                identification_code = item.identification_code or ''
                if len(identification_code) > 50:
                    identification_code = identification_code[:50] + '...'

                # 获取对应的入库记录以获取单据信息
                document_count = None
                document_no = None
                if item.identification_code:
                    from app.models import InboundRecord
                    inbound_record = InboundRecord.query.filter_by(
                        identification_code=item.identification_code
                    ).first()
                    if inbound_record:
                        document_count = inbound_record.document_count
                        document_no = inbound_record.document_no

                item_dict = {
                    'id': item.id,
                    'customer_name': item.customer_name or '',
                    'identification_code': identification_code,
                    'inbound_pallet_count': item.inbound_pallet_count or 0,
                    'inbound_package_count': item.inbound_package_count or 0,
                    'pallet_count': item.pallet_count or 0,
                    'package_count': item.package_count or 0,
                    'available_pallets': item.pallet_count or 0,  # 可出库板数等于当前库存板数
                    'available_packages': item.package_count or 0,  # 可出库件数等于当前库存件数
                    'weight': item.weight or 0,
                    'volume': item.volume or 0,
                    'location': item.location or '',
                    'documents': item.documents or '',
                    'document_count': document_count,  # 从入库记录获取单据份数
                    'document_no': document_no,        # 从入库记录获取单据号
                    'export_mode': item.export_mode or '',
                    'order_type': item.order_type or '',
                    'customs_broker': item.customs_broker or '',
                    'plate_number': item.plate_number or '',
                    'service_staff': item.service_staff or '',
                    'remark1': '',
                    'remark2': ''
                }

                # 处理日期时间字段
                if item.inbound_time:
                    item_dict['inbound_time'] = item.inbound_time.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    item_dict['inbound_time'] = ''

                if item.last_updated:
                    item_dict['last_updated'] = item.last_updated.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    item_dict['last_updated'] = ''

                items.append(item_dict)
            except Exception as e:
                current_app.logger.error(f"处理前端仓库存项 {item.id} 时出错: {str(e)}")

        current_app.logger.info(f"成功处理前端仓 {len(items)} 条库存记录")

        return jsonify({
            'success': True,
            'inventory': items
        })
    except Exception as e:
        current_app.logger.error(f"获取前端仓库存列表出错: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f"获取前端仓库存列表出错: {str(e)}"
        }), 500


@bp.route('/inventory/backend', methods=['GET'])
@csrf.exempt
def get_backend_inventory():
    """获取后端仓库存列表API"""
    try:
        current_app.logger.info("开始处理后端仓库存API请求")

        # 查找后端仓库
        backend_warehouse = Warehouse.query.filter_by(warehouse_name='凭祥北投仓').first()

        if not backend_warehouse:
            current_app.logger.warning("未找到后端仓库")
            return jsonify({
                'success': True,
                'inventory': [],
                'message': '未找到后端仓库'
            })

        current_app.logger.info(f"后端仓库ID: {backend_warehouse.id}")

        # 获取查询参数
        customer_name = request.args.get('customer_name', '')
        location = request.args.get('location', '')

        # 构建查询 - 只查询后端仓库的库存
        query = Inventory.query.filter(Inventory.operated_warehouse_id == backend_warehouse.id)

        # 只显示库存不为0的记录
        query = query.filter((Inventory.pallet_count > 0) | (Inventory.package_count > 0))

        # 按客户名称筛选
        if customer_name:
            query = query.filter(Inventory.customer_name.like(f'%{customer_name}%'))

        # 按库位筛选
        if location:
            query = query.filter(Inventory.location == location)

        # 执行查询
        inventory_items = query.all()
        current_app.logger.info(f"查询到后端仓 {len(inventory_items)} 条库存记录")

        # 转换为字典列表
        items = []
        for item in inventory_items:
            try:
                identification_code = item.identification_code or ''
                if len(identification_code) > 50:
                    identification_code = identification_code[:50] + '...'

                item_dict = {
                    'id': item.id,
                    'customer_name': item.customer_name,
                    'identification_code': identification_code,
                    'inbound_pallet_count': item.inbound_pallet_count,
                    'inbound_package_count': item.inbound_package_count,
                    'pallet_count': item.pallet_count,
                    'package_count': item.package_count,
                    'weight': item.weight,
                    'volume': item.volume,
                    'location': item.location,
                    'documents': item.documents,
                    'export_mode': item.export_mode,
                    'order_type': item.order_type,
                    'customs_broker': item.customs_broker,
                    'plate_number': item.plate_number,
                    'service_staff': item.service_staff,
                    'remark1': '',
                    'remark2': ''
                }

                # 处理日期时间字段
                if item.inbound_time:
                    item_dict['inbound_time'] = item.inbound_time.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    item_dict['inbound_time'] = ''

                if item.last_updated:
                    item_dict['last_updated'] = item.last_updated.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    item_dict['last_updated'] = ''

                items.append(item_dict)
            except Exception as e:
                current_app.logger.error(f"处理后端仓库存项 {item.id} 时出错: {str(e)}")

        current_app.logger.info(f"成功处理后端仓 {len(items)} 条库存记录")

        return jsonify({
            'success': True,
            'data': items  # 修复：前端期望的是 'data' 字段
        })
    except Exception as e:
        current_app.logger.error(f"获取后端仓库存列表出错: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f"获取后端仓库存列表出错: {str(e)}"
        }), 500


@bp.route('/receivers', methods=['GET'])
@csrf.exempt
def get_receivers():
    """获取收货人信息列表API"""
    try:
        from flask_login import current_user
        current_app.logger.info("开始处理收货人信息API请求")

        # 权限检查 - 需要登录
        if not current_user.is_authenticated:
            return jsonify({
                'success': False,
                'message': '需要登录才能访问收货人信息'
            }), 401

        # 获取所有收货人信息
        receivers = Receiver.query.all()
        current_app.logger.info(f"查询到 {len(receivers)} 条收货人记录")

        # 转换为数组格式，同时保持字典格式兼容性
        receiver_list = []
        receiver_data = {}
        for receiver in receivers:
            # 数组格式（新格式）
            receiver_list.append({
                'warehouse_name': receiver.warehouse_name,
                'contact': receiver.contact,
                'address': receiver.address
            })
            # 字典格式（兼容旧格式）
            receiver_data[receiver.warehouse_name] = {
                'contact': receiver.contact,
                'address': receiver.address
            }

        current_app.logger.info(f"成功处理收货人信息: {list(receiver_data.keys())}")

        return jsonify({
            'success': True,
            'receivers': receiver_list,  # 新格式
            'data': receiver_data        # 兼容旧格式
        })
    except Exception as e:
        current_app.logger.error(f"获取收货人信息出错: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f"获取收货人信息出错: {str(e)}"
        }), 500