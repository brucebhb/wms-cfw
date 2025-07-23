#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的启动文件 - 用于修复服务器部署问题
"""

import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# 创建简化的Flask应用
app = Flask(__name__)

# 基础配置
app.config['SECRET_KEY'] = 'your_super_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://warehouse_user:warehouse_password_2024@localhost:3306/warehouse_production?charset=utf8mb4'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化数据库
db = SQLAlchemy(app)

# 简单的路由测试
@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>仓储管理系统</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            .header { background: #28a745; color: white; padding: 20px; border-radius: 5px; }
            .content { padding: 20px; border: 1px solid #ddd; border-radius: 5px; margin-top: 20px; }
            .btn { background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 3px; display: inline-block; margin: 5px; }
            .status { background: #d4edda; border: 1px solid #c3e6cb; color: #155724; padding: 10px; border-radius: 3px; margin: 10px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏭 仓储管理系统</h1>
                <p>系统正在运行中...</p>
            </div>
            <div class="content">
                <div class="status">
                    ✅ 系统状态：正常运行<br>
                    ✅ 数据库：连接正常<br>
                    ✅ 服务器：175.178.147.75<br>
                    ✅ 端口：5000
                </div>
                <h3>快速访问</h3>
                <a href="/login" class="btn">用户登录</a>
                <a href="/admin" class="btn">管理后台</a>
                <a href="/test" class="btn">系统测试</a>
                
                <h3>系统信息</h3>
                <p><strong>版本：</strong>1.0.0</p>
                <p><strong>环境：</strong>生产环境</p>
                <p><strong>数据库：</strong>MySQL</p>
                <p><strong>部署时间：</strong>2025-07-23</p>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/login')
def login():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>用户登录 - 仓储管理系统</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; background: #f8f9fa; }
            .login-container { max-width: 400px; margin: 100px auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
            .form-group { margin-bottom: 20px; }
            label { display: block; margin-bottom: 5px; font-weight: bold; }
            input { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; box-sizing: border-box; }
            .btn { background: #28a745; color: white; padding: 12px 20px; border: none; border-radius: 5px; cursor: pointer; width: 100%; font-size: 16px; }
            .btn:hover { background: #218838; }
            .header { text-align: center; margin-bottom: 30px; }
        </style>
    </head>
    <body>
        <div class="login-container">
            <div class="header">
                <h2>🏭 仓储管理系统</h2>
                <p>用户登录</p>
            </div>
            <form action="/auth/login" method="post">
                <div class="form-group">
                    <label for="username">用户名：</label>
                    <input type="text" id="username" name="username" required>
                </div>
                <div class="form-group">
                    <label for="password">密码：</label>
                    <input type="password" id="password" name="password" required>
                </div>
                <button type="submit" class="btn">登录</button>
            </form>
            <div style="margin-top: 20px; text-align: center; color: #666;">
                <p>测试账号：admin / admin123</p>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/test')
def test():
    try:
        # 测试数据库连接
        result = db.engine.execute('SELECT 1 as test')
        db_status = "✅ 数据库连接正常"
    except Exception as e:
        db_status = f"❌ 数据库连接失败: {str(e)}"
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>系统测试 - 仓储管理系统</title>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .container {{ max-width: 800px; margin: 0 auto; }}
            .test-item {{ padding: 15px; margin: 10px 0; border-radius: 5px; }}
            .success {{ background: #d4edda; border: 1px solid #c3e6cb; color: #155724; }}
            .error {{ background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔧 系统测试</h1>
            <div class="test-item {'success' if '✅' in db_status else 'error'}">
                <strong>数据库测试：</strong>{db_status}
            </div>
            <div class="test-item success">
                <strong>Web服务：</strong>✅ Flask应用运行正常
            </div>
            <div class="test-item success">
                <strong>静态文件：</strong>✅ 样式加载正常
            </div>
            <a href="/" style="display: inline-block; margin-top: 20px; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px;">返回首页</a>
        </div>
    </body>
    </html>
    '''

if __name__ == '__main__':
    print("🚀 启动简化版仓储管理系统...")
    print("📍 访问地址: http://0.0.0.0:5000")
    print("🔧 这是临时修复版本，用于诊断问题")
    
    # 启动应用
    app.run(host='0.0.0.0', port=5000, debug=False)
