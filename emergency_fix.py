#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
紧急修复Internal Server Error问题
解决识别编码重复插入和模型属性错误
"""

import os
import sys
from datetime import datetime
import traceback

def fix_model_attributes():
    """修复模型属性错误"""
    print("🔧 修复模型属性错误...")
    
    # 读取models.py文件
    models_path = 'app/models.py'
    try:
        with open(models_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 修复常见的属性错误
        fixes = [
            # 修复exit_mode -> export_mode
            ("record.exit_mode", "record.export_mode"),
            ("'exit_mode'", "'export_mode'"),
            (".exit_mode", ".export_mode"),
            
            # 修复inventory_type字段（如果不存在则添加）
            # 这个需要在OutboundRecord类中检查
        ]
        
        original_content = content
        for old, new in fixes:
            content = content.replace(old, new)
        
        if content != original_content:
            # 备份原文件
            backup_path = f"{models_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(original_content)
            
            # 写入修复后的内容
            with open(models_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ 已修复模型属性错误，备份文件: {backup_path}")
        else:
            print("ℹ️  模型文件无需修复")
            
    except Exception as e:
        print(f"❌ 修复模型属性失败: {e}")

def fix_routes_errors():
    """修复路由中的常见错误"""
    print("🔧 修复路由错误...")
    
    routes_path = 'app/main/routes.py'
    try:
        with open(routes_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 修复常见的属性错误
        fixes = [
            # 修复exit_mode -> export_mode
            (".exit_mode", ".export_mode"),
            ("'exit_mode'", "'export_mode'"),
            ("exit_mode=", "export_mode="),
            
            # 修复warehouse.name -> warehouse.warehouse_name
            ("warehouse.name", "warehouse.warehouse_name"),
            
            # 修复user.associated_warehouse_id -> user.warehouse_id
            ("user.associated_warehouse_id", "user.warehouse_id"),
            
            # 修复inbound_time属性错误
            ("record.inbound_time", "record.outbound_time"),
        ]
        
        original_content = content
        for old, new in fixes:
            content = content.replace(old, new)
        
        if content != original_content:
            # 备份原文件
            backup_path = f"{routes_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(original_content)
            
            # 写入修复后的内容
            with open(routes_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ 已修复路由错误，备份文件: {backup_path}")
        else:
            print("ℹ️  路由文件无需修复")
            
    except Exception as e:
        print(f"❌ 修复路由错误失败: {e}")

def create_database_fix_script():
    """创建数据库修复脚本"""
    print("📝 创建数据库修复脚本...")
    
    sql_script = '''-- 紧急修复数据库约束和字段问题
-- 执行前请备份数据库！

-- 1. 检查当前约束
SELECT 
    CONSTRAINT_NAME,
    COLUMN_NAME,
    CONSTRAINT_TYPE
FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
WHERE TABLE_NAME = 'outbound_record' 
    AND TABLE_SCHEMA = DATABASE()
    AND COLUMN_NAME = 'identification_code';

-- 2. 删除错误的唯一约束（如果存在）
SET @constraint_name = (
    SELECT CONSTRAINT_NAME 
    FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
    WHERE TABLE_NAME = 'outbound_record' 
        AND TABLE_SCHEMA = DATABASE()
        AND COLUMN_NAME = 'identification_code'
        AND CONSTRAINT_NAME LIKE '%identification%'
        AND CONSTRAINT_NAME != 'PRIMARY'
    LIMIT 1
);

SET @sql = CASE 
    WHEN @constraint_name IS NOT NULL THEN 
        CONCAT('ALTER TABLE outbound_record DROP INDEX ', @constraint_name)
    ELSE 
        'SELECT "没有找到需要删除的约束" as message'
END;

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 3. 修复batch_sequence，确保同一识别编码的记录有正确的批次序号
UPDATE outbound_record o1
JOIN (
    SELECT 
        id,
        identification_code,
        ROW_NUMBER() OVER (PARTITION BY identification_code ORDER BY created_at) AS new_batch_sequence
    FROM outbound_record 
    WHERE identification_code IS NOT NULL
) o2 ON o1.id = o2.id
SET o1.batch_sequence = o2.new_batch_sequence;

-- 4. 创建正确的复合唯一约束（可选）
-- ALTER TABLE outbound_record 
-- ADD CONSTRAINT uk_outbound_identification_batch 
-- UNIQUE (identification_code, batch_sequence);

-- 5. 检查inventory表是否缺少inventory_type字段
SELECT COUNT(*) as has_inventory_type
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'inventory' 
    AND TABLE_SCHEMA = DATABASE()
    AND COLUMN_NAME = 'inventory_type';

-- 6. 如果缺少inventory_type字段，添加它
-- ALTER TABLE inventory ADD COLUMN inventory_type VARCHAR(20) DEFAULT 'normal' COMMENT '库存类型';

-- 7. 验证修复结果
SELECT '=== 修复验证 ===' as status;

-- 检查重复的识别编码
SELECT 
    identification_code,
    COUNT(*) as count,
    GROUP_CONCAT(batch_sequence ORDER BY batch_sequence) as batch_sequences
FROM outbound_record 
WHERE identification_code IS NOT NULL
GROUP BY identification_code 
HAVING COUNT(*) > 1
LIMIT 5;

-- 检查是否还有重复的 (identification_code, batch_sequence) 组合
SELECT 
    identification_code,
    batch_sequence,
    COUNT(*) as count
FROM outbound_record 
GROUP BY identification_code, batch_sequence
HAVING COUNT(*) > 1;
'''
    
    with open('database_emergency_fix.sql', 'w', encoding='utf-8') as f:
        f.write(sql_script)
    
    print("✅ 已创建数据库修复脚本: database_emergency_fix.sql")

def create_safe_startup_script():
    """创建安全启动脚本"""
    print("🚀 创建安全启动脚本...")
    
    startup_script = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全启动脚本 - 避免Internal Server Error
"""

import os
import sys
from flask import Flask
from app import create_app, db

def safe_create_app():
    """安全创建应用"""
    try:
        # 设置环境变量
        os.environ['FLASK_ENV'] = 'development'
        os.environ['FLASK_DEBUG'] = '1'
        
        # 创建应用
        app = create_app()
        
        # 配置错误处理
        @app.errorhandler(500)
        def handle_internal_error(error):
            """处理500错误"""
            import traceback
            error_info = traceback.format_exc()
            
            # 记录错误到日志
            app.logger.error(f"Internal Server Error: {error_info}")
            
            # 返回友好的错误页面
            return f"""
            <h1>系统维护中</h1>
            <p>系统正在进行维护，请稍后再试。</p>
            <details>
                <summary>技术详情（仅供开发人员参考）</summary>
                <pre>{error_info}</pre>
            </details>
            <p><a href="/">返回首页</a></p>
            """, 500
        
        @app.errorhandler(Exception)
        def handle_exception(error):
            """处理所有未捕获的异常"""
            import traceback
            error_info = traceback.format_exc()
            
            app.logger.error(f"Unhandled Exception: {error_info}")
            
            return f"""
            <h1>系统错误</h1>
            <p>系统遇到了一个错误，我们正在处理中。</p>
            <details>
                <summary>错误详情</summary>
                <pre>{error_info}</pre>
            </details>
            <p><a href="/">返回首页</a></p>
            """, 500
        
        return app
        
    except Exception as e:
        print(f"❌ 创建应用失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """主函数"""
    print("🛡️  启动安全模式...")
    
    app = safe_create_app()
    if not app:
        print("❌ 应用创建失败，退出")
        return
    
    print("✅ 应用创建成功")
    print("🌐 访问地址: http://localhost:5000")
    print("🛡️  安全模式已启用，所有错误都会被捕获")
    print("=" * 50)
    
    # 启动应用
    try:
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            use_reloader=False  # 禁用重载器避免问题
        )
    except Exception as e:
        print(f"❌ 应用启动失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
'''
    
    with open('safe_start.py', 'w', encoding='utf-8') as f:
        f.write(startup_script)
    
    print("✅ 已创建安全启动脚本: safe_start.py")

def create_quick_test_script():
    """创建快速测试脚本"""
    print("🧪 创建快速测试脚本...")
    
    test_script = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试脚本 - 检查系统状态
"""

def test_imports():
    """测试导入"""
    print("🔍 测试模块导入...")
    
    try:
        from app import create_app, db
        print("✅ 核心模块导入成功")
    except Exception as e:
        print(f"❌ 核心模块导入失败: {e}")
        return False
    
    try:
        from app.models import User, Warehouse, OutboundRecord, Inventory
        print("✅ 模型导入成功")
    except Exception as e:
        print(f"❌ 模型导入失败: {e}")
        return False
    
    return True

def test_app_creation():
    """测试应用创建"""
    print("🔍 测试应用创建...")
    
    try:
        from app import create_app
        app = create_app()
        print("✅ 应用创建成功")
        return True
    except Exception as e:
        print(f"❌ 应用创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_connection():
    """测试数据库连接"""
    print("🔍 测试数据库连接...")
    
    try:
        from app import create_app, db
        app = create_app()
        
        with app.app_context():
            # 尝试执行简单查询
            result = db.engine.execute("SELECT 1").fetchone()
            print("✅ 数据库连接成功")
            return True
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False

def main():
    """主函数"""
    print("🧪 系统快速诊断")
    print("=" * 40)
    
    tests = [
        ("模块导入", test_imports),
        ("应用创建", test_app_creation),
        ("数据库连接", test_database_connection),
    ]
    
    passed = 0
    total = len(tests)
    
    for name, test_func in tests:
        print(f"\\n📋 {name}测试:")
        if test_func():
            passed += 1
    
    print("\\n" + "=" * 40)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 系统状态良好，可以正常启动")
    else:
        print("⚠️  系统存在问题，需要修复")
        print("💡 建议:")
        print("   1. 运行 python emergency_fix.py 进行修复")
        print("   2. 检查数据库连接配置")
        print("   3. 使用 python safe_start.py 安全启动")

if __name__ == '__main__':
    main()
'''
    
    with open('quick_test.py', 'w', encoding='utf-8') as f:
        f.write(test_script)
    
    print("✅ 已创建快速测试脚本: quick_test.py")

def main():
    """主函数"""
    print("🚨 紧急修复Internal Server Error")
    print("=" * 60)
    print("问题分析:")
    print("1. 识别编码重复插入 - 违反唯一性约束")
    print("2. 模型属性错误 - exit_mode, inventory_type等")
    print("3. 数据库字段不匹配")
    print("4. 事务管理问题")
    print("=" * 60)
    
    try:
        # 1. 修复模型属性错误
        fix_model_attributes()
        
        # 2. 修复路由错误
        fix_routes_errors()
        
        # 3. 创建数据库修复脚本
        create_database_fix_script()
        
        # 4. 创建安全启动脚本
        create_safe_startup_script()
        
        # 5. 创建快速测试脚本
        create_quick_test_script()
        
        print("\n🎉 紧急修复完成！")
        print("\n📋 下一步操作:")
        print("1. 运行测试: python quick_test.py")
        print("2. 修复数据库: 在MySQL中执行 database_emergency_fix.sql")
        print("3. 安全启动: python safe_start.py")
        print("\n⚠️  重要提醒:")
        print("- 执行数据库脚本前请备份数据库")
        print("- 如果问题持续，请检查具体的错误日志")
        print("- 建议在测试环境先验证修复效果")
        
    except Exception as e:
        print(f"❌ 紧急修复失败: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
