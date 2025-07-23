from flask import Blueprint

bp = Blueprint('admin', __name__)

from app.admin import routes
from app.admin import user_permission_routes
from app.admin import permission_management_routes
