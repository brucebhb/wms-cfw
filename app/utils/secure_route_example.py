#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全路由示例
展示如何在路由中集成所有安全机制
"""

from flask import request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models import InboundRecord, Inventory
from app.utils.exception_handler import handle_exceptions, DataValidator, BusinessValidator
from app.utils.input_validator import FormValidator, InputSanitizer, RequestValidator
from app.utils.concurrency_control import safe_inventory_update, with_inventory_lock
from app.utils.sql_security import SafeQueryBuilder, QueryOptimizer, validate_query_params

# 示例1: 安全的入库记录创建
@login_required
@handle_exceptions(return_json=True, flash_errors=False)
def secure_create_inbound():
    """安全的入库记录创建示例"""
    
    # 1. 验证请求格式
    data = RequestValidator.validate_json_request()
    
    # 2. 输入验证和清理
    inbound_time = FormValidator.validate_datetime(
        data.get('inbound_time'), '入库时间', required=True
    )
    
    plate_number = FormValidator.validate_plate_number(
        data.get('plate_number'), required=True
    )
    
    customer_name = FormValidator.validate_customer_name(
        data.get('customer_name'), required=True
    )
    
    identification_code = FormValidator.validate_identification_code(
        data.get('identification_code'), required=True
    )
    
    # 3. 数值验证
    pallet_count = InputSanitizer.sanitize_integer(
        data.get('pallet_count'), '板数', min_value=0
    )
    
    package_count = InputSanitizer.sanitize_integer(
        data.get('package_count'), '件数', min_value=0
    )
    
    weight = InputSanitizer.sanitize_number(
        data.get('weight'), '重量', min_value=0, decimal_places=2
    )
    
    volume = InputSanitizer.sanitize_number(
        data.get('volume'), '体积', min_value=0, decimal_places=2
    )
    
    # 4. 业务逻辑验证
    BusinessValidator.validate_warehouse_permission(
        current_user, current_user.warehouse_id, 'create_inbound'
    )
    
    # 5. 检查识别编码唯一性
    existing_record = InboundRecord.query.filter_by(
        identification_code=identification_code
    ).first()
    
    if existing_record:
        raise ValidationException(f"识别编码已存在: {identification_code}")
    
    # 6. 创建记录（使用事务）
    try:
        with db.session.begin():
            # 创建入库记录
            inbound_record = InboundRecord(
                inbound_time=inbound_time,
                plate_number=plate_number,
                customer_name=customer_name,
                identification_code=identification_code,
                pallet_count=pallet_count,
                package_count=package_count,
                weight=weight,
                volume=volume,
                warehouse_id=current_user.warehouse_id,
                operated_by_user_id=current_user.id
            )
            
            db.session.add(inbound_record)
            db.session.flush()  # 获取ID
            
            # 创建或更新库存（使用安全的库存更新）
            safe_inventory_update(
                identification_code=identification_code,
                operation_type='add',
                pallet_count=pallet_count,
                package_count=package_count,
                weight=weight,
                volume=volume,
                customer_name=customer_name,
                warehouse_id=current_user.warehouse_id
            )
            
            db.session.commit()
    
    except Exception as e:
        db.session.rollback()
        raise
    
    return jsonify({
        'success': True,
        'message': '入库记录创建成功',
        'data': {
            'id': inbound_record.id,
            'identification_code': identification_code
        }
    })

# 示例2: 安全的库存查询
@login_required
@validate_query_params(['customer_name', 'identification_code', 'warehouse_id', 'page', 'per_page'])
@handle_exceptions(return_json=True)
def secure_inventory_search():
    """安全的库存查询示例"""
    
    # 1. 验证分页参数
    page, per_page = RequestValidator.validate_pagination_params()
    
    # 2. 获取和验证搜索参数
    customer_name = request.args.get('customer_name', '').strip()
    identification_code = request.args.get('identification_code', '').strip()
    warehouse_id = request.args.get('warehouse_id', type=int)
    
    # 3. 权限检查
    if not current_user.is_admin and warehouse_id != current_user.warehouse_id:
        raise PermissionException("无权限查看其他仓库的库存")
    
    # 4. 构建安全查询
    query = db.session.query(Inventory)
    
    # 添加仓库过滤
    if warehouse_id:
        query = query.filter(Inventory.warehouse_id == warehouse_id)
    elif not current_user.is_admin:
        query = query.filter(Inventory.warehouse_id == current_user.warehouse_id)
    
    # 添加搜索条件
    if customer_name:
        condition = SafeQueryBuilder.build_like_condition(
            Inventory.customer_name, customer_name
        )
        if condition is not None:
            query = query.filter(condition)
    
    if identification_code:
        condition = SafeQueryBuilder.build_like_condition(
            Inventory.identification_code, identification_code
        )
        if condition is not None:
            query = query.filter(condition)
    
    # 5. 应用分页
    query = QueryOptimizer.optimize_pagination_query(query, page, per_page)
    
    # 6. 执行查询
    inventories = query.all()
    
    # 7. 格式化响应
    result = []
    for inventory in inventories:
        result.append({
            'id': inventory.id,
            'identification_code': inventory.identification_code,
            'customer_name': inventory.customer_name,
            'pallet_count': inventory.pallet_count,
            'package_count': inventory.package_count,
            'weight': float(inventory.weight),
            'volume': float(inventory.volume)
        })
    
    return jsonify({
        'success': True,
        'data': result,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': len(result)
        }
    })

# 示例3: 安全的批量出库操作
@login_required
@handle_exceptions(return_json=True)
def secure_batch_outbound():
    """安全的批量出库操作示例"""
    
    # 1. 验证请求
    data = RequestValidator.validate_json_request()
    
    # 2. 验证批量数据
    from app.utils.input_validator import BatchValidator
    records = BatchValidator.validate_batch_data(data.get('records', []), max_records=50)
    
    # 3. 验证每条记录
    validated_records = []
    for i, record in enumerate(records):
        try:
            identification_code = FormValidator.validate_identification_code(
                record.get('identification_code'), required=True
            )
            
            outbound_pallet = InputSanitizer.sanitize_integer(
                record.get('pallet_count'), f'第{i+1}条记录的板数', min_value=0
            )
            
            outbound_package = InputSanitizer.sanitize_integer(
                record.get('package_count'), f'第{i+1}条记录的件数', min_value=0
            )
            
            validated_records.append({
                'identification_code': identification_code,
                'pallet_count': outbound_pallet,
                'package_count': outbound_package
            })
            
        except Exception as e:
            raise ValidationException(f"第{i+1}条记录验证失败: {str(e)}")
    
    # 4. 执行批量出库（使用锁机制）
    success_count = 0
    failed_records = []
    
    for record in validated_records:
        try:
            with_inventory_lock_decorator = with_inventory_lock('identification_code')
            
            @with_inventory_lock_decorator
            def process_single_outbound(identification_code, pallet_count, package_count):
                # 检查库存
                inventory = Inventory.query.filter_by(
                    identification_code=identification_code
                ).first()
                
                if not inventory:
                    raise ValidationException(f"库存记录不存在: {identification_code}")
                
                # 权限检查
                BusinessValidator.validate_warehouse_permission(
                    current_user, inventory.warehouse_id, 'outbound'
                )
                
                # 库存充足性检查
                BusinessValidator.validate_inventory_sufficient(
                    inventory, pallet_count, package_count
                )
                
                # 执行出库
                safe_inventory_update(
                    identification_code=identification_code,
                    operation_type='subtract',
                    pallet_count=pallet_count,
                    package_count=package_count
                )
                
                return True
            
            # 执行单条出库
            process_single_outbound(
                record['identification_code'],
                record['pallet_count'],
                record['package_count']
            )
            
            success_count += 1
            
        except Exception as e:
            failed_records.append({
                'identification_code': record['identification_code'],
                'error': str(e)
            })
    
    return jsonify({
        'success': True,
        'message': f'批量出库完成，成功{success_count}条，失败{len(failed_records)}条',
        'data': {
            'success_count': success_count,
            'failed_count': len(failed_records),
            'failed_records': failed_records
        }
    })

# 示例4: 安全的数据导出
@login_required
@handle_exceptions(return_json=True)
def secure_export_data():
    """安全的数据导出示例"""
    
    # 1. 权限检查
    if not current_user.is_admin:
        # 非管理员只能导出自己仓库的数据
        warehouse_filter = current_user.warehouse_id
    else:
        warehouse_filter = request.args.get('warehouse_id', type=int)
    
    # 2. 验证导出参数
    export_type = request.args.get('export_type', 'inventory')
    if export_type not in ['inventory', 'inbound', 'outbound']:
        raise ValidationException("无效的导出类型")
    
    # 3. 日期范围验证
    start_date = FormValidator.validate_datetime(
        request.args.get('start_date'), '开始日期', required=False
    )
    end_date = FormValidator.validate_datetime(
        request.args.get('end_date'), '结束日期', required=False
    )
    
    # 4. 构建安全查询
    if export_type == 'inventory':
        query = db.session.query(Inventory)
        if warehouse_filter:
            query = query.filter(Inventory.warehouse_id == warehouse_filter)
    
    # 5. 限制导出数量
    total_count = query.count()
    if total_count > 10000:
        raise ValidationException("导出数据量过大，请缩小查询范围")
    
    # 6. 执行查询并返回
    data = query.limit(10000).all()
    
    return jsonify({
        'success': True,
        'message': f'数据导出成功，共{len(data)}条记录',
        'data': [item.to_dict() for item in data]  # 假设模型有to_dict方法
    })
