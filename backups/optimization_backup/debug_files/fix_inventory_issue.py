#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from app import create_app, db
from app.models import Inventory, OutboundRecord, InboundRecord, TransitCargo

def fix_inventory_issue():
    """修复库存问题"""
    app = create_app()
    with app.app_context():
        target_code = 'PH/泰塑/粤BR77A0/20250712/001'
        print(f'修复库存问题 - 识别编码: {target_code}')
        print('=' * 60)
        
        # 查找前端仓库存记录
        frontend_inventory = Inventory.query.filter_by(
            identification_code=target_code,
            operated_warehouse_id=1  # 平湖仓
        ).first()
        
        # 查找后端仓库存记录
        backend_inventory = Inventory.query.filter_by(
            identification_code=target_code,
            operated_warehouse_id=4  # 凭祥北投仓
        ).first()
        
        print('修复前状态:')
        if frontend_inventory:
            print(f'  前端仓库存: {frontend_inventory.pallet_count}板')
        if backend_inventory:
            print(f'  后端仓库存: {backend_inventory.pallet_count}板')
        
        # 查找前端仓到后端仓的出库记录
        outbound_to_backend = OutboundRecord.query.filter_by(
            identification_code=target_code,
            operated_warehouse_id=1,  # 从平湖仓出库
            destination='凭祥北投仓'
        ).first()
        
        if outbound_to_backend:
            print(f'\n找到前端仓到后端仓的出库记录:')
            print(f'  出库板数: {outbound_to_backend.pallet_count}')
            print(f'  出库时间: {outbound_to_backend.outbound_time}')
            
            # 检查在途货物状态
            transit = TransitCargo.query.filter_by(
                identification_code=target_code,
                batch_no=outbound_to_backend.batch_no
            ).first()
            
            if transit and transit.status == 'received':
                print(f'  在途状态: {transit.status} (已接收)')
                
                # 修复前端仓库存：应该减去已发货的数量
                if frontend_inventory:
                    original_pallet = frontend_inventory.pallet_count
                    # 前端仓原本4板，发出2板，应该剩2板
                    # 但是现在显示2板，说明没有正确扣减
                    # 我们需要检查入库记录来确定原始数量
                    
                    inbound_record = InboundRecord.query.filter_by(
                        identification_code=target_code,
                        operated_warehouse_id=1
                    ).first()
                    
                    if inbound_record:
                        original_inbound = inbound_record.pallet_count
                        outbound_amount = outbound_to_backend.pallet_count
                        correct_remaining = original_inbound - outbound_amount
                        
                        print(f'\n库存修复计算:')
                        print(f'  原始入库: {original_inbound}板')
                        print(f'  已出库: {outbound_amount}板')
                        print(f'  应该剩余: {correct_remaining}板')
                        print(f'  当前显示: {original_pallet}板')
                        
                        if original_pallet != correct_remaining:
                            print(f'\n执行修复...')
                            frontend_inventory.pallet_count = correct_remaining
                            db.session.commit()
                            print(f'✅ 前端仓库存已修复: {original_pallet}板 -> {correct_remaining}板')
                        else:
                            print(f'✅ 前端仓库存正确，无需修复')
                
                # 检查后端仓库存是否正确
                if backend_inventory:
                    expected_backend = outbound_to_backend.pallet_count
                    if backend_inventory.pallet_count == expected_backend:
                        print(f'✅ 后端仓库存正确: {backend_inventory.pallet_count}板')
                    else:
                        print(f'❌ 后端仓库存不正确: 期望{expected_backend}板，实际{backend_inventory.pallet_count}板')
            else:
                print(f'  在途状态: {transit.status if transit else "未找到"} (未接收)')
        else:
            print('未找到前端仓到后端仓的出库记录')
        
        # 验证修复结果
        print('\n修复后状态:')
        frontend_inventory = Inventory.query.filter_by(
            identification_code=target_code,
            operated_warehouse_id=1
        ).first()
        
        backend_inventory = Inventory.query.filter_by(
            identification_code=target_code,
            operated_warehouse_id=4
        ).first()
        
        frontend_count = frontend_inventory.pallet_count if frontend_inventory else 0
        backend_count = backend_inventory.pallet_count if backend_inventory else 0
        total_count = frontend_count + backend_count
        
        print(f'  前端仓库存: {frontend_count}板')
        print(f'  后端仓库存: {backend_count}板')
        print(f'  总库存: {total_count}板')
        
        # 检查是否符合预期
        if frontend_count == 2 and backend_count == 2:
            print('\n✅ 库存分布正确！')
            print('  前端仓: 2板 ✓')
            print('  后端仓: 2板 ✓')
        else:
            print('\n❌ 库存分布仍有问题')

if __name__ == '__main__':
    fix_inventory_issue()
