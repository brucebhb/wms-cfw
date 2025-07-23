from flask import render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from app import db, csrf
from app.customer import bp
from app.models import InboundRecord, OutboundRecord, User
from app.decorators import require_permission
from datetime import datetime, timedelta

@bp.route('/dashboard')
@login_required
# @require_permission('CUSTOMER_INBOUND_VIEW')  # 临时禁用权限检查
def dashboard():
    """客户中心首页"""
    return render_template('customer/dashboard.html', title='客户中心')

@bp.route('/inbound')
@login_required
# @require_permission('CUSTOMER_INBOUND_VIEW')  # 临时禁用权限检查
def inbound():
    """客户入库记录页面"""
    return render_template('customer/inbound.html', title='入库记录')

@bp.route('/outbound')
@login_required
# @require_permission('CUSTOMER_OUTBOUND_VIEW')  # 临时禁用权限检查
def outbound():
    """客户出库记录页面"""
    return render_template('customer/outbound.html', title='出库记录')

@bp.route('/inventory')
@login_required
# @require_permission('CUSTOMER_INVENTORY_VIEW')  # 临时禁用权限检查
def inventory():
    """客户库存页面"""
    return render_template('customer/inventory.html', title='当前库存')

@bp.route('/reports')
@login_required
# @require_permission('CUSTOMER_REPORT_VIEW')  # 临时禁用权限检查
def reports():
    """客户报表页面"""
    return render_template('customer/reports.html', title='数据报表')

# API接口

@bp.route('/api/customer/stats')
@csrf.exempt
@login_required
@require_permission('CUSTOMER_INBOUND_VIEW')
def api_customer_stats():
    """获取客户数据统计"""
    try:
        customer_name = current_user.real_name
        
        # 统计入库记录
        inbound_count = InboundRecord.query.filter_by(customer_name=customer_name).count()
        
        # 统计出库记录
        outbound_count = OutboundRecord.query.filter_by(customer_name=customer_name).count()
        
        # 统计当前库存（入库减去出库）
        # 这里简化处理，实际应该根据具体业务逻辑计算
        inventory_count = max(0, inbound_count - outbound_count)
        
        # 统计总重量
        inbound_weight = db.session.query(db.func.sum(InboundRecord.weight)).filter_by(customer_name=customer_name).scalar() or 0
        outbound_weight = db.session.query(db.func.sum(OutboundRecord.weight)).filter_by(customer_name=customer_name).scalar() or 0
        total_weight = max(0, inbound_weight - outbound_weight)
        
        return jsonify({
            'inbound_count': inbound_count,
            'outbound_count': outbound_count,
            'inventory_count': inventory_count,
            'total_weight': float(total_weight)
        })
        
    except Exception as e:
        current_app.logger.error(f"获取客户统计数据失败: {str(e)}")
        return jsonify({'error': '获取统计数据失败'}), 500

@bp.route('/api/customer/recent-inbound')
@csrf.exempt
@login_required
@require_permission('CUSTOMER_INBOUND_VIEW')
def api_recent_inbound():
    """获取客户最近入库记录"""
    try:
        customer_name = current_user.real_name
        
        records = InboundRecord.query.filter_by(customer_name=customer_name)\
                                   .order_by(InboundRecord.inbound_time.desc())\
                                   .limit(10).all()
        
        return jsonify({
            'records': [{
                'id': record.id,
                'identification_code': record.identification_code,
                'inbound_time': record.inbound_time.strftime('%Y-%m-%d %H:%M') if record.inbound_time else '',
                'pallet_count': record.pallet_count,
                'package_count': record.package_count,
                'weight': float(record.weight) if record.weight else 0,
                'plate_number': record.plate_number
            } for record in records]
        })
        
    except Exception as e:
        current_app.logger.error(f"获取客户入库记录失败: {str(e)}")
        return jsonify({'error': '获取入库记录失败'}), 500

@bp.route('/api/customer/recent-outbound')
@csrf.exempt
@login_required
@require_permission('CUSTOMER_OUTBOUND_VIEW')
def api_recent_outbound():
    """获取客户最近出库记录"""
    try:
        customer_name = current_user.real_name
        
        records = OutboundRecord.query.filter_by(customer_name=customer_name)\
                                    .order_by(OutboundRecord.outbound_time.desc())\
                                    .limit(10).all()
        
        return jsonify({
            'records': [{
                'id': record.id,
                'identification_code': record.identification_code,
                'outbound_time': record.outbound_time.strftime('%Y-%m-%d %H:%M') if record.outbound_time else '',
                'pallet_count': record.pallet_count,
                'package_count': record.package_count,
                'weight': float(record.weight) if record.weight else 0,
                'destination': record.destination,
                'plate_number': record.plate_number
            } for record in records]
        })
        
    except Exception as e:
        current_app.logger.error(f"获取客户出库记录失败: {str(e)}")
        return jsonify({'error': '获取出库记录失败'}), 500

@bp.route('/api/customer/inbound-list')
@csrf.exempt
@login_required
@require_permission('CUSTOMER_INBOUND_VIEW')
def api_customer_inbound_list():
    """获取客户入库记录列表"""
    try:
        customer_name = current_user.real_name
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # 日期过滤
        date_start = request.args.get('date_start')
        date_end = request.args.get('date_end')
        
        query = InboundRecord.query.filter_by(customer_name=customer_name)
        
        if date_start:
            query = query.filter(InboundRecord.inbound_time >= datetime.strptime(date_start, '%Y-%m-%d'))
        if date_end:
            query = query.filter(InboundRecord.inbound_time <= datetime.strptime(date_end + ' 23:59:59', '%Y-%m-%d %H:%M:%S'))
        
        records = query.order_by(InboundRecord.inbound_time.desc())\
                      .paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'records': [{
                'id': record.id,
                'inbound_time': record.inbound_time.strftime('%Y-%m-%d %H:%M') if record.inbound_time else '',
                'plate_number': record.plate_number,
                'identification_code': record.identification_code,
                'pallet_count': record.pallet_count,
                'package_count': record.package_count,
                'weight': float(record.weight) if record.weight else 0,
                'volume': float(record.volume) if record.volume else 0,
                'location': record.location,
                'service_staff': record.service_staff
            } for record in records.items],
            'total': records.total,
            'pages': records.pages,
            'current_page': records.page,
            'has_next': records.has_next,
            'has_prev': records.has_prev
        })
        
    except Exception as e:
        current_app.logger.error(f"获取客户入库列表失败: {str(e)}")
        return jsonify({'error': '获取入库列表失败'}), 500

@bp.route('/api/customer/outbound-list')
@csrf.exempt
@login_required
@require_permission('CUSTOMER_OUTBOUND_VIEW')
def api_customer_outbound_list():
    """获取客户出库记录列表"""
    try:
        customer_name = current_user.real_name
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # 日期过滤
        date_start = request.args.get('date_start')
        date_end = request.args.get('date_end')
        
        query = OutboundRecord.query.filter_by(customer_name=customer_name)
        
        if date_start:
            query = query.filter(OutboundRecord.outbound_time >= datetime.strptime(date_start, '%Y-%m-%d'))
        if date_end:
            query = query.filter(OutboundRecord.outbound_time <= datetime.strptime(date_end + ' 23:59:59', '%Y-%m-%d %H:%M:%S'))
        
        records = query.order_by(OutboundRecord.outbound_time.desc())\
                      .paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'records': [{
                'id': record.id,
                'outbound_time': record.outbound_time.strftime('%Y-%m-%d %H:%M') if record.outbound_time else '',
                'plate_number': record.plate_number,
                'identification_code': record.identification_code,
                'pallet_count': record.pallet_count,
                'package_count': record.package_count,
                'weight': float(record.weight) if record.weight else 0,
                'volume': float(record.volume) if record.volume else 0,
                'destination': record.destination,
                'transport_company': record.transport_company,
                'service_staff': record.service_staff
            } for record in records.items],
            'total': records.total,
            'pages': records.pages,
            'current_page': records.page,
            'has_next': records.has_next,
            'has_prev': records.has_prev
        })
        
    except Exception as e:
        current_app.logger.error(f"获取客户出库列表失败: {str(e)}")
        return jsonify({'error': '获取出库列表失败'}), 500
