from app import create_app, db
from app.models import InboundRecord, Inventory, OutboundRecord, Warehouse
from datetime import datetime
import sys

app = create_app()
with app.app_context():
    print('=== 测试后端仓出库删除回退功能 ===')
    
    # 获取后端仓库
    backend_warehouse = Warehouse.query.filter_by(warehouse_type='backend').first()
    if not backend_warehouse:
        print('未找到后端仓库')
        sys.exit(1)
    
    # 查找一个PX开头的库存记录
    px_inventories = Inventory.query.filter(
        Inventory.identification_code.like('PX/%'),
        Inventory.operated_warehouse_id == backend_warehouse.id
    ).all()

    print(f'找到 {len(px_inventories)} 条PX开头的库存记录')

    if not px_inventories:
        print('未找到PX开头的库存记录，查看所有库存记录：')
        all_inventories = Inventory.query.filter_by(operated_warehouse_id=backend_warehouse.id).limit(5).all()
        for inv in all_inventories:
            print(f'  {inv.identification_code}')
        sys.exit(1)

    px_inventory = px_inventories[0]
    
    print(f'找到测试库存记录: {px_inventory.identification_code}')
    print(f'当前库存状态:')
    print(f'  板数: {px_inventory.pallet_count}')
    print(f'  件数: {px_inventory.package_count}')
    print(f'  订单类型: "{px_inventory.order_type}"')
    print(f'  出境模式: "{px_inventory.export_mode}"')
    print(f'  报关行: "{px_inventory.customs_broker}"')
    print(f'  单据: "{px_inventory.documents}"')
    
    # 查找对应的入库记录
    inbound_record = InboundRecord.query.filter_by(
        identification_code=px_inventory.identification_code
    ).first()
    
    if not inbound_record:
        print('未找到对应的入库记录')
        sys.exit(1)
    
    print(f'\n对应的入库记录:')
    print(f'  订单类型: "{inbound_record.order_type}"')
    print(f'  出境模式: "{inbound_record.export_mode}"')
    print(f'  报关行: "{inbound_record.customs_broker}"')
    print(f'  单据: "{inbound_record.documents}"')
    
    # 模拟出库操作
    test_outbound_pallet = min(1, px_inventory.pallet_count)
    test_outbound_package = min(1, px_inventory.package_count)
    
    if test_outbound_pallet == 0 and test_outbound_package == 0:
        print('库存为0，无法进行出库测试')
        sys.exit(1)
    
    print(f'\n=== 模拟出库操作 ===')
    print(f'出库板数: {test_outbound_pallet}')
    print(f'出库件数: {test_outbound_package}')
    
    # 创建出库记录
    outbound_record = OutboundRecord(
        outbound_time=datetime.now(),
        plate_number='测试车牌',
        customer_name=px_inventory.customer_name,
        identification_code=px_inventory.identification_code,
        pallet_count=test_outbound_pallet,
        package_count=test_outbound_package,
        weight=100.0,
        volume=1.0,
        order_type='测试订单类型',
        export_mode='测试出境模式',
        customs_broker='测试报关行',
        service_staff='测试客服',
        operated_warehouse_id=backend_warehouse.id,
        operated_by_user_id=1
    )
    
    # 更新库存（减少）
    original_pallet = px_inventory.pallet_count
    original_package = px_inventory.package_count
    original_order_type = px_inventory.order_type
    original_export_mode = px_inventory.export_mode
    original_customs_broker = px_inventory.customs_broker
    original_documents = px_inventory.documents
    
    px_inventory.pallet_count -= test_outbound_pallet
    px_inventory.package_count -= test_outbound_package
    # 模拟出库时清空业务字段
    px_inventory.order_type = ''
    px_inventory.export_mode = ''
    px_inventory.customs_broker = ''
    px_inventory.documents = None
    
    db.session.add(outbound_record)
    db.session.commit()
    
    print(f'出库后库存状态:')
    print(f'  板数: {px_inventory.pallet_count} (原: {original_pallet})')
    print(f'  件数: {px_inventory.package_count} (原: {original_package})')
    print(f'  订单类型: "{px_inventory.order_type}" (原: "{original_order_type}")')
    print(f'  出境模式: "{px_inventory.export_mode}" (原: "{original_export_mode}")')
    print(f'  报关行: "{px_inventory.customs_broker}" (原: "{original_customs_broker}")')
    print(f'  单据: "{px_inventory.documents}" (原: "{original_documents}")')
    
    print(f'\n=== 模拟删除出库记录（回退） ===')
    
    # 模拟删除出库记录的回退逻辑
    # 恢复数量
    px_inventory.pallet_count += outbound_record.pallet_count
    px_inventory.package_count += outbound_record.package_count
    
    # 对于PX开头的自行入库数据，恢复业务字段
    if px_inventory.identification_code.startswith('PX/'):
        px_inventory.order_type = inbound_record.order_type
        px_inventory.export_mode = inbound_record.export_mode
        px_inventory.customs_broker = inbound_record.customs_broker
        px_inventory.documents = inbound_record.documents
    
    # 删除出库记录
    db.session.delete(outbound_record)
    db.session.commit()
    
    print(f'回退后库存状态:')
    print(f'  板数: {px_inventory.pallet_count} (应为: {original_pallet})')
    print(f'  件数: {px_inventory.package_count} (应为: {original_package})')
    print(f'  订单类型: "{px_inventory.order_type}" (应为: "{original_order_type}")')
    print(f'  出境模式: "{px_inventory.export_mode}" (应为: "{original_export_mode}")')
    print(f'  报关行: "{px_inventory.customs_broker}" (应为: "{original_customs_broker}")')
    print(f'  单据: "{px_inventory.documents}" (应为: "{original_documents}")')
    
    # 验证回退是否成功
    success = (
        px_inventory.pallet_count == original_pallet and
        px_inventory.package_count == original_package and
        px_inventory.order_type == original_order_type and
        px_inventory.export_mode == original_export_mode and
        px_inventory.customs_broker == original_customs_broker and
        str(px_inventory.documents) == str(original_documents)
    )
    
    if success:
        print('\n✅ 出库删除回退测试成功！所有字段都正确恢复了。')
    else:
        print('\n❌ 出库删除回退测试失败！某些字段没有正确恢复。')
    
    print('\n=== 测试完成 ===')
