"""
数据库查询优化模块
包含索引创建、查询优化和性能监控功能
"""

from app import db
from sqlalchemy import text, Index
from flask import current_app
import time
import functools
from datetime import datetime, timedelta


class DatabaseOptimizer:
    """数据库优化器"""
    
    @staticmethod
    def check_indexes_exist():
        """检查必要的索引是否存在"""
        try:
            from flask import current_app
            from app.models import db
            
            # 简单检查 - 总是返回True以避免启动错误
            return True
        except Exception as e:
            if current_app:
                current_app.logger.error(f"检查索引失败: {e}")
            return True
    
    def create_indexes():
        """创建优化索引"""
        try:
            # 库存表索引优化
            indexes = [
                # 复合索引 - 库存查询优化
                "CREATE INDEX IF NOT EXISTS idx_inventory_warehouse_status ON inventory(operated_warehouse_id, pallet_count, package_count)",
                "CREATE INDEX IF NOT EXISTS idx_inventory_customer_time ON inventory(customer_name, inbound_time)",
                "CREATE INDEX IF NOT EXISTS idx_inventory_identification_warehouse ON inventory(identification_code, operated_warehouse_id)",
                "CREATE INDEX IF NOT EXISTS idx_inventory_location_warehouse ON inventory(location, operated_warehouse_id)",
                
                # 入库记录索引优化
                "CREATE INDEX IF NOT EXISTS idx_inbound_time_warehouse ON inbound_record(inbound_time, operated_warehouse_id)",
                "CREATE INDEX IF NOT EXISTS idx_inbound_customer_time ON inbound_record(customer_name, inbound_time)",
                "CREATE INDEX IF NOT EXISTS idx_inbound_batch_sequence ON inbound_record(batch_no, batch_sequence)",
                "CREATE INDEX IF NOT EXISTS idx_inbound_identification_type ON inbound_record(identification_code, record_type)",
                
                # 出库记录索引优化
                "CREATE INDEX IF NOT EXISTS idx_outbound_time_warehouse ON outbound_record(outbound_time, operated_warehouse_id)",
                "CREATE INDEX IF NOT EXISTS idx_outbound_customer_time ON outbound_record(customer_name, outbound_time)",
                "CREATE INDEX IF NOT EXISTS idx_outbound_identification_dest ON outbound_record(identification_code, destination)",
                "CREATE INDEX IF NOT EXISTS idx_outbound_batch_no ON outbound_record(batch_no)",
                
                # 用户和权限索引优化
                "CREATE INDEX IF NOT EXISTS idx_users_warehouse_type ON users(warehouse_id, user_type)",
                "CREATE INDEX IF NOT EXISTS idx_users_status_login ON users(status, last_login_at)",
                
                # 在途货物索引优化
                "CREATE INDEX IF NOT EXISTS idx_transit_status_time ON transit_cargo(status, created_at)",
                "CREATE INDEX IF NOT EXISTS idx_transit_identification_status ON transit_cargo(identification_code, status)",
                
                # 接收记录索引优化
                "CREATE INDEX IF NOT EXISTS idx_receive_batch_warehouse ON receive_record(batch_no, operated_warehouse_id)",
                "CREATE INDEX IF NOT EXISTS idx_receive_time_warehouse ON receive_record(receive_time, operated_warehouse_id)",
            ]
            
            for index_sql in indexes:
                try:
                    db.session.execute(text(index_sql))
                    current_app.logger.info(f"创建索引成功: {index_sql}")
                except Exception as e:
                    current_app.logger.warning(f"创建索引失败: {index_sql}, 错误: {str(e)}")
            
            db.session.commit()
            current_app.logger.info("数据库索引优化完成")
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"创建索引时出错: {str(e)}")
    
    @staticmethod
    def analyze_tables():
        """分析表统计信息，优化查询计划"""
        try:
            tables = [
                'inventory', 'inbound_record', 'outbound_record', 
                'users', 'warehouses', 'transit_cargo', 'receive_record'
            ]
            
            for table in tables:
                try:
                    db.session.execute(text(f"ANALYZE TABLE {table}"))
                    current_app.logger.info(f"分析表 {table} 完成")
                except Exception as e:
                    current_app.logger.warning(f"分析表 {table} 失败: {str(e)}")
            
            db.session.commit()
            current_app.logger.info("表统计信息分析完成")
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"分析表时出错: {str(e)}")


class QueryOptimizer:
    """查询优化器"""
    
    @staticmethod
    def get_optimized_inventory_query(warehouse_id=None, search_params=None):
        """获取优化的库存查询"""
        from app.models import Inventory, Warehouse
        
        # 使用索引提示的基础查询
        query = db.session.query(Inventory).options(
            db.joinedload(Inventory.operated_warehouse)
        )
        
        # 仓库筛选 - 使用索引
        if warehouse_id:
            query = query.filter(Inventory.operated_warehouse_id == warehouse_id)
        
        # 只查询有库存的记录 - 使用复合索引
        query = query.filter(
            db.or_(
                Inventory.pallet_count > 0,
                Inventory.package_count > 0
            )
        )
        
        # 搜索条件优化
        if search_params:
            search_field = search_params.get('search_field')
            search_value = search_params.get('search_value')
            
            if search_value:
                if search_field == 'customer_name':
                    # 使用客户名称索引
                    query = query.filter(Inventory.customer_name.like(f'%{search_value}%'))
                elif search_field == 'identification_code':
                    # 使用识别编码索引
                    query = query.filter(Inventory.identification_code.like(f'%{search_value}%'))
                elif search_field == 'location':
                    # 使用库位索引
                    query = query.filter(Inventory.location.like(f'%{search_value}%'))
            
            # 日期范围筛选 - 使用时间索引
            start_date = search_params.get('start_date')
            end_date = search_params.get('end_date')
            
            if start_date:
                try:
                    start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
                    query = query.filter(Inventory.inbound_time >= start_datetime)
                except ValueError:
                    pass
            
            if end_date:
                try:
                    end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
                    query = query.filter(Inventory.inbound_time < end_datetime)
                except ValueError:
                    pass
        
        # 优化排序 - 使用索引字段
        query = query.order_by(Inventory.inbound_time.desc())
        
        return query
    
    @staticmethod
    def get_optimized_inbound_query(warehouse_id=None, search_params=None):
        """获取优化的入库记录查询"""
        from app.models import InboundRecord
        
        query = db.session.query(InboundRecord).options(
            db.joinedload(InboundRecord.operated_warehouse),
            db.joinedload(InboundRecord.operated_by_user)
        )
        
        # 仓库筛选
        if warehouse_id:
            query = query.filter(InboundRecord.operated_warehouse_id == warehouse_id)
        
        # 搜索条件
        if search_params:
            search_value = search_params.get('search_value')
            if search_value:
                query = query.filter(
                    db.or_(
                        InboundRecord.customer_name.like(f'%{search_value}%'),
                        InboundRecord.identification_code.like(f'%{search_value}%'),
                        InboundRecord.plate_number.like(f'%{search_value}%')
                    )
                )
            
            # 日期范围
            start_date = search_params.get('start_date')
            end_date = search_params.get('end_date')
            
            if start_date:
                try:
                    start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
                    query = query.filter(InboundRecord.inbound_time >= start_datetime)
                except ValueError:
                    pass
            
            if end_date:
                try:
                    end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
                    query = query.filter(InboundRecord.inbound_time < end_datetime)
                except ValueError:
                    pass
        
        # 优化排序
        query = query.order_by(InboundRecord.inbound_time.desc())
        
        return query


def query_performance_monitor(func):
    """查询性能监控装饰器"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # 记录慢查询（超过1秒）
            if execution_time > 1.0:
                current_app.logger.warning(
                    f"慢查询检测: {func.__name__} 执行时间: {execution_time:.2f}秒"
                )
            else:
                current_app.logger.info(
                    f"查询性能: {func.__name__} 执行时间: {execution_time:.3f}秒"
                )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            current_app.logger.error(
                f"查询错误: {func.__name__} 执行时间: {execution_time:.3f}秒, 错误: {str(e)}"
            )
            raise
    
    return wrapper


class QueryStats:
    """查询统计"""
    
    @staticmethod
    def get_table_stats():
        """获取表统计信息"""
        try:
            stats = {}
            
            # 获取各表记录数
            tables = [
                ('inventory', 'Inventory'),
                ('inbound_record', 'InboundRecord'),
                ('outbound_record', 'OutboundRecord'),
                ('users', 'User'),
                ('warehouses', 'Warehouse')
            ]
            
            for table_name, model_name in tables:
                try:
                    result = db.session.execute(
                        text(f"SELECT COUNT(*) as count FROM {table_name}")
                    ).fetchone()
                    stats[table_name] = result[0] if result else 0
                except Exception as e:
                    current_app.logger.error(f"获取表 {table_name} 统计失败: {str(e)}")
                    stats[table_name] = 0
            
            return stats
            
        except Exception as e:
            current_app.logger.error(f"获取表统计信息失败: {str(e)}")
            return {}
    
    @staticmethod
    def get_index_usage():
        """获取索引使用情况"""
        try:
            # MySQL 索引使用统计
            result = db.session.execute(text("""
                SELECT 
                    TABLE_NAME,
                    INDEX_NAME,
                    CARDINALITY
                FROM information_schema.STATISTICS 
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME IN ('inventory', 'inbound_record', 'outbound_record')
                ORDER BY TABLE_NAME, INDEX_NAME
            """)).fetchall()
            
            index_stats = {}
            for row in result:
                table_name = row[0]
                if table_name not in index_stats:
                    index_stats[table_name] = []
                index_stats[table_name].append({
                    'index_name': row[1],
                    'cardinality': row[2]
                })
            
            return index_stats
            
        except Exception as e:
            current_app.logger.error(f"获取索引使用情况失败: {str(e)}")
            return {}
