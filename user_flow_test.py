#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户操作流程测试 - 模拟真实用户操作
"""

import requests
import re
from urllib.parse import urljoin

class UserFlowTester:
    def __init__(self, base_url='http://127.0.0.1:5000'):
        self.base_url = base_url
        self.session = requests.Session()
        self.csrf_token = None
    
    def get_csrf_token(self, html_content):
        """从HTML中提取CSRF token"""
        # 查找CSRF token
        csrf_match = re.search(r'name="csrf_token"[^>]*value="([^"]*)"', html_content)
        if csrf_match:
            return csrf_match.group(1)
        
        # 备用方法：查找meta标签中的CSRF token
        meta_match = re.search(r'<meta name="csrf-token" content="([^"]*)"', html_content)
        if meta_match:
            return meta_match.group(1)
        
        return None
    
    def step1_visit_homepage(self):
        """步骤1：访问首页"""
        print("🔍 步骤1：访问首页")
        try:
            response = self.session.get(self.base_url)
            print(f"   状态码: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ 首页访问成功")
                return True
            else:
                print(f"   ❌ 首页访问失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ 首页访问异常: {e}")
            return False
    
    def step2_visit_login_page(self):
        """步骤2：访问登录页面"""
        print("\n🔍 步骤2：访问登录页面")
        try:
            login_url = urljoin(self.base_url, '/auth/login')
            response = self.session.get(login_url)
            print(f"   状态码: {response.status_code}")
            
            if response.status_code == 200:
                # 提取CSRF token
                self.csrf_token = self.get_csrf_token(response.text)
                if self.csrf_token:
                    print(f"   ✅ 登录页面访问成功，CSRF token: {self.csrf_token[:20]}...")
                else:
                    print("   ⚠️  登录页面访问成功，但未找到CSRF token")
                return True
            else:
                print(f"   ❌ 登录页面访问失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ 登录页面访问异常: {e}")
            return False
    
    def step3_attempt_login(self, username='admin', password='admin123'):
        """步骤3：尝试登录"""
        print(f"\n🔍 步骤3：尝试登录 (用户名: {username})")
        try:
            login_url = urljoin(self.base_url, '/auth/login')
            
            # 准备登录数据
            login_data = {
                'username': username,
                'password': password,
                'remember_me': False
            }
            
            # 如果有CSRF token，添加到数据中
            if self.csrf_token:
                login_data['csrf_token'] = self.csrf_token
            
            print(f"   发送登录请求...")
            response = self.session.post(login_url, data=login_data, allow_redirects=False)
            print(f"   状态码: {response.status_code}")
            
            if response.status_code == 302:
                # 重定向，通常表示登录成功
                redirect_location = response.headers.get('Location', '')
                print(f"   ✅ 登录成功，重定向到: {redirect_location}")
                return True, redirect_location
            elif response.status_code == 200:
                # 返回200可能表示登录失败，停留在登录页面
                if '用户名或密码错误' in response.text or 'error' in response.text.lower():
                    print("   ❌ 登录失败：用户名或密码错误")
                else:
                    print("   ⚠️  登录请求返回200，可能有其他问题")
                    print(f"   响应内容片段: {response.text[:200]}...")
                return False, None
            else:
                print(f"   ❌ 登录失败: {response.status_code}")
                print(f"   响应内容: {response.text[:500]}...")
                return False, None
                
        except Exception as e:
            print(f"   ❌ 登录异常: {e}")
            return False, None
    
    def step4_access_dashboard(self, redirect_url=None):
        """步骤4：访问登录后的页面"""
        print("\n🔍 步骤4：访问登录后的页面")
        try:
            # 如果有重定向URL，使用它；否则访问首页
            if redirect_url:
                if redirect_url.startswith('/'):
                    dashboard_url = urljoin(self.base_url, redirect_url)
                else:
                    dashboard_url = redirect_url
            else:
                dashboard_url = urljoin(self.base_url, '/')
            
            print(f"   访问URL: {dashboard_url}")
            response = self.session.get(dashboard_url)
            print(f"   状态码: {response.status_code}")
            
            if response.status_code == 200:
                # 检查是否成功登录（查找登出链接或用户信息）
                if '登出' in response.text or '退出' in response.text or 'logout' in response.text.lower():
                    print("   ✅ 成功访问登录后页面")
                    return True
                elif '请登录' in response.text or 'login' in response.text.lower():
                    print("   ❌ 未成功登录，仍显示登录提示")
                    return False
                else:
                    print("   ⚠️  页面访问成功，但无法确定登录状态")
                    print(f"   页面内容片段: {response.text[:300]}...")
                    return True
            else:
                print(f"   ❌ 页面访问失败: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ 页面访问异常: {e}")
            return False
    
    def step5_test_main_functions(self):
        """步骤5：测试主要功能页面"""
        print("\n🔍 步骤5：测试主要功能页面")
        
        # 测试的页面列表
        test_pages = [
            ('/inventory/list', '库存管理'),
            ('/frontend/inbound', '前端入库'),
            ('/frontend/outbound', '前端出库'),
            ('/backend/inbound', '后端入库'),
            ('/backend/outbound', '后端出库'),
        ]
        
        success_count = 0
        total_count = len(test_pages)
        
        for page_url, page_name in test_pages:
            try:
                full_url = urljoin(self.base_url, page_url)
                print(f"   测试 {page_name}: {page_url}")
                
                response = self.session.get(full_url)
                print(f"     状态码: {response.status_code}")
                
                if response.status_code == 200:
                    print(f"     ✅ {page_name} 访问成功")
                    success_count += 1
                elif response.status_code == 404:
                    print(f"     ⚠️  {page_name} 页面不存在 (404)")
                elif response.status_code == 500:
                    print(f"     ❌ {page_name} 服务器错误 (500)")
                    print(f"     错误内容: {response.text[:200]}...")
                else:
                    print(f"     ❌ {page_name} 访问失败: {response.status_code}")
                    
            except Exception as e:
                print(f"     ❌ {page_name} 访问异常: {e}")
        
        print(f"\n   📊 功能页面测试结果: {success_count}/{total_count} 成功")
        return success_count, total_count
    
    def run_full_test(self):
        """运行完整的用户流程测试"""
        print("🧪 开始用户操作流程测试")
        print("=" * 60)
        
        # 步骤1：访问首页
        if not self.step1_visit_homepage():
            print("❌ 测试终止：首页访问失败")
            return False
        
        # 步骤2：访问登录页面
        if not self.step2_visit_login_page():
            print("❌ 测试终止：登录页面访问失败")
            return False
        
        # 步骤3：尝试登录
        login_success, redirect_url = self.step3_attempt_login()
        if not login_success:
            print("❌ 测试终止：登录失败")
            return False
        
        # 步骤4：访问登录后页面
        if not self.step4_access_dashboard(redirect_url):
            print("❌ 测试终止：登录后页面访问失败")
            return False
        
        # 步骤5：测试主要功能
        success_count, total_count = self.step5_test_main_functions()

        # 步骤6：测试具体的错误场景
        self.step6_test_error_scenarios()

        print("\n" + "=" * 60)
        print("📋 测试总结:")
        print("✅ 首页访问正常")
        print("✅ 登录页面正常")
        print("✅ 用户登录成功")
        print("✅ 登录后页面正常")
        print(f"📊 功能页面: {success_count}/{total_count} 正常")

        if success_count == total_count:
            print("🎉 所有测试通过！系统运行正常")
            return True
        else:
            print("⚠️  部分功能存在问题，需要进一步检查")
            return False

    def step6_test_error_scenarios(self):
        """步骤6：测试具体的错误场景"""
        print("\n🔍 步骤6：测试具体的错误场景")

        # 测试可能导致Internal Server Error的页面
        error_test_pages = [
            ('/inventory/list', '库存列表'),
            ('/frontend/outbound/list', '前端出库列表'),
            ('/backend/outbound/list', '后端出库列表'),
            ('/frontend/inbound/list', '前端入库列表'),
            ('/backend/inbound/list', '后端入库列表'),
        ]

        for page_url, page_name in error_test_pages:
            try:
                full_url = urljoin(self.base_url, page_url)
                print(f"   测试 {page_name}: {page_url}")

                response = self.session.get(full_url)
                print(f"     状态码: {response.status_code}")

                if response.status_code == 200:
                    print(f"     ✅ {page_name} 正常")
                elif response.status_code == 500:
                    print(f"     ❌ {page_name} Internal Server Error")
                    # 检查错误内容
                    if '系统异常' in response.text or '系统错误' in response.text:
                        print(f"     🔍 错误被捕获，显示友好错误页面")
                    else:
                        print(f"     🔍 原始错误页面")
                        print(f"     错误内容片段: {response.text[:200]}...")
                elif response.status_code == 404:
                    print(f"     ⚠️  {page_name} 页面不存在")
                else:
                    print(f"     ❌ {page_name} 其他错误: {response.status_code}")

            except Exception as e:
                print(f"     ❌ {page_name} 访问异常: {e}")

        print(f"\n   📊 错误场景测试完成")

def main():
    """主函数"""
    tester = UserFlowTester()
    tester.run_full_test()

if __name__ == "__main__":
    main()
