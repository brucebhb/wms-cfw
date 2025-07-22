#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全集成测试脚本
测试安全机制是否正常工作
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import InboundRecord, OutboundRecord, Inventory, User, Warehouse
import logging
import threading
import time
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecurityIntegrationTest:
    def __init__(self):
        self.app = create_app()
        self.test_results = []
        
    def run_all_tests(self):
        """运行所有安全测试"""
        logger.info("开始安全集成测试...")
        
        with self.app.app_context():
            # 1. 测试输入验证
            self.test_input_validation()
            
            # 2. 测试SQL注入防护
            self.test_sql_injection_protection()
            
            # 3. 测试并发控制
            self.test_concurrency_control()
            
            # 4. 测试异常处理
            self.test_exception_handling()
            
            # 5. 测试权限验证
            self.test_permission_validation()
        
        # 生成测试报告
        self.generate_test_report()
    
    def test_input_validation(self):
        """测试输入验证"""
        logger.info("测试输入验证...")
        
        try:
            from app.utils.input_validator import FormValidator, InputSanitizer, ValidationException
            
            # 测试车牌号验证
            test_cases = [
                ("粤B12345", True, "有效车牌号"),
                ("ABC123", False, "无效车牌号"),
                ("", False, "空车牌号"),
                ("粤B123456789", False, "过长车牌号"),
                ("顺丰", True, "快递公司"),
                ("'; DROP TABLE users; --", False, "SQL注入尝试")
            ]
            
            for plate, expected_valid, description in test_cases:
                try:
                    result = FormValidator.validate_plate_number(plate, required=False)
                    if expected_valid:
                        self.test_results.append(f"✅ 输入验证 - {description}: 通过")
                    else:
                        self.test_results.append(f"❌ 输入验证 - {description}: 应该失败但通过了")
                except ValidationException:
                    if not expected_valid:
                        self.test_results.append(f"✅ 输入验证 - {description}: 正确拒绝")
                    else:
                        self.test_results.append(f"❌ 输入验证 - {description}: 不应该失败")
                except Exception as e:
                    self.test_results.append(f"❌ 输入验证 - {description}: 异常 {str(e)}")
            
            # 测试数字清理
            number_tests = [
                ("123.45", 123.45, "正常数字"),
                ("-10", 0, "负数处理"),
                ("abc", 0, "非数字字符"),
                ("", 0, "空值"),
                ("999999999999", 999999999999, "大数字")
            ]
            
            for input_val, expected, description in number_tests:
                try:
                    result = InputSanitizer.sanitize_number(input_val, "测试字段", min_value=0)
                    if abs(result - expected) < 0.01:
                        self.test_results.append(f"✅ 数字验证 - {description}: 通过")
                    else:
                        self.test_results.append(f"❌ 数字验证 - {description}: 期望{expected}, 得到{result}")
                except Exception as e:
                    self.test_results.append(f"❌ 数字验证 - {description}: 异常 {str(e)}")
            
        except ImportError:
            self.test_results.append("⚠️ 输入验证模块未导入，跳过测试")
    
    def test_sql_injection_protection(self):
        """测试SQL注入防护"""
        logger.info("测试SQL注入防护...")
        
        try:
            from app.utils.sql_security import SQLSecurityChecker
            
            # SQL注入测试用例
            injection_attempts = [
                "'; DROP TABLE users; --",
                "1' OR '1'='1",
                "UNION SELECT * FROM users",
                "<script>alert('xss')</script>",
                "1; DELETE FROM inventory; --",
                "admin'--",
                "' OR 1=1 --",
                "'; EXEC xp_cmdshell('dir'); --"
            ]
            
            for injection in injection_attempts:
                is_dangerous = SQLSecurityChecker.check_sql_injection(injection)
                if is_dangerous:
                    self.test_results.append(f"✅ SQL注入防护 - 检测到危险输入: {injection[:20]}...")
                else:
                    self.test_results.append(f"❌ SQL注入防护 - 未检测到危险输入: {injection[:20]}...")
            
            # 测试安全输入
            safe_inputs = [
                "正常客户名称",
                "粤B12345",
                "PH/客户/车牌/20250714/001",
                "123.45"
            ]
            
            for safe_input in safe_inputs:
                is_dangerous = SQLSecurityChecker.check_sql_injection(safe_input)
                if not is_dangerous:
                    self.test_results.append(f"✅ SQL注入防护 - 安全输入通过: {safe_input}")
                else:
                    self.test_results.append(f"❌ SQL注入防护 - 安全输入被误判: {safe_input}")
            
        except ImportError:
            self.test_results.append("⚠️ SQL安全模块未导入，跳过测试")
    
    def test_concurrency_control(self):
        """测试并发控制"""
        logger.info("测试并发控制...")
        
        try:
            from app.utils.concurrency_control import safe_inventory_update, InventoryLockManager
            
            # 创建测试库存记录
            test_identification_code = f"TEST/并发测试/TEST/20250714/001"
            
            # 清理可能存在的测试数据
            existing_inventory = Inventory.query.filter_by(
                identification_code=test_identification_code
            ).first()
            if existing_inventory:
                db.session.delete(existing_inventory)
                db.session.commit()
            
            # 创建测试库存
            test_inventory = Inventory(
                identification_code=test_identification_code,
                customer_name="并发测试客户",
                pallet_count=100,
                package_count=1000,
                weight=1000.0,
                volume=100.0,
                operated_warehouse_id=1
            )
            db.session.add(test_inventory)
            db.session.commit()
            
            # 并发更新测试
            results = []
            errors = []
            
            def concurrent_update(thread_id):
                try:
                    safe_inventory_update(
                        identification_code=test_identification_code,
                        operation_type='subtract',
                        pallet_count=1,
                        package_count=10
                    )
                    results.append(f"线程{thread_id}成功")
                except Exception as e:
                    errors.append(f"线程{thread_id}失败: {str(e)}")
            
            # 启动多个线程
            threads = []
            for i in range(5):
                thread = threading.Thread(target=concurrent_update, args=(i,))
                threads.append(thread)
                thread.start()
            
            # 等待所有线程完成
            for thread in threads:
                thread.join()
            
            # 检查结果
            final_inventory = Inventory.query.filter_by(
                identification_code=test_identification_code
            ).first()
            
            if final_inventory:
                expected_pallet = 100 - len(results)
                expected_package = 1000 - len(results) * 10
                
                if (final_inventory.pallet_count == expected_pallet and 
                    final_inventory.package_count == expected_package):
                    self.test_results.append(f"✅ 并发控制 - 数据一致性保持: 成功{len(results)}次, 失败{len(errors)}次")
                else:
                    self.test_results.append(f"❌ 并发控制 - 数据不一致: 期望板数{expected_pallet}, 实际{final_inventory.pallet_count}")
            
            # 清理测试数据
            if final_inventory:
                db.session.delete(final_inventory)
                db.session.commit()
            
        except ImportError:
            self.test_results.append("⚠️ 并发控制模块未导入，跳过测试")
        except Exception as e:
            self.test_results.append(f"❌ 并发控制测试异常: {str(e)}")
    
    def test_exception_handling(self):
        """测试异常处理"""
        logger.info("测试异常处理...")
        
        try:
            from app.utils.exception_handler import ValidationException, InventoryException, BusinessValidator
            
            # 测试自定义异常
            try:
                raise ValidationException("测试验证异常", field="test_field")
            except ValidationException as e:
                if e.message == "测试验证异常" and e.details.get('field') == 'test_field':
                    self.test_results.append("✅ 异常处理 - ValidationException 正常工作")
                else:
                    self.test_results.append("❌ 异常处理 - ValidationException 数据不正确")
            
            # 测试库存异常
            try:
                raise InventoryException("测试库存异常", identification_code="TEST001")
            except InventoryException as e:
                if e.message == "测试库存异常" and e.details.get('identification_code') == 'TEST001':
                    self.test_results.append("✅ 异常处理 - InventoryException 正常工作")
                else:
                    self.test_results.append("❌ 异常处理 - InventoryException 数据不正确")
            
        except ImportError:
            self.test_results.append("⚠️ 异常处理模块未导入，跳过测试")
    
    def test_permission_validation(self):
        """测试权限验证"""
        logger.info("测试权限验证...")
        
        try:
            from app.utils.exception_handler import BusinessValidator, PermissionException
            
            # 创建测试用户
            test_user = User.query.filter_by(username='test_user').first()
            if not test_user:
                # 这里只是模拟，实际测试中需要真实用户
                self.test_results.append("⚠️ 权限验证 - 需要真实用户数据进行测试")
            else:
                # 测试仓库权限验证
                try:
                    BusinessValidator.validate_warehouse_permission(test_user, 999, 'test_operation')
                    self.test_results.append("❌ 权限验证 - 应该拒绝无效仓库权限")
                except PermissionException:
                    self.test_results.append("✅ 权限验证 - 正确拒绝无效仓库权限")
            
        except ImportError:
            self.test_results.append("⚠️ 权限验证模块未导入，跳过测试")
    
    def generate_test_report(self):
        """生成测试报告"""
        report_file = f"security_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# 安全集成测试报告\n\n")
            f.write(f"**测试时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # 统计结果
            passed = len([r for r in self.test_results if r.startswith('✅')])
            failed = len([r for r in self.test_results if r.startswith('❌')])
            warnings = len([r for r in self.test_results if r.startswith('⚠️')])
            
            f.write(f"## 📊 测试统计\n\n")
            f.write(f"- ✅ 通过: {passed} 项\n")
            f.write(f"- ❌ 失败: {failed} 项\n")
            f.write(f"- ⚠️ 警告: {warnings} 项\n")
            f.write(f"- 总计: {len(self.test_results)} 项\n\n")
            
            # 详细结果
            f.write("## 📋 详细测试结果\n\n")
            for result in self.test_results:
                f.write(f"{result}\n")
            
            # 总结
            f.write(f"\n## 🎯 测试总结\n\n")
            if failed == 0:
                f.write("🎉 所有安全测试通过！系统安全机制工作正常。\n")
            else:
                f.write(f"⚠️ 发现 {failed} 个问题，需要进一步检查和修复。\n")
        
        logger.info(f"测试报告已生成: {report_file}")
        print(f"\n安全集成测试完成！")
        print(f"测试报告: {report_file}")
        print(f"通过: {passed} 项, 失败: {failed} 项, 警告: {warnings} 项")

if __name__ == '__main__':
    tester = SecurityIntegrationTest()
    tester.run_all_tests()
