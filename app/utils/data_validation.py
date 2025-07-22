#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据验证和一致性检查工具
用于预防数据不一致问题
"""

import re
from flask import current_app
from app import db
from app.models import InboundRecord, Inventory, OutboundRecord, TransitCargo

class DataValidator:
    """数据验证器"""
    
    @staticmethod
    def validate_identification_code(identification_code):
        """
        验证识别编码格式：仓库前缀/客户名称/车牌/日期/序号
        """
        if not identification_code:
            return False, "识别编码不能为空"
        
        parts = identification_code.split('/')
        if len(parts) != 5:
            return False, "识别编码格式错误，应为：仓库前缀/客户名称/车牌/日期/序号"
        
        warehouse_prefix, customer_name, plate_number, date_str, sequence = parts
        
        # 验证仓库前缀
        valid_prefixes = ['PH', 'KS', 'CD', 'PX']
        if warehouse_prefix not in valid_prefixes:
            return False, f"仓库前缀错误，应为：{', '.join(valid_prefixes)}"
        
        # 验证客户名称
        if not customer_name or len(customer_name) < 1:
            return False, "客户名称不能为空"
        
        # 验证车牌号格式
        plate_pattern = r'^[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼使领A-Z]{1}[A-Z]{1}[A-Z0-9]{4}[A-Z0-9挂学警港澳]{1}$'
        if not re.match(plate_pattern, plate_number):
            return False, f"车牌号格式错误：{plate_number}"
        
        # 验证日期格式
        if not re.match(r'^\d{8}$', date_str):
            return False, f"日期格式错误，应为YYYYMMDD：{date_str}"
        
        # 验证序号
        if not re.match(r'^\d{3}$', sequence):
            return False, f"序号格式错误，应为3位数字：{sequence}"
        
        return True, "验证通过"
    
    @staticmethod
    def extract_info_from_identification_code(identification_code):
        """
        从识别编码中提取信息
        """
        is_valid, message = DataValidator.validate_identification_code(identification_code)
        if not is_valid:
            return None, message
        
        parts = identification_code.split('/')
        return {
            'warehouse_prefix': parts[0],
            'customer_name': parts[1],
            'plate_number': parts[2],
            'date': parts[3],
            'sequence': parts[4]
        }, "提取成功"
    
    @staticmethod
    def validate_data_consistency(identification_code, customer_name, plate_number):
        """
        验证数据一致性：确保客户名称和车牌号与识别编码一致
        """
        info, message = DataValidator.extract_info_from_identification_code(identification_code)
        if not info:
            return False, message
        
        if info['customer_name'] != customer_name:
            return False, f"客户名称不一致：识别编码中为'{info['customer_name']}'，但传入为'{customer_name}'"
        
        if info['plate_number'] != plate_number:
            return False, f"车牌号不一致：识别编码中为'{info['plate_number']}'，但传入为'{plate_number}'"
        
        return True, "数据一致性验证通过"

class DataIntegrityChecker:
    """数据完整性检查器"""
    
    @staticmethod
    def check_inventory_consistency():
        """
        检查库存数据一致性
        """
        issues = []
        
        # 检查同一识别编码是否有不同的客户名称
        inconsistent_records = db.session.query(
            Inventory.identification_code,
            db.func.count(db.func.distinct(Inventory.customer_name)).label('customer_count'),
            db.func.group_concat(db.func.distinct(Inventory.customer_name)).label('customer_names')
        ).group_by(
            Inventory.identification_code
        ).having(
            db.func.count(db.func.distinct(Inventory.customer_name)) > 1
        ).all()
        
        for record in inconsistent_records:
            issues.append({
                'type': 'customer_name_inconsistency',
                'identification_code': record.identification_code,
                'customer_names': record.customer_names,
                'description': f'识别编码 {record.identification_code} 有多个不同的客户名称: {record.customer_names}'
            })
        
        # 检查客户名称与识别编码是否匹配
        all_inventory = Inventory.query.all()
        for inv in all_inventory:
            info, _ = DataValidator.extract_info_from_identification_code(inv.identification_code)
            if info and info['customer_name'] != inv.customer_name:
                issues.append({
                    'type': 'customer_name_mismatch',
                    'identification_code': inv.identification_code,
                    'expected_customer': info['customer_name'],
                    'actual_customer': inv.customer_name,
                    'description': f'识别编码 {inv.identification_code} 中的客户名称应为 {info["customer_name"]}，但实际为 {inv.customer_name}'
                })
        
        return issues
    
    @staticmethod
    def fix_customer_name_inconsistency(identification_code):
        """
        修复客户名称不一致问题
        """
        try:
            # 从识别编码中提取正确的客户名称
            info, message = DataValidator.extract_info_from_identification_code(identification_code)
            if not info:
                return False, message
            
            correct_customer_name = info['customer_name']
            correct_plate_number = info['plate_number']
            
            # 更新库存记录
            inventory_records = Inventory.query.filter_by(identification_code=identification_code).all()
            for inv in inventory_records:
                inv.customer_name = correct_customer_name
                inv.plate_number = correct_plate_number
            
            # 更新出库记录
            outbound_records = OutboundRecord.query.filter_by(identification_code=identification_code).all()
            for out in outbound_records:
                out.customer_name = correct_customer_name
                out.plate_number = correct_plate_number
            
            # 更新在途记录
            transit_records = TransitCargo.query.filter_by(identification_code=identification_code).all()
            for transit in transit_records:
                transit.customer_name = correct_customer_name
                transit.plate_number = correct_plate_number
            
            db.session.commit()
            return True, f"已修复识别编码 {identification_code} 的客户名称不一致问题"
            
        except Exception as e:
            db.session.rollback()
            return False, f"修复失败: {str(e)}"

class BusinessFieldValidator:
    """业务字段验证器"""
    
    @staticmethod
    def ensure_business_fields_consistency(identification_code):
        """
        确保业务字段的一致性
        优先级：入库记录 -> 最新出库记录 -> 库存记录
        """
        try:
            # 获取入库记录（最权威的数据源）
            inbound_record = InboundRecord.query.filter_by(identification_code=identification_code).first()
            if not inbound_record:
                return False, f"未找到识别编码 {identification_code} 的入库记录"
            
            # 获取业务字段
            business_fields = {
                'export_mode': inbound_record.export_mode,
                'customs_broker': inbound_record.customs_broker,
                'service_staff': inbound_record.service_staff,
                'order_type': inbound_record.order_type,
                'documents': inbound_record.documents,
                'weight': inbound_record.weight,
                'volume': inbound_record.volume
            }
            
            # 更新所有相关记录
            inventory_records = Inventory.query.filter_by(identification_code=identification_code).all()
            for inv in inventory_records:
                for field, value in business_fields.items():
                    if hasattr(inv, field) and value:
                        setattr(inv, field, value)
            
            outbound_records = OutboundRecord.query.filter_by(identification_code=identification_code).all()
            for out in outbound_records:
                for field, value in business_fields.items():
                    if hasattr(out, field) and value and field not in ['weight', 'volume']:  # 出库记录的重量体积可能不同
                        setattr(out, field, value)
            
            transit_records = TransitCargo.query.filter_by(identification_code=identification_code).all()
            for transit in transit_records:
                for field, value in business_fields.items():
                    if hasattr(transit, field) and value and field not in ['weight', 'volume']:  # 在途记录的重量体积可能不同
                        setattr(transit, field, value)
            
            db.session.commit()
            return True, f"已同步识别编码 {identification_code} 的业务字段"
            
        except Exception as e:
            db.session.rollback()
            return False, f"同步失败: {str(e)}"

def validate_before_save(model_instance):
    """
    保存前验证数据
    """
    if hasattr(model_instance, 'identification_code') and model_instance.identification_code:
        # 验证识别编码格式
        is_valid, message = DataValidator.validate_identification_code(model_instance.identification_code)
        if not is_valid:
            raise ValueError(f"识别编码验证失败: {message}")
        
        # 验证数据一致性
        if hasattr(model_instance, 'customer_name') and hasattr(model_instance, 'plate_number'):
            is_consistent, message = DataValidator.validate_data_consistency(
                model_instance.identification_code,
                model_instance.customer_name,
                model_instance.plate_number
            )
            if not is_consistent:
                # 自动修正数据
                info, _ = DataValidator.extract_info_from_identification_code(model_instance.identification_code)
                if info:
                    model_instance.customer_name = info['customer_name']
                    model_instance.plate_number = info['plate_number']
                    current_app.logger.warning(f"自动修正数据不一致: {message}")
                else:
                    raise ValueError(f"数据一致性验证失败: {message}")
