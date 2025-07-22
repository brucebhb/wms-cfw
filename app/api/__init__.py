from flask import Blueprint

bp = Blueprint('api', __name__, url_prefix='/api')

# 导入路由，确保它们被注册到蓝图
from app.api import inventory_routes, outbound_routes, startup_routes, backend_routes

# 确保所有路由函数被导入
from app.api.inventory_routes import get_inventory
from app.api.outbound_routes import save_outbound_batch, get_outbound_list, get_outbound_history
from app.api.startup_routes import get_startup_status, health_check, get_system_info
from app.api.backend_routes import backend_statistics, backend_dashboard