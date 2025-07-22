#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from app import create_app, db
from app.models import OutboundRecord

def fix_existing_data():
    """修复现有数据中的空字段"""
    app = create_app()
    with app.app_context():
        print('修复现有数据中的空字段')
        print('=' * 60)
        
        # 查找出境模式为空的记录
        empty_export_mode = OutboundRecord.query.filter(
            (OutboundRecord.export_mode == '') | (OutboundRecord.export_mode.is_(None))
        ).filter(OutboundRecord.destination.like('%春疆%')).all()
        
        print(f'找到 {len(empty_export_mode)} 条出境模式为空的春疆货场记录')
        
        # 查找报关行为空的记录
        empty_customs_broker = OutboundRecord.query.filter(
            (OutboundRecord.customs_broker == '') | (OutboundRecord.customs_broker.is_(None))
        ).filter(OutboundRecord.destination.like('%春疆%')).all()
        
        print(f'找到 {len(empty_customs_broker)} 条报关行为空的春疆货场记录')
        
        # 查找订单类型为空的记录
        empty_order_type = OutboundRecord.query.filter(
            OutboundRecord.order_type.is_(None)
        ).filter(OutboundRecord.destination.like('%春疆%')).all()
        
        print(f'找到 {len(empty_order_type)} 条订单类型为空的春疆货场记录')
        
        # 修复这些记录
        fixed_count = 0
        
        for record in empty_export_mode:
            if not record.export_mode:
                record.export_mode = '保税'  # 设置默认值
                fixed_count += 1
        
        for record in empty_customs_broker:
            if not record.customs_broker:
                record.customs_broker = 'CFW'  # 设置默认值
                fixed_count += 1
        
        for record in empty_order_type:
            if record.order_type is None:
                record.order_type = '换车出境'  # 设置默认值
                fixed_count += 1
        
        # 提交更改
        if fixed_count > 0:
            db.session.commit()
            print(f'已修复 {fixed_count} 个字段')
        else:
            print('没有需要修复的字段')
        
        # 验证修复结果
        print('\n验证修复结果:')
        
        # 重新查询最新的记录
        recent_records = OutboundRecord.query.filter(
            OutboundRecord.destination.like('%春疆%')
        ).order_by(OutboundRecord.outbound_time.desc()).limit(5).all()
        
        for record in recent_records:
            print(f'记录ID: {record.id}')
            print(f'  客户: {record.customer_name}')
            print(f'  出境模式: "{record.export_mode}"')
            print(f'  报关行: "{record.customs_broker}"')
            print(f'  订单类型: "{record.order_type}"')
            print('---')

if __name__ == '__main__':
    fix_existing_data()
