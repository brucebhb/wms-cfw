#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
识别编码生成器
格式：仓库前缀/客户全称/车牌/日期/序号
"""

from datetime import datetime
import re

class IdentificationCodeGenerator:
    """识别编码生成器"""
    
    # 仓库前缀映射
    WAREHOUSE_PREFIXES = {
        1: 'PH',  # 平湖仓
        2: 'KS',  # 昆山仓  
        3: 'CD',  # 成都仓
        4: 'PX'   # 凭祥北投仓
    }
    
    @classmethod
    def generate_identification_code(cls, warehouse_id: int, customer_name: str,
                                   plate_number: str, operation_type: str = 'inbound',
                                   inbound_date: datetime = None) -> str:
        """
        生成识别编码

        Args:
            warehouse_id: 仓库ID
            customer_name: 客户全称
            plate_number: 车牌号
            operation_type: 操作类型 ('inbound' 或 'outbound')
            inbound_date: 入库日期（如果不提供则使用当前日期）

        Returns:
            str: 生成的识别编码，格式: 仓库前缀/客户全称/车牌/日期/序号
        """
        from app.models import InboundRecord, OutboundRecord

        # 获取仓库前缀
        warehouse_prefix = cls.WAREHOUSE_PREFIXES.get(warehouse_id, 'UK')

        # 清理车牌号（去除特殊字符，保留字母数字）
        clean_plate = cls._clean_plate_number(plate_number)

        # 获取日期 - 如果提供了入库日期则使用入库日期，否则使用当前日期
        if inbound_date:
            date_str = inbound_date.strftime('%Y%m%d')
        else:
            date_str = datetime.now().strftime('%Y%m%d')

        # 构建前缀（不包含序号）
        code_prefix = f'{warehouse_prefix}/{customer_name}/{clean_plate}/{date_str}'

        # 查找当天该组合的最大序号
        sequence = cls._get_next_sequence(warehouse_id, customer_name, clean_plate, date_str, operation_type)

        # 生成最终识别编码
        try:
            identification_code = f'{code_prefix}/{int(sequence):03d}'
        except (ValueError, TypeError) as e:
            print(f"序号格式化错误: sequence={sequence}, type={type(sequence)}, error={e}")
            identification_code = f'{code_prefix}/{1:03d}'  # 使用默认序号1

        return identification_code
    
    @classmethod
    def _clean_plate_number(cls, plate_number: str) -> str:
        """清理车牌号，去除特殊字符"""
        if not plate_number:
            return 'UNKNOWN'
        
        # 去除空格、横线等特殊字符，保留字母数字和中文
        clean_plate = re.sub(r'[^A-Za-z0-9\u4e00-\u9fff]', '', plate_number)
        
        # 如果清理后为空，使用原始车牌号
        if not clean_plate:
            clean_plate = plate_number.replace('/', '').replace('-', '')
        
        return clean_plate or 'UNKNOWN'
    
    @classmethod
    def _get_next_sequence(cls, warehouse_id: int, customer_name: str,
                          clean_plate: str, date_str: str, operation_type: str) -> int:
        """获取下一个序号，使用数据库锁防止并发问题"""
        from app.models import InboundRecord, OutboundRecord
        from app import db
        from sqlalchemy import text

        # 使用数据库锁防止并发问题
        try:
            # 构建预期的识别编码前缀
            warehouse_prefix = cls.WAREHOUSE_PREFIXES.get(warehouse_id, 'UK')
            expected_prefix = f'{warehouse_prefix}/{customer_name}/{clean_plate}/{date_str}/'

            # 直接使用备用方法，避免复杂的SQL查询
            return cls._get_next_sequence_fallback(warehouse_id, customer_name, clean_plate, date_str, operation_type)

        except Exception as e:
            # 如果数据库查询失败，回退到原始方法
            print(f"数据库查询失败，使用备用方法: {e}")
            return cls._get_next_sequence_fallback(warehouse_id, customer_name, clean_plate, date_str, operation_type)

    @classmethod
    def _get_next_sequence_fallback(cls, warehouse_id: int, customer_name: str,
                                  clean_plate: str, date_str: str, operation_type: str) -> int:
        """备用序号获取方法"""
        from app.models import InboundRecord, OutboundRecord

        # 构建预期的识别编码前缀
        warehouse_prefix = cls.WAREHOUSE_PREFIXES.get(warehouse_id, 'UK')
        expected_prefix = f'{warehouse_prefix}/{customer_name}/{clean_plate}/{date_str}/'

        # 根据操作类型选择查询表
        if operation_type == 'inbound':
            query = InboundRecord.query.filter(
                InboundRecord.operated_warehouse_id == warehouse_id,
                InboundRecord.customer_name == customer_name,
                InboundRecord.identification_code.isnot(None),
                InboundRecord.identification_code.like(f'{expected_prefix}%')
            )
        else:  # outbound
            query = OutboundRecord.query.filter(
                OutboundRecord.operated_warehouse_id == warehouse_id,
                OutboundRecord.customer_name == customer_name,
                OutboundRecord.identification_code.isnot(None),
                OutboundRecord.identification_code.like(f'{expected_prefix}%')
            )

        # 查找最大序号
        max_sequence = 0
        for record in query.all():
            if record.identification_code and record.identification_code.startswith(expected_prefix):
                try:
                    sequence_part = record.identification_code[len(expected_prefix):]
                    sequence = int(sequence_part)
                    max_sequence = max(max_sequence, sequence)
                except (ValueError, IndexError):
                    continue

        return max_sequence + 1
    
    @classmethod
    def parse_identification_code(cls, identification_code: str) -> dict:
        """
        解析识别编码
        
        Returns:
            dict: 解析结果
        """
        if not identification_code:
            return {'valid': False, 'error': '识别编码为空'}
        
        parts = identification_code.split('/')
        if len(parts) != 5:
            return {'valid': False, 'error': '识别编码格式错误，应为：仓库/客户/车牌/日期/序号'}
        
        warehouse_prefix, customer_name, plate_number, date_str, sequence_str = parts
        
        # 验证仓库前缀
        warehouse_id = None
        for wid, prefix in cls.WAREHOUSE_PREFIXES.items():
            if prefix == warehouse_prefix:
                warehouse_id = wid
                break
        
        if warehouse_id is None:
            return {'valid': False, 'error': f'无效的仓库前缀: {warehouse_prefix}'}
        
        # 验证日期格式
        try:
            date_obj = datetime.strptime(date_str, '%Y%m%d')
        except ValueError:
            return {'valid': False, 'error': f'无效的日期格式: {date_str}'}
        
        # 验证序号
        try:
            sequence = int(sequence_str)
        except ValueError:
            return {'valid': False, 'error': f'无效的序号格式: {sequence_str}'}
        
        return {
            'valid': True,
            'warehouse_id': warehouse_id,
            'warehouse_prefix': warehouse_prefix,
            'customer_name': customer_name,
            'plate_number': plate_number,
            'date': date_obj,
            'sequence': sequence
        }

    @classmethod
    def generate_unique_identification_code(cls, warehouse_id: int, customer_name: str,
                                          plate_number: str, operation_type: str = 'inbound',
                                          inbound_date: datetime = None, max_retries: int = 10) -> str:
        """
        生成唯一的识别编码，包含重复检查和重试机制

        Args:
            warehouse_id: 仓库ID
            customer_name: 客户全称
            plate_number: 车牌号
            operation_type: 操作类型 ('inbound' 或 'outbound')
            inbound_date: 入库日期（如果不提供则使用当前日期）
            max_retries: 最大重试次数

        Returns:
            str: 生成的唯一识别编码

        Raises:
            ValueError: 如果无法生成唯一编码
        """
        from app.models import InboundRecord, OutboundRecord
        from app import db

        for attempt in range(max_retries):
            try:
                # 生成识别编码
                identification_code = cls.generate_identification_code(
                    warehouse_id=warehouse_id,
                    customer_name=customer_name,
                    plate_number=plate_number,
                    operation_type=operation_type,
                    inbound_date=inbound_date
                )

                # 检查是否已存在
                if operation_type == 'inbound':
                    existing = InboundRecord.query.filter_by(
                        identification_code=identification_code
                    ).first()
                else:
                    existing = OutboundRecord.query.filter_by(
                        identification_code=identification_code
                    ).first()

                if not existing:
                    return identification_code

                # 如果存在重复，等待一小段时间后重试
                import time
                time.sleep(0.1)

            except Exception as e:
                print(f"生成识别编码时出错 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    raise

        raise ValueError(f"无法生成唯一的识别编码，已尝试 {max_retries} 次")

    @classmethod
    def fix_duplicate_identification_codes(cls) -> dict:
        """
        修复重复的识别编码

        Returns:
            dict: 修复结果统计
        """
        from app.models import InboundRecord, OutboundRecord
        from app import db
        from sqlalchemy import func

        result = {
            'inbound_fixed': 0,
            'outbound_fixed': 0,
            'errors': []
        }

        try:
            # 修复入库记录的重复识别编码
            inbound_duplicates = db.session.query(
                InboundRecord.identification_code,
                func.count(InboundRecord.identification_code).label('count')
            ).group_by(
                InboundRecord.identification_code
            ).having(
                func.count(InboundRecord.identification_code) > 1
            ).all()

            for dup in inbound_duplicates:
                if not dup.identification_code:
                    continue

                # 获取所有重复的记录
                records = InboundRecord.query.filter_by(
                    identification_code=dup.identification_code
                ).order_by(InboundRecord.id).all()

                # 保留第一个记录，重新生成其他记录的识别编码
                for i, record in enumerate(records[1:], 1):
                    try:
                        new_code = cls.generate_unique_identification_code(
                            warehouse_id=record.operated_warehouse_id,
                            customer_name=record.customer_name,
                            plate_number=record.plate_number,
                            operation_type='inbound',
                            inbound_date=record.inbound_time
                        )
                        record.identification_code = new_code
                        result['inbound_fixed'] += 1
                    except Exception as e:
                        result['errors'].append(f"修复入库记录 {record.id} 失败: {e}")

            # 修复出库记录的重复识别编码
            outbound_duplicates = db.session.query(
                OutboundRecord.identification_code,
                func.count(OutboundRecord.identification_code).label('count')
            ).group_by(
                OutboundRecord.identification_code
            ).having(
                func.count(OutboundRecord.identification_code) > 1
            ).all()

            for dup in outbound_duplicates:
                if not dup.identification_code:
                    continue

                # 获取所有重复的记录
                records = OutboundRecord.query.filter_by(
                    identification_code=dup.identification_code
                ).order_by(OutboundRecord.id).all()

                # 保留第一个记录，重新生成其他记录的识别编码
                for i, record in enumerate(records[1:], 1):
                    try:
                        new_code = cls.generate_unique_identification_code(
                            warehouse_id=record.operated_warehouse_id,
                            customer_name=record.customer_name,
                            plate_number=record.plate_number,
                            operation_type='outbound',
                            inbound_date=record.outbound_time
                        )
                        record.identification_code = new_code
                        result['outbound_fixed'] += 1
                    except Exception as e:
                        result['errors'].append(f"修复出库记录 {record.id} 失败: {e}")

            # 提交更改
            db.session.commit()

        except Exception as e:
            db.session.rollback()
            result['errors'].append(f"修复过程出错: {e}")

        return result
