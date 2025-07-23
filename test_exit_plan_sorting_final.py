#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from app import create_app, db
from app.models import OutboundRecord
from datetime import datetime
import sys

app = create_app()
with app.app_context():
    print('=== 测试出境计划单排序功能 ===')
    
    # 查询出境计划单记录（发往春疆货场/保税仓的记录）
    query = OutboundRecord.query.filter(
        db.and_(
            db.or_(
                OutboundRecord.destination == '春疆货场',
                OutboundRecord.destination == '凭祥保税仓',
                OutboundRecord.destination.like('%春疆%'),
                OutboundRecord.destination.like('%保税仓%'),
                OutboundRecord.detailed_address == '谅山春疆货场',
                OutboundRecord.detailed_address.like('%春疆%'),
                OutboundRecord.detailed_address.like('%保税仓%')
            ),
            # 排除后端仓返回前端仓的记录
            ~OutboundRecord.remarks.like('%后端仓返回前端仓%')
        )
    )
    
    # 按记录生成时间降序排序（最新创建的记录在前）
    records = query.order_by(OutboundRecord.created_at.desc()).limit(10).all()
    
    if not records:
        print('未找到出境计划单记录')
        sys.exit(1)
    
    print(f'找到 {len(records)} 条出境计划单记录（按创建时间降序排序）：')
    print()
    print('序号 | 记录ID | 创建时间                | 出库时间                | 客户名称     | 批次号      | 目的地')
    print('-' * 100)
    
    for i, record in enumerate(records, 1):
        created_time = record.created_at.strftime('%Y-%m-%d %H:%M:%S') if record.created_at else '无'
        outbound_time = record.outbound_time.strftime('%Y-%m-%d %H:%M:%S') if record.outbound_time else '无'
        customer_name = record.customer_name[:8] + '...' if len(record.customer_name) > 8 else record.customer_name
        batch_no = record.batch_no[:10] + '...' if record.batch_no and len(record.batch_no) > 10 else (record.batch_no or '无')
        destination = record.destination[:8] + '...' if record.destination and len(record.destination) > 8 else (record.destination or '无')
        
        print(f'{i:2d}   | {record.id:6d} | {created_time} | {outbound_time} | {customer_name:10s} | {batch_no:10s} | {destination}')
    
    print()
    print('=== 验证排序是否正确 ===')
    
    # 检查是否按创建时间降序排序
    is_sorted_correctly = True
    for i in range(len(records) - 1):
        current_time = records[i].created_at
        next_time = records[i + 1].created_at
        
        if current_time and next_time and current_time < next_time:
            is_sorted_correctly = False
            print(f'❌ 排序错误：第{i+1}条记录的创建时间 ({current_time}) 早于第{i+2}条记录 ({next_time})')
            break
    
    if is_sorted_correctly:
        print('✅ 排序正确：记录按创建时间降序排列（最新创建的在前）')
    else:
        print('❌ 排序错误：记录没有按创建时间降序排列')
    
    print()
    print('=== 测试完成 ===')
    
    # 额外测试：检查前端页面的排序逻辑
    print()
    print('=== 测试前端页面排序逻辑 ===')
    
    # 模拟前端页面的查询逻辑
    from app.main.routes import OutboundRecord
    
    # 按记录生成时间降序排序，再按批次号降序排序，最后按操作顺序降序排序
    frontend_query = OutboundRecord.query.filter(
        db.and_(
            db.or_(
                OutboundRecord.destination == '春疆货场',
                OutboundRecord.destination == '凭祥保税仓',
                OutboundRecord.destination.like('%春疆%'),
                OutboundRecord.destination.like('%保税仓%'),
                OutboundRecord.detailed_address == '谅山春疆货场',
                OutboundRecord.detailed_address.like('%春疆%'),
                OutboundRecord.detailed_address.like('%保税仓%')
            ),
            ~OutboundRecord.remarks.like('%后端仓返回前端仓%')
        )
    ).order_by(OutboundRecord.created_at.desc(), OutboundRecord.batch_no.desc(), OutboundRecord.batch_sequence.desc())
    
    frontend_records = frontend_query.limit(5).all()
    
    print(f'前端页面排序测试：找到 {len(frontend_records)} 条记录')
    for i, record in enumerate(frontend_records, 1):
        created_time = record.created_at.strftime('%Y-%m-%d %H:%M:%S') if record.created_at else '无'
        print(f'{i}. ID:{record.id} 创建时间:{created_time} 批次:{record.batch_no} 客户:{record.customer_name}')
    
    print('✅ 前端页面排序逻辑测试完成')
