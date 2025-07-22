#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据恢复选项
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import InboundRecord, OutboundRecord
from datetime import datetime, timedelta

def check_recovery_options():
    """检查数据恢复选项"""
    
    app = create_app()
    with app.app_context():
        print("=== 检查数据恢复选项 ===")
        
        # 1. 检查是否有created_at或updated_at时间戳可以帮助识别原始数据
        print("\n1. 检查记录的时间戳信息")
        print("-" * 50)
        
        # 检查最近修改的记录
        recent_inbound = InboundRecord.query.filter(
            InboundRecord.updated_at >= datetime.now() - timedelta(hours=2)
        ).order_by(InboundRecord.updated_at.desc()).limit(10).all()
        
        print(f"最近2小时内修改的入库记录: {len(recent_inbound)}条")
        for record in recent_inbound[:5]:
            print(f"  ID: {record.id}, 客户: {record.customer_name}, 更新时间: {record.updated_at}")
        
        recent_outbound = OutboundRecord.query.filter(
            OutboundRecord.updated_at >= datetime.now() - timedelta(hours=2)
        ).order_by(OutboundRecord.updated_at.desc()).limit(10).all()
        
        print(f"\n最近2小时内修改的出库记录: {len(recent_outbound)}条")
        for record in recent_outbound[:5]:
            print(f"  ID: {record.id}, 客户: {record.customer_name}, 更新时间: {record.updated_at}")
        
        # 2. 检查是否有其他字段可以推断原始单据份数
        print("\n2. 检查是否有其他相关字段")
        print("-" * 50)
        
        # 检查documents字段是否还保留了原始信息
        inbound_with_docs = InboundRecord.query.filter(
            InboundRecord.documents.isnot(None),
            InboundRecord.documents != '',
            InboundRecord.documents != '1'
        ).limit(10).all()
        
        print(f"入库记录中documents字段不为'1'的记录: {len(inbound_with_docs)}条")
        for record in inbound_with_docs:
            print(f"  ID: {record.id}, 客户: {record.customer_name}, documents: '{record.documents}'")
        
        outbound_with_docs = OutboundRecord.query.filter(
            OutboundRecord.documents.isnot(None),
            OutboundRecord.documents != '',
            OutboundRecord.documents != '1份'
        ).limit(10).all()
        
        print(f"\n出库记录中documents字段不为'1份'的记录: {len(outbound_with_docs)}条")
        for record in outbound_with_docs:
            print(f"  ID: {record.id}, 客户: {record.customer_name}, documents: '{record.documents}'")
        
        # 3. 检查数据库配置，看是否启用了二进制日志
        print("\n3. 检查数据库恢复选项")
        print("-" * 50)
        
        try:
            # 检查MySQL配置
            result = db.session.execute(db.text("SHOW VARIABLES LIKE 'log_bin'")).fetchone()
            if result:
                print(f"MySQL二进制日志状态: {result[1]}")
            
            # 检查是否有binlog文件
            result = db.session.execute(db.text("SHOW BINARY LOGS")).fetchall()
            if result:
                print(f"可用的二进制日志文件: {len(result)}个")
                for log in result[-3:]:  # 显示最后3个
                    print(f"  {log[0]} - {log[1]} bytes")
            else:
                print("没有找到二进制日志文件")
                
        except Exception as e:
            print(f"检查数据库日志时出错: {str(e)}")
        
        # 4. 建议恢复方案
        print("\n4. 数据恢复建议")
        print("-" * 50)
        print("由于我错误地修改了您的数据，以下是可能的恢复方案：")
        print("1. 如果您有数据库备份文件，可以从备份恢复")
        print("2. 如果MySQL启用了二进制日志，可以通过日志回滚")
        print("3. 如果您记得原始的单据份数规则，我可以帮您重新设置")
        print("4. 检查是否有其他系统或文件保存了原始数据")
        
        print("\n请告诉我：")
        print("- 您是否有数据库备份？")
        print("- 您记得原始的单据份数是如何分布的吗？")
        print("- 是否有特定的业务规则来确定单据份数？")

if __name__ == "__main__":
    try:
        check_recovery_options()
    except Exception as e:
        print(f"\n❌ 检查过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()
