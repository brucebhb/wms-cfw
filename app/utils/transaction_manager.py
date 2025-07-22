#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
事务管理器 - 确保数据库操作的原子性
"""

from contextlib import contextmanager
from functools import wraps
from flask import current_app
from app import db
from sqlalchemy.exc import SQLAlchemyError
import traceback
import time

class TransactionManager:
    """事务管理器"""
    
    @staticmethod
    @contextmanager
    def atomic_transaction():
        """
        原子事务上下文管理器
        确保所有操作要么全部成功，要么全部回滚
        """
        transaction_start_time = time.time()
        try:
            current_app.logger.info("开始原子事务")
            yield
            db.session.commit()
            transaction_time = time.time() - transaction_start_time
            current_app.logger.info(f"事务提交成功，耗时: {transaction_time:.3f}秒")
        except Exception as e:
            db.session.rollback()
            transaction_time = time.time() - transaction_start_time
            current_app.logger.error(f"事务回滚，耗时: {transaction_time:.3f}秒，错误: {str(e)}")
            current_app.logger.error(f"错误堆栈: {traceback.format_exc()}")
            raise
    
    @staticmethod
    @contextmanager
    def nested_transaction():
        """
        嵌套事务上下文管理器
        用于在已有事务中创建保存点
        """
        savepoint = None
        try:
            savepoint = db.session.begin_nested()
            current_app.logger.info("创建事务保存点")
            yield
            savepoint.commit()
            current_app.logger.info("保存点提交成功")
        except Exception as e:
            if savepoint:
                savepoint.rollback()
                current_app.logger.error(f"回滚到保存点，错误: {str(e)}")
            raise
    
    @staticmethod
    def atomic_operation(operation_name="未知操作"):
        """
        原子操作装饰器
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                with TransactionManager.atomic_transaction():
                    current_app.logger.info(f"执行原子操作: {operation_name}")
                    result = func(*args, **kwargs)
                    current_app.logger.info(f"原子操作完成: {operation_name}")
                    return result
            return wrapper
        return decorator

class OutboundTransactionManager:
    """出库事务管理器 - 专门处理出库操作的原子性"""
    
    @staticmethod
    @contextmanager
    def outbound_transaction(identification_code, operation_type="出库"):
        """
        出库事务上下文管理器
        """
        operation_start_time = time.time()
        try:
            current_app.logger.info(f"开始{operation_type}事务: {identification_code}")
            
            # 记录操作前的状态
            from app.models import Inventory
            pre_inventory = Inventory.query.filter_by(identification_code=identification_code).all()
            pre_state = [(inv.operated_warehouse_id, inv.pallet_count, inv.package_count) for inv in pre_inventory]
            
            yield
            
            # 验证操作后的状态
            post_inventory = Inventory.query.filter_by(identification_code=identification_code).all()
            post_state = [(inv.operated_warehouse_id, inv.pallet_count, inv.package_count) for inv in post_inventory]
            
            db.session.commit()
            
            operation_time = time.time() - operation_start_time
            current_app.logger.info(f"{operation_type}事务提交成功: {identification_code}，耗时: {operation_time:.3f}秒")
            current_app.logger.info(f"库存变化: {pre_state} -> {post_state}")
            
        except Exception as e:
            db.session.rollback()
            operation_time = time.time() - operation_start_time
            current_app.logger.error(f"{operation_type}事务回滚: {identification_code}，耗时: {operation_time:.3f}秒")
            current_app.logger.error(f"错误详情: {str(e)}")
            current_app.logger.error(f"错误堆栈: {traceback.format_exc()}")
            raise
    
    @staticmethod
    def batch_outbound_transaction(identification_codes, operation_type="批量出库"):
        """
        批量出库事务管理器
        """
        @contextmanager
        def batch_transaction():
            operation_start_time = time.time()
            try:
                current_app.logger.info(f"开始{operation_type}事务，涉及 {len(identification_codes)} 个识别编码")
                
                yield
                
                db.session.commit()
                operation_time = time.time() - operation_start_time
                current_app.logger.info(f"{operation_type}事务提交成功，耗时: {operation_time:.3f}秒")
                
            except Exception as e:
                db.session.rollback()
                operation_time = time.time() - operation_start_time
                current_app.logger.error(f"{operation_type}事务回滚，耗时: {operation_time:.3f}秒")
                current_app.logger.error(f"错误详情: {str(e)}")
                raise
        
        return batch_transaction()

class InventoryTransactionManager:
    """库存事务管理器"""
    
    @staticmethod
    @contextmanager
    def inventory_update_transaction(identification_code, operation_type="库存更新"):
        """
        库存更新事务管理器
        """
        operation_start_time = time.time()
        try:
            current_app.logger.info(f"开始{operation_type}事务: {identification_code}")
            
            # 获取操作前的库存快照
            from app.models import Inventory
            pre_inventory = {}
            inventory_records = Inventory.query.filter_by(identification_code=identification_code).all()
            for inv in inventory_records:
                pre_inventory[inv.operated_warehouse_id] = {
                    'pallet_count': inv.pallet_count,
                    'package_count': inv.package_count,
                    'weight': inv.weight,
                    'volume': inv.volume
                }
            
            yield pre_inventory
            
            # 验证操作后的库存状态
            post_inventory = {}
            inventory_records = Inventory.query.filter_by(identification_code=identification_code).all()
            for inv in inventory_records:
                post_inventory[inv.operated_warehouse_id] = {
                    'pallet_count': inv.pallet_count,
                    'package_count': inv.package_count,
                    'weight': inv.weight,
                    'volume': inv.volume
                }
            
            # 记录库存变化
            for warehouse_id in set(list(pre_inventory.keys()) + list(post_inventory.keys())):
                pre = pre_inventory.get(warehouse_id, {})
                post = post_inventory.get(warehouse_id, {})
                if pre != post:
                    current_app.logger.info(f"仓库 {warehouse_id} 库存变化: {pre} -> {post}")
            
            db.session.commit()
            operation_time = time.time() - operation_start_time
            current_app.logger.info(f"{operation_type}事务提交成功: {identification_code}，耗时: {operation_time:.3f}秒")
            
        except Exception as e:
            db.session.rollback()
            operation_time = time.time() - operation_start_time
            current_app.logger.error(f"{operation_type}事务回滚: {identification_code}，耗时: {operation_time:.3f}秒")
            current_app.logger.error(f"错误详情: {str(e)}")
            current_app.logger.error(f"错误堆栈: {traceback.format_exc()}")
            raise

class TransitTransactionManager:
    """在途货物事务管理器"""
    
    @staticmethod
    @contextmanager
    def transit_transaction(identification_code, operation_type="在途操作"):
        """
        在途货物事务管理器
        """
        operation_start_time = time.time()
        try:
            current_app.logger.info(f"开始{operation_type}事务: {identification_code}")
            
            yield
            
            db.session.commit()
            operation_time = time.time() - operation_start_time
            current_app.logger.info(f"{operation_type}事务提交成功: {identification_code}，耗时: {operation_time:.3f}秒")
            
        except Exception as e:
            db.session.rollback()
            operation_time = time.time() - operation_start_time
            current_app.logger.error(f"{operation_type}事务回滚: {identification_code}，耗时: {operation_time:.3f}秒")
            current_app.logger.error(f"错误详情: {str(e)}")
            current_app.logger.error(f"错误堆栈: {traceback.format_exc()}")
            raise

def retry_on_deadlock(max_retries=3, delay=0.1):
    """
    死锁重试装饰器
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except SQLAlchemyError as e:
                    if "deadlock" in str(e).lower() and attempt < max_retries - 1:
                        current_app.logger.warning(f"检测到死锁，第 {attempt + 1} 次重试: {str(e)}")
                        time.sleep(delay * (2 ** attempt))  # 指数退避
                        continue
                    else:
                        raise
            return None
        return wrapper
    return decorator

# 使用示例装饰器
def atomic_outbound_operation(identification_code):
    """出库操作原子性装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with OutboundTransactionManager.outbound_transaction(identification_code, "出库操作"):
                return func(*args, **kwargs)
        return wrapper
    return decorator

def atomic_inventory_operation(identification_code):
    """库存操作原子性装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with InventoryTransactionManager.inventory_update_transaction(identification_code, "库存操作"):
                return func(*args, **kwargs)
        return wrapper
    return decorator
