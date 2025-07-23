#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from app import create_app, db
from app.models import Inventory
import sys

app = create_app()
with app.app_context():
    print('=== 测试简单API ===')
    
    try:
        # 直接查询后端仓库存
        inventory_records = Inventory.query.filter(
            Inventory.operated_warehouse_id == 4,  # 后端仓ID
            db.or_(
                Inventory.pallet_count > 0,
                Inventory.package_count > 0
            )
        ).limit(5).all()
        
        print(f'找到 {len(inventory_records)} 条后端仓库存记录')
        
        for record in inventory_records:
            print(f'- ID: {record.id}, 客户: {record.customer_name}, 识别编码: {record.identification_code}')
            print(f'  板数: {record.pallet_count}, 件数: {record.package_count}')
            print(f'  库存类型: {getattr(record, "inventory_type", "未定义")}')
            print()
        
        print('✅ 直接查询成功')
        
    except Exception as e:
        print(f'❌ 直接查询失败: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print('=== 测试完成 ===')
