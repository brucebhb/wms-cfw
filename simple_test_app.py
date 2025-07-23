#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单测试应用 - 检查基本功能
"""

from flask import Flask, jsonify
import os
import sys

app = Flask(__name__)

@app.route('/')
def index():
    return """
    <h1>仓储管理系统 - 权限测试</h1>
    <p>Flask应用运行正常</p>
    <p>文件权限正常</p>
    <p><a href="/test">运行系统测试</a></p>
    """

@app.route('/test')
def test():
    """系统测试"""
    results = {
        'python_version': sys.version,
        'working_directory': os.getcwd(),
        'user': os.getenv('USERNAME', 'Unknown'),
        'flask_working': True,
        'file_permissions': 'OK'
    }
    
    # 测试文件读写
    try:
        test_file = 'test_permissions.txt'
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write('permission test')
        
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        os.remove(test_file)
        results['file_write_test'] = 'OK'
    except Exception as e:
        results['file_write_test'] = f'FAILED: {str(e)}'
    
    return jsonify(results)

if __name__ == '__main__':
    print("启动简单测试应用")
    print("访问地址: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
