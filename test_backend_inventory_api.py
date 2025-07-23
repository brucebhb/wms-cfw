#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import sys

def test_backend_inventory_api():
    """测试后端仓库存API"""
    
    # API端点
    url = 'http://127.0.0.1:5000/api/inventory/backend'
    
    try:
        print('=== 测试后端仓库存API ===')
        print(f'请求URL: {url}')
        
        # 发送GET请求
        response = requests.get(url, timeout=10)
        
        print(f'响应状态码: {response.status_code}')
        print(f'响应头: {dict(response.headers)}')
        
        if response.status_code == 200:
            try:
                data = response.json()
                print('✅ API请求成功')
                print(f'响应数据: {json.dumps(data, ensure_ascii=False, indent=2)}')
                
                if data.get('success'):
                    inventory_data = data.get('data', [])
                    print(f'📦 库存记录数量: {len(inventory_data)}')
                    
                    if inventory_data:
                        print('\n前5条库存记录:')
                        for i, item in enumerate(inventory_data[:5], 1):
                            print(f'{i}. 客户: {item.get("customer_name", "")}, '
                                  f'识别编码: {item.get("identification_code", "")}, '
                                  f'板数: {item.get("pallet_count", 0)}, '
                                  f'件数: {item.get("package_count", 0)}')
                else:
                    print(f'❌ API返回失败: {data.get("message", "未知错误")}')
                    
            except json.JSONDecodeError as e:
                print(f'❌ JSON解析失败: {e}')
                print(f'原始响应内容: {response.text[:500]}...')
                
        else:
            print(f'❌ HTTP请求失败: {response.status_code}')
            print(f'错误内容: {response.text[:500]}...')
            
    except requests.exceptions.ConnectionError:
        print('❌ 连接失败: 服务器可能未启动')
        print('请确保Flask服务器正在运行在 http://127.0.0.1:5000')
        
    except requests.exceptions.Timeout:
        print('❌ 请求超时')
        
    except Exception as e:
        print(f'❌ 请求异常: {e}')

if __name__ == '__main__':
    test_backend_inventory_api()
