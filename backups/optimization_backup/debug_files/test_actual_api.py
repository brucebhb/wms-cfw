#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试实际的全库存查询API
"""

import requests
import json

def test_actual_api():
    # 测试实际的API调用
    base_url = "http://127.0.0.1:5000"
    
    print("=== 测试实际的全库存查询API ===\n")
    
    # 1. 测试库存列表页面
    print("1. 测试库存列表页面:")
    try:
        response = requests.get(f"{base_url}/inventory", params={
            'search_field': 'customer_name',
            'search_value': '泰塑',
            'warehouse_id': '',  # 全部仓库
            'start_date': '',
            'end_date': '',
            'stock_status': '',
            'cargo_status': ''
        })
        
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            # 检查响应中是否包含两条记录
            content = response.text
            
            # 计算包含"泰塑"的行数
            lines_with_taisu = [line for line in content.split('\n') if '泰塑' in line]
            print(f"包含'泰塑'的行数: {len(lines_with_taisu)}")
            
            # 检查是否包含平湖仓和凭祥北投仓
            has_pinghu = '平湖仓' in content
            has_pingxiang = '凭祥北投仓' in content
            
            print(f"包含平湖仓: {has_pinghu}")
            print(f"包含凭祥北投仓: {has_pingxiang}")
            
            # 查找表格行
            import re
            table_rows = re.findall(r'<tr[^>]*>.*?</tr>', content, re.DOTALL)
            data_rows = [row for row in table_rows if 'PH/泰塑/粤BR77A0/20250712/001' in row]
            print(f"包含目标识别编码的表格行数: {len(data_rows)}")
            
            if len(data_rows) > 0:
                print("找到的表格行:")
                for i, row in enumerate(data_rows):
                    print(f"  行 {i+1}: {row[:200]}...")
        else:
            print(f"请求失败: {response.text}")
    
    except Exception as e:
        print(f"请求出错: {e}")
    
    print()
    
    # 2. 测试API接口
    print("2. 测试库存API接口:")
    try:
        response = requests.get(f"{base_url}/api/inventory/list", params={
            'search_field': 'customer_name',
            'search_value': '泰塑',
            'warehouse_id': '',
            'refresh': 'true'  # 强制刷新缓存
        })
        
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if 'data' in data:
                records = data['data']
                print(f"API返回记录数: {len(records)}")
                
                for i, record in enumerate(records):
                    if 'PH/泰塑/粤BR77A0/20250712/001' in record.get('identification_code', ''):
                        print(f"  记录 {i+1}:")
                        print(f"    识别编码: {record.get('identification_code')}")
                        print(f"    客户名称: {record.get('customer_name')}")
                        print(f"    仓库: {record.get('warehouse_name', 'N/A')}")
                        print(f"    板数: {record.get('pallet_count')}")
                        print()
            else:
                print(f"API响应格式异常: {data}")
        else:
            print(f"API请求失败: {response.text}")
    
    except Exception as e:
        print(f"API请求出错: {e}")

if __name__ == "__main__":
    test_actual_api()
