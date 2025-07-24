#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
异常处理工具类
统一的异常处理和错误响应机制
"""

import traceback
import logging
from functools import wraps
from flask import jsonify, flash, request, current_app
from sqlalchemy.exc import IntegrityError, OperationalError, DataError
from werkzeug.exceptions import BadRequest, Unauthorized, Forbidden, NotFound

# 自定义异常类
class BusinessException(Exception):
    """业务逻辑异常"""
    def __init__(self, message, code=400, details=None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)

class ValidationException(BusinessException):
    """数据验证异常"""
    def __init__(self, message, field=None, value=None):
        details = {}
        if field:
            details['field'] = field
        if value:
            details['value'] = value
        super().__init__(message, code=400, details=details)

class InventoryException(BusinessException):
    """库存相关异常"""
    def __init__(self, message, identification_code=None, current_stock=None):
        details = {}
        if identification_code:
            details['identification_code'] = identification_code
        if current_stock:
            details['current_stock'] = current_stock
        super().__init__(message, code=409, details=details)

class PermissionException(BusinessException):
    """权限异常"""
    def __init__(self, message, required_permission=None):
        details = {}
        if required_permission:
            details['required_permission'] = required_permission
        super().__init__(message, code=403, details=details)

# 异常处理装饰器
def handle_exceptions(return_json=False, flash_errors=True):
    """
    统一异常处理装饰器
    
    Args:
        return_json: 是否返回JSON响应
        flash_errors: 是否显示flash消息
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ValidationException as e:
                current_app.logger.warning(f"验证异常: {e.message}, 详情: {e.details}")
                if return_json:
                    return jsonify({
                        'success': False,
                        'error': e.message,
                        'error_type': 'validation',
                        'details': e.details
                    }), e.code
                else:
                    if flash_errors:
                        flash(f'输入验证错误: {e.message}', 'error')
                    return None
            
            except InventoryException as e:
                current_app.logger.warning(f"库存异常: {e.message}, 详情: {e.details}")
                if return_json:
                    return jsonify({
                        'success': False,
                        'error': e.message,
                        'error_type': 'inventory',
                        'details': e.details
                    }), e.code
                else:
                    if flash_errors:
                        flash(f'库存操作错误: {e.message}', 'error')
                    return None
            
            except PermissionException as e:
                current_app.logger.warning(f"权限异常: {e.message}, 用户: {request.remote_addr}")
                if return_json:
                    return jsonify({
                        'success': False,
                        'error': '权限不足',
                        'error_type': 'permission'
                    }), e.code
                else:
                    if flash_errors:
                        flash('权限不足，无法执行此操作', 'error')
                    return None
            
            except IntegrityError as e:
                current_app.logger.error(f"数据完整性错误: {str(e)}")
                error_msg = "数据完整性错误，可能存在重复或关联约束问题"
                if "Duplicate entry" in str(e):
                    error_msg = "数据重复，请检查输入"
                elif "foreign key constraint" in str(e).lower():
                    error_msg = "数据关联错误，请检查相关记录"
                
                if return_json:
                    return jsonify({
                        'success': False,
                        'error': error_msg,
                        'error_type': 'integrity'
                    }), 400
                else:
                    if flash_errors:
                        flash(error_msg, 'error')
                    return None
            
            except OperationalError as e:
                current_app.logger.error(f"数据库操作错误: {str(e)}")
                error_msg = "数据库操作失败"
                if "Deadlock" in str(e):
                    error_msg = "系统繁忙，请稍后重试"
                elif "Lock wait timeout" in str(e):
                    error_msg = "操作超时，请稍后重试"
                
                if return_json:
                    return jsonify({
                        'success': False,
                        'error': error_msg,
                        'error_type': 'database'
                    }), 500
                else:
                    if flash_errors:
                        flash(error_msg, 'error')
                    return None
            
            except BusinessException as e:
                current_app.logger.warning(f"业务异常: {e.message}")
                if return_json:
                    return jsonify({
                        'success': False,
                        'error': e.message,
                        'error_type': 'business',
                        'details': e.details
                    }), e.code
                else:
                    if flash_errors:
                        flash(e.message, 'error')
                    return None
            
            except Exception as e:
                current_app.logger.error(f"未处理异常: {str(e)}\n{traceback.format_exc()}")
                if return_json:
                    return jsonify({
                        'success': False,
                        'error': '系统内部错误，请联系管理员',
                        'error_type': 'system'
                    }), 500
                else:
                    if flash_errors:
                        flash('系统内部错误，请联系管理员', 'error')
                    return None
        
        return wrapper
    return decorator

# 数据验证工具
class DataValidator:
    """数据验证工具类"""
    
    @staticmethod
    def validate_required(value, field_name):
        """验证必填字段"""
        if not value or (isinstance(value, str) and not value.strip()):
            raise ValidationException(f"{field_name}不能为空", field=field_name)
    
    @staticmethod
    def validate_positive_number(value, field_name):
        """验证正数"""
        try:
            num_value = float(value) if value else 0
            if num_value < 0:
                raise ValidationException(f"{field_name}不能为负数", field=field_name, value=value)
            return num_value
        except (ValueError, TypeError):
            raise ValidationException(f"{field_name}必须是有效数字", field=field_name, value=value)
    
    @staticmethod
    def validate_integer(value, field_name, min_value=0):
        """验证整数"""
        try:
            int_value = int(value) if value else 0
            if int_value < min_value:
                raise ValidationException(f"{field_name}不能小于{min_value}", field=field_name, value=value)
            return int_value
        except (ValueError, TypeError):
            raise ValidationException(f"{field_name}必须是有效整数", field=field_name, value=value)
    
    @staticmethod
    def validate_identification_code(code):
        """验证识别编码格式"""
        if not code:
            raise ValidationException("识别编码不能为空")
        
        parts = code.split('/')
        if len(parts) < 4:
            raise ValidationException("识别编码格式错误，应为：仓库前缀/客户全称/车牌/日期/序号")
        
        warehouse_prefix = parts[0]
        if warehouse_prefix not in ['PH', 'KS', 'CD', 'PX']:
            raise ValidationException(f"无效的仓库前缀: {warehouse_prefix}")
        
        return code
    
    @staticmethod
    def validate_plate_number(plate_number):
        """验证车牌号格式"""
        if not plate_number:
            return plate_number
        
        # 简单的车牌号验证
        plate_number = plate_number.strip().upper()
        if len(plate_number) < 6 or len(plate_number) > 10:
            raise ValidationException("车牌号格式错误", field="plate_number", value=plate_number)
        
        return plate_number

# 业务逻辑验证
class BusinessValidator:
    """业务逻辑验证工具类"""
    
    @staticmethod
    def validate_inventory_sufficient(inventory, required_pallet, required_package):
        """验证库存是否充足"""
        if inventory.pallet_count < required_pallet:
            raise InventoryException(
                f"板数库存不足，当前: {inventory.pallet_count}, 需要: {required_pallet}",
                identification_code=inventory.identification_code,
                current_stock={'pallet_count': inventory.pallet_count, 'package_count': inventory.package_count}
            )
        
        if inventory.package_count < required_package:
            raise InventoryException(
                f"件数库存不足，当前: {inventory.package_count}, 需要: {required_package}",
                identification_code=inventory.identification_code,
                current_stock={'pallet_count': inventory.pallet_count, 'package_count': inventory.package_count}
            )
    
    @staticmethod
    def validate_warehouse_permission(user, warehouse_id, operation):
        """验证仓库操作权限 - 支持admin用户智能匹配"""
        # 超级管理员拥有所有权限
        if user.is_super_admin():
            return True

        # 兼容旧的is_admin属性
        if hasattr(user, 'is_admin') and user.is_admin:
            return True

        # 普通用户需要检查仓库权限
        if not hasattr(user, 'warehouse_id') or user.warehouse_id != warehouse_id:
            raise PermissionException(
                f"无权限操作其他仓库的数据",
                required_permission=f"warehouse_{warehouse_id}_{operation}"
            )

        return True
    
    @staticmethod
    def validate_batch_operation(records):
        """验证批量操作"""
        if not records:
            raise ValidationException("批量操作记录不能为空")
        
        if len(records) > 100:
            raise ValidationException("批量操作记录数量不能超过100条")
        
        # 检查重复的识别编码
        codes = [record.get('identification_code') for record in records if record.get('identification_code')]
        if len(codes) != len(set(codes)):
            raise ValidationException("批量操作中存在重复的识别编码")

# 错误日志记录
def log_business_error(operation, error_details, user_id=None):
    """记录业务错误日志"""
    log_data = {
        'operation': operation,
        'error_details': error_details,
        'user_id': user_id,
        'ip_address': request.remote_addr if request else None,
        'user_agent': request.headers.get('User-Agent') if request else None
    }
    
    current_app.logger.error(f"业务错误: {log_data}")

# 成功操作日志
def log_business_success(operation, details, user_id=None):
    """记录业务成功日志"""
    log_data = {
        'operation': operation,
        'details': details,
        'user_id': user_id,
        'ip_address': request.remote_addr if request else None
    }
    
    current_app.logger.info(f"业务操作成功: {log_data}")
