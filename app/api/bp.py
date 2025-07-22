from flask import Blueprint

bp = Blueprint('api', __name__, url_prefix='/api')

# 导入路由，确保它们被注册到蓝图
from app.api import outbound_routes, inventory_routes, backend_routes