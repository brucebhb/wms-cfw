#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from app import create_app, db
from app.models import OutboundRecord, Inventory

def verify_deletion():
    """验证删除结果"""
    app = create_app()
    with app.app_context():
        batch_no = 'PX25071502'
        identification_code = 'PH/泰塑/粤BR77A0/20250712/001'
        
        print(f'验证删除结果')
        print('=' * 40)
        
        # 检查出库记录
        outbound_records = OutboundRecord.query.filter_by(batch_no=batch_no).all()
        print(f'批次 {batch_no} 的出库记录数量: {len(outbound_records)}')
        
        # 检查特定识别编码的出库记录
        specific_outbound = OutboundRecord.query.filter_by(identification_code=identification_code).all()
        print(f'识别编码 {identification_code} 的出库记录数量: {len(specific_outbound)}')
        
        # 检查库存记录
        inventory_records = Inventory.query.filter_by(identification_code=identification_code).all()
        print(f'识别编码 {identification_code} 的库存记录数量: {len(inventory_records)}')
        
        for inv in inventory_records:
            warehouse_name = inv.operated_warehouse.warehouse_name if inv.operated_warehouse else "未知"
            print(f'  库存记录: 仓库={warehouse_name}, 板数={inv.pallet_count}, 件数={inv.package_count}')
        
        if len(outbound_records) == 0 and len(inventory_records) > 0:
            print('\n✅ 删除成功！出库记录已删除，库存已回退')
        elif len(outbound_records) > 0:
            print('\n❌ 删除失败！出库记录仍然存在')
        else:
            print('\n⚠️  删除成功但没有库存回退')

if __name__ == '__main__':
    verify_deletion()
