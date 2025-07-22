"""
数据库查询优化器
专门用于优化数据库查询性能，不禁用功能
"""

from flask import current_app
from sqlalchemy import text, event
from sqlalchemy.engine import Engine
import time
import logging

class DatabaseQueryOptimizer:
    """数据库查询优化器"""
    
    def __init__(self):
        self.slow_queries = []
        self.query_cache = {}
        self.optimization_applied = False
    
    @staticmethod
    def init_app(app):
        """初始化数据库查询优化"""
        optimizer = DatabaseQueryOptimizer()
        
        # 1. 启用查询监控
        optimizer.setup_query_monitoring()
        
        # 2. 应用查询优化
        optimizer.apply_query_optimizations()
        
        # 3. 设置连接池优化
        optimizer.optimize_connection_pool(app)
        
        app.logger.info("🗃️ 数据库查询优化器已启用")
        return optimizer
    
    def setup_query_monitoring(self):
        """设置查询监控"""
        @event.listens_for(Engine, "before_cursor_execute")
        def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            context._query_start_time = time.time()
        
        @event.listens_for(Engine, "after_cursor_execute")
        def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            total = time.time() - context._query_start_time
            
            # 记录慢查询（超过100ms）
            if total > 0.1:
                self.slow_queries.append({
                    'query': statement[:200] + '...' if len(statement) > 200 else statement,
                    'time': total,
                    'timestamp': time.time()
                })
                
                # 只保留最近的50个慢查询
                if len(self.slow_queries) > 50:
                    self.slow_queries = self.slow_queries[-50:]
                
                current_app.logger.warning(f"慢查询检测: {total:.3f}s - {statement[:100]}...")
    
    def apply_query_optimizations(self):
        """应用查询优化"""
        if self.optimization_applied:
            return
        
        try:
            from app import db
            
            # 1. 创建关键索引
            self.create_performance_indexes(db)
            
            # 2. 优化查询设置
            self.optimize_query_settings(db)
            
            self.optimization_applied = True
            current_app.logger.info("✅ 数据库查询优化已应用")
            
        except Exception as e:
            current_app.logger.error(f"数据库查询优化失败: {e}")
    
    def create_performance_indexes(self, db):
        """创建性能索引"""
        indexes = [
            # 入库记录索引
            "CREATE INDEX IF NOT EXISTS idx_inbound_time ON inbound_records(inbound_time)",
            "CREATE INDEX IF NOT EXISTS idx_inbound_customer ON inbound_records(customer_name)",
            "CREATE INDEX IF NOT EXISTS idx_inbound_warehouse ON inbound_records(operated_warehouse_id)",
            
            # 出库记录索引
            "CREATE INDEX IF NOT EXISTS idx_outbound_time ON outbound_records(departure_time)",
            "CREATE INDEX IF NOT EXISTS idx_outbound_customer ON outbound_records(customer_name)",
            "CREATE INDEX IF NOT EXISTS idx_outbound_warehouse ON outbound_records(operated_warehouse_id)",
            
            # 接收记录索引
            "CREATE INDEX IF NOT EXISTS idx_receive_time ON receive_records(inbound_time)",
            "CREATE INDEX IF NOT EXISTS idx_receive_batch ON receive_records(batch_no)",
            
            # 库存索引
            "CREATE INDEX IF NOT EXISTS idx_inventory_warehouse ON inventory(warehouse_id)",
            "CREATE INDEX IF NOT EXISTS idx_inventory_customer ON inventory(customer_name)",
            
            # 用户相关索引
            "CREATE INDEX IF NOT EXISTS idx_user_username ON users(username)",
            "CREATE INDEX IF NOT EXISTS idx_user_active ON users(is_active)",
        ]
        
        for index_sql in indexes:
            try:
                db.session.execute(text(index_sql))
                db.session.commit()
            except Exception as e:
                # 索引可能已存在，忽略错误
                db.session.rollback()
                if "already exists" not in str(e).lower():
                    current_app.logger.warning(f"创建索引失败: {e}")
    
    def optimize_query_settings(self, db):
        """优化查询设置"""
        try:
            # MySQL特定优化
            optimizations = [
                "SET SESSION query_cache_type = ON",
                "SET SESSION query_cache_size = 67108864",  # 64MB
                "SET SESSION tmp_table_size = 67108864",    # 64MB
                "SET SESSION max_heap_table_size = 67108864", # 64MB
                "SET SESSION join_buffer_size = 2097152",   # 2MB
                "SET SESSION sort_buffer_size = 2097152",   # 2MB
            ]
            
            for opt_sql in optimizations:
                try:
                    db.session.execute(text(opt_sql))
                except Exception as e:
                    # 某些设置可能不被支持，忽略错误
                    pass
            
            db.session.commit()
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.warning(f"查询设置优化失败: {e}")
    
    def optimize_connection_pool(self, app):
        """优化连接池设置"""
        # 这些设置已在 app/__init__.py 中应用
        current_app.logger.info("连接池优化设置已应用")
    
    def get_slow_queries(self):
        """获取慢查询列表"""
        return self.slow_queries
    
    def clear_slow_queries(self):
        """清除慢查询记录"""
        self.slow_queries.clear()
    
    @staticmethod
    def optimize_query(query):
        """优化单个查询"""
        # 添加查询提示
        if "SELECT" in query.upper() and "LIMIT" not in query.upper():
            # 为没有LIMIT的查询添加合理的限制
            if "ORDER BY" in query.upper():
                query += " LIMIT 1000"
            else:
                query += " ORDER BY id DESC LIMIT 1000"
        
        return query
    
    @staticmethod
    def create_optimized_query_builder():
        """创建优化的查询构建器"""
        class OptimizedQuery:
            def __init__(self, model):
                self.model = model
                self.query = model.query
            
            def filter_by_date_range(self, date_field, start_date, end_date):
                """优化的日期范围查询"""
                if start_date and end_date:
                    return self.query.filter(
                        date_field >= start_date,
                        date_field <= end_date
                    ).order_by(date_field.desc())
                return self.query.order_by(date_field.desc())
            
            def paginate_optimized(self, page, per_page=20):
                """优化的分页查询"""
                # 使用更小的页面大小以提高性能
                actual_per_page = min(per_page, 50)
                return self.query.paginate(
                    page=page,
                    per_page=actual_per_page,
                    error_out=False
                )
        
        return OptimizedQuery

# 全局优化器实例
_optimizer = None

def get_db_optimizer():
    """获取数据库优化器实例"""
    global _optimizer
    if _optimizer is None:
        _optimizer = DatabaseQueryOptimizer()
    return _optimizer

def init_db_optimization(app):
    """初始化数据库优化"""
    return DatabaseQueryOptimizer.init_app(app)
