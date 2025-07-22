#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据验证模块 - 防止数据逻辑错误
"""

from app.models import Warehouse
from app.utils.identification_generator import IdentificationCodeGenerator

class DataValidator:
    """数据验证器"""
    
    @staticmethod
    def validate_receive_record_logic(identification_code: str, operated_warehouse_id: int, 
                                    record_type: str = 'receive') -> dict:
        """
        验证接收记录的业务逻辑
        
        Args:
            identification_code: 识别编码
            operated_warehouse_id: 操作仓库ID
            record_type: 记录类型 ('receive' 或 'inbound')
            
        Returns:
            dict: 验证结果 {'valid': bool, 'error': str, 'warnings': list}
        """
        result = {
            'valid': True,
            'error': '',
            'warnings': []
        }
        
        if not identification_code or not operated_warehouse_id:
            result['valid'] = False
            result['error'] = '识别编码和操作仓库ID不能为空'
            return result
        
        # 解析识别编码
        code_info = IdentificationCodeGenerator.parse_identification_code(identification_code)
        if not code_info['valid']:
            result['valid'] = False
            result['error'] = f'识别编码格式错误: {code_info["error"]}'
            return result
        
        # 获取操作仓库信息
        warehouse = Warehouse.query.get(operated_warehouse_id)
        if not warehouse:
            result['valid'] = False
            result['error'] = f'找不到仓库ID: {operated_warehouse_id}'
            return result
        
        # 获取仓库前缀
        warehouse_prefix = IdentificationCodeGenerator.WAREHOUSE_PREFIXES.get(warehouse.id, 'UK')
        code_prefix = code_info['warehouse_prefix']
        
        # 验证业务逻辑
        if record_type == 'receive':
            # 接收记录验证
            
            # 1. 仓库不应该接收自己发出的货物
            if code_prefix == warehouse_prefix:
                result['valid'] = False
                result['error'] = f'仓库不能接收自己发出的货物 (识别编码前缀: {code_prefix}, 仓库前缀: {warehouse_prefix})'
                return result
            
            # 2. 前端仓应该使用InboundRecord表，后端仓使用ReceiveRecord表
            if warehouse.warehouse_type == 'frontend':
                result['warnings'].append('前端仓接收记录应该使用InboundRecord表，而不是ReceiveRecord表')
            elif warehouse.warehouse_type == 'backend':
                result['warnings'].append('后端仓接收记录应该使用ReceiveRecord表，而不是InboundRecord表')
        
        elif record_type == 'inbound':
            # 入库记录验证
            
            # 1. 正常入库记录的识别编码前缀应该与仓库匹配
            if code_prefix != warehouse_prefix:
                result['warnings'].append(f'入库记录的识别编码前缀({code_prefix})与仓库前缀({warehouse_prefix})不匹配，请确认这是接收记录')
        
        return result
    
    @staticmethod
    def validate_outbound_record_logic(identification_code: str, operated_warehouse_id: int,
                                     destination_warehouse_id: int = None) -> dict:
        """
        验证出库记录的业务逻辑
        
        Args:
            identification_code: 识别编码
            operated_warehouse_id: 操作仓库ID
            destination_warehouse_id: 目标仓库ID
            
        Returns:
            dict: 验证结果
        """
        result = {
            'valid': True,
            'error': '',
            'warnings': []
        }
        
        if not identification_code or not operated_warehouse_id:
            result['valid'] = False
            result['error'] = '识别编码和操作仓库ID不能为空'
            return result
        
        # 解析识别编码
        code_info = IdentificationCodeGenerator.parse_identification_code(identification_code)
        if not code_info['valid']:
            result['valid'] = False
            result['error'] = f'识别编码格式错误: {code_info["error"]}'
            return result
        
        # 获取操作仓库信息
        warehouse = Warehouse.query.get(operated_warehouse_id)
        if not warehouse:
            result['valid'] = False
            result['error'] = f'找不到仓库ID: {operated_warehouse_id}'
            return result
        
        # 获取仓库前缀
        warehouse_prefix = IdentificationCodeGenerator.WAREHOUSE_PREFIXES.get(warehouse.id, 'UK')
        code_prefix = code_info['warehouse_prefix']
        
        # 验证识别编码前缀与操作仓库匹配
        if code_prefix != warehouse_prefix:
            result['valid'] = False
            result['error'] = f'识别编码前缀({code_prefix})与操作仓库前缀({warehouse_prefix})不匹配'
            return result
        
        # 验证目标仓库
        if destination_warehouse_id:
            dest_warehouse = Warehouse.query.get(destination_warehouse_id)
            if not dest_warehouse:
                result['warnings'].append(f'找不到目标仓库ID: {destination_warehouse_id}')
            elif dest_warehouse.id == warehouse.id:
                result['valid'] = False
                result['error'] = '不能向自己仓库发货'
                return result
        
        return result
    
    @staticmethod
    def validate_test_data_cleanup(record_data: dict) -> bool:
        """
        检查是否为测试数据，便于清理
        
        Args:
            record_data: 记录数据字典
            
        Returns:
            bool: 是否为测试数据
        """
        test_indicators = [
            'TEST', 'test', '测试', 'demo', 'DEMO',
            '测试客户', '测试公司', 'Test', 'Demo'
        ]
        
        # 检查各个字段
        fields_to_check = [
            'customer_name', 'batch_no', 'identification_code',
            'remark1', 'remark2', 'service_staff'
        ]
        
        for field in fields_to_check:
            value = record_data.get(field, '')
            if value and isinstance(value, str):
                for indicator in test_indicators:
                    if indicator in value:
                        return True
        
        return False
    
    @staticmethod
    def get_validation_summary() -> dict:
        """
        获取数据验证规则摘要
        
        Returns:
            dict: 验证规则摘要
        """
        return {
            'receive_record_rules': [
                '仓库不能接收自己发出的货物（识别编码前缀不能与操作仓库前缀相同）',
                '前端仓接收记录应使用InboundRecord表',
                '后端仓接收记录应使用ReceiveRecord表',
                '识别编码格式必须正确：仓库前缀/客户名称/车牌/日期/序号'
            ],
            'outbound_record_rules': [
                '识别编码前缀必须与操作仓库前缀匹配',
                '不能向自己仓库发货',
                '目标仓库必须存在',
                '识别编码格式必须正确'
            ],
            'test_data_rules': [
                '测试数据应包含明确标识（TEST、测试等）',
                '测试数据应定期清理',
                '生产环境不应包含测试数据'
            ]
        }

# 装饰器：自动验证接收记录
def validate_receive_record(func):
    """装饰器：自动验证接收记录逻辑"""
    def wrapper(*args, **kwargs):
        # 从参数中提取验证所需信息
        identification_code = kwargs.get('identification_code')
        operated_warehouse_id = kwargs.get('operated_warehouse_id')
        record_type = kwargs.get('record_type', 'receive')
        
        if identification_code and operated_warehouse_id:
            validation_result = DataValidator.validate_receive_record_logic(
                identification_code, operated_warehouse_id, record_type
            )
            
            if not validation_result['valid']:
                raise ValueError(f"数据验证失败: {validation_result['error']}")
            
            # 记录警告
            for warning in validation_result['warnings']:
                print(f"警告: {warning}")
        
        return func(*args, **kwargs)
    
    return wrapper

# 装饰器：自动验证出库记录
def validate_outbound_record(func):
    """装饰器：自动验证出库记录逻辑"""
    def wrapper(*args, **kwargs):
        # 从参数中提取验证所需信息
        identification_code = kwargs.get('identification_code')
        operated_warehouse_id = kwargs.get('operated_warehouse_id')
        destination_warehouse_id = kwargs.get('destination_warehouse_id')
        
        if identification_code and operated_warehouse_id:
            validation_result = DataValidator.validate_outbound_record_logic(
                identification_code, operated_warehouse_id, destination_warehouse_id
            )
            
            if not validation_result['valid']:
                raise ValueError(f"数据验证失败: {validation_result['error']}")
            
            # 记录警告
            for warning in validation_result['warnings']:
                print(f"警告: {warning}")
        
        return func(*args, **kwargs)
    
    return wrapper


def validate_identification_code_consistency(identification_code: str, operated_warehouse_id: int) -> dict:
    """
    验证识别编码前缀与操作仓库的一致性

    Args:
        identification_code: 识别编码
        operated_warehouse_id: 操作仓库ID

    Returns:
        dict: 验证结果 {'valid': bool, 'error': str, 'expected_warehouse_id': int}
    """
    result = {
        'valid': True,
        'error': '',
        'expected_warehouse_id': None
    }

    if not identification_code or not operated_warehouse_id:
        result['valid'] = False
        result['error'] = '识别编码和操作仓库ID不能为空'
        return result

    # 解析识别编码前缀
    parts = identification_code.split('/')
    if len(parts) < 1:
        result['valid'] = False
        result['error'] = '识别编码格式错误'
        return result

    code_prefix = parts[0]

    # 获取仓库前缀映射
    warehouse_prefixes = IdentificationCodeGenerator.WAREHOUSE_PREFIXES
    prefix_to_warehouse = {v: k for k, v in warehouse_prefixes.items()}
    expected_warehouse_id = prefix_to_warehouse.get(code_prefix)

    if not expected_warehouse_id:
        result['valid'] = False
        result['error'] = f'未知的识别编码前缀: {code_prefix}'
        return result

    result['expected_warehouse_id'] = expected_warehouse_id

    if expected_warehouse_id != operated_warehouse_id:
        # 获取仓库名称
        expected_warehouse = Warehouse.query.get(expected_warehouse_id)
        actual_warehouse = Warehouse.query.get(operated_warehouse_id)

        expected_name = expected_warehouse.warehouse_name if expected_warehouse else '未知'
        actual_name = actual_warehouse.warehouse_name if actual_warehouse else '未知'

        result['valid'] = False
        result['error'] = (
            f"识别编码前缀 '{code_prefix}' 与操作仓库不匹配！\n"
            f"识别编码: {identification_code}\n"
            f"期望仓库: {expected_name} (ID: {expected_warehouse_id})\n"
            f"实际仓库: {actual_name} (ID: {operated_warehouse_id})"
        )

    return result
