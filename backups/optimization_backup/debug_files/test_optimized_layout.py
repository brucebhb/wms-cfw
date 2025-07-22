#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试优化后的后端仓出库记录界面列宽分配
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import OutboundRecord
from datetime import datetime

def analyze_column_content():
    """分析各列内容长度，验证列宽分配的合理性"""
    app = create_app()
    
    with app.app_context():
        print("📊 后端仓出库记录列宽优化分析")
        print("=" * 60)
        
        # 获取样本数据
        records = OutboundRecord.query.limit(50).all()
        
        if not records:
            print("❌ 没有找到出库记录数据")
            return
        
        print(f"📋 分析样本: {len(records)} 条记录")
        print("-" * 60)
        
        # 分析各列内容长度
        columns_analysis = {
            '客户名称': [],
            '识别编码': [],
            '入库车牌': [],
            '板数': [],
            '件数': [],
            '重量': [],
            '体积': [],
            '报关行': [],
            '跟单客服': [],
            '备注': [],
            '入库日期': []
        }
        
        for record in records:
            # 客户名称
            customer_name = record.customer_name or '-'
            columns_analysis['客户名称'].append(len(customer_name))
            
            # 识别编码
            identification_code = record.identification_code or '-'
            columns_analysis['识别编码'].append(len(identification_code))
            
            # 入库车牌
            inbound_plate = record.inbound_plate or '-'
            columns_analysis['入库车牌'].append(len(inbound_plate))
            
            # 板数
            pallet_count = str(record.pallet_count or '-')
            columns_analysis['板数'].append(len(pallet_count))
            
            # 件数
            package_count = str(record.package_count or '-')
            columns_analysis['件数'].append(len(package_count))
            
            # 重量
            weight = f"{record.weight:.1f}" if record.weight else '-'
            columns_analysis['重量'].append(len(weight))
            
            # 体积
            volume = f"{record.volume:.2f}" if record.volume else '-'
            columns_analysis['体积'].append(len(volume))
            
            # 报关行
            customs_broker = record.customs_broker or '-'
            columns_analysis['报关行'].append(len(customs_broker))
            
            # 跟单客服
            service_staff = record.service_staff or '-'
            columns_analysis['跟单客服'].append(len(service_staff))
            
            # 备注
            remarks = record.remarks or '-'
            columns_analysis['备注'].append(len(remarks))
            
            # 入库日期
            inbound_date = record.inbound_date.strftime('%Y-%m-%d') if record.inbound_date else '-'
            columns_analysis['入库日期'].append(len(inbound_date))
        
        # 输出分析结果
        print("📈 各列内容长度分析:")
        print(f"{'列名':<10} {'新宽度':<8} {'平均长度':<8} {'最大长度':<8} {'建议'}")
        print("-" * 60)
        
        column_widths = {
            '客户名称': '8%',
            '识别编码': '20%',
            '入库车牌': '8%',
            '板数': '4%',
            '件数': '4%',
            '重量': '6%',
            '体积': '6%',
            '报关行': '8%',
            '跟单客服': '6%',
            '备注': '18%',
            '入库日期': '7%'
        }
        
        for col_name, lengths in columns_analysis.items():
            avg_length = sum(lengths) / len(lengths)
            max_length = max(lengths)
            width = column_widths[col_name]
            
            # 评估宽度是否合理
            if col_name in ['板数', '件数']:
                suggestion = "✅ 合适" if max_length <= 3 else "⚠️ 可能需要更宽"
            elif col_name == '识别编码':
                suggestion = "✅ 合适" if max_length <= 60 else "⚠️ 可能需要更宽"
            elif col_name == '备注':
                suggestion = "✅ 合适" if max_length <= 100 else "⚠️ 可能需要更宽"
            elif col_name in ['客户名称', '报关行']:
                suggestion = "✅ 合适" if max_length <= 15 else "⚠️ 可能需要更宽"
            else:
                suggestion = "✅ 合适"
            
            print(f"{col_name:<10} {width:<8} {avg_length:<8.1f} {max_length:<8} {suggestion}")

def show_layout_comparison():
    """显示布局对比"""
    print("\n" + "=" * 60)
    print("📋 列宽分配对比")
    print("=" * 60)
    
    print("🔄 优化前 vs 优化后:")
    print("-" * 60)
    
    comparisons = [
        ("客户名称", "12%", "8%", "减少，内容通常较短"),
        ("识别编码", "18%", "20%", "增加，内容较长且重要"),
        ("入库车牌", "10%", "8%", "减少，车牌长度固定"),
        ("板数", "5%", "4%", "减少，数字通常较短"),
        ("件数", "5%", "4%", "减少，数字通常较短"),
        ("重量(KG)", "7%", "6%", "减少，数字长度适中"),
        ("体积(CBM)", "7%", "6%", "减少，数字长度适中"),
        ("报关行", "10%", "8%", "减少，名称通常较短"),
        ("跟单客服", "8%", "6%", "减少，姓名通常较短"),
        ("备注", "10%", "18%", "增加，内容可能较长"),
        ("入库日期", "8%", "7%", "减少，日期格式固定"),
        ("操作", "6%", "5%", "减少，按钮大小固定")
    ]
    
    print(f"{'列名':<12} {'优化前':<8} {'优化后':<8} {'说明'}")
    print("-" * 60)
    
    for col_name, old_width, new_width, reason in comparisons:
        change_icon = "📈" if new_width > old_width else "📉" if new_width < old_width else "➡️"
        print(f"{col_name:<12} {old_width:<8} {new_width:<8} {change_icon} {reason}")

def show_alignment_strategy():
    """显示对齐策略"""
    print("\n" + "=" * 60)
    print("🎯 对齐策略优化")
    print("=" * 60)
    
    alignments = [
        ("客户名称", "左对齐", "便于阅读文本内容"),
        ("识别编码", "居中对齐", "等宽字体，便于识别"),
        ("入库车牌", "居中对齐", "车牌格式统一"),
        ("板数", "右对齐", "数字便于比较"),
        ("件数", "右对齐", "数字便于比较"),
        ("重量(KG)", "右对齐", "数字便于比较"),
        ("体积(CBM)", "右对齐", "数字便于比较"),
        ("报关行", "居中对齐", "名称显示"),
        ("跟单客服", "居中对齐", "姓名显示"),
        ("备注", "左对齐", "便于阅读长文本"),
        ("入库日期", "居中对齐", "日期格式统一"),
        ("操作", "居中对齐", "按钮居中显示")
    ]
    
    print(f"{'列名':<12} {'对齐方式':<10} {'原因'}")
    print("-" * 50)
    
    for col_name, alignment, reason in alignments:
        print(f"{col_name:<12} {alignment:<10} {reason}")

def show_optimization_summary():
    """显示优化总结"""
    print("\n" + "=" * 60)
    print("✨ 优化总结")
    print("=" * 60)
    
    print("🎯 主要改进:")
    print("1️⃣ 列宽精细化调整")
    print("   - 根据实际内容长度重新分配")
    print("   - 重要信息列(识别编码、备注)获得更多空间")
    print("   - 短内容列(板数、件数)减少空间浪费")
    
    print("\n2️⃣ 对齐方式优化")
    print("   - 数字列右对齐，便于数值比较")
    print("   - 文本列左对齐，符合阅读习惯")
    print("   - 标识列居中对齐，保持整齐")
    
    print("\n3️⃣ 视觉效果提升")
    print("   - 减少表格最小宽度(1600px→1400px)")
    print("   - 优化单元格内边距")
    print("   - 识别编码使用等宽字体")
    
    print("\n4️⃣ 用户体验改善")
    print("   - 信息密度更合理")
    print("   - 重要信息更突出")
    print("   - 减少横向滚动需求")
    
    print("\n✅ 预期效果:")
    print("   📊 更高的信息利用率")
    print("   👁️ 更好的视觉层次")
    print("   🚀 更快的信息获取")
    print("   📱 更好的屏幕适配")

if __name__ == '__main__':
    analyze_column_content()
    show_layout_comparison()
    show_alignment_strategy()
    show_optimization_summary()
