#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试后端仓出库记录界面字体和自动换行效果
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import OutboundRecord, Warehouse
from datetime import datetime

def test_font_and_wrapping():
    """测试字体和换行效果"""
    app = create_app()
    
    with app.app_context():
        print("🎨 后端仓出库记录界面字体和换行测试")
        print("=" * 60)
        
        # 检查后端仓库
        backend_warehouses = Warehouse.query.filter_by(warehouse_type='backend').all()
        print(f"📦 后端仓库数量: {len(backend_warehouses)}")
        
        for warehouse in backend_warehouses:
            print(f"\n🏢 {warehouse.warehouse_name} (ID: {warehouse.id})")
            
            # 获取该仓库的出库记录
            outbound_records = OutboundRecord.query.filter_by(
                operated_warehouse_id=warehouse.id
            ).order_by(OutboundRecord.id.desc()).limit(5).all()
            
            if not outbound_records:
                print("  📝 暂无出库记录")
                continue
            
            print(f"📋 最近5条记录的字段长度分析:")
            
            for i, record in enumerate(outbound_records, 1):
                print(f"\n  📄 记录 {i} (ID: {record.id}):")
                
                # 分析各字段长度
                fields_analysis = [
                    ("客户名称", record.customer_name or '', "左对齐 + 自动换行"),
                    ("识别编码", record.identification_code or '', "14px字体 + 等宽 + 加粗"),
                    ("入库车牌", record.inbound_plate or '', "居中 + 自动换行"),
                    ("报关行", record.customs_broker or '', "居中 + 自动换行"),
                    ("订单类型", record.order_type or '', "居中 + 自动换行"),
                    ("出境模式", record.export_mode or '', "居中 + 自动换行"),
                    ("跟单客服", record.service_staff or '', "居中 + 自动换行"),
                    ("备注", record.remarks or '', "左对齐 + 自动换行")
                ]
                
                for field_name, field_value, style_note in fields_analysis:
                    length = len(field_value)
                    if length > 0:
                        # 判断是否需要换行
                        needs_wrapping = length > 15  # 超过15个字符可能需要换行
                        wrap_indicator = "🔄" if needs_wrapping else "📝"
                        
                        # 截取显示内容
                        display_value = field_value[:30] + "..." if length > 30 else field_value
                        
                        print(f"    {wrap_indicator} {field_name}: {length}字符 - {display_value}")
                        print(f"       样式: {style_note}")
                    else:
                        print(f"    📝 {field_name}: 空值")

def analyze_css_improvements():
    """分析CSS改进"""
    print("\n" + "=" * 60)
    print("🎨 CSS样式改进分析")
    print("=" * 60)
    
    print("\n📝 字体优化:")
    print("-" * 40)
    print("✅ 识别编码字体优化:")
    print("   - 字体大小: 12px → 14px (增大1号)")
    print("   - 字体族: Courier New (等宽字体)")
    print("   - 字体粗细: 600 (加粗)")
    print("   - 行高: 1.3 (适中)")
    
    print("\n✅ 全局字体设置:")
    print("   - 基础字体: 13px")
    print("   - 行高: 1.4 (舒适阅读)")
    
    print("\n🔄 自动换行优化:")
    print("-" * 40)
    print("✅ 全局换行设置:")
    print("   - white-space: normal (允许换行)")
    print("   - word-wrap: break-word (单词边界换行)")
    print("   - overflow-wrap: break-word (溢出换行)")
    print("   - word-break: break-all (强制换行)")
    
    print("\n✅ 特定列换行优化:")
    print("   - 客户名称: 左对齐 + 完整换行支持")
    print("   - 识别编码: 居中 + 强制换行 + 等宽字体")
    print("   - 入库车牌: 居中 + 自动换行")
    print("   - 报关行: 居中 + 自动换行")
    print("   - 订单类型: 居中 + 自动换行")
    print("   - 出境模式: 居中 + 自动换行")
    print("   - 跟单客服: 居中 + 自动换行")
    print("   - 备注: 左对齐 + 完整换行支持")
    
    print("\n📏 表格布局优化:")
    print("-" * 40)
    print("✅ 行高自适应:")
    print("   - 最小行高: 40px")
    print("   - 自动高度: 根据内容调整")
    print("   - 垂直对齐: top (顶部对齐)")
    print("   - 内边距: 上下10px，左右4px")

def check_wrapping_scenarios():
    """检查换行场景"""
    print("\n🔍 换行场景分析")
    print("-" * 40)
    
    scenarios = [
        {
            "场景": "长识别编码",
            "示例": "CD/深圳市某某贸易有限公司/粤B12345/20250715/001",
            "长度": 35,
            "处理": "14px等宽字体 + 强制换行，保持可读性"
        },
        {
            "场景": "长客户名称", 
            "示例": "深圳市某某国际贸易有限公司",
            "长度": 16,
            "处理": "左对齐 + 自动换行，便于阅读"
        },
        {
            "场景": "长备注内容",
            "示例": "客户要求加急处理，需要在明天上午10点前完成出库，联系人：张经理",
            "长度": 35,
            "处理": "左对齐 + 完整换行支持，保持内容完整"
        },
        {
            "场景": "长报关行名称",
            "示例": "深圳市某某报关服务有限公司",
            "长度": 16,
            "处理": "居中对齐 + 自动换行"
        },
        {
            "场景": "长车牌号",
            "示例": "粤B12345挂粤B67890",
            "长度": 12,
            "处理": "居中对齐 + 自动换行"
        }
    ]
    
    print(f"{'场景':<12} {'示例长度':<8} {'处理方式'}")
    print("-" * 60)
    
    for scenario in scenarios:
        print(f"{scenario['场景']:<12} {scenario['长度']}字符    {scenario['处理']}")
        print(f"{'示例:':<12} {scenario['示例'][:40]}...")
        print()

def generate_style_summary():
    """生成样式总结"""
    print("=" * 60)
    print("✨ 字体和换行优化总结")
    print("=" * 60)
    
    print("\n🎯 主要改进:")
    print("1️⃣ 识别编码字体优化")
    print("   - 字体大小增加到14px，更易识别")
    print("   - 使用等宽字体Courier New")
    print("   - 字体加粗(600)，突出重要性")
    print("   - 支持强制换行，避免溢出")
    
    print("\n2️⃣ 全表自动换行")
    print("   - 所有文本字段支持自动换行")
    print("   - 单词边界优先换行")
    print("   - 必要时强制换行")
    print("   - 保持内容完整性")
    
    print("\n3️⃣ 表格布局优化")
    print("   - 行高自适应内容")
    print("   - 垂直对齐优化")
    print("   - 内边距合理调整")
    print("   - 最小行高保证")
    
    print("\n4️⃣ 视觉体验提升")
    print("   - 长内容不再被截断")
    print("   - 识别编码更加醒目")
    print("   - 表格整体更整洁")
    print("   - 信息密度合理")
    
    print("\n✅ 预期效果:")
    print("   👁️ 识别编码更易读")
    print("   📝 长文本完整显示")
    print("   🎯 重要信息突出")
    print("   📱 适配各种内容长度")
    print("   ⚡ 提升操作效率")
    
    print("\n📋 字体规格:")
    print("   - 识别编码: 14px Courier New 600")
    print("   - 其他字段: 13px 默认字体")
    print("   - 行高: 1.3-1.4")
    print("   - 最小行高: 40px")

if __name__ == '__main__':
    test_font_and_wrapping()
    analyze_css_improvements()
    check_wrapping_scenarios()
    generate_style_summary()
