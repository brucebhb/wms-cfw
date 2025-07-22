"""
临时维护蓝图 - 解决模板错误
"""
from flask import Blueprint, jsonify

maintenance_bp = Blueprint('maintenance', __name__)

@maintenance_bp.route('/index')
def index():
    """临时维护页面"""
    return jsonify({'message': '维护功能暂时禁用'})
