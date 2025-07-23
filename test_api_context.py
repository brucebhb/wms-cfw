#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from app import create_app, db
from app.models import Inventory, Warehouse
import sys

app = create_app()
with app.app_context():
    print('=== 测试API上下文 ===')
    
    try:
        # 模拟API端点的逻辑
        print('1. 查找后端仓库...')
        backend_warehouse = Warehouse.query.filter_by(warehouse_name='凭祥北投仓').first()
        
        if not backend_warehouse:
            print('❌ 未找到后端仓库')
            sys.exit(1)
        
        print(f'✅ 找到后端仓库: ID={backend_warehouse.id}, 名称={backend_warehouse.warehouse_name}')
        
        print('2. 查询后端仓库存...')
        query = Inventory.query.filter(Inventory.operated_warehouse_id == backend_warehouse.id)
        query = query.filter((Inventory.pallet_count > 0) | (Inventory.package_count > 0))
        
        inventory_items = query.limit(3).all()
        print(f'✅ 查询到 {len(inventory_items)} 条库存记录')
        
        print('3. 转换为字典...')
        items = []
        for item in inventory_items:
            try:
                identification_code = item.identification_code or ''
                if len(identification_code) > 50:
                    identification_code = identification_code[:50] + '...'

                item_dict = {
                    'id': item.id,
                    'customer_name': item.customer_name,
                    'identification_code': identification_code,
                    'inbound_pallet_count': item.inbound_pallet_count,
                    'inbound_package_count': item.inbound_package_count,
                    'pallet_count': item.pallet_count,
                    'package_count': item.package_count,
                    'weight': item.weight,
                    'volume': item.volume,
                    'location': item.location,
                    'documents': item.documents,
                    'export_mode': item.export_mode,
                    'order_type': item.order_type,
                    'customs_broker': item.customs_broker,
                    'plate_number': item.plate_number,
                    'service_staff': item.service_staff,
                    'remark1': '',
                    'remark2': ''
                }

                # 处理日期时间字段
                if item.inbound_time:
                    item_dict['inbound_time'] = item.inbound_time.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    item_dict['inbound_time'] = ''

                if item.last_updated:
                    item_dict['last_updated'] = item.last_updated.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    item_dict['last_updated'] = ''

                items.append(item_dict)
                print(f'  - 处理记录 {item.id}: {item.customer_name}')
                
            except Exception as e:
                print(f'❌ 处理库存项 {item.id} 时出错: {str(e)}')
                import traceback
                traceback.print_exc()
        
        print(f'✅ 成功处理 {len(items)} 条库存记录')
        
        # 模拟返回JSON
        result = {
            'success': True,
            'data': items
        }
        
        print(f'✅ API逻辑测试成功，返回数据包含 {len(result["data"])} 条记录')
        
    except Exception as e:
        print(f'❌ API逻辑测试失败: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print('=== 测试完成 ===')
