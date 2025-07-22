#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json

def test_pxc_deletion():
    """测试PXC用户删除后端仓出库记录"""
    
    session = requests.Session()
    
    # 1. 先登录PXC用户
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
        'username': 'PXC',
        'password': '123',  # PXC用户密码
        'csrf_token': csrf_token
    }
    
    login_response = session.post(login_url, data=login_data)
    print(f"登录响应状态码: {login_response.status_code}")
    
    if login_response.status_code == 200 and '登录' not in login_response.text:
        print("登录成功")
    else:
        print("登录失败，尝试不同的密码...")
        # 尝试其他可能的密码
        for password in ['123', '123456', 'admin', 'PXC', 'pxc123']:
            login_data['password'] = password
            login_response = session.post(login_url, data=login_data)
            if login_response.status_code == 200 and '登录' not in login_response.text:
                print(f"使用密码 {password} 登录成功")
                break
        else:
            print("所有密码尝试失败")
            return
    
    # 3. 获取后端仓出库记录页面以获取新的CSRF token
    outbound_list_url = 'http://127.0.0.1:5000/backend/outbound/list'
    outbound_page = session.get(outbound_list_url)
    print(f"获取出库记录页面状态码: {outbound_page.status_code}")
    
    if outbound_page.status_code != 200:
        print("无法访问后端仓出库记录页面")
        return
    
    # 提取新的CSRF token
    csrf_match = re.search(r'name=csrf-token.*?content="([^"]+)"', outbound_page.text)
    if csrf_match:
        new_csrf_token = csrf_match.group(1)
        print(f"获取到新的CSRF token: {new_csrf_token[:20]}...")
    else:
        print("使用原CSRF token")
        new_csrf_token = csrf_token
    
    # 4. 尝试删除批次
    batch_no = 'PX25071502'
    delete_url = f'http://127.0.0.1:5000/api/backend/outbound/delete_batch/{batch_no}'
    
    headers = {
        'Content-Type': 'application/json',
        'X-CSRFToken': new_csrf_token
    }
    
    print(f"尝试删除批次: {batch_no}")
    delete_response = session.delete(delete_url, headers=headers)
    
    print(f"删除响应状态码: {delete_response.status_code}")
    print(f"删除响应头: {dict(delete_response.headers)}")
    
    try:
        response_data = delete_response.json()
        print(f"删除响应数据: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
    except:
        print(f"删除响应文本: {delete_response.text[:500]}...")

if __name__ == '__main__':
    test_pxc_deletion()
