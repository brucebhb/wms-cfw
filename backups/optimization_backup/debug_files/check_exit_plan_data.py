#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from app import create_app, db
from app.models import OutboundRecord

def check_exit_plan_data():
    """检查出境计划单数据"""
    app = create_app()
    with app.app_context():
        print('检查出境计划单数据')
        print('=' * 60)
        
        # 查找最近的出库记录，特别是发往春疆货场的
        recent_records = OutboundRecord.query.filter(
            OutboundRecord.destination.like('%春疆%')
        ).order_by(OutboundRecord.outbound_time.desc()).limit(10).all()
        
        print(f'找到 {len(recent_records)} 条发往春疆货场的记录:')
        
        for record in recent_records:
            print(f'\n记录ID: {record.id}')
            print(f'  客户: {record.customer_name}')
            print(f'  识别编码: {record.identification_code}')
            print(f'  批次号: {record.batch_no}')
            print(f'  出境模式: "{record.export_mode}"')
            print(f'  报关行: "{record.customs_broker}"')
            print(f'  订单类型: "{record.order_type}"')
            print(f'  目的地: {record.destination}')
            print(f'  出库时间: {record.outbound_time}')
            
            # 检查字段是否为None或空字符串
            if not record.export_mode:
                print(f'  ⚠️  出境模式为空')
            if not record.customs_broker:
                print(f'  ⚠️  报关行为空')
            if not record.order_type:
                print(f'  ⚠️  订单类型为空')
        
        # 也检查一些其他的出库记录
        print(f'\n检查所有最近的出库记录:')
        all_recent = OutboundRecord.query.order_by(OutboundRecord.outbound_time.desc()).limit(5).all()
        
        for record in all_recent:
            print(f'\n记录ID: {record.id} - {record.customer_name}')
            print(f'  出境模式: "{record.export_mode}" (类型: {type(record.export_mode)})')
            print(f'  报关行: "{record.customs_broker}" (类型: {type(record.customs_broker)})')
            print(f'  订单类型: "{record.order_type}" (类型: {type(record.order_type)})')

if __name__ == '__main__':
    check_exit_plan_data()
