#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据一致性检查工具
"""

from flask import current_app
from app import db
from app.models import InboundRecord, Inventory, OutboundRecord, TransitCargo, Warehouse
from sqlalchemy import func, text
from datetime import datetime
import json

class DataConsistencyChecker:
    """数据一致性检查器"""
    
    @staticmethod
    def check_identification_code_consistency():
        """检查识别编码一致性"""
        issues = []
        
        # 1. 检查同一识别编码是否有不同的客户名称
        inconsistent_customers = db.session.query(
            Inventory.identification_code,
            func.count(func.distinct(Inventory.customer_name)).label('customer_count'),
            func.group_concat(func.distinct(Inventory.customer_name)).label('customer_names')
        ).group_by(
            Inventory.identification_code
        ).having(
            func.count(func.distinct(Inventory.customer_name)) > 1
        ).all()
        
        for record in inconsistent_customers:
            issues.append({
                'type': 'customer_name_inconsistency',
                'severity': 'high',
                'identification_code': record.identification_code,
                'details': f'同一识别编码有多个客户名称: {record.customer_names}',
                'affected_tables': ['inventory'],
                'fix_suggestion': '统一客户名称为识别编码中的客户名称'
            })
        
        # 2. 检查客户名称与识别编码是否匹配
        all_inventory = Inventory.query.all()
        for inv in all_inventory:
            try:
                code_parts = inv.identification_code.split('/')
                if len(code_parts) >= 2:
                    expected_customer = code_parts[1]
                    if expected_customer != inv.customer_name:
                        issues.append({
                            'type': 'customer_name_mismatch',
                            'severity': 'medium',
                            'identification_code': inv.identification_code,
                            'details': f'客户名称不匹配: 识别编码中为"{expected_customer}"，数据库中为"{inv.customer_name}"',
                            'affected_tables': ['inventory'],
                            'fix_suggestion': f'将客户名称修正为"{expected_customer}"'
                        })
            except Exception as e:
                issues.append({
                    'type': 'identification_code_format_error',
                    'severity': 'high',
                    'identification_code': inv.identification_code,
                    'details': f'识别编码格式错误: {str(e)}',
                    'affected_tables': ['inventory'],
                    'fix_suggestion': '检查识别编码格式是否符合标准'
                })
        
        return issues
    
    @staticmethod
    def check_inventory_balance():
        """检查库存平衡性"""
        issues = []
        
        # 检查负库存
        negative_inventory = Inventory.query.filter(
            db.or_(
                Inventory.pallet_count < 0,
                Inventory.package_count < 0
            )
        ).all()
        
        for inv in negative_inventory:
            issues.append({
                'type': 'negative_inventory',
                'severity': 'high',
                'identification_code': inv.identification_code,
                'warehouse_id': inv.operated_warehouse_id,
                'details': f'负库存: 板数={inv.pallet_count}, 件数={inv.package_count}',
                'affected_tables': ['inventory'],
                'fix_suggestion': '检查出库记录，修正库存数量'
            })
        
        # 检查库存与出入库记录的一致性
        all_codes = db.session.query(Inventory.identification_code).distinct().all()
        
        for (code,) in all_codes:
            # 计算理论库存
            inbound_total = db.session.query(
                func.sum(InboundRecord.pallet_count).label('total_pallet'),
                func.sum(InboundRecord.package_count).label('total_package')
            ).filter_by(identification_code=code).first()
            
            outbound_total = db.session.query(
                func.sum(OutboundRecord.pallet_count).label('total_pallet'),
                func.sum(OutboundRecord.package_count).label('total_package')
            ).filter_by(identification_code=code).first()
            
            actual_total = db.session.query(
                func.sum(Inventory.pallet_count).label('total_pallet'),
                func.sum(Inventory.package_count).label('total_package')
            ).filter_by(identification_code=code).first()
            
            # 计算理论值
            theoretical_pallet = (inbound_total.total_pallet or 0) - (outbound_total.total_pallet or 0)
            theoretical_package = (inbound_total.total_package or 0) - (outbound_total.total_package or 0)
            
            actual_pallet = actual_total.total_pallet or 0
            actual_package = actual_total.total_package or 0
            
            if theoretical_pallet != actual_pallet or theoretical_package != actual_package:
                issues.append({
                    'type': 'inventory_balance_mismatch',
                    'severity': 'high',
                    'identification_code': code,
                    'details': f'库存不平衡: 理论值(板:{theoretical_pallet},件:{theoretical_package}) vs 实际值(板:{actual_pallet},件:{actual_package})',
                    'affected_tables': ['inventory', 'inbound_record', 'outbound_record'],
                    'fix_suggestion': '重新计算库存或检查出入库记录'
                })
        
        return issues
    
    @staticmethod
    def check_business_field_consistency():
        """检查业务字段一致性"""
        issues = []
        
        # 检查同一识别编码在不同表中的业务字段是否一致
        all_codes = db.session.query(Inventory.identification_code).distinct().all()
        
        for (code,) in all_codes:
            # 获取入库记录的业务字段（作为标准）
            inbound = InboundRecord.query.filter_by(identification_code=code).first()
            if not inbound:
                continue
            
            # 检查库存记录的业务字段
            inventory_records = Inventory.query.filter_by(identification_code=code).all()
            for inv in inventory_records:
                fields_to_check = ['export_mode', 'customs_broker', 'service_staff', 'order_type']
                for field in fields_to_check:
                    inbound_value = getattr(inbound, field, None)
                    inventory_value = getattr(inv, field, None)
                    
                    if inbound_value and inventory_value and inbound_value != inventory_value:
                        issues.append({
                            'type': 'business_field_inconsistency',
                            'severity': 'medium',
                            'identification_code': code,
                            'field': field,
                            'details': f'{field}不一致: 入库记录为"{inbound_value}"，库存记录为"{inventory_value}"',
                            'affected_tables': ['inventory', 'inbound_record'],
                            'fix_suggestion': f'将库存记录的{field}修正为"{inbound_value}"'
                        })
        
        return issues
    
    @staticmethod
    def check_transit_consistency():
        """检查在途货物一致性"""
        issues = []
        
        # 检查在途状态与库存的一致性
        transit_records = TransitCargo.query.filter_by(status='in_transit').all()
        
        for transit in transit_records:
            # 检查来源仓库是否还有库存
            source_inventory = Inventory.query.filter_by(
                identification_code=transit.identification_code,
                operated_warehouse_id=transit.source_warehouse_id
            ).first()
            
            if source_inventory and (source_inventory.pallet_count > 0 or source_inventory.package_count > 0):
                issues.append({
                    'type': 'transit_source_inventory_mismatch',
                    'severity': 'medium',
                    'identification_code': transit.identification_code,
                    'details': f'在途货物的来源仓库仍有库存: 板数={source_inventory.pallet_count}, 件数={source_inventory.package_count}',
                    'affected_tables': ['transit_cargo', 'inventory'],
                    'fix_suggestion': '检查出库记录或在途状态'
                })
            
            # 检查目标仓库是否已有库存（对于in_transit状态不应该有）
            dest_inventory = Inventory.query.filter_by(
                identification_code=transit.identification_code,
                operated_warehouse_id=transit.destination_warehouse_id
            ).first()
            
            if dest_inventory and (dest_inventory.pallet_count > 0 or dest_inventory.package_count > 0):
                issues.append({
                    'type': 'transit_destination_inventory_premature',
                    'severity': 'high',
                    'identification_code': transit.identification_code,
                    'details': f'在途货物的目标仓库已有库存: 板数={dest_inventory.pallet_count}, 件数={dest_inventory.package_count}',
                    'affected_tables': ['transit_cargo', 'inventory'],
                    'fix_suggestion': '检查接收记录或在途状态'
                })
        
        return issues
    
    @staticmethod
    def run_full_consistency_check():
        """运行完整的一致性检查"""
        current_app.logger.info("开始数据一致性检查...")
        
        all_issues = []
        
        # 运行各项检查
        checks = [
            ('识别编码一致性', DataConsistencyChecker.check_identification_code_consistency),
            ('库存平衡性', DataConsistencyChecker.check_inventory_balance),
            ('业务字段一致性', DataConsistencyChecker.check_business_field_consistency),
            ('在途货物一致性', DataConsistencyChecker.check_transit_consistency)
        ]
        
        for check_name, check_func in checks:
            try:
                current_app.logger.info(f"执行{check_name}检查...")
                issues = check_func()
                all_issues.extend(issues)
                current_app.logger.info(f"{check_name}检查完成，发现 {len(issues)} 个问题")
            except Exception as e:
                current_app.logger.error(f"{check_name}检查失败: {str(e)}")
                all_issues.append({
                    'type': 'check_error',
                    'severity': 'high',
                    'details': f'{check_name}检查失败: {str(e)}',
                    'affected_tables': ['unknown'],
                    'fix_suggestion': '检查系统日志'
                })
        
        # 按严重程度排序
        severity_order = {'high': 0, 'medium': 1, 'low': 2}
        all_issues.sort(key=lambda x: severity_order.get(x.get('severity', 'low'), 2))
        
        current_app.logger.info(f"数据一致性检查完成，共发现 {len(all_issues)} 个问题")
        
        return {
            'total_issues': len(all_issues),
            'high_severity': len([i for i in all_issues if i.get('severity') == 'high']),
            'medium_severity': len([i for i in all_issues if i.get('severity') == 'medium']),
            'low_severity': len([i for i in all_issues if i.get('severity') == 'low']),
            'issues': all_issues,
            'check_time': datetime.now().isoformat()
        }
    
    @staticmethod
    def fix_customer_name_issues():
        """自动修复客户名称不一致问题"""
        fixed_count = 0
        
        try:
            with db.session.begin():
                # 获取所有库存记录
                inventory_records = Inventory.query.all()
                
                for inv in inventory_records:
                    try:
                        code_parts = inv.identification_code.split('/')
                        if len(code_parts) >= 2:
                            correct_customer = code_parts[1]
                            if correct_customer != inv.customer_name:
                                current_app.logger.info(f"修复客户名称: {inv.identification_code} {inv.customer_name} -> {correct_customer}")
                                inv.customer_name = correct_customer
                                fixed_count += 1
                    except Exception as e:
                        current_app.logger.error(f"修复客户名称失败: {inv.identification_code}, 错误: {str(e)}")
                
                current_app.logger.info(f"客户名称修复完成，共修复 {fixed_count} 条记录")
                
        except Exception as e:
            current_app.logger.error(f"客户名称修复失败: {str(e)}")
            raise
        
        return fixed_count
