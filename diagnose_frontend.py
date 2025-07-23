#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
前端页面问题诊断脚本
"""

import requests
import json
from bs4 import BeautifulSoup

def test_login_and_pages():
    """测试登录和页面访问"""
    session = requests.Session()
    
    print("🔍 开始诊断前端页面问题...")
    
    # 1. 测试主页访问
    print("\n1. 测试主页访问...")
    try:
        response = session.get('http://175.178.147.75/')
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ 主页访问正常")
        else:
            print(f"   ❌ 主页访问异常: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 主页访问失败: {e}")
    
    # 2. 测试登录页面
    print("\n2. 测试登录页面...")
    try:
        response = session.get('http://175.178.147.75/auth/login')
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ 登录页面正常")
            
            # 解析登录表单
            soup = BeautifulSoup(response.text, 'html.parser')
            csrf_token = soup.find('input', {'name': 'csrf_token'})
            if csrf_token:
                csrf_value = csrf_token.get('value')
                print(f"   ✅ 找到CSRF令牌")
                
                # 3. 尝试登录
                print("\n3. 尝试登录...")
                login_data = {
                    'username': 'admin',
                    'password': 'admin123',
                    'csrf_token': csrf_value
                }
                
                login_response = session.post('http://175.178.147.75/auth/login', data=login_data)
                print(f"   登录响应状态码: {login_response.status_code}")
                
                if login_response.status_code == 302:  # 重定向表示登录成功
                    print("   ✅ 登录成功")
                    
                    # 4. 测试入库页面
                    print("\n4. 测试入库页面...")
                    inbound_response = session.get('http://175.178.147.75/frontend/inbound')
                    print(f"   入库页面状态码: {inbound_response.status_code}")
                    
                    if inbound_response.status_code == 200:
                        print("   ✅ 入库页面访问成功")
                        
                        # 检查页面内容
                        soup = BeautifulSoup(inbound_response.text, 'html.parser')
                        
                        # 检查CSS文件
                        css_links = soup.find_all('link', {'rel': 'stylesheet'})
                        print(f"   CSS文件数量: {len(css_links)}")
                        for css in css_links[:3]:  # 只显示前3个
                            href = css.get('href', '')
                            print(f"     - {href}")
                        
                        # 检查JS文件
                        js_scripts = soup.find_all('script', {'src': True})
                        print(f"   JS文件数量: {len(js_scripts)}")
                        for js in js_scripts[:3]:  # 只显示前3个
                            src = js.get('src', '')
                            print(f"     - {src}")
                        
                        # 检查数据卡片
                        cards = soup.find_all('div', class_='card')
                        print(f"   数据卡片数量: {len(cards)}")
                        
                        # 检查表格
                        tables = soup.find_all('table')
                        print(f"   表格数量: {len(tables)}")
                        
                    else:
                        print(f"   ❌ 入库页面访问失败: {inbound_response.status_code}")
                        
                    # 5. 测试API接口
                    print("\n5. 测试API接口...")
                    try:
                        api_response = session.get('http://175.178.147.75/api/frontend/inbound/stats')
                        print(f"   API状态码: {api_response.status_code}")
                        if api_response.status_code == 200:
                            print("   ✅ API接口正常")
                            try:
                                data = api_response.json()
                                print(f"   API数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
                            except:
                                print("   ⚠️  API响应不是JSON格式")
                        else:
                            print(f"   ❌ API接口异常: {api_response.status_code}")
                    except Exception as e:
                        print(f"   ❌ API测试失败: {e}")
                        
                else:
                    print(f"   ❌ 登录失败: {login_response.status_code}")
                    print(f"   响应内容: {login_response.text[:200]}...")
            else:
                print("   ❌ 未找到CSRF令牌")
        else:
            print(f"   ❌ 登录页面异常: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 登录页面访问失败: {e}")
    
    # 6. 测试静态文件
    print("\n6. 测试静态文件...")
    static_files = [
        '/static/css/style.css',
        '/static/js/common.js',
        '/static/css/bootstrap.min.css'
    ]
    
    for file_path in static_files:
        try:
            response = session.get(f'http://175.178.147.75{file_path}')
            print(f"   {file_path}: {response.status_code}")
        except Exception as e:
            print(f"   {file_path}: 失败 - {e}")

if __name__ == '__main__':
    test_login_and_pages()
