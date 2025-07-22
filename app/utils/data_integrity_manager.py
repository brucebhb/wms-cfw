#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据完整性管理系统
集成事务管理、一致性检查、操作日志、备份等功能
"""

from flask import current_app
from app import db
from app.utils.transaction_manager import TransactionManager, OutboundTransactionManager
from app.utils.data_consistency_checker import DataConsistencyChecker
from app.utils.operation_logger import OperationLogger
from app.utils.backup_manager import get_backup_manager
from contextlib import contextmanager
from functools import wraps
import time
from datetime import datetime

class DataIntegrityManager:
    """数据完整性管理器"""
    
    def __init__(self):
        self.backup_manager = get_backup_manager()
        self.consistency_checker = DataConsistencyChecker()
        self.operation_logger = OperationLogger()
    
    @contextmanager
    def safe_operation(self, operation_type, identification_code, auto_backup=False):
        """
        安全操作上下文管理器
        集成事务管理、日志记录、一致性检查
        """
        operation_start_time = time.time()
        operation_id = f"{operation_type}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        # 记录操作前状态
        pre_state = self._capture_state(identification_code)
        
        try:
            current_app.logger.info(f"开始安全操作: {operation_type} (ID: {operation_id})")
            
            with TransactionManager.atomic_transaction():
                yield operation_id
                
                # 记录操作后状态
                post_state = self._capture_state(identification_code)
                
                # 记录操作日志
                self.operation_logger.log_inventory_change(
                    operation_type=operation_type,
                    identification_code=identification_code,
                    before_state=pre_state,
                    after_state=post_state,
                    additional_info={'operation_id': operation_id}
                )
                
                # 验证数据一致性
                self._validate_operation_consistency(identification_code, operation_type)
                
                operation_time = time.time() - operation_start_time
                current_app.logger.info(f"安全操作完成: {operation_type} (ID: {operation_id}), 耗时: {operation_time:.3f}秒")
                
                # 可选的自动备份
                if auto_backup:
                    self._create_operation_backup(operation_id, identification_code)
                
        except Exception as e:
            operation_time = time.time() - operation_start_time
            current_app.logger.error(f"安全操作失败: {operation_type} (ID: {operation_id}), 耗时: {operation_time:.3f}秒")
            
            # 记录错误日志
            self.operation_logger.log_error_operation(
                operation_type=operation_type,
                identification_code=identification_code,
                error_message=str(e),
                additional_info={
                    'operation_id': operation_id,
                    'pre_state': pre_state,
                    'duration': operation_time
                }
            )
            
            raise
    
    def _capture_state(self, identification_code):
        """捕获当前状态快照"""
        try:
            from app.models import Inventory, TransitCargo
            
            state = {
                'timestamp': datetime.now().isoformat(),
                'identification_code': identification_code,
                'inventory': [],
                'transit': []
            }
            
            # 捕获库存状态
            inventory_records = Inventory.query.filter_by(identification_code=identification_code).all()
            for inv in inventory_records:
                state['inventory'].append({
                    'warehouse_id': inv.operated_warehouse_id,
                    'pallet_count': inv.pallet_count,
                    'package_count': inv.package_count,
                    'weight': inv.weight,
                    'volume': inv.volume,
                    'customer_name': inv.customer_name,
                    'plate_number': inv.plate_number
                })
            
            # 捕获在途状态
            transit_records = TransitCargo.query.filter_by(identification_code=identification_code).all()
            for transit in transit_records:
                state['transit'].append({
                    'source_warehouse_id': transit.source_warehouse_id,
                    'destination_warehouse_id': transit.destination_warehouse_id,
                    'status': transit.status,
                    'pallet_count': transit.pallet_count,
                    'package_count': transit.package_count
                })
            
            return state
            
        except Exception as e:
            current_app.logger.error(f"捕获状态失败: {str(e)}")
            return {'error': str(e)}
    
    def _validate_operation_consistency(self, identification_code, operation_type):
        """验证操作后的数据一致性"""
        try:
            # 运行针对性的一致性检查
            issues = []
            
            # 检查识别编码一致性
            code_issues = self.consistency_checker.check_identification_code_consistency()
            relevant_issues = [issue for issue in code_issues if issue.get('identification_code') == identification_code]
            issues.extend(relevant_issues)
            
            # 检查库存平衡性
            balance_issues = self.consistency_checker.check_inventory_balance()
            relevant_balance_issues = [issue for issue in balance_issues if issue.get('identification_code') == identification_code]
            issues.extend(relevant_balance_issues)
            
            if issues:
                high_severity_issues = [issue for issue in issues if issue.get('severity') == 'high']
                if high_severity_issues:
                    error_msg = f"操作后发现高严重性数据一致性问题: {[issue['details'] for issue in high_severity_issues]}"
                    current_app.logger.error(error_msg)
                    raise Exception(error_msg)
                else:
                    current_app.logger.warning(f"操作后发现数据一致性问题: {[issue['details'] for issue in issues]}")
            
        except Exception as e:
            current_app.logger.error(f"一致性验证失败: {str(e)}")
            raise
    
    def _create_operation_backup(self, operation_id, identification_code):
        """为操作创建备份"""
        try:
            backup_name = f"operation_{operation_id}_{identification_code.replace('/', '_')}"
            backup_file = self.backup_manager.create_data_export(backup_name=backup_name)
            if backup_file:
                current_app.logger.info(f"操作备份创建成功: {backup_file}")
            else:
                current_app.logger.warning(f"操作备份创建失败: {operation_id}")
        except Exception as e:
            current_app.logger.error(f"创建操作备份失败: {str(e)}")
    
    def safe_outbound_operation(self, identification_code, outbound_data):
        """安全出库操作"""
        with self.safe_operation("outbound", identification_code, auto_backup=True) as operation_id:
            from app.models import Inventory, OutboundRecord, TransitCargo
            
            # 验证出库前的库存
            inventory = Inventory.query.filter_by(
                identification_code=identification_code,
                operated_warehouse_id=outbound_data['operated_warehouse_id']
            ).first()
            
            if not inventory:
                raise Exception(f"未找到库存记录: {identification_code}")
            
            # 检查库存是否足够
            if outbound_data.get('pallet_count', 0) > inventory.pallet_count:
                raise Exception(f"板数不足: 需要{outbound_data['pallet_count']}板，库存{inventory.pallet_count}板")
            
            if outbound_data.get('package_count', 0) > inventory.package_count:
                raise Exception(f"件数不足: 需要{outbound_data['package_count']}件，库存{inventory.package_count}件")
            
            # 创建出库记录
            outbound_record = OutboundRecord(**outbound_data)
            db.session.add(outbound_record)
            
            # 更新库存
            inventory.pallet_count -= outbound_data.get('pallet_count', 0)
            inventory.package_count -= outbound_data.get('package_count', 0)
            
            # 如果是发往后端仓库，创建在途记录
            if outbound_data.get('destination') in ['凭祥北投仓', '保税仓']:
                transit_data = {
                    'identification_code': identification_code,
                    'customer_name': inventory.customer_name,
                    'plate_number': inventory.plate_number,
                    'source_warehouse_id': outbound_data['operated_warehouse_id'],
                    'destination_warehouse_id': 4,  # 凭祥北投仓ID
                    'pallet_count': outbound_data.get('pallet_count', 0),
                    'package_count': outbound_data.get('package_count', 0),
                    'weight': outbound_data.get('weight', 0),
                    'volume': outbound_data.get('volume', 0),
                    'status': 'in_transit',
                    'departure_time': outbound_data.get('outbound_time', datetime.now()),
                    'export_mode': outbound_data.get('export_mode'),
                    'customs_broker': outbound_data.get('customs_broker'),
                    'service_staff': outbound_data.get('service_staff'),
                    'order_type': outbound_data.get('order_type')
                }
                
                transit_record = TransitCargo(**transit_data)
                db.session.add(transit_record)
            
            current_app.logger.info(f"出库操作完成: {identification_code}, 操作ID: {operation_id}")
            return outbound_record
    
    def safe_receive_operation(self, identification_code, receive_data):
        """安全接收操作"""
        with self.safe_operation("receive", identification_code, auto_backup=True) as operation_id:
            from app.models import Inventory, TransitCargo
            
            # 查找在途记录
            transit_record = TransitCargo.query.filter_by(
                identification_code=identification_code,
                destination_warehouse_id=receive_data['destination_warehouse_id'],
                status='in_transit'
            ).first()
            
            if not transit_record:
                raise Exception(f"未找到在途记录: {identification_code}")
            
            # 更新在途状态
            transit_record.status = 'received'
            transit_record.arrival_time = receive_data.get('receive_time', datetime.now())
            
            # 创建或更新目标仓库库存
            inventory = Inventory.query.filter_by(
                identification_code=identification_code,
                operated_warehouse_id=receive_data['destination_warehouse_id']
            ).first()
            
            if inventory:
                # 更新现有库存
                inventory.pallet_count += receive_data.get('pallet_count', 0)
                inventory.package_count += receive_data.get('package_count', 0)
            else:
                # 创建新库存记录
                inventory_data = {
                    'identification_code': identification_code,
                    'customer_name': transit_record.customer_name,
                    'plate_number': transit_record.plate_number,
                    'operated_warehouse_id': receive_data['destination_warehouse_id'],
                    'pallet_count': receive_data.get('pallet_count', 0),
                    'package_count': receive_data.get('package_count', 0),
                    'weight': transit_record.weight,
                    'volume': transit_record.volume,
                    'inbound_time': receive_data.get('receive_time', datetime.now()),
                    'export_mode': transit_record.export_mode,
                    'customs_broker': transit_record.customs_broker,
                    'service_staff': transit_record.service_staff,
                    'order_type': transit_record.order_type
                }
                
                inventory = Inventory(**inventory_data)
                db.session.add(inventory)
            
            current_app.logger.info(f"接收操作完成: {identification_code}, 操作ID: {operation_id}")
            return inventory
    
    def run_maintenance_check(self):
        """运行维护检查"""
        try:
            current_app.logger.info("开始数据完整性维护检查...")
            
            # 运行一致性检查
            consistency_results = self.consistency_checker.run_full_consistency_check()
            
            # 自动修复客户名称问题
            if consistency_results['high_severity'] > 0:
                current_app.logger.warning(f"发现 {consistency_results['high_severity']} 个高严重性问题")
                
                # 尝试自动修复客户名称不一致问题
                fixed_count = self.consistency_checker.fix_customer_name_issues()
                if fixed_count > 0:
                    current_app.logger.info(f"自动修复了 {fixed_count} 个客户名称问题")
            
            # 清理旧备份
            self.backup_manager.cleanup_old_backups()
            
            current_app.logger.info("数据完整性维护检查完成")
            return consistency_results
            
        except Exception as e:
            current_app.logger.error(f"维护检查失败: {str(e)}")
            raise

# 装饰器函数
def safe_inventory_operation(operation_type):
    """安全库存操作装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 尝试从参数中提取识别编码
            identification_code = kwargs.get('identification_code')
            if not identification_code and len(args) > 0:
                # 尝试从第一个参数获取
                if hasattr(args[0], 'get'):
                    identification_code = args[0].get('identification_code')
            
            if not identification_code:
                identification_code = "unknown"
            
            manager = DataIntegrityManager()
            with manager.safe_operation(operation_type, identification_code):
                return func(*args, **kwargs)
        return wrapper
    return decorator

# 全局实例
data_integrity_manager = DataIntegrityManager()
