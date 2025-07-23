#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
仓储管理系统性能测试脚本
模拟15人并发访问，每日200条记录的负载
"""

import requests
import threading
import time
import random
from datetime import datetime
import json

class PerformanceTest:
    def __init__(self):
        self.base_url = "http://175.178.147.75"
        self.session = requests.Session()
        self.results = []
        self.lock = threading.Lock()
        
    def login(self, username, password):
        """用户登录"""
        try:
            # 获取登录页面
            login_page = self.session.get(f"{self.base_url}/auth/login")
            
            # 提取CSRF token
            csrf_token = None
            if 'csrf_token' in login_page.text:
                import re
                match = re.search(r'name="csrf_token".*?value="([^"]+)"', login_page.text)
                if match:
                    csrf_token = match.group(1)
            
            # 登录请求
            login_data = {
                'username': username,
                'password': password,
                'csrf_token': csrf_token
            }
            
            response = self.session.post(f"{self.base_url}/auth/login", data=login_data)
            return response.status_code == 200 or 'dashboard' in response.url
            
        except Exception as e:
            print(f"登录失败: {e}")
            return False
    
    def test_page_load(self, url, description):
        """测试页面加载时间"""
        start_time = time.time()
        try:
            response = self.session.get(f"{self.base_url}{url}", timeout=10)
            end_time = time.time()
            
            result = {
                'url': url,
                'description': description,
                'status_code': response.status_code,
                'response_time': end_time - start_time,
                'success': response.status_code == 200,
                'timestamp': datetime.now().isoformat()
            }
            
            with self.lock:
                self.results.append(result)
                
            return result
            
        except Exception as e:
            end_time = time.time()
            result = {
                'url': url,
                'description': description,
                'status_code': None,
                'response_time': end_time - start_time,
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            
            with self.lock:
                self.results.append(result)
                
            return result
    
    def simulate_user_session(self, user_id):
        """模拟用户会话"""
        # 用户账号配置
        users = [
            ('admin', 'admin123'),
            ('PHC', 'PHC123'),
            ('KSC', 'KSC123'),
            ('CDC', 'CDC123'),
            ('PXC', 'PXC123'),
            ('MG', 'MG123')
        ]
        
        username, password = users[user_id % len(users)]
        
        print(f"🔄 用户 {username} 开始测试...")
        
        # 登录
        if not self.login(username, password):
            print(f"❌ 用户 {username} 登录失败")
            return
        
        # 测试页面访问
        test_pages = [
            ('/', '首页'),
            ('/inventory/list', '库存列表'),
            ('/inbound/list', '入库记录'),
            ('/outbound/list', '出库记录'),
            ('/admin/users', '用户管理'),
        ]
        
        for url, desc in test_pages:
            result = self.test_page_load(url, f"{username} - {desc}")
            status = "✅" if result['success'] else "❌"
            print(f"  {status} {desc}: {result['response_time']:.3f}s")
            
            # 随机等待，模拟真实用户行为
            time.sleep(random.uniform(0.5, 2.0))
        
        print(f"✅ 用户 {username} 测试完成")
    
    def run_concurrent_test(self, concurrent_users=15):
        """运行并发测试"""
        print(f"🚀 开始性能测试 - {concurrent_users}个并发用户")
        print("=" * 60)
        
        start_time = time.time()
        
        # 创建线程
        threads = []
        for i in range(concurrent_users):
            thread = threading.Thread(target=self.simulate_user_session, args=(i,))
            threads.append(thread)
        
        # 启动所有线程
        for thread in threads:
            thread.start()
            time.sleep(0.1)  # 稍微错开启动时间
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print("=" * 60)
        print(f"📊 测试完成，总耗时: {total_time:.2f}秒")
        
        # 分析结果
        self.analyze_results()
    
    def analyze_results(self):
        """分析测试结果"""
        if not self.results:
            print("❌ 没有测试结果")
            return
        
        successful_requests = [r for r in self.results if r['success']]
        failed_requests = [r for r in self.results if not r['success']]
        
        if successful_requests:
            response_times = [r['response_time'] for r in successful_requests]
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            min_response_time = min(response_times)
        else:
            avg_response_time = max_response_time = min_response_time = 0
        
        print(f"📈 性能统计:")
        print(f"   总请求数: {len(self.results)}")
        print(f"   成功请求: {len(successful_requests)}")
        print(f"   失败请求: {len(failed_requests)}")
        print(f"   成功率: {len(successful_requests)/len(self.results)*100:.1f}%")
        print(f"   平均响应时间: {avg_response_time:.3f}秒")
        print(f"   最快响应时间: {min_response_time:.3f}秒")
        print(f"   最慢响应时间: {max_response_time:.3f}秒")
        
        # 性能评估
        print(f"\n💡 性能评估:")
        if avg_response_time < 1.0:
            print("   ✅ 响应时间优秀")
        elif avg_response_time < 2.0:
            print("   ⚠️  响应时间良好")
        else:
            print("   ❌ 响应时间需要优化")
        
        if len(successful_requests)/len(self.results) > 0.95:
            print("   ✅ 系统稳定性优秀")
        elif len(successful_requests)/len(self.results) > 0.90:
            print("   ⚠️  系统稳定性良好")
        else:
            print("   ❌ 系统稳定性需要改进")
        
        # 保存详细结果
        with open('performance_test_results.json', 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        print(f"\n📄 详细结果已保存到: performance_test_results.json")

if __name__ == "__main__":
    tester = PerformanceTest()
    tester.run_concurrent_test(concurrent_users=15)
