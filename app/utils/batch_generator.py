#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批次号生成器
"""

from datetime import datetime
from sqlalchemy import and_

def generate_batch_number(warehouse_id, destination_prefix=None, db_session=None):
    """
    生成批次号
    
    Args:
        warehouse_id: 仓库ID
        destination_prefix: 目的地前缀 (CJ=春疆货场, PB=凭祥保税仓, CK=客户配送, RT=返回)
        db_session: 数据库会话
        
    Returns:
        str: 生成的批次号
    """
    from app.models import OutboundRecord
    
    # 仓库前缀映射
    warehouse_prefixes = {
        1: 'PH',  # 平湖仓
        2: 'KS',  # 昆山仓
        3: 'CD',  # 成都仓
        4: 'PX'   # 凭祥北投仓
    }
    
    # 获取日期前缀
    today = datetime.now()
    date_prefix = today.strftime('%y%m%d')  # 年月日，如"250707"
    
    # 确定批次号前缀
    if destination_prefix:
        # 特殊目的地批次号 (如春疆货场CJ, 凭祥保税仓PB)
        batch_prefix = destination_prefix
    else:
        # 普通仓库间转运批次号
        warehouse_prefix = warehouse_prefixes.get(warehouse_id, 'UK')
        batch_prefix = warehouse_prefix
    
    # 查询今天已有的批次号
    today_start = today.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    if db_session:
        # 使用传入的数据库会话，并强制刷新以确保看到最新数据
        db_session.flush()
        existing_batches = db_session.query(OutboundRecord).filter(
            and_(
                OutboundRecord.operated_warehouse_id == warehouse_id,
                OutboundRecord.batch_no.isnot(None),
                OutboundRecord.batch_no.like(f'{batch_prefix}{date_prefix}%')
            )
        ).all()
    else:
        # 使用默认查询
        existing_batches = OutboundRecord.query.filter(
            and_(
                OutboundRecord.operated_warehouse_id == warehouse_id,
                OutboundRecord.batch_no.isnot(None),
                OutboundRecord.batch_no.like(f'{batch_prefix}{date_prefix}%')
            )
        ).all()
    
    # 找到最大序号
    max_seq = 0
    expected_prefix = f'{batch_prefix}{date_prefix}'
    
    for batch in existing_batches:
        if batch.batch_no and batch.batch_no.startswith(expected_prefix):
            try:
                # 提取序号部分
                seq_part = batch.batch_no[len(expected_prefix):]
                seq = int(seq_part)
                max_seq = max(max_seq, seq)
            except (ValueError, IndexError):
                continue
    
    # 生成新的批次号，并确保唯一性
    max_attempts = 10  # 最多尝试10次
    for attempt in range(max_attempts):
        new_seq = max_seq + 1 + attempt
        batch_number = f'{batch_prefix}{date_prefix}{new_seq:02d}'

        # 检查生成的批次号是否已存在
        if db_session:
            existing_check = db_session.query(OutboundRecord).filter(
                OutboundRecord.batch_no == batch_number
            ).first()
        else:
            existing_check = OutboundRecord.query.filter(
                OutboundRecord.batch_no == batch_number
            ).first()

        if not existing_check:
            # 找到唯一的批次号
            return batch_number

    # 如果所有尝试都失败，使用时间戳确保唯一性
    import time
    timestamp_suffix = str(int(time.time() * 1000))[-4:]  # 取时间戳后4位
    batch_number = f'{batch_prefix}{date_prefix}{new_seq:02d}{timestamp_suffix}'

    return batch_number


def parse_batch_number(batch_number):
    """
    解析批次号
    
    Args:
        batch_number: 批次号字符串
        
    Returns:
        dict: 解析结果
    """
    if not batch_number or len(batch_number) < 8:
        return {'valid': False, 'error': '批次号格式错误'}
    
    try:
        # 提取前缀 (2位字母)
        prefix = batch_number[:2]
        
        # 提取日期部分 (6位数字)
        date_part = batch_number[2:8]
        
        # 提取序号部分 (剩余数字)
        seq_part = batch_number[8:]
        
        # 验证日期格式
        date_obj = datetime.strptime(date_part, '%y%m%d')
        
        # 验证序号
        sequence = int(seq_part) if seq_part else 0
        
        return {
            'valid': True,
            'prefix': prefix,
            'date': date_obj,
            'sequence': sequence,
            'date_str': date_part
        }
        
    except (ValueError, IndexError) as e:
        return {'valid': False, 'error': f'批次号解析失败: {str(e)}'}


def get_batch_statistics(warehouse_id, date=None):
    """
    获取批次号统计信息
    
    Args:
        warehouse_id: 仓库ID
        date: 指定日期，默认为今天
        
    Returns:
        dict: 统计信息
    """
    from app.models import OutboundRecord
    
    if date is None:
        date = datetime.now()
    
    date_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
    date_end = date.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    # 查询当天的出库记录
    records = OutboundRecord.query.filter(
        and_(
            OutboundRecord.operated_warehouse_id == warehouse_id,
            OutboundRecord.outbound_time.between(date_start, date_end),
            OutboundRecord.batch_no.isnot(None)
        )
    ).all()
    
    # 统计不同前缀的批次号
    prefix_stats = {}
    total_batches = 0
    
    for record in records:
        if record.batch_no:
            parsed = parse_batch_number(record.batch_no)
            if parsed['valid']:
                prefix = parsed['prefix']
                if prefix not in prefix_stats:
                    prefix_stats[prefix] = {
                        'count': 0,
                        'max_sequence': 0,
                        'batches': []
                    }
                
                prefix_stats[prefix]['count'] += 1
                prefix_stats[prefix]['max_sequence'] = max(
                    prefix_stats[prefix]['max_sequence'], 
                    parsed['sequence']
                )
                prefix_stats[prefix]['batches'].append(record.batch_no)
                total_batches += 1
    
    return {
        'date': date.strftime('%Y-%m-%d'),
        'warehouse_id': warehouse_id,
        'total_batches': total_batches,
        'prefix_statistics': prefix_stats
    }
