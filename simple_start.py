#!/usr/bin/env python3
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
