#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试单据打印列表，包含车挂/柜号数据的记录
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

def test_print_list_with_trailer():
    """测试单据打印列表，扩大日期范围以包含车挂/柜号数据"""
    
    # 测试URL
    base_url = "http://127.0.0.1:5000"
    login_url = f"{base_url}/auth/login"
    
    # 设置日期范围，包含有车挂/柜号数据的记录
    date_start = "2025-07-13"  # 包含2025-07-13的记录
    date_end = "2025-07-15"    # 包含2025-07-15的记录
    print_list_url = f"{base_url}/outbound/print_list?date_start={date_start}&date_end={date_end}"
    
    # 创建会话
    session = requests.Session()
    
    try:
        # 1. 登录
        print("1. 执行登录...")
        response = session.get(login_url)
        if response.status_code != 200:
            print(f"❌ 无法访问登录页面，状态码: {response.status_code}")
            return
        
        soup = BeautifulSoup(response.text, 'html.parser')
        csrf_token = soup.find('input', {'name': 'csrf_token'})
        if not csrf_token:
            print("❌ 无法找到CSRF token")
            return
        csrf_token = csrf_token.get('value')
        
        login_data = {
            'username': 'admin',
            'password': 'admin123',
            'csrf_token': csrf_token
        }
        
        response = session.post(login_url, data=login_data)
        if response.status_code not in [200, 302]:
            print(f"❌ 登录失败，状态码: {response.status_code}")
            return
        
        print("✅ 登录成功")
        
        # 2. 访问单据打印列表页面（扩大日期范围）
        print(f"2. 访问单据打印列表页面（日期范围: {date_start} 到 {date_end}）...")
        response = session.get(print_list_url)
        if response.status_code != 200:
            print(f"❌ 无法访问单据打印页面，状态码: {response.status_code}")
            return
        
        print("✅ 成功访问单据打印页面")
        
        # 3. 解析页面内容
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 查找车挂/柜号列的索引
        table_headers = soup.find_all('th')
        header_texts = [th.get_text().strip() for th in table_headers]
        
        trailer_column_index = -1
        for i, header in enumerate(header_texts):
            if '车挂/柜号' in header:
                trailer_column_index = i
                print(f"✅ 找到车挂/柜号列，索引: {i}")
                break
        
        if trailer_column_index == -1:
            print("❌ 未找到车挂/柜号列")
            return
        
        # 4. 查找表格数据行
        print("\n=== 检查车挂/柜号数据 ===")
        table_rows = soup.find_all('tr')
        data_rows = []
        
        for row in table_rows:
            cells = row.find_all('td')
            if cells and len(cells) > trailer_column_index:  # 确保有足够的列
                cell_texts = [cell.get_text().strip() for cell in cells]
                data_rows.append(cell_texts)
        
        print(f"找到 {len(data_rows)} 行数据")
        
        # 5. 检查车挂/柜号列的数据
        trailer_data_found = 0
        for i, row in enumerate(data_rows):
            if len(row) > trailer_column_index:
                trailer_cell = row[trailer_column_index]
                if trailer_cell and trailer_cell.strip():
                    trailer_data_found += 1
                    print(f"第{i+1}行车挂/柜号数据: '{trailer_cell}'")
                    if trailer_data_found >= 5:  # 只显示前5个
                        break
        
        if trailer_data_found == 0:
            print("❌ 车挂/柜号列中没有数据")
            
            # 检查是否有包含车挂/柜号信息的文本
            page_text = soup.get_text()
            if '车挂:' in page_text or '柜号:' in page_text:
                print("⚠️ 页面包含车挂/柜号文本，但不在车挂/柜号列中")
                
                # 查找包含车挂/柜号的所有文本
                import re
                trailer_matches = re.findall(r'车挂:\s*([^;,\n]+)', page_text)
                container_matches = re.findall(r'柜号:\s*([^;,\n]+)', page_text)
                
                if trailer_matches:
                    print(f"  页面中的车挂信息: {set(trailer_matches)}")
                if container_matches:
                    print(f"  页面中的柜号信息: {set(container_matches)}")
            else:
                print("❌ 页面完全不包含车挂/柜号信息")
        else:
            print(f"✅ 找到 {trailer_data_found} 行包含车挂/柜号数据")
        
        # 6. 检查特定的有车挂/柜号数据的记录是否在页面中
        print("\n=== 检查特定记录 ===")
        page_text = soup.get_text()
        target_customers = ['裕同', 'ACKN', '测试客户A']
        found_targets = []

        for customer in target_customers:
            if customer in page_text:
                found_targets.append(customer)
                print(f"✅ 找到客户: {customer}")
            else:
                print(f"❌ 未找到客户: {customer}")
        
        if found_targets:
            print(f"✅ 在页面中找到 {len(found_targets)} 个目标客户")
        else:
            print("❌ 未找到任何目标客户")
        
        # 7. 总结
        print("\n=== 测试结果总结 ===")
        print(f"日期范围: {date_start} 到 {date_end}")
        print(f"数据行数: {len(data_rows)}")
        print(f"车挂/柜号数据行数: {trailer_data_found}")
        print(f"目标客户找到数: {len(found_targets)}")
        
        if trailer_data_found > 0:
            print("✅ 车挂/柜号功能正常工作")
        else:
            print("❌ 车挂/柜号功能需要进一步检查")
        
    except Exception as e:
        print(f"❌ 测试过程中出错: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_print_list_with_trailer()
