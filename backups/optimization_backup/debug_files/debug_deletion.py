#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from app import create_app, db
from app.models import User, OutboundRecord, Inventory, TransitCargo
from flask_login import login_user
import traceback

def debug_deletion():
    """调试删除功能"""
    app = create_app()
    with app.app_context():
        try:
            batch_no = 'PX25071502'
            print(f'调试删除批次: {batch_no}')
            print('=' * 60)
            
            # 1. 检查PXC用户权限
            pxc_user = User.query.filter_by(username='PXC').first()
            if not pxc_user:
                print("错误：未找到PXC用户")
                return
            
            print(f'PXC用户信息:')
            print(f'  用户名: {pxc_user.username}')
            print(f'  仓库ID: {pxc_user.warehouse_id}')
            print(f'  仓库类型: {pxc_user.warehouse.warehouse_type if pxc_user.warehouse else "无"}')
            print(f'  是否超级管理员: {pxc_user.is_super_admin()}')
            print(f'  有OUTBOUND_DELETE权限: {pxc_user.has_permission("OUTBOUND_DELETE")}')
            
            # 2. 检查仓库权限
            from app.main.routes import check_warehouse_permission
            with app.test_request_context():
                # 模拟登录PXC用户
                login_user(pxc_user)
                from flask_login import current_user
                print(f'当前用户: {current_user.username}')
                
                # 检查仓库权限
                has_backend_delete = check_warehouse_permission('backend', 'delete')
                print(f'有后端仓删除权限: {has_backend_delete}')
            
            # 3. 查找批次记录
            outbound_records = OutboundRecord.query.filter_by(batch_no=batch_no).all()
            print(f'\n找到 {len(outbound_records)} 条出库记录:')
            
            for record in outbound_records:
                print(f'  记录ID: {record.id}')
                print(f'  客户: {record.customer_name}')
                print(f'  识别编码: {record.identification_code}')
                print(f'  仓库ID: {record.operated_warehouse_id}')
                print(f'  仓库名称: {record.operated_warehouse.warehouse_name if record.operated_warehouse else "无"}')
                print(f'  板数: {record.pallet_count}')
                print(f'  件数: {record.package_count}')
                print('  ---')
            
            # 4. 检查对应的库存记录
            print('\n检查对应的库存记录:')
            for record in outbound_records:
                inventory = Inventory.query.filter_by(
                    customer_name=record.customer_name,
                    identification_code=record.identification_code,
                    operated_warehouse_id=record.operated_warehouse_id
                ).first()
                
                if inventory:
                    print(f'  找到库存记录: {record.identification_code}')
                    print(f'    库存板数: {inventory.pallet_count}')
                    print(f'    库存件数: {inventory.package_count}')
                else:
                    print(f'  未找到库存记录: {record.identification_code}')
            
            # 5. 检查在途货物记录
            transit_records = TransitCargo.query.filter_by(batch_no=batch_no).all()
            print(f'\n找到 {len(transit_records)} 条在途货物记录:')
            for transit in transit_records:
                print(f'  在途ID: {transit.id}')
                print(f'  识别编码: {transit.identification_code}')
                print(f'  状态: {transit.status}')
                print(f'  板数: {transit.pallet_count}')
            
            # 6. 模拟删除过程
            print('\n=== 模拟删除过程 ===')
            
            if not outbound_records:
                print("错误：没有找到要删除的出库记录")
                return
            
            print("开始模拟删除...")
            
            for i, record in enumerate(outbound_records):
                print(f'\n处理第 {i+1} 条记录:')
                print(f'  识别编码: {record.identification_code}')
                print(f'  要回退的板数: {record.pallet_count}')
                print(f'  要回退的件数: {record.package_count}')
                
                # 查找库存记录
                inventory = Inventory.query.filter_by(
                    customer_name=record.customer_name,
                    identification_code=record.identification_code,
                    operated_warehouse_id=record.operated_warehouse_id
                ).first()
                
                if inventory:
                    new_pallet = (inventory.pallet_count or 0) + (record.pallet_count or 0)
                    new_package = (inventory.package_count or 0) + (record.package_count or 0)
                    print(f'  更新库存: 板数 {inventory.pallet_count} -> {new_pallet}')
                    print(f'  更新库存: 件数 {inventory.package_count} -> {new_package}')
                else:
                    print(f'  需要创建新库存记录: 板数={record.pallet_count}, 件数={record.package_count}')
            
            print('\n模拟删除完成，没有发现明显问题')
            
        except Exception as e:
            print(f'调试过程中出错: {str(e)}')
            print(traceback.format_exc())

if __name__ == '__main__':
    debug_deletion()
