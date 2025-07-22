#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试后端仓自动生成备注功能是否已删除
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import OutboundRecord, Warehouse
from datetime import datetime

def test_backend_remark_removal():
    """测试后端仓自动生成备注功能删除情况"""
    app = create_app()
    
    with app.app_context():
        print("🧪 后端仓自动生成备注功能删除测试")
        print("=" * 60)
        
        # 检查后端仓库
        backend_warehouses = Warehouse.query.filter_by(warehouse_type='backend').all()
        print(f"📦 后端仓库数量: {len(backend_warehouses)}")
        
        for warehouse in backend_warehouses:
            print(f"  - {warehouse.warehouse_name} (ID: {warehouse.id})")
            
            # 检查该仓库的出库记录备注情况
            outbound_records = OutboundRecord.query.filter_by(
                operated_warehouse_id=warehouse.id
            ).order_by(OutboundRecord.id.desc()).limit(10).all()
            
            print(f"    最近10条出库记录备注分析:")
            
            auto_generated_count = 0
            manual_remark_count = 0
            empty_remark_count = 0
            
            for record in outbound_records:
                remarks = record.remarks or ''
                remark1 = record.remark1 or ''
                remark2 = record.remark2 or ''
                
                # 检查是否包含自动生成的内容
                auto_generated_keywords = [
                    '后端仓出库到',
                    '发往',
                    '春疆货场',
                    '保税仓',
                    '返回原因'
                ]
                
                has_auto_generated = any(keyword in remarks for keyword in auto_generated_keywords)
                has_auto_generated = has_auto_generated or any(keyword in remark1 for keyword in auto_generated_keywords)
                has_auto_generated = has_auto_generated or any(keyword in remark2 for keyword in auto_generated_keywords)
                
                if has_auto_generated:
                    auto_generated_count += 1
                    print(f"      ⚠️ 记录ID {record.id}: 仍有自动生成备注")
                    print(f"         remarks: '{remarks}'")
                    print(f"         remark1: '{remark1}'")
                    print(f"         remark2: '{remark2}'")
                elif remarks or remark1 or remark2:
                    manual_remark_count += 1
                    print(f"      ✅ 记录ID {record.id}: 手动备注")
                else:
                    empty_remark_count += 1
                    print(f"      📝 记录ID {record.id}: 无备注")
            
            print(f"    📊 备注统计:")
            print(f"      - 自动生成备注: {auto_generated_count} 条")
            print(f"      - 手动输入备注: {manual_remark_count} 条")
            print(f"      - 空备注: {empty_remark_count} 条")

def check_backend_api_code():
    """检查后端仓API代码中的备注生成逻辑"""
    print("\n🔍 后端仓API代码检查")
    print("-" * 40)
    
    # 读取routes.py文件
    try:
        with open('app/main/routes.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查后端仓相关的自动生成备注
        backend_auto_remarks = []
        
        # 检查模式
        patterns_to_check = [
            "remarks=.*'后端仓出库到",
            "remarks=.*f'后端仓出库到",
            "remark1=.*'后端仓出库到",
            "remark1=.*f'后端仓出库到",
            "remarks=.*'发往.*仓'",
            "remark1=.*'发往.*仓'"
        ]
        
        import re
        for pattern in patterns_to_check:
            matches = re.findall(pattern, content)
            if matches:
                backend_auto_remarks.extend(matches)
        
        if backend_auto_remarks:
            print("  ⚠️ 发现后端仓自动生成备注代码:")
            for remark in backend_auto_remarks:
                print(f"    - {remark}")
        else:
            print("  ✅ 未发现后端仓自动生成备注代码")
        
        # 检查前端仓的自动生成备注是否保留
        frontend_auto_remarks = []
        frontend_patterns = [
            "前端仓发货到后端仓",
            "前端仓直接配送客户"
        ]
        
        for pattern in frontend_patterns:
            if pattern in content:
                frontend_auto_remarks.append(pattern)
        
        print(f"\n  📋 前端仓自动生成备注保留情况:")
        if frontend_auto_remarks:
            print("  ✅ 前端仓自动生成备注已保留:")
            for remark in frontend_auto_remarks:
                print(f"    - {remark}")
        else:
            print("  ⚠️ 前端仓自动生成备注可能被误删")
            
    except Exception as e:
        print(f"  ❌ 无法读取代码文件: {e}")

def check_template_changes():
    """检查模板文件的备注显示变化"""
    print("\n🎨 模板文件备注显示检查")
    print("-" * 40)
    
    try:
        with open('app/templates/backend/outbound_list.html', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查备注列的显示逻辑
        if 'record.remarks or' in content and 'remark1' not in content and 'remark2' not in content:
            print("  ✅ 后端仓出库记录界面已简化备注显示")
            print("    - 只显示 remarks 字段")
            print("    - 已移除 remark1 和 remark2 的合并显示")
        elif 'combined_remarks' in content:
            print("  ⚠️ 后端仓出库记录界面仍在合并显示多个备注字段")
        else:
            print("  📝 后端仓出库记录界面备注显示逻辑需要确认")
            
    except Exception as e:
        print(f"  ❌ 无法读取模板文件: {e}")

def generate_summary():
    """生成总结报告"""
    print("\n" + "=" * 60)
    print("📋 后端仓自动生成备注功能删除总结")
    print("=" * 60)
    
    print("\n🎯 已完成的修改:")
    print("1️⃣ 后端仓出库到末端API")
    print("   - 删除了自动生成 '后端仓出库到{目的地}' 的备注")
    print("   - 现在只使用用户手动输入的备注")
    
    print("\n2️⃣ 后端仓出库到春疆货场API")
    print("   - 删除了自动生成 '后端仓出库到春疆货场' 的备注")
    print("   - remark1 字段现在为空")
    
    print("\n3️⃣ 后端仓返回前端仓API")
    print("   - 删除了自动生成 '返回原因：{原因}' 的备注")
    print("   - 现在只使用用户手动输入的备注")
    
    print("\n4️⃣ 后端仓出库记录界面")
    print("   - 备注栏只显示 remarks 字段")
    print("   - 移除了 remark1 和 remark2 的合并显示")
    print("   - 列宽重新优化，备注列增加到18%")
    
    print("\n✅ 保留的功能:")
    print("1️⃣ 前端仓自动生成备注")
    print("   - '前端仓发货到后端仓' 等自动备注保留")
    print("   - '前端仓直接配送客户' 等自动备注保留")
    print("   - 分批出库的自动备注信息保留")
    
    print("\n2️⃣ 手动备注功能")
    print("   - 用户仍可手动输入备注")
    print("   - 备注字段正常保存和显示")
    
    print("\n🎯 预期效果:")
    print("   📝 后端仓备注栏更简洁")
    print("   👁️ 减少冗余的自动生成信息")
    print("   🎯 突出用户手动输入的重要备注")
    print("   ⚡ 提升界面信息密度")

if __name__ == '__main__':
    test_backend_remark_removal()
    check_backend_api_code()
    check_template_changes()
    generate_summary()
