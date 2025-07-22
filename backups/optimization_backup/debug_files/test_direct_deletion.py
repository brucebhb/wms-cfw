#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from app import create_app, db
from app.models import User, OutboundRecord, Inventory
from app.main.routes import api_backend_outbound_delete_batch
from flask_login import login_user
import traceback

def test_direct_deletion():
    """直接测试删除API函数"""
    app = create_app()
    with app.app_context():
        try:
            batch_no = 'PX25071502'
            print(f'直接测试删除批次: {batch_no}')
            print('=' * 60)
            
            # 获取PXC用户并模拟登录
            pxc_user = User.query.filter_by(username='PXC').first()
            if not pxc_user:
                print("错误：未找到PXC用户")
                return
            
            # 记录删除前的状态
            print("删除前状态:")
            outbound_records = OutboundRecord.query.filter_by(batch_no=batch_no).all()
            print(f"  出库记录数量: {len(outbound_records)}")
            
            for record in outbound_records:
                print(f"  记录ID: {record.id}, 识别编码: {record.identification_code}")
                
                # 检查对应的库存
                inventory = Inventory.query.filter_by(
                    customer_name=record.customer_name,
                    identification_code=record.identification_code,
                    operated_warehouse_id=record.operated_warehouse_id
                ).first()
                
                if inventory:
                    print(f"    对应库存: 板数={inventory.pallet_count}, 件数={inventory.package_count}")
                else:
                    print(f"    无对应库存记录")
            
            # 使用Flask测试客户端模拟请求
            with app.test_client() as client:
                with client.session_transaction() as sess:
                    # 模拟用户登录
                    sess['_user_id'] = str(pxc_user.id)
                    sess['_fresh'] = True
                
                # 模拟请求上下文
                with app.test_request_context(f'/api/backend/outbound/delete_batch/{batch_no}', method='DELETE'):
                    # 手动设置当前用户
                    login_user(pxc_user)
                    
                    print(f"\n开始执行删除...")
                    
                    # 直接调用API函数
                    response = api_backend_outbound_delete_batch(batch_no)
                    
                    print(f"API响应: {response}")
                    
                    # 如果是元组，提取响应数据和状态码
                    if isinstance(response, tuple):
                        response_data, status_code = response
                        print(f"状态码: {status_code}")
                        print(f"响应数据: {response_data.get_json()}")
                    else:
                        print(f"响应数据: {response.get_json()}")
            
            # 检查删除后的状态
            print("\n删除后状态:")
            outbound_records_after = OutboundRecord.query.filter_by(batch_no=batch_no).all()
            print(f"  出库记录数量: {len(outbound_records_after)}")
            
            # 检查库存是否正确回退
            for record in outbound_records:
                inventory = Inventory.query.filter_by(
                    customer_name=record.customer_name,
                    identification_code=record.identification_code,
                    operated_warehouse_id=record.operated_warehouse_id
                ).first()
                
                if inventory:
                    print(f"  库存记录: {record.identification_code}")
                    print(f"    板数: {inventory.pallet_count}, 件数: {inventory.package_count}")
                else:
                    print(f"  无库存记录: {record.identification_code}")
            
        except Exception as e:
            print(f'测试过程中出错: {str(e)}')
            print(traceback.format_exc())

if __name__ == '__main__':
    test_direct_deletion()
