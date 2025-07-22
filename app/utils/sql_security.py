#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQL安全工具类
防止SQL注入和提供安全的数据库查询方法
"""

import re
from sqlalchemy import text, and_, or_
from sqlalchemy.orm import Query
from flask import current_app
from app import db
from app.utils.exception_handler import ValidationException

class SQLSecurityChecker:
    """SQL安全检查器"""
    
    # 危险的SQL关键字
    DANGEROUS_KEYWORDS = [
        'DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE', 'INSERT', 'UPDATE',
        'EXEC', 'EXECUTE', 'UNION', 'SCRIPT', 'DECLARE', 'CAST', 'CONVERT',
        'INFORMATION_SCHEMA', 'SYSOBJECTS', 'SYSCOLUMNS', 'MASTER', 'MSDB',
        'TEMPDB', 'MODEL', 'XP_', 'SP_', 'OPENROWSET', 'OPENDATASOURCE'
    ]
    
    # SQL注入模式
    INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
        r"(--|#|/\*|\*/)",
        r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
        r"(\b(OR|AND)\s+['\"].*['\"])",
        r"(UNION\s+(ALL\s+)?SELECT)",
        r"(\bINTO\s+(OUTFILE|DUMPFILE))",
        r"(\bLOAD_FILE\s*\()",
        r"(\bBENCHMARK\s*\()",
        r"(\bSLEEP\s*\()",
        r"(\bWAITFOR\s+DELAY)",
    ]
    
    @classmethod
    def check_sql_injection(cls, input_string):
        """检查SQL注入攻击"""
        if not input_string:
            return False
        
        input_upper = str(input_string).upper()
        
        # 检查危险关键字
        for keyword in cls.DANGEROUS_KEYWORDS:
            if keyword in input_upper:
                current_app.logger.warning(f"检测到危险SQL关键字: {keyword} in {input_string}")
                return True
        
        # 检查注入模式
        for pattern in cls.INJECTION_PATTERNS:
            if re.search(pattern, input_upper, re.IGNORECASE):
                current_app.logger.warning(f"检测到SQL注入模式: {pattern} in {input_string}")
                return True
        
        return False
    
    @classmethod
    def sanitize_search_input(cls, input_string):
        """清理搜索输入"""
        if not input_string:
            return ''
        
        # 检查SQL注入
        if cls.check_sql_injection(input_string):
            raise ValidationException("输入包含非法字符，请重新输入")
        
        # 转义特殊字符
        sanitized = str(input_string).strip()
        
        # 移除或转义危险字符
        sanitized = re.sub(r'[<>"\';]', '', sanitized)
        
        # 限制长度
        if len(sanitized) > 200:
            sanitized = sanitized[:200]
        
        return sanitized

class SafeQueryBuilder:
    """安全查询构建器"""
    
    @staticmethod
    def build_like_condition(column, value, case_sensitive=False):
        """构建安全的LIKE条件"""
        if not value:
            return None
        
        # 清理输入
        clean_value = SQLSecurityChecker.sanitize_search_input(value)
        
        # 转义LIKE特殊字符
        escaped_value = clean_value.replace('%', r'\%').replace('_', r'\_')
        
        if case_sensitive:
            return column.like(f'%{escaped_value}%')
        else:
            return column.ilike(f'%{escaped_value}%')
    
    @staticmethod
    def build_date_range_condition(column, start_date, end_date):
        """构建安全的日期范围条件"""
        conditions = []
        
        if start_date:
            conditions.append(column >= start_date)
        
        if end_date:
            conditions.append(column <= end_date)
        
        return and_(*conditions) if conditions else None
    
    @staticmethod
    def build_in_condition(column, values):
        """构建安全的IN条件"""
        if not values:
            return None
        
        # 清理每个值
        clean_values = []
        for value in values:
            if SQLSecurityChecker.check_sql_injection(str(value)):
                current_app.logger.warning(f"跳过危险输入值: {value}")
                continue
            clean_values.append(value)
        
        return column.in_(clean_values) if clean_values else None
    
    @staticmethod
    def build_search_conditions(model, search_fields, search_value):
        """构建多字段搜索条件"""
        if not search_value or not search_fields:
            return None
        
        # 清理搜索值
        clean_value = SQLSecurityChecker.sanitize_search_input(search_value)
        
        conditions = []
        for field_name in search_fields:
            if hasattr(model, field_name):
                column = getattr(model, field_name)
                condition = SafeQueryBuilder.build_like_condition(column, clean_value)
                if condition is not None:
                    conditions.append(condition)
        
        return or_(*conditions) if conditions else None

class SafeRawQuery:
    """安全的原生SQL查询"""
    
    @staticmethod
    def execute_safe_query(sql_template, parameters=None):
        """执行安全的参数化查询"""
        if not sql_template:
            raise ValidationException("SQL模板不能为空")
        
        # 检查SQL模板是否包含危险操作
        if SQLSecurityChecker.check_sql_injection(sql_template):
            raise ValidationException("SQL模板包含危险操作")
        
        # 验证参数
        if parameters:
            for key, value in parameters.items():
                if SQLSecurityChecker.check_sql_injection(str(value)):
                    raise ValidationException(f"参数 {key} 包含非法字符")
        
        try:
            result = db.session.execute(text(sql_template), parameters or {})
            return result
        except Exception as e:
            current_app.logger.error(f"SQL查询执行失败: {sql_template}, 参数: {parameters}, 错误: {str(e)}")
            raise
    
    @staticmethod
    def get_table_statistics(table_name):
        """获取表统计信息（安全版本）"""
        # 验证表名
        valid_tables = ['inbound_record', 'outbound_record', 'inventory', 'receive_records', 'user', 'warehouse']
        if table_name not in valid_tables:
            raise ValidationException(f"无效的表名: {table_name}")
        
        sql = f"SELECT COUNT(*) as total_count FROM {table_name}"
        result = SafeRawQuery.execute_safe_query(sql)
        return result.scalar()
    
    @staticmethod
    def get_inventory_summary(warehouse_id=None):
        """获取库存汇总（安全版本）"""
        sql = """
        SELECT 
            warehouse_id,
            COUNT(*) as record_count,
            SUM(pallet_count) as total_pallets,
            SUM(package_count) as total_packages,
            SUM(weight) as total_weight,
            SUM(volume) as total_volume
        FROM inventory 
        WHERE (:warehouse_id IS NULL OR warehouse_id = :warehouse_id)
        GROUP BY warehouse_id
        """
        
        result = SafeRawQuery.execute_safe_query(sql, {'warehouse_id': warehouse_id})
        return result.fetchall()

class QueryOptimizer:
    """查询优化器"""
    
    @staticmethod
    def optimize_pagination_query(query, page, per_page, max_per_page=1000):
        """优化分页查询"""
        # 验证分页参数
        if page < 1:
            page = 1
        if per_page < 1 or per_page > max_per_page:
            per_page = 50
        
        # 计算偏移量
        offset = (page - 1) * per_page
        
        # 应用分页
        return query.offset(offset).limit(per_page)
    
    @staticmethod
    def add_search_filters(query, model, filters):
        """添加搜索过滤器"""
        for field_name, field_value in filters.items():
            if not field_value:
                continue
            
            if not hasattr(model, field_name):
                current_app.logger.warning(f"模型 {model.__name__} 没有字段 {field_name}")
                continue
            
            column = getattr(model, field_name)
            
            # 根据字段类型选择过滤方式
            if isinstance(field_value, str):
                condition = SafeQueryBuilder.build_like_condition(column, field_value)
            elif isinstance(field_value, (list, tuple)):
                condition = SafeQueryBuilder.build_in_condition(column, field_value)
            else:
                condition = column == field_value
            
            if condition is not None:
                query = query.filter(condition)
        
        return query
    
    @staticmethod
    def add_date_range_filter(query, date_column, start_date, end_date):
        """添加日期范围过滤器"""
        condition = SafeQueryBuilder.build_date_range_condition(date_column, start_date, end_date)
        if condition is not None:
            query = query.filter(condition)
        return query

# 装饰器：自动验证查询参数
def validate_query_params(allowed_params=None):
    """验证查询参数装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            from flask import request
            
            # 验证查询参数
            for param_name, param_value in request.args.items():
                if allowed_params and param_name not in allowed_params:
                    current_app.logger.warning(f"未授权的查询参数: {param_name}")
                    continue
                
                # 检查参数值是否安全
                if SQLSecurityChecker.check_sql_injection(param_value):
                    raise ValidationException(f"查询参数 {param_name} 包含非法字符")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

# 使用示例和最佳实践
class SecureQueryExamples:
    """安全查询示例"""
    
    @staticmethod
    def search_inbound_records(customer_name=None, plate_number=None, start_date=None, end_date=None):
        """安全的入库记录搜索"""
        from app.models import InboundRecord
        
        query = db.session.query(InboundRecord)
        
        # 使用安全的搜索条件构建
        if customer_name:
            condition = SafeQueryBuilder.build_like_condition(
                InboundRecord.customer_name, customer_name
            )
            if condition is not None:
                query = query.filter(condition)
        
        if plate_number:
            condition = SafeQueryBuilder.build_like_condition(
                InboundRecord.plate_number, plate_number
            )
            if condition is not None:
                query = query.filter(condition)
        
        # 添加日期范围过滤
        query = QueryOptimizer.add_date_range_filter(
            query, InboundRecord.inbound_time, start_date, end_date
        )
        
        return query
    
    @staticmethod
    def get_inventory_by_codes(identification_codes):
        """根据识别编码获取库存（安全版本）"""
        from app.models import Inventory
        
        # 验证识别编码
        clean_codes = []
        for code in identification_codes:
            if not SQLSecurityChecker.check_sql_injection(code):
                clean_codes.append(code)
        
        if not clean_codes:
            return []
        
        return db.session.query(Inventory).filter(
            Inventory.identification_code.in_(clean_codes)
        ).all()
