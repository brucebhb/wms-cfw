from flask import request, jsonify, current_app
from flask_login import current_user
from app import db, csrf
from app.api import bp
from app.models import OutboundRecord, Inventory, InboundRecord
from datetime import datetime
import traceback
import json
from sqlalchemy import func, or_

# 确保API路由被正确注册到蓝图
__all__ = ['save_outbound_batch', 'get_outbound_list', 'get_outbound_history', 'save_frontend_outbound_to_backend']



@bp.route('/outbound/batch', methods=['POST'])
@csrf.exempt  # 豁免CSRF保护，因为这是API接口
def save_outbound_batch():
    """
    保存出库批次数据API
    """
    try:
        # 获取请求数据
        data = request.get_json()
        
        # 调试日志
        current_app.logger.info(f"收到出库批次数据请求: {json.dumps(data, ensure_ascii=False)}")
        
        if not data:
            current_app.logger.error("请求数据为空")
            return jsonify({
                'success': False,
                'message': '请求数据为空'
            }), 400
            
        if ('items' not in data and 'records' not in data) or 'common' not in data:
            current_app.logger.error(f"数据格式不正确，缺少必要字段。数据键: {list(data.keys())}")
            return jsonify({
                'success': False,
                'message': '数据格式不正确，必须包含common和items字段'
            }), 400
        
        # 兼容前端可能发送的两种格式
        items = data.get('items', []) or data.get('records', [])
        common = data.get('common', {})
        
        # 预加载所有需要更新的库存记录,减少数据库查询次数
        identification_codes = [item.get('identification_code') for item in items if item.get('identification_code')]
        inventory_dict = {}
        if identification_codes:
            current_app.logger.info(f"预加载库存记录,识别码: {identification_codes}")
            inventories = Inventory.query.filter(Inventory.identification_code.in_(identification_codes)).all()
            for inv in inventories:
                inventory_dict[inv.identification_code] = inv
            current_app.logger.info(f"已加载 {len(inventory_dict)} 条库存记录")
        
        current_app.logger.info(f"解析后的数据: items数量={len(items)}, common={common}")
        
        if not items:
            current_app.logger.error("没有提供出库记录数据")
            return jsonify({
                'success': False,
                'message': '没有提供出库记录数据'
            }), 400
        
        # 从common中提取公共信息
        plate_number = common.get('outbound_plate', '') or common.get('plate_number', '')  # 同时支持两种前端字段名
        departure_time = common.get('departure_time', '')
        destination = common.get('destination', '')
        transport_company = common.get('transport_company', '')
        receiver_id = common.get('receiver_id', '')
        large_layer = common.get('large_layer', 0)
        small_layer = common.get('small_layer', 0)
        pallet_board = common.get('pallet_board', 0)
        
        current_app.logger.info(f"公共信息: 出库车牌={plate_number}, 目的地={destination}, 接收方ID={receiver_id}")
        
        # 批量创建出库记录
        saved_count = 0
        for idx, item in enumerate(items):
            try:
                current_app.logger.info(f"处理第{idx+1}条记录: 客户={item.get('customer_name')}, 识别码={item.get('identification_code')}")
                
                # 获取出库数量，确保是整数
                try:
                    pallet_value = item.get('pallet_count', 0)
                    package_value = item.get('package_count', 0)

                    # 检查是否为小数
                    if isinstance(pallet_value, (int, float)) and pallet_value != int(pallet_value):
                        errors.append(f"第{idx+1}条记录：板数必须是整数，不能是小数")
                        continue
                    if isinstance(package_value, (int, float)) and package_value != int(package_value):
                        errors.append(f"第{idx+1}条记录：件数必须是整数，不能是小数")
                        continue

                    outbound_pallet_count = int(pallet_value)
                    outbound_package_count = int(package_value)

                    if outbound_pallet_count < 0 or outbound_package_count < 0:
                        errors.append(f"第{idx+1}条记录：板数和件数不能为负数")
                        continue

                except (ValueError, TypeError):
                    errors.append(f"第{idx+1}条记录：板数和件数必须是有效的整数")
                    continue
                identification_code = item.get('identification_code', '')

                # 获取库存信息用于生成拆票分装备注
                inventory = inventory_dict.get(identification_code) if identification_code else None

                # 获取前端传递的单据份数，允许空值
                document_count_raw = item.get('document_count')
                document_count = None  # 默认为None
                if document_count_raw is not None and document_count_raw != '':
                    try:
                        document_count = int(document_count_raw)
                        current_app.logger.info(f"使用前端传递的单据份数: 识别编码={identification_code}, 单据份数={document_count}")
                    except (ValueError, TypeError):
                        current_app.logger.warning(f"前端传递的单据份数格式无效: {document_count_raw}，设置为None")
                        document_count = None
                else:
                    current_app.logger.info(f"前端未传递单据份数或为空值，设置为None: 识别编码={identification_code}")

                # 直接使用用户输入的备注，不自动生成
                remark1_value = item.get('remark1') if item.get('remark1') is not None else ''

                # 创建出库记录基本信息
                outbound_record = OutboundRecord(
                    outbound_time=datetime.now(),  # 默认使用当前时间
                    plate_number=plate_number,
                    customer_name=item.get('customer_name', ''),
                    identification_code=identification_code,
                    pallet_count=outbound_pallet_count,
                    package_count=outbound_package_count,
                    weight=float(item.get('weight', 0)) if item.get('weight') not in (None, '') else None,
                    volume=float(item.get('volume', 0)) if item.get('volume') not in (None, '') else None,
                    destination=destination,
                    transport_company=transport_company,
                    order_type=item.get('order_type', ''),
                    service_staff=item.get('service_staff', ''),
                    receiver_id=receiver_id,
                    large_layer=large_layer,
                    small_layer=small_layer,
                    pallet_board=pallet_board,
                    inbound_plate=item.get('inbound_plate', ''),
                    document_no=item.get('document_no', ''),
                    document_count=document_count,  # 添加单据份数字段
                    export_mode=item.get('export_mode', ''),
                    customs_broker=item.get('customs_broker', ''),
                    location=item.get('location', ''),
                    remarks=item.get('remarks', '') or remark1_value or '',  # 兼容旧字段
                    remark1=remark1_value,
                    remark2=item.get('remark2') if item.get('remark2') is not None else '',
                    create_time=datetime.now()
                )
                
                # 如果有出库时间，尝试解析（支持多种格式）
                time_to_parse = item.get('outbound_time') or departure_time
                if time_to_parse:
                    try:
                        # 尝试多种时间格式
                        time_formats = [
                            '%Y-%m-%d %H:%M',      # 2025-07-22 16:00
                            '%Y-%m-%d %H:%M:%S',   # 2025-07-22 16:00:00
                            '%Y-%m-%d',            # 2025-07-22
                        ]

                        parsed_time = None
                        for fmt in time_formats:
                            try:
                                parsed_time = datetime.strptime(time_to_parse, fmt)
                                break
                            except ValueError:
                                continue

                        if parsed_time:
                            outbound_record.outbound_time = parsed_time
                            current_app.logger.info(f"设置出库时间: {outbound_record.outbound_time}")
                        else:
                            raise ValueError(f"无法解析日期时间: {time_to_parse}")

                    except Exception as e:
                        current_app.logger.warning(f"解析出库时间失败: {str(e)}, 使用当前时间")

                # 设置操作用户ID和操作仓库ID
                if current_user.is_authenticated:
                    outbound_record.operated_by_user_id = current_user.id
                    outbound_record.operated_warehouse_id = current_user.warehouse_id
                    current_app.logger.info(f"设置操作信息: 用户ID={current_user.id}, 仓库ID={current_user.warehouse_id}")
                else:
                    current_app.logger.warning("用户未认证，无法设置操作信息")

                db.session.add(outbound_record)
                current_app.logger.info(f"添加出库记录: ID={outbound_record.id}")
                
                # 更新库存
                if identification_code and inventory:
                    # 记录更新前的库存
                    old_pallet = inventory.pallet_count
                    old_package = inventory.package_count

                    # 更新库存数量
                    inventory.pallet_count = max(0, inventory.pallet_count - outbound_pallet_count)
                    inventory.package_count = max(0, inventory.package_count - outbound_package_count)

                    current_app.logger.info(f"更新库存: ID={inventory.id}, 识别编码={inventory.identification_code}, "
                                          f"板数: {old_pallet} -> {inventory.pallet_count} (减少{outbound_pallet_count}), "
                                          f"件数: {old_package} -> {inventory.package_count} (减少{outbound_package_count})")

                    # 如果库存为0，删除库存记录
                    if inventory.pallet_count <= 0 and inventory.package_count <= 0:
                        current_app.logger.info(f"删除零库存记录: ID={inventory.id}, 识别编码={inventory.identification_code}")
                        db.session.delete(inventory)
                elif identification_code:
                    current_app.logger.warning(f"未找到识别编码为 {identification_code} 的库存记录")
                
                saved_count += 1
                
            except Exception as e:
                current_app.logger.error(f"处理第{idx+1}条记录时出错: {str(e)}")
                current_app.logger.error(traceback.format_exc())
                # 继续处理下一条记录，不中断整个批次
        
        # 提交事务
        db.session.commit()
        current_app.logger.info(f"成功提交事务，保存了 {saved_count} 条出库记录")
        
        # 返回成功响应
        return jsonify({
            'success': True,
            'message': f'成功保存 {saved_count} 条出库记录，更新了 {len(inventory_dict)} 条库存记录',
            'saved_count': saved_count,
            'batch_no': f"B{datetime.now().strftime('%Y%m%d%H%M')}"
        })
    except Exception as e:
        # 回滚事务
        db.session.rollback()
        
        # 记录错误
        current_app.logger.error(f"保存出库批次数据出错: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        
        # 返回错误响应
        return jsonify({
            'success': False,
            'message': f"保存出库批次数据出错: {str(e)}"
        }), 500

@bp.route('/outbound/list', methods=['GET'])
@csrf.exempt  # 豁免CSRF保护，提高API响应速度
def get_outbound_list():
    """获取出库记录列表API"""
    try:
        current_app.logger.info("开始处理出库记录列表API请求")
        # 获取查询参数
        customer_name = request.args.get('customer_name', '')
        plate_number = request.args.get('plate_number', '')
        date_start = request.args.get('date_start', '')
        date_end = request.args.get('date_end', '')
        
        # 构建查询
        query = OutboundRecord.query
        
        # 按客户名称筛选
        if customer_name:
            query = query.filter(OutboundRecord.customer_name.like(f'%{customer_name}%'))
            current_app.logger.info(f"按客户名称筛选: {customer_name}")
        
        # 按车牌号筛选
        if plate_number:
            query = query.filter(OutboundRecord.plate_number.like(f'%{plate_number}%'))
            current_app.logger.info(f"按车牌号筛选: {plate_number}")
        
        # 按日期范围筛选
        if date_start:
            try:
                start_date = datetime.strptime(date_start, '%Y-%m-%d')
                query = query.filter(OutboundRecord.outbound_time >= start_date)
                current_app.logger.info(f"按开始日期筛选: {date_start}")
            except ValueError:
                current_app.logger.warning(f"无效的开始日期格式: {date_start}")
                pass
        
        if date_end:
            try:
                end_date = datetime.strptime(date_end, '%Y-%m-%d')
                end_date = end_date.replace(hour=23, minute=59, second=59)
                query = query.filter(OutboundRecord.outbound_time <= end_date)
                current_app.logger.info(f"按结束日期筛选: {date_end}")
            except ValueError:
                current_app.logger.warning(f"无效的结束日期格式: {date_end}")
                pass
        
        # 按出库时间降序排序
        query = query.order_by(OutboundRecord.outbound_time.desc())
        
        # 执行查询
        records = query.all()
        current_app.logger.info(f"查询到 {len(records)} 条出库记录")
        
        # 转换为字典列表
        result = []
        for record in records:
            try:
                # 创建基本字典，只包含必要字段
                record_dict = {
                    'id': record.id,
                    'outbound_time': record.outbound_time.strftime('%Y-%m-%d %H:%M:%S') if record.outbound_time else '',
                    'plate_number': record.plate_number,
                    'customer_name': record.customer_name,
                    'identification_code': record.identification_code,
                    'pallet_count': record.pallet_count,
                    'package_count': record.package_count
                }
                
                result.append(record_dict)
                current_app.logger.debug(f"处理出库记录: ID={record.id}, 客户={record.customer_name}")
            except Exception as e:
                current_app.logger.error(f"处理出库记录 {record.id} 时出错: {str(e)}")
                current_app.logger.error(traceback.format_exc())
                # 继续处理下一条记录
        
        current_app.logger.info(f"成功处理 {len(result)} 条出库记录")
        
        return jsonify({
            'success': True,
            'records': result,
            'count': len(result)
        })
    except Exception as e:
        current_app.logger.error(f"获取出库记录列表出错: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f"获取出库记录列表出错: {str(e)}"
        }), 500

@bp.route('/outbound/history', methods=['GET'])
@csrf.exempt  # 豁免CSRF保护，提高API响应速度
def get_outbound_history():
    """获取指定识别编码的出库历史记录API"""
    try:
        current_app.logger.info("开始处理出库历史记录API请求")

        # 获取查询参数
        identification_code = request.args.get('identification_code', '')

        if not identification_code:
            return jsonify({
                'success': False,
                'message': '识别编码不能为空'
            }), 400

        current_app.logger.info(f"查询识别编码 {identification_code} 的出库历史记录")

        # 构建查询，按出库时间升序排序
        query = OutboundRecord.query.filter(
            OutboundRecord.identification_code == identification_code
        ).order_by(OutboundRecord.outbound_time.asc())

        # 执行查询
        records = query.all()
        current_app.logger.info(f"查询到 {len(records)} 条出库历史记录")

        # 转换为字典列表
        result = []
        for record in records:
            try:
                record_dict = {
                    'id': record.id,
                    'outbound_time': record.outbound_time.strftime('%Y-%m-%d %H:%M:%S') if record.outbound_time else '',
                    'plate_number': record.plate_number,
                    'customer_name': record.customer_name,
                    'identification_code': record.identification_code,
                    'pallet_count': record.pallet_count,
                    'package_count': record.package_count,
                    'remark1': record.remark1 or '',
                    'remark2': record.remark2 or ''
                }

                result.append(record_dict)
                current_app.logger.debug(f"处理出库历史记录: ID={record.id}, 客户={record.customer_name}")
            except Exception as e:
                current_app.logger.error(f"处理出库历史记录 {record.id} 时出错: {str(e)}")
                current_app.logger.error(traceback.format_exc())
                # 继续处理下一条记录

        current_app.logger.info(f"成功处理 {len(result)} 条出库历史记录")

        return jsonify({
            'success': True,
            'records': result,
            'count': len(result)
        })
    except Exception as e:
        current_app.logger.error(f"获取出库历史记录出错: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f"获取出库历史记录出错: {str(e)}"
        }), 500

@bp.route('/backend/outbound/save', methods=['POST'])
@csrf.exempt  # 豁免CSRF保护，因为这是API接口
def save_backend_outbound():
    """
    保存后端仓库出库到最终目的地的记录API
    """
    try:
        # 获取请求数据
        data = request.get_json()

        # 调试日志
        current_app.logger.info(f"收到后端仓库出库数据请求: {json.dumps(data, ensure_ascii=False)}")

        if not data:
            return jsonify({'success': False, 'message': '请求数据为空'}), 400

        # 验证必需字段
        required_fields = ['departure_date', 'plate_number', 'receiver_info', 'cargo_list']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'success': False, 'message': f'缺少必需字段: {field}'}), 400

        # 验证货物列表
        cargo_list = data['cargo_list']
        if not isinstance(cargo_list, list) or len(cargo_list) == 0:
            return jsonify({'success': False, 'message': '货物列表不能为空'}), 400

        # 验证每个货物项
        for i, cargo in enumerate(cargo_list):
            if not cargo.get('id'):
                return jsonify({'success': False, 'message': f'货物项 {i+1} 缺少ID'}), 400
            if not cargo.get('outbound_pallet_count') and not cargo.get('outbound_package_count'):
                return jsonify({'success': False, 'message': f'货物项 {i+1} 必须设置出库数量'}), 400

        # 开始数据库事务
        saved_records = []

        for cargo in cargo_list:
            # 查找对应的库存记录
            inventory = Inventory.query.get(cargo['id'])
            if not inventory:
                return jsonify({'success': False, 'message': f'未找到ID为 {cargo["id"]} 的库存记录'}), 400

            # 验证出库数量
            outbound_pallet = int(cargo.get('outbound_pallet_count', 0))
            outbound_package = int(cargo.get('outbound_package_count', 0))

            if outbound_pallet > inventory.pallet_count:
                return jsonify({'success': False, 'message': f'出库板数 {outbound_pallet} 超过库存板数 {inventory.pallet_count}'}), 400

            if outbound_package > inventory.package_count:
                return jsonify({'success': False, 'message': f'出库件数 {outbound_package} 超过库存件数 {inventory.package_count}'}), 400

            # 获取前端传递的单据份数，允许空值
            document_count_raw = cargo.get('document_count')
            document_count = None  # 默认为None
            if document_count_raw is not None and document_count_raw != '':
                try:
                    document_count = int(document_count_raw)
                    current_app.logger.info(f"使用前端传递的单据份数: 识别编码={inventory.identification_code}, 单据份数={document_count}")
                except (ValueError, TypeError):
                    current_app.logger.warning(f"前端传递的单据份数格式无效: {document_count_raw}，设置为None")
                    document_count = None
            else:
                current_app.logger.info(f"前端未传递单据份数或为空值，设置为None: 识别编码={inventory.identification_code}")

            # 创建出库记录
            outbound_record = OutboundRecord(
                outbound_time=datetime.strptime(data['departure_date'], '%Y-%m-%d'),
                plate_number=data['plate_number'],
                delivery_plate_number=data.get('delivery_truck', ''),  # 送货干线车
                customer_name=inventory.customer_name,
                identification_code=inventory.identification_code,
                pallet_count=outbound_pallet,
                package_count=outbound_package,
                weight=round((inventory.weight / max(inventory.pallet_count, inventory.package_count, 1)) * max(outbound_pallet, outbound_package), 2),
                volume=round((inventory.volume / max(inventory.pallet_count, inventory.package_count, 1)) * max(outbound_pallet, outbound_package), 2),
                export_mode=data.get('export_mode', '') or inventory.export_mode,  # 优先使用前端传递的值
                customs_broker=data.get('customs_broker', '') or inventory.customs_broker,  # 优先使用前端传递的值
                order_type=inventory.order_type,
                service_staff=inventory.service_staff,
                vehicle_type=data.get('vehicle_type', ''),  # 车型
                destination=data['receiver_info'].get('name', ''),  # 使用destination字段存储收货人名称
                warehouse_address=data['receiver_info'].get('address', ''),  # 使用warehouse_address存储收货地址
                contact_window=data['receiver_info'].get('phone', ''),  # 使用contact_window存储收货人电话
                remarks=cargo.get('outbound_remarks', ''),
                document_count=document_count,  # 添加单据份数字段
                inbound_plate=inventory.plate_number if hasattr(inventory, 'plate_number') else '',  # 入库车牌
                inbound_date=inventory.inbound_date if hasattr(inventory, 'inbound_date') else None,  # 入库日期
                location=inventory.location if hasattr(inventory, 'location') else ''  # 库位
            )

            # 不自动生成拆票分装备注，直接使用用户输入的备注

            db.session.add(outbound_record)

            # 更新库存
            inventory.pallet_count -= outbound_pallet
            inventory.package_count -= outbound_package

            # 如果库存为0，删除库存记录
            if inventory.pallet_count <= 0 and inventory.package_count <= 0:
                db.session.delete(inventory)

            saved_records.append({
                'id': outbound_record.id if hasattr(outbound_record, 'id') else None,
                'customer_name': outbound_record.customer_name,
                'identification_code': outbound_record.identification_code,
                'pallet_count': outbound_record.pallet_count,
                'package_count': outbound_record.package_count
            })

        # 提交事务
        db.session.commit()

        current_app.logger.info(f"成功保存 {len(saved_records)} 条后端仓库出库记录")

        return jsonify({
            'success': True,
            'message': f'成功保存 {len(saved_records)} 条出库记录',
            'data': saved_records
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"保存后端仓库出库记录时发生错误: {str(e)}")
        current_app.logger.error(f"错误详情: {traceback.format_exc()}")
        return jsonify({'success': False, 'message': f'保存失败: {str(e)}'}), 500

@bp.route('/backend/outbound/return', methods=['POST'])
@csrf.exempt  # 豁免CSRF保护，因为这是API接口
def save_backend_outbound_return():
    """
    保存后端仓库退货到前端仓的出库记录API
    """
    try:
        # 获取请求数据
        data = request.get_json()

        # 调试日志
        current_app.logger.info(f"收到后端仓库退货数据请求: {json.dumps(data, ensure_ascii=False)}")

        if not data:
            current_app.logger.error("请求数据为空")
            return jsonify({
                'success': False,
                'message': '请求数据为空'
            }), 400

        if 'records' not in data:
            current_app.logger.error(f"数据格式不正确，缺少records字段。数据键: {list(data.keys())}")
            return jsonify({
                'success': False,
                'message': '数据格式不正确，必须包含records字段'
            }), 400

        records = data.get('records', [])

        current_app.logger.info(f"解析后的数据: records数量={len(records)}")

        if not records:
            current_app.logger.error("没有提供出库记录数据")
            return jsonify({
                'success': False,
                'message': '没有提供出库记录数据'
            }), 400

        # 预加载所有需要更新的库存记录,减少数据库查询次数
        identification_codes = [record.get('identification_code') for record in records if record.get('identification_code')]
        inventory_dict = {}
        if identification_codes:
            current_app.logger.info(f"预加载库存记录,识别码: {identification_codes}")
            inventories = Inventory.query.filter(Inventory.identification_code.in_(identification_codes)).all()
            for inv in inventories:
                inventory_dict[inv.identification_code] = inv
            current_app.logger.info(f"已加载 {len(inventory_dict)} 条库存记录")

        # 生成批次号
        batch_no = f"BR{datetime.now().strftime('%Y%m%d%H%M')}"
        current_app.logger.info(f"生成批次号: {batch_no}")

        # 批量创建出库记录
        saved_count = 0
        errors = []

        for idx, record in enumerate(records):
            try:
                current_app.logger.info(f"处理第{idx+1}条记录: 客户={record.get('customer_name')}, 识别码={record.get('identification_code')}")

                # 获取出库数量，确保是整数
                try:
                    pallet_value = record.get('pallet_count', 0)
                    package_value = record.get('package_count', 0)

                    # 检查是否为小数
                    if isinstance(pallet_value, (int, float)) and pallet_value != int(pallet_value):
                        errors.append(f"第{idx+1}条记录：板数必须是整数，不能是小数")
                        continue
                    if isinstance(package_value, (int, float)) and package_value != int(package_value):
                        errors.append(f"第{idx+1}条记录：件数必须是整数，不能是小数")
                        continue

                    outbound_pallet_count = int(pallet_value)
                    outbound_package_count = int(package_value)

                    if outbound_pallet_count < 0 or outbound_package_count < 0:
                        errors.append(f"第{idx+1}条记录：板数和件数不能为负数")
                        continue

                except (ValueError, TypeError):
                    errors.append(f"第{idx+1}条记录：板数和件数必须是有效的整数")
                    continue

                identification_code = record.get('identification_code', '')

                # 获取库存信息
                inventory = inventory_dict.get(identification_code) if identification_code else None

                # 获取前端传递的单据份数，允许空值
                document_count_raw = record.get('document_count')
                document_count = None  # 默认为None
                if document_count_raw is not None and document_count_raw != '':
                    try:
                        document_count = int(document_count_raw)
                        current_app.logger.info(f"使用前端传递的单据份数: 识别编码={identification_code}, 单据份数={document_count}")
                    except (ValueError, TypeError):
                        current_app.logger.warning(f"前端传递的单据份数格式无效: {document_count_raw}，设置为None")
                        document_count = None
                else:
                    current_app.logger.info(f"前端未传递单据份数或为空值，设置为None: 识别编码={identification_code}")

                # 解析出库时间
                outbound_time = datetime.now()  # 默认当前时间
                if record.get('outbound_time'):
                    try:
                        outbound_time = datetime.fromisoformat(record.get('outbound_time').replace('T', ' '))
                        current_app.logger.info(f"设置出库时间: {outbound_time}")
                    except Exception as e:
                        current_app.logger.warning(f"解析出库时间失败: {str(e)}, 使用当前时间")

                # 创建出库记录
                outbound_record = OutboundRecord(
                    outbound_time=outbound_time,
                    plate_number=record.get('plate_number', '') or record.get('delivery_plate_number', ''),
                    customer_name=record.get('customer_name', ''),
                    identification_code=identification_code,
                    pallet_count=outbound_pallet_count,
                    package_count=outbound_package_count,
                    weight=float(record.get('weight', 0)) if record.get('weight') not in (None, '') else None,
                    volume=float(record.get('volume', 0)) if record.get('volume') not in (None, '') else None,
                    destination=record.get('target_warehouse', ''),
                    order_type=record.get('order_type', ''),
                    service_staff=record.get('service_staff', ''),
                    inbound_plate=record.get('inbound_plate', ''),
                    export_mode=record.get('export_mode', ''),
                    customs_broker=record.get('customs_broker', ''),
                    document_count=document_count,  # 添加单据份数字段
                    remark1=record.get('remark1', ''),
                    remark2=record.get('remark2', ''),
                    batch_no=batch_no,  # 设置批次号
                    operated_warehouse_id=4,  # 设置后端仓库ID (凭祥北投仓)
                    create_time=datetime.now()
                )

                db.session.add(outbound_record)
                current_app.logger.info(f"添加后端仓库退货出库记录: 客户={outbound_record.customer_name}")

                # 更新库存
                if identification_code and inventory:
                    # 记录更新前的库存
                    old_pallet = inventory.pallet_count
                    old_package = inventory.package_count

                    # 更新库存数量
                    inventory.pallet_count = max(0, inventory.pallet_count - outbound_pallet_count)
                    inventory.package_count = max(0, inventory.package_count - outbound_package_count)

                    current_app.logger.info(f"更新库存: ID={inventory.id}, 识别编码={inventory.identification_code}, "
                                          f"板数: {old_pallet} -> {inventory.pallet_count} (减少{outbound_pallet_count}), "
                                          f"件数: {old_package} -> {inventory.package_count} (减少{outbound_package_count})")

                    # 如果库存为0，删除库存记录
                    if inventory.pallet_count <= 0 and inventory.package_count <= 0:
                        current_app.logger.info(f"删除零库存记录: ID={inventory.id}, 识别编码={inventory.identification_code}")
                        db.session.delete(inventory)
                elif identification_code:
                    current_app.logger.warning(f"未找到识别编码为 {identification_code} 的库存记录")

                saved_count += 1

            except Exception as e:
                current_app.logger.error(f"处理第{idx+1}条记录时出错: {str(e)}")
                current_app.logger.error(traceback.format_exc())
                errors.append(f"第{idx+1}条记录处理失败: {str(e)}")
                # 继续处理下一条记录，不中断整个批次

        # 如果有错误，返回错误信息
        if errors:
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': '部分记录处理失败: ' + '; '.join(errors)
            }), 400

        # 提交事务
        db.session.commit()
        current_app.logger.info(f"成功提交事务，保存了 {saved_count} 条后端仓库退货出库记录")

        # 返回成功响应
        return jsonify({
            'success': True,
            'message': f'成功保存 {saved_count} 条返回前端仓记录',
            'saved_count': saved_count,
            'batch_no': batch_no
        })

    except Exception as e:
        # 回滚事务
        db.session.rollback()

        # 记录错误
        current_app.logger.error(f"保存后端仓库退货数据出错: {str(e)}")
        current_app.logger.error(traceback.format_exc())

        # 返回错误响应
        return jsonify({
            'success': False,
            'message': f"保存后端仓库退货数据出错: {str(e)}"
        }), 500

@bp.route('/backend/inventory', methods=['GET'])
@csrf.exempt  # 豁免CSRF保护，提高API响应速度
def get_backend_inventory_for_outbound():
    """获取后端仓库库存数据API"""
    try:
        current_app.logger.info("开始处理后端仓库库存数据API请求")

        # 查询有库存的记录（板数或件数大于0）
        query = Inventory.query.filter(
            or_(
                Inventory.pallet_count > 0,
                Inventory.package_count > 0
            )
        ).order_by(Inventory.create_time.desc())

        # 执行查询
        inventories = query.all()
        current_app.logger.info(f"查询到 {len(inventories)} 条库存记录")

        # 转换为字典列表
        result = []
        for inventory in inventories:
            try:
                inventory_dict = {
                    'id': inventory.id,
                    'customer_name': inventory.customer_name or '',
                    'plate_number': inventory.plate_number or '',
                    'identification_code': inventory.identification_code or '',
                    'order_type': inventory.order_type or '',
                    'pallet_count': inventory.pallet_count or 0,
                    'package_count': inventory.package_count or 0,
                    'weight': inventory.weight or 0,
                    'volume': inventory.volume or 0,
                    'export_mode': inventory.export_mode or '普通',
                    'customs_broker': inventory.customs_broker or '',
                    'delivery_truck': '',  # 后端仓库退货时的送货干线车字段
                    'service_staff': inventory.service_staff or '',
                    'remark1': inventory.remark1 or '',
                    'remark2': inventory.remark2 or ''
                }

                result.append(inventory_dict)
                current_app.logger.debug(f"处理库存记录: ID={inventory.id}, 客户={inventory.customer_name}")
            except Exception as e:
                current_app.logger.error(f"处理库存记录 {inventory.id} 时出错: {str(e)}")
                current_app.logger.error(traceback.format_exc())
                # 继续处理下一条记录

        current_app.logger.info(f"成功处理 {len(result)} 条库存记录")

        return jsonify({
            'success': True,
            'data': result,
            'count': len(result)
        })

    except Exception as e:
        current_app.logger.error(f"获取后端仓库库存数据出错: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f"获取后端仓库库存数据出错: {str(e)}"
        }), 500


@bp.route('/frontend/outbound/to_backend', methods=['POST'])
@csrf.exempt  # 豁免CSRF保护，因为这是API接口
def save_frontend_outbound_to_backend():
    """
    保存前端仓库出库到后端仓库的记录API
    支持admin用户根据始发仓智能匹配权限
    """
    try:
        # 获取请求数据
        data = request.get_json()

        # 调试日志
        current_app.logger.info(f"收到前端仓库出库到后端仓库数据请求: {json.dumps(data, ensure_ascii=False)}")

        if not data:
            current_app.logger.error("请求数据为空")
            return jsonify({
                'success': False,
                'message': '请求数据为空'
            }), 400

        # 验证必需字段
        if 'commonData' not in data or 'records' not in data:
            current_app.logger.error(f"数据格式不正确，缺少必要字段。数据键: {list(data.keys())}")
            return jsonify({
                'success': False,
                'message': '数据格式不正确，必须包含commonData和records字段'
            }), 400

        common_data = data['commonData']
        records = data['records']

        # 验证记录列表
        if not isinstance(records, list) or len(records) == 0:
            return jsonify({
                'success': False,
                'message': '出库记录列表不能为空'
            }), 400

        # 权限检查 - 特殊处理admin用户
        if not current_user.is_authenticated:
            return jsonify({
                'success': False,
                'message': '用户未登录'
            }), 401

        # 获取始发仓库信息
        origin_warehouse_name = common_data.get('originWarehouse', '')
        current_app.logger.info(f"始发仓库: {origin_warehouse_name}")

        # admin用户权限检查 - 根据始发仓智能匹配
        if current_user.is_super_admin():
            current_app.logger.info(f"管理员用户 {current_user.username} 操作前端仓库出库到后端仓库，始发仓: {origin_warehouse_name}")
            # admin用户可以操作任何仓库的出库
        else:
            # 普通用户需要检查仓库权限
            if not hasattr(current_user, 'warehouse') or not current_user.warehouse:
                return jsonify({
                    'success': False,
                    'message': '用户没有关联仓库，请联系管理员'
                }), 403

            # 检查用户仓库是否与始发仓库匹配
            user_warehouse_name = current_user.warehouse.warehouse_name
            if user_warehouse_name != origin_warehouse_name:
                return jsonify({
                    'success': False,
                    'message': f'您只能操作 {user_warehouse_name} 的出库，无法操作 {origin_warehouse_name} 的出库'
                }), 403

        # 开始数据库事务
        try:
            saved_records = []

            for record in records:
                # 验证必需字段
                identification_code = record.get('identification_code', '').strip()
                if not identification_code:
                    current_app.logger.error(f"记录缺少识别编码: {record}")
                    continue

                # 查找对应的库存记录
                inventory = Inventory.query.filter_by(
                    identification_code=identification_code
                ).first()

                if not inventory:
                    current_app.logger.error(f"未找到识别编码为 {identification_code} 的库存记录")
                    return jsonify({
                        'success': False,
                        'message': f'未找到识别编码为 {identification_code} 的库存记录'
                    }), 400

                # 验证出库数量
                outbound_pallet = int(record.get('pallet_count', 0))
                outbound_package = int(record.get('package_count', 0))

                if outbound_pallet > inventory.pallet_count:
                    return jsonify({
                        'success': False,
                        'message': f'出库板数 {outbound_pallet} 超过库存板数 {inventory.pallet_count}'
                    }), 400

                if outbound_package > inventory.package_count:
                    return jsonify({
                        'success': False,
                        'message': f'出库件数 {outbound_package} 超过库存件数 {inventory.package_count}'
                    }), 400

                # 创建出库记录
                outbound_record = OutboundRecord(
                    outbound_time=datetime.strptime(record.get('outbound_time', ''), '%Y-%m-%d').date(),
                    customer_name=record.get('customer_name', ''),
                    identification_code=identification_code,
                    pallet_count=outbound_pallet,
                    package_count=outbound_package,
                    weight=float(record.get('weight', 0)),
                    volume=float(record.get('volume', 0)),
                    batch_number=record.get('batch_number', ''),
                    documents=record.get('documents', ''),
                    remarks=record.get('remarks', ''),
                    remarks2=record.get('remarks2', ''),

                    # 运输信息
                    plate_number=common_data.get('trunkPlate', ''),
                    vehicle_type=common_data.get('vehicleType', ''),
                    driver_name=common_data.get('driverName', ''),
                    driver_phone=common_data.get('driverPhone', ''),

                    # 时间信息
                    arrival_time=datetime.strptime(common_data.get('arrivalTime', ''), '%Y-%m-%d %H:%M') if common_data.get('arrivalTime') else None,
                    loading_start_time=datetime.strptime(common_data.get('loadingStartTime', ''), '%Y-%m-%d %H:%M') if common_data.get('loadingStartTime') else None,
                    loading_end_time=datetime.strptime(common_data.get('loadingEndTime', ''), '%Y-%m-%d %H:%M') if common_data.get('loadingEndTime') else None,
                    departure_time=datetime.strptime(common_data.get('departureTime', ''), '%Y-%m-%d %H:%M') if common_data.get('departureTime') else None,

                    # 仓库信息
                    origin_warehouse=common_data.get('originWarehouse', ''),
                    destination_warehouse=common_data.get('destinationWarehouse', ''),
                    origin_contact=common_data.get('originContact', ''),
                    destination_contact=common_data.get('destinationContact', ''),
                    origin_address=common_data.get('originAddress', ''),
                    destination_address=common_data.get('destinationAddress', ''),

                    # 托盘信息
                    large_pallet=int(common_data.get('largePallet', 0)) if common_data.get('largePallet') else 0,
                    small_pallet=int(common_data.get('smallPallet', 0)) if common_data.get('smallPallet') else 0,
                    card_pallet=int(common_data.get('cardPallet', 0)) if common_data.get('cardPallet') else 0,

                    # 业务字段
                    inbound_plate=record.get('inbound_plate', ''),
                    order_type=record.get('order_type', ''),
                    export_mode=record.get('export_mode', ''),
                    customs_broker=record.get('customs_broker', ''),
                    service_staff=record.get('service_staff', ''),
                    document_count=record.get('document_count', ''),

                    # 目的地类型
                    destination_type='backend_warehouse',

                    # 操作信息
                    operated_warehouse_id=inventory.operated_warehouse_id,
                    create_time=datetime.now(),
                    update_time=datetime.now()
                )

                db.session.add(outbound_record)

                # 更新库存
                inventory.pallet_count -= outbound_pallet
                inventory.package_count -= outbound_package
                inventory.update_time = datetime.now()

                saved_records.append({
                    'identification_code': identification_code,
                    'customer_name': record.get('customer_name', ''),
                    'pallet_count': outbound_pallet,
                    'package_count': outbound_package
                })

            # 提交事务
            db.session.commit()

            current_app.logger.info(f"成功保存 {len(saved_records)} 条前端仓库出库到后端仓库记录")

            return jsonify({
                'success': True,
                'message': f'成功保存 {len(saved_records)} 条出库记录',
                'count': len(saved_records),
                'records': saved_records
            })

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"保存前端仓库出库到后端仓库记录时发生错误: {str(e)}")
            current_app.logger.error(traceback.format_exc())
            return jsonify({
                'success': False,
                'message': f'保存失败: {str(e)}'
            }), 500

    except Exception as e:
        current_app.logger.error(f"处理前端仓库出库到后端仓库请求时发生错误: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'处理请求失败: {str(e)}'
        }), 500