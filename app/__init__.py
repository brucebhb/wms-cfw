from flask import Flask, g, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager
import logging
import os
import time

# 创建数据库实例
db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()
login_manager = LoginManager()

def create_app(config_class=None):
    """创建最小化Flask应用"""
    app = Flask(__name__)
    
    # 使用简化配置
    if config_class is None:
        from config import Config
        config_class = Config
    
    app.config.from_object(config_class)
    
    # 简化数据库配置
    if 'mysql' in app.config['SQLALCHEMY_DATABASE_URI'].lower():
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_pre_ping': True,
            'pool_recycle': 300,
            'pool_timeout': 20,
            'max_overflow': 10,
            'pool_size': 10,
            'echo': False
        }
    
    # 初始化扩展（移除复杂的后台初始化）
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    # CSRF错误处理
    from flask_wtf.csrf import CSRFError
    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        """处理CSRF错误"""
        from flask import request, redirect, url_for, flash, jsonify

        app.logger.warning(f"CSRF错误: {e.description}, IP: {request.remote_addr}")

        # 如果是AJAX请求，返回JSON错误
        if request.is_json or 'application/json' in request.headers.get('Content-Type', ''):
            return jsonify({
                'success': False,
                'error': '安全验证失败，请刷新页面重试',
                'error_type': 'csrf'
            }), 400

        # 普通请求，重定向到登录页面
        flash('安全验证失败，请重新登录', 'error')
        return redirect(url_for('auth.login'))

    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '请先登录以访问此页面。'
    
    # 注册蓝图（只注册必要的）
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    # 注册API蓝图
    try:
        from app.api.bp import bp as api_bp
        app.register_blueprint(api_bp)
    except ImportError as e:
        app.logger.warning(f'API蓝图未找到，跳过注册: {e}')

    # 注册reports蓝图（避免模板URL构建错误）
    try:
        from app.reports import bp as reports_bp
        app.register_blueprint(reports_bp, url_prefix='/reports')
    except ImportError:
        app.logger.warning('Reports蓝图未找到，跳过注册')

    # 注册admin蓝图（避免模板URL构建错误）
    try:
        from app.admin import bp as admin_bp
        app.register_blueprint(admin_bp, url_prefix='/admin')
    except ImportError:
        app.logger.warning('Admin蓝图未找到，跳过注册')

    # 注册customer蓝图（避免模板URL构建错误）
    try:
        from app.customer import bp as customer_bp
        app.register_blueprint(customer_bp, url_prefix='/customer')
    except ImportError:
        app.logger.warning('Customer蓝图未找到，跳过注册')
    
    # 移除复杂的缓存和优化系统初始化

    # CSRF错误处理
    @app.errorhandler(400)
    def handle_csrf_error(error):
        """处理CSRF错误"""
        from flask import request, redirect, url_for, flash

        # 如果是CSRF错误，重定向到登录页面
        if 'CSRF' in str(error) or 'csrf' in str(error).lower():
            app.logger.warning(f"CSRF错误: {error}, IP: {request.remote_addr}")
            flash('安全验证失败，请重新登录', 'error')
            return redirect(url_for('auth.login'))

        return f"""
        <h1>请求错误</h1>
        <p>请求格式不正确。</p>
        <p><a href="/">返回首页</a></p>
        """, 400

    # 简化的错误处理
    @app.errorhandler(500)
    def handle_internal_error(error):
        """处理500错误"""
        import traceback
        error_info = traceback.format_exc()
        app.logger.error(f"Internal Server Error: {error_info}")

        return f"""
        <h1>系统维护中</h1>
        <p>系统正在进行维护，请稍后再试。</p>
        <details>
            <summary>错误详情</summary>
            <pre>{error_info}</pre>
        </details>
        <p><a href="/">返回首页</a></p>
        """, 500
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        """处理所有异常"""
        import traceback
        error_info = traceback.format_exc()
        app.logger.error(f"Unhandled Exception: {error_info}")
        
        return f"""
        <h1>系统异常</h1>
        <p>系统遇到了一个错误。</p>
        <details>
            <summary>错误详情</summary>
            <pre>{error_info}</pre>
        </details>
        <p><a href="/">返回首页</a></p>
        """, 500
    
    # 简化的数据库初始化
    with app.app_context():
        try:
            db.create_all()
            app.logger.info('数据库初始化完成')
        except Exception as e:
            app.logger.error(f'数据库初始化失败: {e}')
    
    # 用户加载器
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))
    
    # 模板上下文处理器
    @app.context_processor
    def inject_csrf_token():
        from flask_wtf.csrf import generate_csrf
        return dict(csrf_token=generate_csrf)

    # 添加权限检查函数到模板上下文（正确的权限控制）
    @app.context_processor
    def inject_permission_functions():
        from flask_login import current_user
        from app.utils.permission_manager import PermissionManager

        def has_menu_permission(menu_code):
            """检查菜单权限"""
            try:
                if not current_user.is_authenticated:
                    return False

                # 超级管理员拥有所有权限
                if current_user.is_super_admin():
                    return True

                # 使用权限管理器检查菜单权限
                return PermissionManager.has_menu_permission(current_user.id, menu_code)
            except Exception as e:
                app.logger.error(f"检查菜单权限失败: {e}")
                return False

        def has_page_permission(page_code):
            """检查页面权限"""
            try:
                if not current_user.is_authenticated:
                    return False

                # 超级管理员拥有所有权限
                if current_user.is_super_admin():
                    return True

                # 使用权限管理器检查页面权限
                return PermissionManager.has_page_permission(current_user.id, page_code)
            except Exception as e:
                app.logger.error(f"检查页面权限失败: {e}")
                return False

        def has_operation_permission(operation_code):
            """检查操作权限"""
            try:
                if not current_user.is_authenticated:
                    return False

                # 超级管理员拥有所有权限
                if current_user.is_super_admin():
                    return True

                # 使用权限管理器检查操作权限
                return PermissionManager.has_operation_permission(current_user.id, operation_code)
            except Exception as e:
                app.logger.error(f"检查操作权限失败: {e}")
                return False

        def has_warehouse_permission(warehouse_id, warehouse_permission_code):
            """检查仓库权限"""
            try:
                if not current_user.is_authenticated:
                    return False

                # 超级管理员拥有所有权限
                if current_user.is_super_admin():
                    return True

                # 使用权限管理器检查仓库权限
                return PermissionManager.has_warehouse_permission(current_user.id, warehouse_id, warehouse_permission_code)
            except Exception as e:
                app.logger.error(f"检查仓库权限失败: {e}")
                return False

        def moment():
            """简化的时间函数"""
            from datetime import datetime
            class SimpleMoment:
                def format(self, fmt):
                    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            return SimpleMoment()

        return dict(
            has_menu_permission=has_menu_permission,
            has_page_permission=has_page_permission,
            has_operation_permission=has_operation_permission,
            has_warehouse_permission=has_warehouse_permission,
            moment=moment
        )

    return app

from app import models
