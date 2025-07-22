#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from app import create_app, db
from app.models import Inventory, OutboundRecord, InboundRecord, TransitCargo

def check_inventory_distribution():
    """检查库存分布问题"""
    app = create_app()
    with app.app_context():
        target_code = 'PH/泰塑/粤BR77A0/20250712/001'
        print(f'检查库存分布 - 识别编码: {target_code}')
        print('=' * 60)
        
        # 查看所有仓库的库存记录
        inventories = Inventory.query.filter_by(identification_code=target_code).all()
        print(f'当前库存记录数量: {len(inventories)}')
        
        total_pallet = 0
        for inv in inventories:
            warehouse_name = inv.operated_warehouse.warehouse_name if inv.operated_warehouse else "未知"
            warehouse_type = inv.operated_warehouse.warehouse_type if inv.operated_warehouse else "未知"
            print(f'  仓库: {warehouse_name} (ID: {inv.operated_warehouse_id}, 类型: {warehouse_type})')
            print(f'  板数: {inv.pallet_count}')
            print(f'  件数: {inv.package_count}')
            print(f'  入库时间: {inv.inbound_time}')
            total_pallet += inv.pallet_count or 0
            print('---')
        
        print(f'总库存板数: {total_pallet}')
        
        # 查看入库记录
        print('\n=== 入库记录 ===')
        inbound_records = InboundRecord.query.filter_by(identification_code=target_code).all()
        print(f'入库记录数量: {len(inbound_records)}')
        
        total_inbound = 0
        for inbound in inbound_records:
            warehouse_name = inbound.operated_warehouse.warehouse_name if inbound.operated_warehouse else "未知"
            print(f'  入库仓库: {warehouse_name} (ID: {inbound.operated_warehouse_id})')
            print(f'  板数: {inbound.pallet_count}')
            print(f'  入库时间: {inbound.inbound_time}')
            total_inbound += inbound.pallet_count or 0
            print('---')
        
        print(f'总入库板数: {total_inbound}')
        
        # 查看出库记录
        print('\n=== 出库记录 ===')
        outbound_records = OutboundRecord.query.filter_by(identification_code=target_code).all()
        print(f'出库记录数量: {len(outbound_records)}')
        
        total_outbound = 0
        for outbound in outbound_records:
            warehouse_name = outbound.operated_warehouse.warehouse_name if outbound.operated_warehouse else "未知"
            print(f'  出库仓库: {warehouse_name} (ID: {outbound.operated_warehouse_id})')
            print(f'  板数: {outbound.pallet_count}')
            print(f'  出库时间: {outbound.outbound_time}')
            print(f'  目的地: {outbound.destination}')
            total_outbound += outbound.pallet_count or 0
            print('---')
        
        print(f'总出库板数: {total_outbound}')
        
        # 查看在途货物记录
        print('\n=== 在途货物记录 ===')
        transit_records = TransitCargo.query.filter_by(identification_code=target_code).all()
        print(f'在途货物记录数量: {len(transit_records)}')
        
        for transit in transit_records:
            print(f'  批次号: {transit.batch_no}')
            print(f'  状态: {transit.status}')
            print(f'  板数: {transit.pallet_count}')
            print('---')
        
        # 分析问题
        print('\n=== 问题分析 ===')
        print(f'入库总数: {total_inbound} 板')
        print(f'出库总数: {total_outbound} 板')
        print(f'库存总数: {total_pallet} 板')
        print(f'理论库存: {total_inbound - total_outbound} 板')
        
        if total_pallet != (total_inbound - total_outbound):
            print('❌ 库存数据不一致！')
        else:
            print('✅ 库存数据一致')
        
        # 检查应该的分布
        print('\n=== 应该的库存分布 ===')
        print('根据您的描述，应该是：')
        print('  前端仓（平湖仓）: 2板')
        print('  后端仓（凭祥北投仓）: 2板')
        print('  总计: 4板')
        
        # 检查前端仓和后端仓的库存
        frontend_inventory = Inventory.query.filter_by(
            identification_code=target_code,
            operated_warehouse_id=1  # 平湖仓
        ).first()
        
        backend_inventory = Inventory.query.filter_by(
            identification_code=target_code,
            operated_warehouse_id=4  # 凭祥北投仓
        ).first()
        
        print('\n当前实际分布：')
        if frontend_inventory:
            print(f'  前端仓（平湖仓）: {frontend_inventory.pallet_count}板')
        else:
            print('  前端仓（平湖仓）: 0板 (无记录)')
            
        if backend_inventory:
            print(f'  后端仓（凭祥北投仓）: {backend_inventory.pallet_count}板')
        else:
            print('  后端仓（凭祥北投仓）: 0板 (无记录)')

if __name__ == '__main__':
    check_inventory_distribution()
