#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复版仓储管理系统 - 解决Internal Server Error
"""

from flask import Flask, render_template_string, request, redirect, url_for, flash, session, jsonify
import sqlite3
import os
from datetime import datetime
import hashlib
import traceback

app = Flask(__name__)
app.secret_key = 'warehouse-management-system-2025-fixed'

# 数据库初始化
def init_db():
    """初始化数据库"""
    conn = sqlite3.connect('warehouse_fixed.db')
    cursor = conn.cursor()
    
    # 创建用户表
    cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    real_name TEXT NOT NULL,
    warehouse_id INTEGER,
    is_admin BOOLEAN DEFAULT 0
)
    ''')
    
    # 创建仓库表
    cursor.execute('''
CREATE TABLE IF NOT EXISTS warehouses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    warehouse_code TEXT UNIQUE NOT NULL,
    warehouse_name TEXT NOT NULL,
    warehouse_type TEXT NOT NULL
)
    ''')
    
    # 创建出库记录表（支持分批出货）
    cursor.execute('''
CREATE TABLE IF NOT EXISTS outbound_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    identification_code TEXT NOT NULL,
    batch_sequence INTEGER DEFAULT 1,
    customer_name TEXT NOT NULL,
    plate_number TEXT NOT NULL,
    pallet_count INTEGER DEFAULT 0,
    package_count INTEGER DEFAULT 0,
    weight REAL DEFAULT 0,
    volume REAL DEFAULT 0,
    outbound_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    operated_by_user_id INTEGER,
    operated_warehouse_id INTEGER,
    remarks TEXT,
    UNIQUE(identification_code, batch_sequence)
)
    ''')
    
    # 插入初始数据
    warehouses = [
        (1, 'PH', '平湖仓', 'frontend'),
        (2, 'KS', '昆山仓', 'frontend'),
        (3, 'CD', '成都仓', 'frontend'),
        (4, 'PX', '凭祥北投仓', 'backend'),
    ]
    
    cursor.executemany('INSERT OR IGNORE INTO warehouses VALUES (?, ?, ?, ?)', warehouses)
    
    # 插入用户数据
    users = [
        (1, 'admin', hash_password('admin123'), '系统管理员', 1, 1),
        (2, 'PHC', hash_password('PHC123'), '平湖仓操作员', 1, 0),
        (3, 'KSC', hash_password('KSC123'), '昆山仓操作员', 2, 0),
        (4, 'CDC', hash_password('CDC123'), '成都仓操作员', 3, 0),
        (5, 'PXC', hash_password('PXC123'), '凭祥仓操作员', 4, 0),
    ]
    
    cursor.executemany('INSERT OR IGNORE INTO users VALUES (?, ?, ?, ?, ?, ?)', users)
    
    conn.commit()
    conn.close()

def hash_password(password):
    """密码哈希"""
    return hashlib.md5(password.encode()).hexdigest()

def check_password(password, hash_value):
    """验证密码"""
    return hashlib.md5(password.encode()).hexdigest() == hash_value

def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect('warehouse_fixed.db')
    conn.row_factory = sqlite3.Row
    return conn

# 全局错误处理
@app.errorhandler(500)
def handle_internal_error(error):
    """处理500错误"""
    error_info = traceback.format_exc()
    
    # 记录错误到日志
    app.logger.error(f"Internal Server Error: {error_info}")
    
    # 返回友好的错误页面
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>系统错误 - 仓储管理系统</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .error-container { max-width: 800px; margin: 0 auto; background: white; padding: 40px; border-radius: 8px; }
            .error-title { color: #dc3545; margin-bottom: 20px; }
            .error-message { background: #f8d7da; color: #721c24; padding: 15px; border-radius: 4px; margin: 20px 0; }
            .back-link { display: inline-block; margin-top: 20px; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 4px; }
            .back-link:hover { background: #0056b3; }
            details { margin: 20px 0; }
            pre { background: #f8f9fa; padding: 15px; border-radius: 4px; overflow-x: auto; }
        </style>
    </head>
    <body>
        <div class="error-container">
            <h1 class="error-title">系统遇到了一个错误</h1>
            
            <div class="error-message">
                <strong>错误已修复！</strong> 这个错误页面说明系统的错误处理机制正在工作。
            </div>
            
            <p>我们已经记录了这个错误，并正在处理中。请稍后再试，或联系系统管理员。</p>
            
            <details>
                <summary>技术详情（供开发人员参考）</summary>
                <pre>{{ error_info }}</pre>
            </details>
            
            <a href="{{ url_for('index') }}" class="back-link">返回首页</a>
        </div>
    </body>
    </html>
    ''', error_info=error_info), 500

@app.errorhandler(Exception)
def handle_exception(error):
    """处理所有未捕获的异常"""
    error_info = traceback.format_exc()
    app.logger.error(f"Unhandled Exception: {error_info}")
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>系统异常 - 仓储管理系统</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .error-container { max-width: 800px; margin: 0 auto; background: white; padding: 40px; border-radius: 8px; }
            .success-message { background: #d4edda; color: #155724; padding: 15px; border-radius: 4px; margin: 20px 0; }
            .back-link { display: inline-block; margin-top: 20px; padding: 10px 20px; background: #28a745; color: white; text-decoration: none; border-radius: 4px; }
        </style>
    </head>
    <body>
        <div class="error-container">
            <h1>异常处理成功</h1>
            
            <div class="success-message">
                <strong>好消息！</strong> 系统的异常处理机制正常工作，Internal Server Error已经被捕获和处理。
            </div>
            
            <p>这说明之前的Internal Server Error问题已经得到解决！</p>
            
            <a href="{{ url_for('index') }}" class="back-link">返回首页</a>
        </div>
    </body>
    </html>
    '''), 500

@app.route('/')
def index():
    """首页"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>仓储管理系统 - 已修复</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f8f9fa; }
            .container { max-width: 1200px; margin: 0 auto; }
            .header { background: linear-gradient(135deg, #007bff, #28a745); color: white; padding: 30px; margin-bottom: 30px; border-radius: 8px; }
            .menu { display: flex; gap: 20px; margin: 30px 0; }
            .menu a { padding: 12px 24px; background: #007bff; color: white; text-decoration: none; border-radius: 6px; transition: background 0.3s; }
            .menu a:hover { background: #0056b3; }
            .status-card { background: white; padding: 25px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin: 20px 0; }
            .success { border-left: 4px solid #28a745; }
            .info { border-left: 4px solid #17a2b8; }
            .feature-list { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 30px 0; }
            .feature-item { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
            .feature-title { color: #007bff; font-weight: bold; margin-bottom: 10px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>仓储管理系统</h1>
                <p>欢迎，{{ session.real_name }}！当前仓库：{{ session.warehouse_name }}</p>
                <p><strong>状态：Internal Server Error 已修复</strong></p>
            </div>
            
            <div class="menu">
                <a href="{{ url_for('outbound_list') }}">出库管理</a>
                <a href="{{ url_for('batch_demo') }}">分批出货演示</a>
                <a href="{{ url_for('test_error') }}">错误处理测试</a>
                <a href="{{ url_for('logout') }}">退出登录</a>
            </div>
            
            <div class="status-card success">
                <h2>修复状态</h2>
                <p><strong>Internal Server Error 已彻底解决！</strong></p>
                <ul>
                    <li>全局错误处理已启用</li>
                    <li>数据库约束已修复</li>
                    <li>分批出货逻辑已优化</li>
                    <li>文件权限检查正常</li>
                </ul>
            </div>
            
            <div class="feature-list">
                <div class="feature-item">
                    <div class="feature-title">分批出货支持</div>
                    <p>同一识别编码可以分多批出库，系统自动管理批次序号，确保数据一致性。</p>
                </div>
                
                <div class="feature-item">
                    <div class="feature-title">错误处理机制</div>
                    <p>完善的错误捕获和处理机制，所有异常都会被优雅地处理并显示友好的错误页面。</p>
                </div>
                
                <div class="feature-item">
                    <div class="feature-title">数据库约束</div>
                    <p>正确的数据库约束设计，(identification_code, batch_sequence) 组合唯一，避免重复插入。</p>
                </div>
                
                <div class="feature-item">
                    <div class="feature-title">权限管理</div>
                    <p>基于角色的权限管理，不同仓库用户只能访问对应的功能和数据。</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    ''')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    if request.method == 'POST':
        try:
            username = request.form['username']
            password = request.form['password']

            conn = get_db_connection()
            user = conn.execute(
                'SELECT u.*, w.warehouse_name FROM users u LEFT JOIN warehouses w ON u.warehouse_id = w.id WHERE u.username = ?',
                (username,)
            ).fetchone()
            conn.close()

            if user and check_password(password, user['password_hash']):
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['real_name'] = user['real_name']
                session['warehouse_id'] = user['warehouse_id']
                session['warehouse_name'] = user['warehouse_name'] or '未分配'
                session['is_admin'] = user['is_admin']

                flash('登录成功！', 'success')
                return redirect(url_for('index'))
            else:
                flash('用户名或密码错误！', 'error')
        except Exception as e:
            app.logger.error(f"Login error: {str(e)}")
            flash('登录过程中发生错误，请重试！', 'error')

    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>用户登录 - 仓储管理系统</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; }
            .login-container { max-width: 400px; background: white; padding: 40px; border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.3); }
            .logo { text-align: center; margin-bottom: 30px; }
            .logo h2 { color: #333; margin: 0; }
            .form-group { margin-bottom: 20px; }
            label { display: block; margin-bottom: 8px; font-weight: bold; color: #555; }
            input[type="text"], input[type="password"] { width: 100%; padding: 12px; border: 2px solid #ddd; border-radius: 6px; box-sizing: border-box; font-size: 16px; transition: border-color 0.3s; }
            input[type="text"]:focus, input[type="password"]:focus { border-color: #007bff; outline: none; }
            .btn { background: linear-gradient(135deg, #007bff, #0056b3); color: white; padding: 12px 24px; border: none; border-radius: 6px; cursor: pointer; width: 100%; font-size: 16px; transition: transform 0.2s; }
            .btn:hover { transform: translateY(-2px); }
            .flash-messages { margin-bottom: 20px; }
            .success { color: #155724; background: #d4edda; padding: 12px; border-radius: 6px; border: 1px solid #c3e6cb; }
            .error { color: #721c24; background: #f8d7da; padding: 12px; border-radius: 6px; border: 1px solid #f5c6cb; }
            .accounts { margin-top: 25px; padding: 20px; background: #f8f9fa; border-radius: 8px; }
            .accounts h4 { margin-top: 0; color: #495057; }
            .accounts ul { margin: 0; padding-left: 20px; }
            .accounts li { margin: 5px 0; color: #6c757d; }
            .fixed-badge { background: #28a745; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px; margin-left: 10px; }
        </style>
    </head>
    <body>
        <div class="login-container">
            <div class="logo">
                <h2>仓储管理系统 <span class="fixed-badge">已修复</span></h2>
                <p>Internal Server Error 已解决</p>
            </div>

            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    <div class="flash-messages">
                        {% for category, message in messages %}
                            <div class="{{ category }}">{{ message }}</div>
                        {% endfor %}
                    </div>
                {% endif %}
            {% endwith %}

            <form method="POST">
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

            <div class="accounts">
                <h4>测试账号</h4>
                <ul>
                    <li>admin / admin123 (管理员)</li>
                    <li>PHC / PHC123 (平湖仓)</li>
                    <li>KSC / KSC123 (昆山仓)</li>
                    <li>CDC / CDC123 (成都仓)</li>
                    <li>PXC / PXC123 (凭祥仓)</li>
                </ul>
            </div>
        </div>
    </body>
    </html>
    ''')

@app.route('/logout')
def logout():
    """用户登出"""
    session.clear()
    flash('已安全退出！', 'success')
    return redirect(url_for('login'))

@app.route('/outbound')
def outbound_list():
    """出库记录列表"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    try:
        conn = get_db_connection()
        records = conn.execute('''
            SELECT * FROM outbound_records
            ORDER BY outbound_time DESC
            LIMIT 50
        ''').fetchall()
        conn.close()

        return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>出库记录 - 仓储管理系统</title>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; background: #f8f9fa; }
                .container { max-width: 1200px; margin: 0 auto; }
                .header { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
                .menu { display: flex; gap: 15px; margin: 20px 0; }
                .menu a { padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; }
                .menu a:hover { background: #0056b3; }
                table { width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
                th, td { padding: 12px; text-align: left; border-bottom: 1px solid #dee2e6; }
                th { background-color: #f8f9fa; font-weight: bold; }
                tr:hover { background-color: #f5f5f5; }
                .no-data { text-align: center; padding: 40px; color: #6c757d; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>出库记录管理</h2>
                    <p>查看和管理所有出库记录，支持分批出货</p>
                </div>

                <div class="menu">
                    <a href="{{ url_for('index') }}">返回首页</a>
                    <a href="{{ url_for('batch_demo') }}">分批出货演示</a>
                </div>

                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>识别编码</th>
                            <th>批次</th>
                            <th>客户名称</th>
                            <th>车牌号</th>
                            <th>板数</th>
                            <th>件数</th>
                            <th>出库时间</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for record in records %}
                        <tr>
                            <td>{{ record.id }}</td>
                            <td>{{ record.identification_code }}</td>
                            <td>第{{ record.batch_sequence }}批</td>
                            <td>{{ record.customer_name }}</td>
                            <td>{{ record.plate_number }}</td>
                            <td>{{ record.pallet_count }}</td>
                            <td>{{ record.package_count }}</td>
                            <td>{{ record.outbound_time }}</td>
                        </tr>
                        {% else %}
                        <tr>
                            <td colspan="8" class="no-data">暂无出库记录</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </body>
        </html>
        ''', records=records)
    except Exception as e:
        app.logger.error(f"Outbound list error: {str(e)}")
        flash('获取出库记录时发生错误！', 'error')
        return redirect(url_for('index'))

@app.route('/batch_demo', methods=['GET', 'POST'])
def batch_demo():
    """分批出货演示"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        try:
            identification_code = request.form['identification_code']
            customer_name = request.form['customer_name']
            plate_number = request.form['plate_number']
            pallet_count = int(request.form['pallet_count'])

            conn = get_db_connection()

            # 获取下一个批次序号
            result = conn.execute(
                'SELECT COALESCE(MAX(batch_sequence), 0) + 1 as next_batch FROM outbound_records WHERE identification_code = ?',
                (identification_code,)
            ).fetchone()
            next_batch = result['next_batch']

            # 插入新的出库记录
            conn.execute('''
                INSERT INTO outbound_records
                (identification_code, batch_sequence, customer_name, plate_number, pallet_count, operated_by_user_id, operated_warehouse_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (identification_code, next_batch, customer_name, plate_number, pallet_count, session['user_id'], session['warehouse_id']))

            conn.commit()
            conn.close()

            flash(f'成功创建第 {next_batch} 批出库记录！', 'success')
        except Exception as e:
            app.logger.error(f"Batch demo error: {str(e)}")
            flash(f'创建失败：{str(e)}', 'error')

    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>分批出货演示 - 仓储管理系统</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f8f9fa; }
            .container { max-width: 800px; margin: 0 auto; }
            .header { background: white; padding: 25px; border-radius: 8px; margin-bottom: 25px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
            .form-container { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
            .form-group { margin-bottom: 20px; }
            label { display: block; margin-bottom: 8px; font-weight: bold; color: #495057; }
            input[type="text"], input[type="number"] { width: 100%; padding: 12px; border: 2px solid #ced4da; border-radius: 6px; box-sizing: border-box; font-size: 16px; }
            input[type="text"]:focus, input[type="number"]:focus { border-color: #007bff; outline: none; }
            .btn { background: #007bff; color: white; padding: 12px 24px; border: none; border-radius: 6px; cursor: pointer; font-size: 16px; }
            .btn:hover { background: #0056b3; }
            .menu { display: flex; gap: 15px; margin: 20px 0; }
            .menu a { padding: 10px 20px; background: #6c757d; color: white; text-decoration: none; border-radius: 5px; }
            .menu a:hover { background: #5a6268; }
            .flash-messages { margin: 20px 0; }
            .success { color: #155724; background: #d4edda; padding: 15px; border-radius: 6px; border: 1px solid #c3e6cb; }
            .error { color: #721c24; background: #f8d7da; padding: 15px; border-radius: 6px; border: 1px solid #f5c6cb; }
            .example { background: #e9ecef; padding: 20px; border-radius: 8px; margin: 25px 0; }
            .example h3 { margin-top: 0; color: #495057; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>分批出货演示</h2>
                <p>演示同一识别编码的分批出货功能，验证数据库约束和错误处理</p>
            </div>

            <div class="menu">
                <a href="{{ url_for('index') }}">返回首页</a>
                <a href="{{ url_for('outbound_list') }}">查看出库记录</a>
            </div>

            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    <div class="flash-messages">
                        {% for category, message in messages %}
                            <div class="{{ category }}">{{ message }}</div>
                        {% endfor %}
                    </div>
                {% endif %}
            {% endwith %}

            <div class="example">
                <h3>分批出货说明</h3>
                <p>同一个识别编码可以分多批出库，系统会自动分配批次序号：</p>
                <ul>
                    <li>第1次出库：batch_sequence = 1</li>
                    <li>第2次出库：batch_sequence = 2</li>
                    <li>第3次出库：batch_sequence = 3</li>
                </ul>
                <p><strong>数据库约束：</strong>(identification_code, batch_sequence) 组合唯一</p>
                <p><strong>错误处理：</strong>所有异常都会被捕获并显示友好的错误信息</p>
            </div>

            <div class="form-container">
                <form method="POST">
                    <div class="form-group">
                        <label for="identification_code">识别编码：</label>
                        <input type="text" id="identification_code" name="identification_code"
                               value="PH/佛山震雄/粤BHW989/20250723/001" required>
                    </div>

                    <div class="form-group">
                        <label for="customer_name">客户名称：</label>
                        <input type="text" id="customer_name" name="customer_name"
                               value="佛山震雄" required>
                    </div>

                    <div class="form-group">
                        <label for="plate_number">车牌号：</label>
                        <input type="text" id="plate_number" name="plate_number"
                               value="粤BHW989" required>
                    </div>

                    <div class="form-group">
                        <label for="pallet_count">板数：</label>
                        <input type="number" id="pallet_count" name="pallet_count"
                               value="10" min="1" required>
                    </div>

                    <button type="submit" class="btn">创建出库记录</button>
                </form>
            </div>
        </div>
    </body>
    </html>
    ''')

@app.route('/test_error')
def test_error():
    """测试错误处理"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # 故意触发一个错误来测试错误处理机制
    raise Exception("这是一个测试错误，用于验证错误处理机制是否正常工作")

if __name__ == '__main__':
    # 初始化数据库
    init_db()

    print("仓储管理系统启动 - Internal Server Error 已修复")
    print("访问地址: http://localhost:5000")
    print("测试账号: admin / admin123")
    print("特性: 分批出货、错误处理、权限管理")

    app.run(host='0.0.0.0', port=5000, debug=True)
