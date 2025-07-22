#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试车挂/柜号字段显示功能
"""

import requests
from bs4 import BeautifulSoup
import re

def test_trailer_container_display():
    """测试车挂/柜号字段在单据打印页面的显示"""
    
    # 测试URL
    base_url = "http://127.0.0.1:5000"
    login_url = f"{base_url}/auth/login"
    print_list_url = f"{base_url}/outbound/print_list"
    
    # 创建会话
    session = requests.Session()
    
    try:
        # 1. 获取登录页面
        print("1. 获取登录页面...")
        response = session.get(login_url)
        if response.status_code != 200:
            print(f"❌ 无法访问登录页面，状态码: {response.status_code}")
            return
        
        # 解析CSRF token
        soup = BeautifulSoup(response.text, 'html.parser')
        csrf_token = soup.find('input', {'name': 'csrf_token'})
        if not csrf_token:
            print("❌ 无法找到CSRF token")
            return
        csrf_token = csrf_token.get('value')
        
        # 2. 登录
        print("2. 执行登录...")
        login_data = {
            'username': 'admin',
            'password': 'admin123',
            'csrf_token': csrf_token
        }
        
        response = session.post(login_url, data=login_data)
        if response.status_code != 200 and response.status_code != 302:
            print(f"❌ 登录失败，状态码: {response.status_code}")
            return
        
        print("✅ 登录成功")
        
        # 3. 访问单据打印列表页面
        print("3. 访问单据打印列表页面...")
        response = session.get(print_list_url)
        if response.status_code != 200:
            print(f"❌ 无法访问单据打印页面，状态码: {response.status_code}")
            return
        
        print("✅ 成功访问单据打印页面")
        
        # 4. 解析页面内容，检查车挂/柜号列
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 查找表格头部
        table_headers = soup.find_all('th')
        header_texts = [th.get_text().strip() for th in table_headers]
        
        print("\n=== 表格头部分析 ===")
        print("找到的表格头部:")
        for i, header in enumerate(header_texts):
            print(f"  {i+1}. {header}")
        
        # 检查是否包含车挂/柜号列
        trailer_container_found = False
        for header in header_texts:
            if '车挂' in header or '柜号' in header:
                trailer_container_found = True
                print(f"✅ 找到车挂/柜号列: {header}")
                break
        
        if not trailer_container_found:
            print("❌ 未找到车挂/柜号列")
        
        # 5. 查找表格数据行，检查车挂/柜号数据
        print("\n=== 表格数据分析 ===")
        table_rows = soup.find_all('tr')
        data_rows = []
        
        for row in table_rows:
            cells = row.find_all('td')
            if cells:  # 只处理数据行，跳过头部行
                cell_texts = [cell.get_text().strip() for cell in cells]
                data_rows.append(cell_texts)
        
        print(f"找到 {len(data_rows)} 行数据")
        
        # 查找包含车挂/柜号信息的行
        trailer_container_data_found = False
        for i, row in enumerate(data_rows[:5]):  # 只检查前5行
            for j, cell in enumerate(row):
                if '车挂:' in cell or '柜号:' in cell:
                    trailer_container_data_found = True
                    print(f"✅ 第{i+1}行第{j+1}列找到车挂/柜号数据: {cell}")
                    break
        
        if not trailer_container_data_found:
            print("⚠️ 在前5行数据中未找到车挂/柜号数据")
        
        # 6. 检查页面是否包含车挂/柜号相关的文本
        page_text = soup.get_text()
        if '车挂:' in page_text or '柜号:' in page_text:
            print("✅ 页面包含车挂/柜号相关文本")
            
            # 提取车挂/柜号信息
            trailer_matches = re.findall(r'车挂:\s*([^;,\n]+)', page_text)
            container_matches = re.findall(r'柜号:\s*([^;,\n]+)', page_text)
            
            if trailer_matches:
                print(f"  找到车挂信息: {trailer_matches[:3]}")  # 只显示前3个
            if container_matches:
                print(f"  找到柜号信息: {container_matches[:3]}")  # 只显示前3个
        else:
            print("❌ 页面不包含车挂/柜号相关文本")
        
        # 7. 总结测试结果
        print("\n=== 测试结果总结 ===")
        if trailer_container_found:
            print("✅ 表格头部包含车挂/柜号列")
        else:
            print("❌ 表格头部缺少车挂/柜号列")
        
        if trailer_container_data_found or ('车挂:' in page_text or '柜号:' in page_text):
            print("✅ 页面包含车挂/柜号数据")
        else:
            print("❌ 页面缺少车挂/柜号数据")
        
    except Exception as e:
        print(f"❌ 测试过程中出错: {str(e)}")

if __name__ == "__main__":
    test_trailer_container_display()
