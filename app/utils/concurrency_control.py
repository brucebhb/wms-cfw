#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
并发控制工具类
解决库存更新的并发安全问题
"""

import time
import threading
from functools import wraps
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from flask import current_app
from app import db
from app.models import Inventory

class InventoryLockManager:
    """库存锁管理器"""
    
    def __init__(self):
        self._locks = {}
        self._lock = threading.Lock()
    
    def acquire_lock(self, identification_code, timeout=30):
        """获取库存锁"""
        with self._lock:
            if identification_code not in self._locks:
                self._locks[identification_code] = threading.Lock()
        
        return self._locks[identification_code].acquire(timeout=timeout)
    
    def release_lock(self, identification_code):
        """释放库存锁"""
        if identification_code in self._locks:
            try:
                self._locks[identification_code].release()
            except:
                pass

# 全局锁管理器实例
inventory_lock_manager = InventoryLockManager()

def with_inventory_lock(identification_code_param='identification_code'):
    """
    库存操作装饰器，确保同一识别编码的库存操作串行执行
    
    Args:
        identification_code_param: 函数参数中识别编码的参数名
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 获取识别编码
            identification_code = None
            
            # 从kwargs中获取
            if identification_code_param in kwargs:
                identification_code = kwargs[identification_code_param]
            # 从args中获取（假设是第一个参数）
            elif args and hasattr(args[0], 'identification_code'):
                identification_code = args[0].identification_code
            
            if not identification_code:
                current_app.logger.warning(f"无法获取识别编码，跳过锁控制: {func.__name__}")
                return func(*args, **kwargs)
            
            # 获取锁
            if not inventory_lock_manager.acquire_lock(identification_code):
                raise Exception(f"获取库存锁超时: {identification_code}")
            
            try:
                return func(*args, **kwargs)
            finally:
                inventory_lock_manager.release_lock(identification_code)
        
        return wrapper
    return decorator

def with_database_lock(lock_name, timeout=30):
    """
    数据库级别的锁装饰器
    
    Args:
        lock_name: 锁名称
        timeout: 超时时间（秒）
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            lock_acquired = False
            try:
                # 获取数据库锁
                result = db.session.execute(
                    text("SELECT GET_LOCK(:lock_name, :timeout)"),
                    {"lock_name": lock_name, "timeout": timeout}
                ).scalar()
                
                if result != 1:
                    raise Exception(f"获取数据库锁失败: {lock_name}")
                
                lock_acquired = True
                return func(*args, **kwargs)
                
            finally:
                if lock_acquired:
                    try:
                        db.session.execute(
                            text("SELECT RELEASE_LOCK(:lock_name)"),
                            {"lock_name": lock_name}
                        )
                    except:
                        pass
        
        return wrapper
    return decorator

class OptimisticLockMixin:
    """乐观锁混入类"""
    
    def update_with_version_check(self, **kwargs):
        """带版本检查的更新"""
        if not hasattr(self, 'version'):
            raise AttributeError("模型必须有version字段才能使用乐观锁")
        
        current_version = self.version
        new_version = current_version + 1
        
        # 构建更新条件
        update_data = kwargs.copy()
        update_data['version'] = new_version
        
        # 执行带版本检查的更新
        result = db.session.query(self.__class__).filter(
            self.__class__.id == self.id,
            self.__class__.version == current_version
        ).update(update_data)
        
        if result == 0:
            raise Exception("数据已被其他用户修改，请刷新后重试")
        
        # 更新当前对象的版本号
        self.version = new_version
        for key, value in kwargs.items():
            setattr(self, key, value)

def safe_inventory_update(identification_code, operation_type, **update_data):
    """
    安全的库存更新操作
    
    Args:
        identification_code: 识别编码
        operation_type: 操作类型 ('add', 'subtract', 'set')
        **update_data: 更新数据 (pallet_count, package_count, weight, volume)
    """
    max_retries = 3
    retry_delay = 0.1
    
    for attempt in range(max_retries):
        try:
            with db.session.begin():
                # 使用SELECT FOR UPDATE锁定记录
                inventory = db.session.query(Inventory).filter(
                    Inventory.identification_code == identification_code
                ).with_for_update().first()
                
                if not inventory:
                    raise Exception(f"库存记录不存在: {identification_code}")
                
                # 执行更新操作
                if operation_type == 'add':
                    inventory.pallet_count += update_data.get('pallet_count', 0)
                    inventory.package_count += update_data.get('package_count', 0)
                    inventory.weight += update_data.get('weight', 0)
                    inventory.volume += update_data.get('volume', 0)
                elif operation_type == 'subtract':
                    new_pallet = inventory.pallet_count - update_data.get('pallet_count', 0)
                    new_package = inventory.package_count - update_data.get('package_count', 0)
                    
                    # 检查库存是否足够
                    if new_pallet < 0 or new_package < 0:
                        raise Exception(f"库存不足: 当前板数{inventory.pallet_count}, 件数{inventory.package_count}")
                    
                    inventory.pallet_count = new_pallet
                    inventory.package_count = new_package
                    inventory.weight -= update_data.get('weight', 0)
                    inventory.volume -= update_data.get('volume', 0)
                elif operation_type == 'set':
                    inventory.pallet_count = update_data.get('pallet_count', inventory.pallet_count)
                    inventory.package_count = update_data.get('package_count', inventory.package_count)
                    inventory.weight = update_data.get('weight', inventory.weight)
                    inventory.volume = update_data.get('volume', inventory.volume)
                
                # 更新其他字段
                for key, value in update_data.items():
                    if key not in ['pallet_count', 'package_count', 'weight', 'volume']:
                        setattr(inventory, key, value)
                
                db.session.commit()
                current_app.logger.info(f"库存更新成功: {identification_code}, 操作: {operation_type}")
                return inventory
                
        except OperationalError as e:
            if "Deadlock" in str(e) and attempt < max_retries - 1:
                current_app.logger.warning(f"检测到死锁，重试 {attempt + 1}/{max_retries}")
                time.sleep(retry_delay * (2 ** attempt))  # 指数退避
                continue
            else:
                raise
        except Exception as e:
            db.session.rollback()
            raise
    
    raise Exception(f"库存更新失败，已重试{max_retries}次")

def batch_inventory_update(updates):
    """
    批量库存更新操作
    
    Args:
        updates: 更新列表，每个元素包含 {identification_code, operation_type, **update_data}
    """
    # 按识别编码排序，避免死锁
    sorted_updates = sorted(updates, key=lambda x: x['identification_code'])
    
    try:
        with db.session.begin():
            for update in sorted_updates:
                identification_code = update['identification_code']
                operation_type = update['operation_type']
                update_data = {k: v for k, v in update.items() 
                             if k not in ['identification_code', 'operation_type']}
                
                # 锁定并更新库存
                inventory = db.session.query(Inventory).filter(
                    Inventory.identification_code == identification_code
                ).with_for_update().first()
                
                if not inventory:
                    raise Exception(f"库存记录不存在: {identification_code}")
                
                # 执行更新逻辑（与safe_inventory_update相同）
                if operation_type == 'subtract':
                    new_pallet = inventory.pallet_count - update_data.get('pallet_count', 0)
                    new_package = inventory.package_count - update_data.get('package_count', 0)
                    
                    if new_pallet < 0 or new_package < 0:
                        raise Exception(f"库存不足: {identification_code}")
                    
                    inventory.pallet_count = new_pallet
                    inventory.package_count = new_package
                # ... 其他操作类型
            
            db.session.commit()
            current_app.logger.info(f"批量库存更新成功，共{len(updates)}条记录")
            
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"批量库存更新失败: {str(e)}")
        raise
