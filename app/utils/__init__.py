# Utils package

import sqlite3
from flask import render_template, request, current_app
from functools import wraps
from datetime import datetime
from app import db

# 导入批次号生成器
from .batch_generator import generate_batch_number, parse_batch_number, get_batch_statistics

# 导入识别编码生成器
from .identification_generator import IdentificationCodeGenerator

def render_ajax_aware(template_name, **context):
    """
    智能渲染函数，根据请求类型选择合适的模板

    Args:
        template_name: 基础模板名称
        **context: 模板上下文
    """
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # AJAX请求，尝试使用AJAX版本的模板
        ajax_template_name = template_name.replace('.html', '_ajax.html')
        try:
            return render_template(ajax_template_name, **context)
        except:
            # 如果AJAX模板不存在，使用普通模板
            pass

    return render_template(template_name, **context)

def get_db_connection():
    """
    获取数据库连接

    Returns:
        SQLite数据库连接对象
    """
    conn = sqlite3.connect(current_app.config['DATABASE_URI'])
    conn.row_factory = sqlite3.Row
    return conn

def strip_whitespace(value):
    """
    去除字符串中的所有空格

    Args:
        value: 输入值，可以是字符串或其他类型

    Returns:
        如果输入是字符串，返回去除空格后的字符串；否则原样返回
    """
    if isinstance(value, str):
        return value.strip()
    return value

def clean_dict_whitespace(data):
    """
    清理字典中所有字符串值的空格

    Args:
        data: 包含键值对的字典

    Returns:
        处理后的字典，所有字符串值都去除了首尾空格
    """
    if not isinstance(data, dict):
        return data

    result = {}
    for key, value in data.items():
        if isinstance(value, str):
            result[key] = value.strip()
        elif isinstance(value, dict):
            result[key] = clean_dict_whitespace(value)
        elif isinstance(value, list):
            result[key] = [clean_dict_whitespace(item) if isinstance(item, dict)
                          else strip_whitespace(item) for item in value]
        else:
            result[key] = value
    return result

def update_inventory_atomically(inventory_id, pallet_decrease=0, package_decrease=0):
    """
    原子性更新库存数量

    Args:
        inventory_id: 库存记录ID
        pallet_decrease: 要减少的板数
        package_decrease: 要减少的件数

    Returns:
        tuple: (success: bool, message: str)
    """
    from app.models import Inventory

    try:
        # 使用数据库锁确保原子性
        inventory = Inventory.query.with_for_update().get(inventory_id)
        if not inventory:
            current_app.logger.error(f"库存记录不存在: ID {inventory_id}")
            return False, "库存记录不存在"

        # 检查库存是否足够
        current_pallet = inventory.pallet_count or 0
        current_package = inventory.package_count or 0

        if current_pallet < pallet_decrease:
            return False, f"板数库存不足，当前: {current_pallet}, 需要: {pallet_decrease}"

        if current_package < package_decrease:
            return False, f"件数库存不足，当前: {current_package}, 需要: {package_decrease}"

        # 更新库存
        old_pallet = current_pallet
        old_package = current_package

        inventory.pallet_count = max(0, current_pallet - pallet_decrease)
        inventory.package_count = max(0, current_package - package_decrease)
        inventory.last_updated = datetime.now()
        inventory.version = (inventory.version or 0) + 1  # 乐观锁版本号

        current_app.logger.info(f"库存更新: ID {inventory_id}, 板数 {old_pallet}->{inventory.pallet_count}, "
                              f"件数 {old_package}->{inventory.package_count}")

        return True, "库存更新成功"

    except Exception as e:
        current_app.logger.error(f"库存更新失败: {str(e)}")
        return False, f"库存更新失败: {str(e)}"

def validate_inventory_consistency(identification_code, warehouse_ids):
    """
    验证库存一致性

    Args:
        identification_code: 识别编码
        warehouse_ids: 仓库ID列表

    Returns:
        tuple: (is_consistent: bool, theoretical_pallet: int, theoretical_package: int)
    """
    from app.models import Inventory, InboundRecord, OutboundRecord

    try:
        # 查找库存记录
        inventory = Inventory.query.filter_by(
            identification_code=identification_code
        ).filter(
            Inventory.operated_warehouse_id.in_(warehouse_ids)
        ).first()

        if not inventory:
            return True, 0, 0  # 没有库存记录，认为是一致的

        # 查找入库记录
        inbound_record = InboundRecord.query.filter_by(
            identification_code=identification_code
        ).first()

        if not inbound_record:
            # 没有入库记录，理论库存应该为0
            return (inventory.pallet_count == 0 and inventory.package_count == 0), 0, 0

        # 查找出库记录
        outbound_records = OutboundRecord.query.filter_by(
            identification_code=identification_code
        ).filter(
            OutboundRecord.operated_warehouse_id.in_(warehouse_ids)
        ).all()

        # 计算理论库存
        original_pallet = inbound_record.pallet_count or 0
        original_package = inbound_record.package_count or 0

        total_out_pallet = sum(rec.pallet_count or 0 for rec in outbound_records)
        total_out_package = sum(rec.package_count or 0 for rec in outbound_records)

        theoretical_pallet = max(0, original_pallet - total_out_pallet)
        theoretical_package = max(0, original_package - total_out_package)

        current_pallet = inventory.pallet_count or 0
        current_package = inventory.package_count or 0

        is_consistent = (current_pallet == theoretical_pallet and
                        current_package == theoretical_package)

        return is_consistent, theoretical_pallet, theoretical_package

    except Exception as e:
        current_app.logger.error(f"验证库存一致性失败: {str(e)}")
        return False, 0, 0
