#!/usr/bin/env python3
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
        print(f"\n📋 {name}测试:")
        if test_func():
            passed += 1
    
    print("\n" + "=" * 40)
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
