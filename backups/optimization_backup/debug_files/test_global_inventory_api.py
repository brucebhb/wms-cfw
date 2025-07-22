#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json

def test_global_inventory_api():
    """测试全库存查询API"""
    
    session = requests.Session()
    
    # 1. 先登录admin用户
    login_url = 'http://127.0.0.1:5000/auth/login'
    
    # 获取登录页面以获取CSRF token
    login_page = session.get(login_url)
    if login_page.status_code != 200:
        print(f"获取登录页面失败: {login_page.status_code}")
        return
    
    # 从页面中提取CSRF token
    import re
    csrf_match = re.search(r'name="csrf_token" value="([^"]+)"', login_page.text)
    if not csrf_match:
        print("无法找到CSRF token")
        return
    
    csrf_token = csrf_match.group(1)
    print(f"获取到CSRF token: {csrf_token[:20]}...")
    
    # 2. 提交登录表单
    login_data = {
        'username': 'admin',
        'password': '123',
        'csrf_token': csrf_token
    }
    
    login_response = session.post(login_url, data=login_data)
    print(f"登录响应状态码: {login_response.status_code}")
    
    if login_response.status_code == 302:
        print("登录成功 (重定向)")
    elif 'index' in login_response.url or '首页' in login_response.text:
        print("登录成功")
    else:
        print("登录失败")
        print(f"响应URL: {login_response.url}")
        print(f"响应内容片段: {login_response.text[:200]}...")
        return
    
    # 3. 测试全库存查询API
    inventory_api_url = 'http://127.0.0.1:5000/api/inventory/list'
    
    # 测试搜索特定识别编码
    search_params = {
        'search': 'PH/泰塑/粤BR77A0/20250712/001',
        'page': 1,
        'per_page': 50
    }
    
    print(f"\n测试全库存查询API...")
    inventory_response = session.get(inventory_api_url, params=search_params)
    
    print(f"API响应状态码: {inventory_response.status_code}")
    
    if inventory_response.status_code == 200:
        try:
            data = inventory_response.json()
            print(f"API响应数据:")
            print(f"  总记录数: {data.get('total', 0)}")
            print(f"  当前页记录数: {len(data.get('data', []))}")
            
            # 显示具体的库存记录
            for i, record in enumerate(data.get('data', [])):
                print(f"\n  记录 {i+1}:")
                print(f"    客户: {record.get('customer_name', '')}")
                print(f"    识别编码: {record.get('identification_code', '')}")
                print(f"    仓库: {record.get('warehouse_name', '')}")
                print(f"    板数: {record.get('pallet_count', 0)}")
                print(f"    件数: {record.get('package_count', 0)}")
                print(f"    入库时间: {record.get('inbound_time', '')}")
            
            # 检查是否显示了所有仓库的库存
            warehouses = set()
            total_pallets = 0
            for record in data.get('data', []):
                if record.get('identification_code') == 'PH/泰塑/粤BR77A0/20250712/001':
                    warehouses.add(record.get('warehouse_name', ''))
                    total_pallets += record.get('pallet_count', 0)
            
            print(f"\n汇总信息:")
            print(f"  涉及仓库: {list(warehouses)}")
            print(f"  总板数: {total_pallets}")
            
            if len(warehouses) == 2 and total_pallets == 4:
                print("✅ 全库存查询显示正确！")
            elif len(warehouses) == 1:
                print("❌ 全库存查询只显示了一个仓库的库存")
            else:
                print("❌ 全库存查询数据异常")
                
        except json.JSONDecodeError:
            print(f"API响应不是有效的JSON: {inventory_response.text[:200]}...")
    else:
        print(f"API请求失败: {inventory_response.text[:200]}...")

if __name__ == '__main__':
    test_global_inventory_api()
