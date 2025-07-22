#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from app import create_app, db
from app.models import Inventory, OutboundRecord, InboundRecord, TransitCargo
from datetime import datetime

def check_deletion_issue():
    app = create_app()
    with app.app_context():
        target_code = 'PH/泰塑/粤BR77A0/20250712/001'
        print(f'检查删除问题 - 识别编码: {target_code}')
        print('=' * 60)
        
        # 查看当前库存记录
        inventories = Inventory.query.filter_by(identification_code=target_code).all()
        print(f'当前库存记录数量: {len(inventories)}')
        for inv in inventories:
            warehouse_name = inv.operated_warehouse.warehouse_name if inv.operated_warehouse else "未知"
            print(f'  库存ID: {inv.id}')
            print(f'  仓库: {warehouse_name} (ID: {inv.operated_warehouse_id})')
            print(f'  板数: {inv.pallet_count}')
            print(f'  件数: {inv.package_count}')
            print('---')
        
        # 查看出库记录
        outbound_records = OutboundRecord.query.filter_by(identification_code=target_code).all()
        print(f'出库记录数量: {len(outbound_records)}')
        for out in outbound_records:
            warehouse_name = out.operated_warehouse.warehouse_name if out.operated_warehouse else "未知"
            print(f'  出库ID: {out.id}')
            print(f'  仓库: {warehouse_name} (ID: {out.operated_warehouse_id})')
            print(f'  板数: {out.pallet_count}')
            print(f'  出库时间: {out.outbound_time}')
            print(f'  批次号: {out.batch_no}')
            print('---')
        
        # 查看在途货物记录
        transit_records = TransitCargo.query.filter_by(identification_code=target_code).all()
        print(f'在途货物记录数量: {len(transit_records)}')
        for transit in transit_records:
            print(f'  在途ID: {transit.id}')
            print(f'  批次号: {transit.batch_no}')
            print(f'  状态: {transit.status}')
            print(f'  板数: {transit.pallet_count}')
            print('---')
        
        # 分析问题
        print("=== 问题分析 ===")
        
        # 检查是否有后端仓的出库记录
        backend_outbound = [out for out in outbound_records if out.operated_warehouse_id == 4]  # 凭祥北投仓ID=4
        frontend_outbound = [out for out in outbound_records if out.operated_warehouse_id == 1]  # 平湖仓ID=1
        
        print(f"前端仓出库记录: {len(frontend_outbound)} 条")
        print(f"后端仓出库记录: {len(backend_outbound)} 条")
        
        if len(backend_outbound) == 0:
            print("问题：没有找到后端仓的出库记录！")
            print("这票货物可能还在后端仓库存中，没有进行出库操作。")
        else:
            print("找到后端仓出库记录，检查批次号...")
            for out in backend_outbound:
                print(f"  后端仓出库批次号: {out.batch_no}")

if __name__ == '__main__':
    check_deletion_issue()
