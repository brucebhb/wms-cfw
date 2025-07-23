#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
错误诊断脚本 - 检查Internal Server Error的具体原因
"""

import os
import sys
import traceback

def diagnose_import_errors():
    """诊断导入错误"""
    print("🔍 检查模块导入...")
    
    modules_to_check = [
        'flask',
        'flask_sqlalchemy',
        'flask_migrate',
        'flask_wtf',
        'flask_login',
        'pymysql',
        'app',
        'app.models',
        'app.main',
        'app.auth'
    ]
    
    for module in modules_to_check:
        try:
            __import__(module)
            print(f"   ✅ {module}")
        except Exception as e:
            print(f"   ❌ {module}: {e}")

def diagnose_database_connection():
    """诊断数据库连接"""
    print("\n🗄️ 检查数据库连接...")
    
    try:
        from app import create_app, db
        app = create_app()
        
        with app.app_context():
            # 测试基本连接
            result = db.engine.execute("SELECT 1").fetchone()
            print("   ✅ 数据库基本连接正常")
            
            # 检查关键表是否存在
            tables_to_check = ['user', 'warehouse', 'inventory', 'outbound_record']
            for table in tables_to_check:
                try:
                    db.engine.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
                    print(f"   ✅ 表 {table} 存在")
                except Exception as e:
                    print(f"   ❌ 表 {table}: {e}")
                    
    except Exception as e:
        print(f"   ❌ 数据库连接失败: {e}")

def diagnose_model_attributes():
    """诊断模型属性"""
    print("\n🏗️ 检查模型属性...")
    
    try:
        from app import create_app, db
        from app.models import User, Warehouse, OutboundRecord, Inventory
        
        app = create_app()
        
        with app.app_context():
            # 检查User模型
            user_attrs = ['id', 'username', 'warehouse_id']  # 不是associated_warehouse_id
            for attr in user_attrs:
                if hasattr(User, attr):
                    print(f"   ✅ User.{attr}")
                else:
                    print(f"   ❌ User.{attr} 缺失")
            
            # 检查Warehouse模型
            warehouse_attrs = ['id', 'warehouse_code', 'warehouse_name']  # 不是name
            for attr in warehouse_attrs:
                if hasattr(Warehouse, attr):
                    print(f"   ✅ Warehouse.{attr}")
                else:
                    print(f"   ❌ Warehouse.{attr} 缺失")
            
            # 检查OutboundRecord模型
            outbound_attrs = ['id', 'identification_code', 'export_mode']  # 不是exit_mode
            for attr in outbound_attrs:
                if hasattr(OutboundRecord, attr):
                    print(f"   ✅ OutboundRecord.{attr}")
                else:
                    print(f"   ❌ OutboundRecord.{attr} 缺失")
                    
    except Exception as e:
        print(f"   ❌ 模型检查失败: {e}")

def main():
    """主函数"""
    print("🔍 Internal Server Error 诊断")
    print("=" * 50)
    
    # 检查导入
    diagnose_import_errors()
    
    # 检查数据库
    diagnose_database_connection()
    
    # 检查模型
    diagnose_model_attributes()
    
    print("\n" + "=" * 50)
    print("📋 诊断完成")
    print("\n💡 修复建议:")
    print("1. 如有导入错误，检查依赖包安装")
    print("2. 如有数据库错误，执行 database_field_fix.sql")
    print("3. 如有模型错误，检查 app/models.py 文件")
    print("4. 使用 python simple_start.py 启动简化版本")

if __name__ == "__main__":
    main()
