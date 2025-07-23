#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务器配置修复脚本 - 解决Internal Server Error的根本问题
"""

import os
import sys
import shutil
from datetime import datetime

def create_minimal_app_config():
    """创建最小化的应用配置"""
    print("🔧 创建最小化应用配置...")
    
    minimal_init = '''from flask import Flask, g, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager
import logging
import os
import time

# 创建数据库实例
db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()
login_manager = LoginManager()

def create_app(config_class=None):
    """创建最小化Flask应用"""
    app = Flask(__name__)
    
    # 使用简化配置
    if config_class is None:
        from config import Config
        config_class = Config
    
    app.config.from_object(config_class)
    
    # 简化数据库配置
    if 'mysql' in app.config['SQLALCHEMY_DATABASE_URI'].lower():
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_pre_ping': True,
            'pool_recycle': 300,
            'pool_timeout': 20,
            'max_overflow': 10,
            'pool_size': 10,
            'echo': False
        }
    
    # 初始化扩展（移除复杂的后台初始化）
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '请先登录以访问此页面。'
    
    # 注册蓝图（只注册必要的）
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)
    
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    # 移除复杂的缓存和优化系统初始化
    
    # 简化的错误处理
    @app.errorhandler(500)
    def handle_internal_error(error):
        """处理500错误"""
        import traceback
        error_info = traceback.format_exc()
        app.logger.error(f"Internal Server Error: {error_info}")
        
        return f"""
        <h1>系统维护中</h1>
        <p>系统正在进行维护，请稍后再试。</p>
        <details>
            <summary>错误详情</summary>
            <pre>{error_info}</pre>
        </details>
        <p><a href="/">返回首页</a></p>
        """, 500
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        """处理所有异常"""
        import traceback
        error_info = traceback.format_exc()
        app.logger.error(f"Unhandled Exception: {error_info}")
        
        return f"""
        <h1>系统异常</h1>
        <p>系统遇到了一个错误。</p>
        <details>
            <summary>错误详情</summary>
            <pre>{error_info}</pre>
        </details>
        <p><a href="/">返回首页</a></p>
        """, 500
    
    # 简化的数据库初始化
    with app.app_context():
        try:
            db.create_all()
            app.logger.info('数据库初始化完成')
        except Exception as e:
            app.logger.error(f'数据库初始化失败: {e}')
    
    # 用户加载器
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))
    
    # 模板上下文处理器
    @app.context_processor
    def inject_csrf_token():
        from flask_wtf.csrf import generate_csrf
        return dict(csrf_token=generate_csrf)
    
    return app

from app import models
'''
    
    # 备份原文件
    original_init = 'app/__init__.py'
    if os.path.exists(original_init):
        backup_path = f"{original_init}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(original_init, backup_path)
        print(f"   ✅ 已备份原配置文件: {backup_path}")
    
    # 写入最小化配置
    with open(original_init, 'w', encoding='utf-8') as f:
        f.write(minimal_init)
    
    print("   ✅ 已创建最小化应用配置")

def fix_model_attributes():
    """修复模型属性错误"""
    print("🔧 修复模型属性错误...")
    
    # 检查models.py文件
    models_path = 'app/models.py'
    if not os.path.exists(models_path):
        print("   ❌ models.py文件不存在")
        return
    
    try:
        with open(models_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 修复常见的属性错误
        fixes = [
            # 修复exit_mode -> export_mode
            ("exit_mode", "export_mode"),
            # 修复warehouse.name -> warehouse.warehouse_name
            ("warehouse.name", "warehouse.warehouse_name"),
            # 修复user.associated_warehouse_id -> user.warehouse_id
            ("associated_warehouse_id", "warehouse_id"),
        ]
        
        original_content = content
        for old, new in fixes:
            content = content.replace(old, new)
        
        if content != original_content:
            # 备份原文件
            backup_path = f"{models_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(models_path, backup_path)
            
            # 写入修复后的内容
            with open(models_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"   ✅ 已修复模型属性错误，备份: {backup_path}")
        else:
            print("   ℹ️  模型文件无需修复")
            
    except Exception as e:
        print(f"   ❌ 修复模型属性失败: {e}")

def create_database_migration_script():
    """创建数据库迁移脚本"""
    print("📝 创建数据库迁移脚本...")
    
    migration_script = '''-- 数据库字段修复脚本
-- 执行前请备份数据库！

-- 1. 检查并添加缺失的字段
-- 检查inventory表是否缺少inventory_type字段
SELECT COUNT(*) as has_inventory_type
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'inventory' 
    AND TABLE_SCHEMA = DATABASE()
    AND COLUMN_NAME = 'inventory_type';

-- 如果缺少inventory_type字段，添加它
-- ALTER TABLE inventory ADD COLUMN inventory_type VARCHAR(20) DEFAULT 'normal' COMMENT '库存类型';

-- 2. 检查outbound_record表的字段
-- 确保export_mode字段存在（而不是exit_mode）
SELECT COUNT(*) as has_export_mode
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'outbound_record' 
    AND TABLE_SCHEMA = DATABASE()
    AND COLUMN_NAME = 'export_mode';

-- 3. 检查warehouse表的字段
-- 确保warehouse_name字段存在（而不是name）
SELECT COUNT(*) as has_warehouse_name
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'warehouse' 
    AND TABLE_SCHEMA = DATABASE()
    AND COLUMN_NAME = 'warehouse_name';

-- 4. 检查user表的字段
-- 确保warehouse_id字段存在（而不是associated_warehouse_id）
SELECT COUNT(*) as has_warehouse_id
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'user' 
    AND TABLE_SCHEMA = DATABASE()
    AND COLUMN_NAME = 'warehouse_id';

-- 5. 修复重复的唯一约束问题
-- 检查当前的唯一约束
SELECT 
    CONSTRAINT_NAME,
    COLUMN_NAME
FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
WHERE TABLE_NAME = 'outbound_record' 
    AND TABLE_SCHEMA = DATABASE()
    AND CONSTRAINT_NAME LIKE '%identification%';

-- 如果有错误的唯一约束，删除它们
-- DROP INDEX uk_outbound_identification_code ON outbound_record;

-- 创建正确的复合唯一约束（支持分批出货）
-- ALTER TABLE outbound_record 
-- ADD CONSTRAINT uk_outbound_identification_batch 
-- UNIQUE (identification_code, batch_sequence);

-- 6. 验证修复结果
SELECT '=== 数据库字段检查完成 ===' as status;
'''
    
    with open('database_field_fix.sql', 'w', encoding='utf-8') as f:
        f.write(migration_script)
    
    print("   ✅ 已创建数据库迁移脚本: database_field_fix.sql")

def create_simple_startup_script():
    """创建简单的启动脚本"""
    print("🚀 创建简单启动脚本...")
    
    startup_script = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的应用启动脚本 - 避免复杂的初始化导致错误
"""

import os
import sys
from app import create_app, db

# 设置环境变量
os.environ['FLASK_ENV'] = 'development'
os.environ['FLASK_DEBUG'] = '1'

def main():
    """主函数"""
    print("🚀 启动仓储管理系统（简化模式）")
    print("📍 访问地址: http://127.0.0.1:5000")
    print("⚠️  如遇到错误，请检查日志文件")
    print("-" * 50)
    
    try:
        # 创建应用
        app = create_app()
        
        # 简单的健康检查
        with app.app_context():
            try:
                # 测试数据库连接
                db.engine.execute("SELECT 1").fetchone()
                print("✅ 数据库连接正常")
            except Exception as e:
                print(f"⚠️  数据库连接异常: {e}")
        
        # 启动应用
        app.run(
            host='127.0.0.1',
            port=5000,
            debug=True,
            use_reloader=False,  # 禁用重载器避免问题
            threaded=True
        )
        
    except Exception as e:
        print(f"❌ 应用启动失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
'''
    
    with open('simple_start.py', 'w', encoding='utf-8') as f:
        f.write(startup_script)
    
    print("   ✅ 已创建简单启动脚本: simple_start.py")

def create_error_diagnosis_script():
    """创建错误诊断脚本"""
    print("🔍 创建错误诊断脚本...")
    
    diagnosis_script = '''#!/usr/bin/env python3
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
    print("\\n🗄️ 检查数据库连接...")
    
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
    print("\\n🏗️ 检查模型属性...")
    
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
    
    print("\\n" + "=" * 50)
    print("📋 诊断完成")
    print("\\n💡 修复建议:")
    print("1. 如有导入错误，检查依赖包安装")
    print("2. 如有数据库错误，执行 database_field_fix.sql")
    print("3. 如有模型错误，检查 app/models.py 文件")
    print("4. 使用 python simple_start.py 启动简化版本")

if __name__ == "__main__":
    main()
'''
    
    with open('error_diagnosis.py', 'w', encoding='utf-8') as f:
        f.write(diagnosis_script)
    
    print("   ✅ 已创建错误诊断脚本: error_diagnosis.py")

def main():
    """主函数"""
    print("🛠️ 服务器配置修复")
    print("=" * 60)
    print("问题分析:")
    print("1. 复杂的应用初始化导致启动错误")
    print("2. 模型属性名称不匹配")
    print("3. 数据库字段缺失或名称错误")
    print("4. 过多的后台线程和缓存系统")
    print("=" * 60)
    
    try:
        # 1. 创建最小化应用配置
        create_minimal_app_config()
        
        # 2. 修复模型属性错误
        fix_model_attributes()
        
        # 3. 创建数据库迁移脚本
        create_database_migration_script()
        
        # 4. 创建简单启动脚本
        create_simple_startup_script()
        
        # 5. 创建错误诊断脚本
        create_error_diagnosis_script()
        
        print("\\n🎉 服务器配置修复完成！")
        print("\\n📋 下一步操作:")
        print("1. 运行诊断: python error_diagnosis.py")
        print("2. 执行数据库修复: database_field_fix.sql")
        print("3. 启动简化版本: python simple_start.py")
        print("4. 如果正常，再逐步恢复功能")
        
        print("\\n⚠️  重要提醒:")
        print("- 已备份原配置文件")
        print("- 数据库操作前请备份")
        print("- 简化版本移除了复杂的缓存和优化系统")
        print("- 如需恢复原功能，可使用备份文件")
        
    except Exception as e:
        print(f"❌ 配置修复失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
