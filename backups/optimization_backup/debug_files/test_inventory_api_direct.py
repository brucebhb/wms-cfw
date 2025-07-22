#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接测试全库存查询API
"""

from app import create_app, db
from app.models import User
from flask import url_for
import json

def test_inventory_api_direct():
    app = create_app()
    
    with app.app_context():
        print("=== 直接测试全库存查询API ===\n")
        
        # 创建测试客户端
        client = app.test_client()
        
        # 测试不同用户的登录
        test_users = ['admin', 'PHC', 'PXC']
        
        for username in test_users:
            user = User.query.filter_by(username=username).first()
            if not user:
                print(f"用户 {username} 不存在")
                continue
            
            print(f"=== 测试用户 {username} ===")
            
            # 模拟登录
            with client.session_transaction() as sess:
                sess['_user_id'] = str(user.id)
                sess['_fresh'] = True
            
            # 测试库存列表页面
            response = client.get('/inventory', query_string={
                'search_field': 'customer_name',
                'search_value': '泰塑',
                'warehouse_id': '',
                'start_date': '',
                'end_date': '',
                'stock_status': '',
                'cargo_status': ''
            })
            
            print(f"页面请求状态码: {response.status_code}")
            
            if response.status_code == 200:
                content = response.get_data(as_text=True)
                
                # 计算包含识别编码的行数
                target_code = 'PH/泰塑/粤BR77A0/20250712/001'
                lines_with_code = content.count(target_code)
                print(f"页面中包含目标识别编码的次数: {lines_with_code}")
                
                # 检查是否包含不同仓库
                has_pinghu = '平湖仓' in content
                has_pingxiang = '凭祥北投仓' in content
                print(f"包含平湖仓: {has_pinghu}")
                print(f"包含凭祥北投仓: {has_pingxiang}")
                
                # 查找表格行中的数据
                import re
                # 查找包含目标识别编码的表格行
                pattern = r'<tr[^>]*>.*?' + re.escape(target_code) + r'.*?</tr>'
                matches = re.findall(pattern, content, re.DOTALL)
                print(f"找到的表格行数: {len(matches)}")
                
                for i, match in enumerate(matches):
                    print(f"  行 {i+1}: {match[:200]}...")
                    
                    # 提取仓库信息
                    if '平湖仓' in match:
                        print(f"    -> 包含平湖仓")
                    if '凭祥北投仓' in match:
                        print(f"    -> 包含凭祥北投仓")
            
            # 测试API接口
            print(f"\n测试API接口:")
            api_response = client.get('/api/inventory/list', query_string={
                'search_field': 'customer_name',
                'search_value': '泰塑',
                'warehouse_id': '',
                'refresh': 'true'
            })
            
            print(f"API请求状态码: {api_response.status_code}")
            
            if api_response.status_code == 200:
                try:
                    api_data = api_response.get_json()
                    if 'data' in api_data:
                        records = api_data['data']
                        print(f"API返回记录数: {len(records)}")
                        
                        target_records = [r for r in records if target_code in r.get('identification_code', '')]
                        print(f"包含目标识别编码的记录数: {len(target_records)}")
                        
                        for i, record in enumerate(target_records):
                            print(f"  记录 {i+1}:")
                            print(f"    识别编码: {record.get('identification_code')}")
                            print(f"    客户名称: {record.get('customer_name')}")
                            print(f"    仓库: {record.get('warehouse_name', 'N/A')}")
                            print(f"    仓库类型: {record.get('warehouse_type', 'N/A')}")
                            print(f"    板数: {record.get('pallet_count')}")
                            print(f"    状态: {record.get('current_status', 'N/A')}")
                    else:
                        print(f"API响应格式异常: {api_data}")
                except Exception as e:
                    print(f"解析API响应失败: {e}")
                    print(f"原始响应: {api_response.get_data(as_text=True)[:500]}")
            
            print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    test_inventory_api_direct()
