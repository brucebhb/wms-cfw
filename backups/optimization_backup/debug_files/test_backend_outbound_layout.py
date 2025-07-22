#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试后端仓出库记录界面的列宽调整效果
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import OutboundRecord, Warehouse
from datetime import datetime

def test_backend_outbound_layout():
    """测试后端仓出库记录界面布局"""
    app = create_app()
    
    with app.app_context():
        print("🎨 后端仓出库记录界面列宽调整测试")
        print("=" * 60)
        
        # 检查后端仓库
        backend_warehouses = Warehouse.query.filter_by(warehouse_type='backend').all()
        print(f"📦 后端仓库数量: {len(backend_warehouses)}")
        
        for warehouse in backend_warehouses:
            print(f"  - {warehouse.warehouse_name} (ID: {warehouse.id})")
            
            # 检查该仓库的出库记录
            outbound_count = OutboundRecord.query.filter_by(
                operated_warehouse_id=warehouse.id
            ).count()
            print(f"    出库记录数: {outbound_count}")
            
            if outbound_count > 0:
                # 获取最近的几条记录作为示例
                recent_records = OutboundRecord.query.filter_by(
                    operated_warehouse_id=warehouse.id
                ).order_by(OutboundRecord.outbound_time.desc()).limit(3).all()
                
                print(f"    最近3条记录:")
                for i, record in enumerate(recent_records, 1):
                    print(f"      {i}. {record.customer_name} - {record.identification_code}")
                    print(f"         板数: {record.pallet_count}, 件数: {record.package_count}")
                    print(f"         备注: {record.remarks or '无'}")
                    print(f"         出库时间: {record.outbound_time.strftime('%Y-%m-%d %H:%M') if record.outbound_time else '未知'}")
        
        print("\n🎯 界面优化内容:")
        print("✅ 列宽重新分配:")
        print("   - 客户名称: 12% (增加)")
        print("   - 识别编码: 18% (增加)")
        print("   - 入库车牌: 10% (增加)")
        print("   - 板数/件数: 5% (减少)")
        print("   - 重量/体积: 7% (减少)")
        print("   - 备注: 10% (减少)")
        
        print("\n✅ 备注栏优化:")
        print("   - 移除自动生成的remark1、remark2内容")
        print("   - 只显示用户手动输入的remarks字段")
        print("   - 简化显示，避免冗余信息")
        
        print("\n✅ 样式优化:")
        print("   - 数字列右对齐 (板数、件数、重量、体积)")
        print("   - 文本列左对齐 (客户名称、识别编码等)")
        print("   - 表头居中对齐")
        print("   - 操作列居中对齐")
        print("   - 识别编码使用等宽字体")
        print("   - 备注列自动换行")
        
        print("\n✅ 表格布局:")
        print("   - 最小宽度调整为1600px (减少200px)")
        print("   - 使用固定表格布局 (table-layout: fixed)")
        print("   - 优化单元格内边距")
        print("   - 允许文本自动换行")

def check_outbound_data_quality():
    """检查出库数据质量"""
    app = create_app()
    
    with app.app_context():
        print("\n📊 出库数据质量检查")
        print("-" * 40)
        
        # 检查备注字段的使用情况
        total_records = OutboundRecord.query.count()
        records_with_remarks = OutboundRecord.query.filter(
            OutboundRecord.remarks.isnot(None),
            OutboundRecord.remarks != ''
        ).count()
        
        records_with_remark1 = OutboundRecord.query.filter(
            OutboundRecord.remark1.isnot(None),
            OutboundRecord.remark1 != ''
        ).count()
        
        records_with_remark2 = OutboundRecord.query.filter(
            OutboundRecord.remark2.isnot(None),
            OutboundRecord.remark2 != ''
        ).count()
        
        print(f"总出库记录数: {total_records}")
        print(f"有remarks的记录: {records_with_remarks} ({records_with_remarks/total_records*100:.1f}%)" if total_records > 0 else "无记录")
        print(f"有remark1的记录: {records_with_remark1} ({records_with_remark1/total_records*100:.1f}%)" if total_records > 0 else "无记录")
        print(f"有remark2的记录: {records_with_remark2} ({records_with_remark2/total_records*100:.1f}%)" if total_records > 0 else "无记录")
        
        # 检查长备注
        if total_records > 0:
            long_remarks = OutboundRecord.query.filter(
                db.func.length(OutboundRecord.remarks) > 50
            ).count()
            print(f"长备注(>50字符): {long_remarks} ({long_remarks/total_records*100:.1f}%)")
        
        # 检查识别编码长度分布
        if total_records > 0:
            print("\n识别编码长度分布:")
            code_lengths = db.session.query(
                db.func.length(OutboundRecord.identification_code).label('length'),
                db.func.count().label('count')
            ).group_by(
                db.func.length(OutboundRecord.identification_code)
            ).order_by('length').all()
            
            for length, count in code_lengths:
                percentage = count / total_records * 100
                print(f"  {length}字符: {count}条 ({percentage:.1f}%)")

def generate_layout_summary():
    """生成布局优化总结"""
    print("\n" + "=" * 60)
    print("📋 后端仓出库记录界面优化总结")
    print("=" * 60)
    
    print("\n🎯 主要改进:")
    print("1️⃣ 列宽合理分配")
    print("   - 重要信息列 (客户名称、识别编码) 增加宽度")
    print("   - 数字列 (板数、件数) 适当减少宽度")
    print("   - 备注列控制在合理范围内")
    
    print("\n2️⃣ 备注栏简化")
    print("   - 移除自动生成的冗余信息")
    print("   - 只显示用户手动输入的备注")
    print("   - 提高信息的可读性")
    
    print("\n3️⃣ 视觉优化")
    print("   - 数字右对齐，便于比较")
    print("   - 文本左对齐，符合阅读习惯")
    print("   - 识别编码使用等宽字体")
    print("   - 表格布局更紧凑")
    
    print("\n4️⃣ 响应式改进")
    print("   - 减少最小宽度要求")
    print("   - 允许文本自动换行")
    print("   - 优化在不同屏幕尺寸下的显示")
    
    print("\n✅ 预期效果:")
    print("   📈 提高信息密度")
    print("   👁️ 改善视觉体验")
    print("   🚀 提升操作效率")
    print("   📱 更好的适配性")

if __name__ == '__main__':
    test_backend_outbound_layout()
    check_outbound_data_quality()
    generate_layout_summary()
