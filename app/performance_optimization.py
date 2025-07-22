"""
仓储管理系统性能优化方案
Performance Optimization for Warehouse Management System
"""

from flask import current_app
from sqlalchemy import text, Index
from app import db
from app.models import InboundRecord, OutboundRecord, Inventory, Warehouse
import time
from functools import wraps

class PerformanceOptimizer:
    """性能优化器"""
    
    def __init__(self):
        self.optimization_log = []
    
    def log_optimization(self, message):
        """记录优化日志"""
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {message}"
        self.optimization_log.append(log_entry)
        current_app.logger.info(f"Performance Optimization: {message}")
    
    def create_database_indexes(self):
        """创建数据库索引以提高查询性能"""
        try:
            # 为入库记录表创建复合索引
            indexes_to_create = [
                # 前端仓入库记录常用查询索引
                "CREATE INDEX IF NOT EXISTS idx_inbound_frontend_query ON inbound_record (operated_warehouse_id, record_type, inbound_time DESC)",
                
                # 客户名称搜索索引
                "CREATE INDEX IF NOT EXISTS idx_inbound_customer_name ON inbound_record (customer_name)",
                
                # 车牌号搜索索引
                "CREATE INDEX IF NOT EXISTS idx_inbound_plate_number ON inbound_record (plate_number)",
                
                # 识别编码索引
                "CREATE INDEX IF NOT EXISTS idx_inbound_identification_code ON inbound_record (identification_code)",
                
                # 日期范围查询索引
                "CREATE INDEX IF NOT EXISTS idx_inbound_time_range ON inbound_record (inbound_time DESC)",
                
                # 出库记录常用查询索引
                "CREATE INDEX IF NOT EXISTS idx_outbound_warehouse_time ON outbound_record (operated_warehouse_id, outbound_time DESC)",
                
                # 库存查询索引
                "CREATE INDEX IF NOT EXISTS idx_inventory_warehouse ON inventory (warehouse_id, identification_code)",
                
                # 仓库类型索引
                "CREATE INDEX IF NOT EXISTS idx_warehouse_type ON warehouse (warehouse_type, status)",
            ]
            
            for index_sql in indexes_to_create:
                try:
                    db.session.execute(text(index_sql))
                    self.log_optimization(f"Created index: {index_sql.split('idx_')[1].split(' ON')[0]}")
                except Exception as e:
                    self.log_optimization(f"Index creation failed or already exists: {str(e)}")
            
            db.session.commit()
            self.log_optimization("Database indexes creation completed")
            
        except Exception as e:
            db.session.rollback()
            self.log_optimization(f"Error creating indexes: {str(e)}")
    
    def optimize_query_performance(self):
        """优化查询性能"""
        try:
            # 分析表统计信息
            db.session.execute(text("ANALYZE TABLE inbound_record"))
            db.session.execute(text("ANALYZE TABLE outbound_record"))
            db.session.execute(text("ANALYZE TABLE inventory"))
            db.session.execute(text("ANALYZE TABLE warehouse"))
            
            self.log_optimization("Table statistics updated")
            
        except Exception as e:
            self.log_optimization(f"Error updating table statistics: {str(e)}")
    
    def get_optimization_suggestions(self):
        """获取性能优化建议"""
        suggestions = [
            "1. 数据库索引优化：为常用查询字段创建复合索引",
            "2. 查询优化：使用 joinedload 预加载关联数据，减少 N+1 查询问题",
            "3. 分页优化：合理设置每页显示数量，避免一次加载过多数据",
            "4. 缓存优化：对不经常变化的数据（如仓库列表）使用缓存",
            "5. 前端优化：使用 AJAX 异步加载，避免整页刷新",
            "6. 数据库连接池优化：合理配置连接池大小",
            "7. 定期清理过期数据：删除或归档旧的记录数据",
            "8. 使用数据库视图：为复杂查询创建视图",
        ]
        return suggestions

def timing_decorator(func):
    """性能监控装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        
        if execution_time > 1.0:  # 如果执行时间超过1秒，记录警告
            current_app.logger.warning(f"Slow query detected: {func.__name__} took {execution_time:.2f} seconds")
        else:
            current_app.logger.info(f"Query performance: {func.__name__} took {execution_time:.3f} seconds")
        
        return result
    return wrapper

class QueryOptimizer:
    """查询优化器"""
    
    @staticmethod
    def optimize_frontend_inbound_query():
        """优化前端仓入库记录查询"""
        # 使用更高效的查询方式
        frontend_warehouse_ids = db.session.query(Warehouse.id).filter_by(warehouse_type='frontend').subquery()
        
        base_query = InboundRecord.query.options(
            db.joinedload(InboundRecord.operated_warehouse)
        ).filter(
            InboundRecord.operated_warehouse_id.in_(frontend_warehouse_ids),
            InboundRecord.record_type == 'direct'
        )
        
        return base_query
    
    @staticmethod
    def get_cached_warehouses():
        """获取缓存的仓库列表"""
        # 这里可以实现缓存逻辑
        return Warehouse.query.filter_by(warehouse_type='frontend', status='active').all()

# 性能监控工具
class PerformanceMonitor:
    """性能监控工具"""
    
    def __init__(self):
        self.query_times = []
        self.slow_queries = []
    
    def record_query_time(self, query_name, execution_time):
        """记录查询时间"""
        self.query_times.append({
            'query': query_name,
            'time': execution_time,
            'timestamp': time.time()
        })
        
        if execution_time > 2.0:  # 超过2秒的查询被认为是慢查询
            self.slow_queries.append({
                'query': query_name,
                'time': execution_time,
                'timestamp': time.time()
            })
    
    def get_performance_report(self):
        """获取性能报告"""
        if not self.query_times:
            return "No query data available"
        
        avg_time = sum(q['time'] for q in self.query_times) / len(self.query_times)
        max_time = max(q['time'] for q in self.query_times)
        slow_query_count = len(self.slow_queries)
        
        report = f"""
        性能监控报告:
        - 总查询次数: {len(self.query_times)}
        - 平均查询时间: {avg_time:.3f}秒
        - 最长查询时间: {max_time:.3f}秒
        - 慢查询次数: {slow_query_count}
        """
        
        if self.slow_queries:
            report += "\n慢查询详情:\n"
            for query in self.slow_queries[-5:]:  # 显示最近5个慢查询
                report += f"- {query['query']}: {query['time']:.3f}秒\n"
        
        return report

# 全局性能监控实例
performance_monitor = PerformanceMonitor()
performance_optimizer = PerformanceOptimizer()

def init_performance_optimization():
    """初始化性能优化"""
    try:
        performance_optimizer.create_database_indexes()
        performance_optimizer.optimize_query_performance()
        current_app.logger.info("Performance optimization initialized successfully")
    except Exception as e:
        current_app.logger.error(f"Failed to initialize performance optimization: {str(e)}")

def get_performance_status():
    """获取性能状态"""
    return {
        'optimization_log': performance_optimizer.optimization_log[-10:],  # 最近10条优化日志
        'performance_report': performance_monitor.get_performance_report(),
        'suggestions': performance_optimizer.get_optimization_suggestions()
    }
