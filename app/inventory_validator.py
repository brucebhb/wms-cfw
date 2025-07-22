#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
库存数据一致性验证器
在关键业务节点自动验证数据一致性
"""

import logging
from datetime import datetime
from functools import wraps
from flask import current_app, g
from sqlalchemy import event
from app.models import InboundRecord, OutboundRecord, Inventory, ReceiveRecord, TransitCargo, db

class InventoryValidator:
    """库存数据一致性验证器"""
    
    @staticmethod
    def validate_identification_code(identification_code):
        """验证特定识别码的库存一致性"""
        try:
            # 计算理论库存
            inbound_records = InboundRecord.query.filter_by(identification_code=identification_code).all()
            outbound_records = OutboundRecord.query.filter_by(identification_code=identification_code).all()
            receive_records = ReceiveRecord.query.filter_by(identification_code=identification_code).all()
            inventory_records = Inventory.query.filter_by(identification_code=identification_code).all()
            
            # 按仓库分组计算理论库存
            warehouse_balance = {}
            
            # 入库增加库存
            for record in inbound_records:
                wh_id = record.operated_warehouse_id
                if wh_id not in warehouse_balance:
                    warehouse_balance[wh_id] = {'pallets': 0, 'packages': 0}
                warehouse_balance[wh_id]['pallets'] += record.pallet_count or 0
                warehouse_balance[wh_id]['packages'] += record.package_count or 0
            
            # 接收增加库存
            for record in receive_records:
                wh_id = record.operated_warehouse_id
                if wh_id not in warehouse_balance:
                    warehouse_balance[wh_id] = {'pallets': 0, 'packages': 0}
                warehouse_balance[wh_id]['pallets'] += record.pallet_count or 0
                warehouse_balance[wh_id]['packages'] += record.package_count or 0
            
            # 出库减少库存
            for record in outbound_records:
                wh_id = record.operated_warehouse_id
                if wh_id in warehouse_balance:
                    warehouse_balance[wh_id]['pallets'] -= record.pallet_count or 0
                    warehouse_balance[wh_id]['packages'] -= record.package_count or 0
            
            # 计算实际库存
            actual_inventory = {}
            for record in inventory_records:
                wh_id = record.operated_warehouse_id
                if wh_id not in actual_inventory:
                    actual_inventory[wh_id] = {'pallets': 0, 'packages': 0}
                actual_inventory[wh_id]['pallets'] += record.pallet_count or 0
                actual_inventory[wh_id]['packages'] += record.package_count or 0
            
            # 检查一致性
            inconsistencies = []
            all_warehouses = set(warehouse_balance.keys()) | set(actual_inventory.keys())
            
            for wh_id in all_warehouses:
                theoretical = warehouse_balance.get(wh_id, {'pallets': 0, 'packages': 0})
                actual = actual_inventory.get(wh_id, {'pallets': 0, 'packages': 0})
                
                if theoretical['pallets'] != actual['pallets'] or theoretical['packages'] != actual['packages']:
                    inconsistencies.append({
                        'warehouse_id': wh_id,
                        'theoretical_pallets': theoretical['pallets'],
                        'actual_pallets': actual['pallets'],
                        'theoretical_packages': theoretical['packages'],
                        'actual_packages': actual['packages'],
                        'pallet_diff': actual['pallets'] - theoretical['pallets'],
                        'package_diff': actual['packages'] - theoretical['packages']
                    })
            
            return len(inconsistencies) == 0, inconsistencies
            
        except Exception as e:
            current_app.logger.error(f"库存一致性验证失败 {identification_code}: {e}")
            return False, [{'error': str(e)}]
    
    @staticmethod
    def log_inconsistency(identification_code, inconsistencies, operation_type="unknown"):
        """记录库存不一致问题"""
        try:
            log_message = f"库存不一致检测 - 操作类型: {operation_type}, 识别码: {identification_code}"
            for item in inconsistencies:
                if 'error' in item:
                    log_message += f"\n  错误: {item['error']}"
                else:
                    log_message += f"\n  仓库ID {item['warehouse_id']}: 理论{item['theoretical_pallets']}板 vs 实际{item['actual_pallets']}板 (差异{item['pallet_diff']}板)"
            
            current_app.logger.warning(log_message)
            
            # 可以在这里添加更多的通知机制，比如发送邮件、钉钉通知等
            
        except Exception as e:
            current_app.logger.error(f"记录库存不一致日志失败: {e}")

def validate_after_operation(operation_type):
    """装饰器：在操作后验证库存一致性"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 执行原始操作
            result = func(*args, **kwargs)
            
            try:
                # 尝试从请求或参数中获取识别码
                identification_code = None
                
                # 从Flask请求中获取
                from flask import request
                if request and request.form:
                    identification_code = request.form.get('identification_code')
                elif request and request.json:
                    identification_code = request.json.get('identification_code')
                
                # 从函数参数中获取
                if not identification_code and args:
                    for arg in args:
                        if hasattr(arg, 'identification_code'):
                            identification_code = arg.identification_code
                            break
                
                # 从kwargs中获取
                if not identification_code:
                    identification_code = kwargs.get('identification_code')
                
                if identification_code:
                    # 验证库存一致性
                    is_consistent, inconsistencies = InventoryValidator.validate_identification_code(identification_code)
                    
                    if not is_consistent:
                        InventoryValidator.log_inconsistency(identification_code, inconsistencies, operation_type)
                        current_app.logger.warning(f"操作后检测到库存不一致: {operation_type} - {identification_code}")
                    else:
                        current_app.logger.info(f"操作后库存一致性验证通过: {operation_type} - {identification_code}")
                
            except Exception as e:
                current_app.logger.error(f"操作后库存验证失败: {e}")
            
            return result
        return wrapper
    return decorator

# 数据库事件监听器
@event.listens_for(ReceiveRecord, 'after_delete')
def after_receive_record_delete(mapper, connection, target):
    """接收记录删除后验证库存一致性"""
    try:
        # 延迟验证，确保事务完成
        def delayed_validation():
            try:
                is_consistent, inconsistencies = InventoryValidator.validate_identification_code(target.identification_code)
                if not is_consistent:
                    InventoryValidator.log_inconsistency(target.identification_code, inconsistencies, "接收记录删除")
            except Exception as e:
                current_app.logger.error(f"接收记录删除后验证失败: {e}")
        
        # 在请求结束后执行验证
        if hasattr(g, 'delayed_validations'):
            g.delayed_validations.append(delayed_validation)
        else:
            g.delayed_validations = [delayed_validation]
            
    except Exception as e:
        current_app.logger.error(f"设置接收记录删除后验证失败: {e}")

@event.listens_for(OutboundRecord, 'after_insert')
def after_outbound_record_insert(mapper, connection, target):
    """出库记录创建后验证库存一致性"""
    try:
        def delayed_validation():
            try:
                is_consistent, inconsistencies = InventoryValidator.validate_identification_code(target.identification_code)
                if not is_consistent:
                    InventoryValidator.log_inconsistency(target.identification_code, inconsistencies, "出库记录创建")
            except Exception as e:
                current_app.logger.error(f"出库记录创建后验证失败: {e}")
        
        if hasattr(g, 'delayed_validations'):
            g.delayed_validations.append(delayed_validation)
        else:
            g.delayed_validations = [delayed_validation]
            
    except Exception as e:
        current_app.logger.error(f"设置出库记录创建后验证失败: {e}")

@event.listens_for(Inventory, 'after_update')
def after_inventory_update(mapper, connection, target):
    """库存记录更新后验证一致性"""
    try:
        def delayed_validation():
            try:
                is_consistent, inconsistencies = InventoryValidator.validate_identification_code(target.identification_code)
                if not is_consistent:
                    InventoryValidator.log_inconsistency(target.identification_code, inconsistencies, "库存记录更新")
            except Exception as e:
                current_app.logger.error(f"库存记录更新后验证失败: {e}")
        
        if hasattr(g, 'delayed_validations'):
            g.delayed_validations.append(delayed_validation)
        else:
            g.delayed_validations = [delayed_validation]
            
    except Exception as e:
        current_app.logger.error(f"设置库存记录更新后验证失败: {e}")

def execute_delayed_validations():
    """执行延迟的验证任务"""
    try:
        if hasattr(g, 'delayed_validations'):
            for validation in g.delayed_validations:
                validation()
            g.delayed_validations = []
    except Exception as e:
        current_app.logger.error(f"执行延迟验证失败: {e}")

def batch_validate_all_inventory():
    """批量验证所有库存的一致性"""
    try:
        current_app.logger.info("开始批量库存一致性验证...")
        
        # 获取所有有库存的识别码
        inventory_codes = db.session.query(Inventory.identification_code).distinct().all()
        inventory_codes = [code[0] for code in inventory_codes if code[0]]
        
        inconsistent_count = 0
        total_count = len(inventory_codes)
        
        for code in inventory_codes:
            is_consistent, inconsistencies = InventoryValidator.validate_identification_code(code)
            if not is_consistent:
                inconsistent_count += 1
                InventoryValidator.log_inconsistency(code, inconsistencies, "批量验证")
        
        current_app.logger.info(f"批量库存验证完成: 总计{total_count}个识别码，发现{inconsistent_count}个不一致")
        
        return total_count, inconsistent_count
        
    except Exception as e:
        current_app.logger.error(f"批量库存验证失败: {e}")
        return 0, 0

def setup_inventory_validation():
    """设置库存验证系统"""
    try:
        current_app.logger.info("库存数据一致性验证系统已启动")
        
        # 注册请求结束后的验证执行
        @current_app.after_request
        def after_request(response):
            execute_delayed_validations()
            return response
        
        return True
    except Exception as e:
        current_app.logger.error(f"设置库存验证系统失败: {e}")
        return False
