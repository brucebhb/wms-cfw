#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
操作日志记录器 - 记录详细的库存变更日志
"""

from flask import current_app, request
from flask_login import current_user
from app import db
from datetime import datetime
import json
import traceback
from functools import wraps

class OperationLogger:
    """操作日志记录器"""
    
    @staticmethod
    def log_inventory_change(operation_type, identification_code, before_state, after_state, 
                           warehouse_id=None, user_id=None, additional_info=None):
        """
        记录库存变更日志
        
        Args:
            operation_type: 操作类型 (inbound, outbound, transfer, receive, etc.)
            identification_code: 识别编码
            before_state: 操作前状态
            after_state: 操作后状态
            warehouse_id: 仓库ID
            user_id: 用户ID
            additional_info: 额外信息
        """
        try:
            # 获取用户信息
            if not user_id and current_user and current_user.is_authenticated:
                user_id = current_user.id
                username = current_user.username
            else:
                username = "系统"
            
            # 获取请求信息
            ip_address = request.remote_addr if request else "系统"
            user_agent = request.headers.get('User-Agent', '') if request else "系统"
            
            # 计算变更量
            changes = OperationLogger._calculate_changes(before_state, after_state)
            
            # 构建日志记录
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'operation_type': operation_type,
                'identification_code': identification_code,
                'warehouse_id': warehouse_id,
                'user_id': user_id,
                'username': username,
                'ip_address': ip_address,
                'user_agent': user_agent,
                'before_state': before_state,
                'after_state': after_state,
                'changes': changes,
                'additional_info': additional_info or {}
            }
            
            # 记录到应用日志
            current_app.logger.info(f"库存变更: {json.dumps(log_entry, ensure_ascii=False, indent=2)}")
            
            # 如果有数据库表，也可以记录到数据库
            # 这里可以扩展为写入专门的操作日志表
            
        except Exception as e:
            current_app.logger.error(f"记录操作日志失败: {str(e)}")
            current_app.logger.error(f"错误堆栈: {traceback.format_exc()}")
    
    @staticmethod
    def _calculate_changes(before_state, after_state):
        """计算状态变更"""
        changes = {}
        
        if isinstance(before_state, dict) and isinstance(after_state, dict):
            all_keys = set(before_state.keys()) | set(after_state.keys())
            
            for key in all_keys:
                before_value = before_state.get(key)
                after_value = after_state.get(key)
                
                if before_value != after_value:
                    changes[key] = {
                        'before': before_value,
                        'after': after_value,
                        'delta': OperationLogger._calculate_delta(before_value, after_value)
                    }
        
        return changes
    
    @staticmethod
    def _calculate_delta(before_value, after_value):
        """计算数值变化量"""
        try:
            if isinstance(before_value, (int, float)) and isinstance(after_value, (int, float)):
                return after_value - before_value
            else:
                return None
        except:
            return None
    
    @staticmethod
    def log_outbound_operation(identification_code, outbound_data, inventory_before, inventory_after):
        """记录出库操作"""
        OperationLogger.log_inventory_change(
            operation_type="outbound",
            identification_code=identification_code,
            before_state=inventory_before,
            after_state=inventory_after,
            warehouse_id=outbound_data.get('operated_warehouse_id'),
            additional_info={
                'destination': outbound_data.get('destination'),
                'outbound_time': outbound_data.get('outbound_time'),
                'pallet_count': outbound_data.get('pallet_count'),
                'package_count': outbound_data.get('package_count'),
                'export_mode': outbound_data.get('export_mode'),
                'customs_broker': outbound_data.get('customs_broker')
            }
        )
    
    @staticmethod
    def log_inbound_operation(identification_code, inbound_data, inventory_after):
        """记录入库操作"""
        OperationLogger.log_inventory_change(
            operation_type="inbound",
            identification_code=identification_code,
            before_state={},
            after_state=inventory_after,
            warehouse_id=inbound_data.get('operated_warehouse_id'),
            additional_info={
                'inbound_time': inbound_data.get('inbound_time'),
                'customer_name': inbound_data.get('customer_name'),
                'plate_number': inbound_data.get('plate_number'),
                'pallet_count': inbound_data.get('pallet_count'),
                'package_count': inbound_data.get('package_count'),
                'weight': inbound_data.get('weight'),
                'volume': inbound_data.get('volume')
            }
        )
    
    @staticmethod
    def log_receive_operation(identification_code, receive_data, inventory_before, inventory_after):
        """记录接收操作"""
        OperationLogger.log_inventory_change(
            operation_type="receive",
            identification_code=identification_code,
            before_state=inventory_before,
            after_state=inventory_after,
            warehouse_id=receive_data.get('destination_warehouse_id'),
            additional_info={
                'source_warehouse_id': receive_data.get('source_warehouse_id'),
                'receive_time': receive_data.get('receive_time'),
                'pallet_count': receive_data.get('pallet_count'),
                'package_count': receive_data.get('package_count')
            }
        )
    
    @staticmethod
    def log_error_operation(operation_type, identification_code, error_message, additional_info=None):
        """记录错误操作"""
        try:
            user_id = current_user.id if current_user and current_user.is_authenticated else None
            username = current_user.username if current_user and current_user.is_authenticated else "系统"
            ip_address = request.remote_addr if request else "系统"
            
            error_log = {
                'timestamp': datetime.now().isoformat(),
                'operation_type': f"{operation_type}_error",
                'identification_code': identification_code,
                'user_id': user_id,
                'username': username,
                'ip_address': ip_address,
                'error_message': error_message,
                'additional_info': additional_info or {},
                'stack_trace': traceback.format_exc()
            }
            
            current_app.logger.error(f"操作错误: {json.dumps(error_log, ensure_ascii=False, indent=2)}")
            
        except Exception as e:
            current_app.logger.error(f"记录错误日志失败: {str(e)}")

def log_operation(operation_type):
    """操作日志装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = datetime.now()
            operation_id = f"{operation_type}_{start_time.strftime('%Y%m%d_%H%M%S_%f')}"
            
            try:
                current_app.logger.info(f"开始操作: {operation_type} (ID: {operation_id})")
                
                result = func(*args, **kwargs)
                
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                current_app.logger.info(f"操作完成: {operation_type} (ID: {operation_id}), 耗时: {duration:.3f}秒")
                
                return result
                
            except Exception as e:
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                current_app.logger.error(f"操作失败: {operation_type} (ID: {operation_id}), 耗时: {duration:.3f}秒, 错误: {str(e)}")
                
                # 记录详细错误信息
                OperationLogger.log_error_operation(
                    operation_type=operation_type,
                    identification_code=kwargs.get('identification_code', 'unknown'),
                    error_message=str(e),
                    additional_info={
                        'operation_id': operation_id,
                        'duration': duration,
                        'args': str(args)[:500],  # 限制长度
                        'kwargs': str(kwargs)[:500]  # 限制长度
                    }
                )
                
                raise
        
        return wrapper
    return decorator

class AuditLogger:
    """审计日志记录器"""
    
    @staticmethod
    def log_data_access(table_name, operation, record_id=None, filters=None):
        """记录数据访问日志"""
        try:
            user_id = current_user.id if current_user and current_user.is_authenticated else None
            username = current_user.username if current_user and current_user.is_authenticated else "匿名"
            ip_address = request.remote_addr if request else "系统"
            
            access_log = {
                'timestamp': datetime.now().isoformat(),
                'table_name': table_name,
                'operation': operation,
                'record_id': record_id,
                'filters': filters,
                'user_id': user_id,
                'username': username,
                'ip_address': ip_address
            }
            
            current_app.logger.info(f"数据访问: {json.dumps(access_log, ensure_ascii=False)}")
            
        except Exception as e:
            current_app.logger.error(f"记录数据访问日志失败: {str(e)}")
    
    @staticmethod
    def log_permission_check(permission, resource, granted):
        """记录权限检查日志"""
        try:
            user_id = current_user.id if current_user and current_user.is_authenticated else None
            username = current_user.username if current_user and current_user.is_authenticated else "匿名"
            
            permission_log = {
                'timestamp': datetime.now().isoformat(),
                'permission': permission,
                'resource': resource,
                'granted': granted,
                'user_id': user_id,
                'username': username
            }
            
            current_app.logger.info(f"权限检查: {json.dumps(permission_log, ensure_ascii=False)}")
            
        except Exception as e:
            current_app.logger.error(f"记录权限检查日志失败: {str(e)}")
