#!/usr/bin/env python3
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
