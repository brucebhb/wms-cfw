#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json

def test_deletion_api():
    """测试后端仓出库记录删除API"""
    
    # 目标批次号
    batch_no = 'PX25071502'
    
    # API URL
    url = f'http://127.0.0.1:5000/api/backend/outbound/delete_batch/{batch_no}'
    
    print(f'测试删除API: {url}')
    print('=' * 60)
    
    try:
        # 发送DELETE请求
        response = requests.delete(url, timeout=10)
        
        print(f'响应状态码: {response.status_code}')
        print(f'响应头: {dict(response.headers)}')
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f'响应数据: {json.dumps(data, ensure_ascii=False, indent=2)}')
            except:
                print(f'响应文本: {response.text}')
        else:
            print(f'错误响应: {response.text}')
            
    except requests.exceptions.RequestException as e:
        print(f'请求异常: {str(e)}')
    except Exception as e:
        print(f'其他异常: {str(e)}')

if __name__ == '__main__':
    test_deletion_api()
