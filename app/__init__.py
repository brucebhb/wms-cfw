from flask import Flask, g, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager
import logging
from logging.handlers import RotatingFileHandler
import os
import time

# 根据环境变量选择配置
def get_config_class():
    """根据环境变量选择配置类"""
    env = os.environ.get('FLASK_ENV', 'production')
    if env == 'production':
        from config_production import ProductionConfig
        return ProductionConfig
    else:
        from config import Config
        return Config

# 创建数据库实例
db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()
login_manager = LoginManager()

def create_app(config_class=None):
    # 如果没有指定配置类，自动选择
    if config_class is None:
        config_class = get_config_class()

    app = Flask(__name__)
    app.config.from_object(config_class)

    # 记录当前使用的配置
    app.logger.info(f"使用配置类: {config_class.__name__}")
    app.logger.info(f"环境模式: {os.environ.get('FLASK_ENV', 'production')}")

    # MySQL专用配置和性能优化
    if 'mysql' in app.config['SQLALCHEMY_DATABASE_URI'].lower():
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_pre_ping': True,
            'pool_recycle': 300,
            'pool_timeout': 10,  # 减少连接超时时间
            'max_overflow': 5,   # 增加溢出连接数
            'pool_size': 15,     # 增加连接池大小
            'echo': False,       # 生产环境关闭SQL日志
            'connect_args': {
                'charset': 'utf8mb4',
                'autocommit': False,
                'connect_timeout': 30,  # 减少连接超时
                'read_timeout': 15,     # 减少读取超时
                'write_timeout': 15     # 减少写入超时
            }
        }
        app.logger.info("MySQL数据库配置已加载")
    else:
        # 如果不是MySQL，记录警告
        app.logger.warning("检测到非MySQL数据库配置，建议使用MySQL以获得最佳性能")
    
    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '请先登录以访问此页面。'
    
    # 初始化启动管理器
    from app.startup_manager import init_startup_manager
    startup_manager = init_startup_manager(app)

    # 注册蓝图
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.api.bp import bp as api_bp
    app.register_blueprint(api_bp)

    from app.api.optimization_routes import optimization_api
    app.register_blueprint(optimization_api, url_prefix='/api/optimization')

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')

    from app.admin.user_permission_routes import bp as user_permission_bp
    app.register_blueprint(user_permission_bp)

    from app.admin.permission_management_routes import permission_bp
    app.register_blueprint(permission_bp, url_prefix='/permission')

    from app.customer import bp as customer_bp
    app.register_blueprint(customer_bp, url_prefix='/customer')

    from app.reports import bp as reports_bp
    app.register_blueprint(reports_bp, url_prefix='/reports')

    # 注册维护管理蓝图（临时修复）
    from app.maintenance import maintenance_bp
    app.register_blueprint(maintenance_bp)

    # 启用自动缓存中间件 - 无需手动操作，自动应用到所有请求
    try:
        from app.cache.auto_cache_middleware import init_auto_cache_middleware
        init_auto_cache_middleware(app)
        app.logger.info("🔄 自动缓存中间件已启用 - 所有请求自动应用缓存优化")
    except Exception as e:
        app.logger.warning(f"自动缓存中间件启用失败: {e}")

    # 自动初始化全系统双层缓存
    def init_system_cache_auto():
        """自动初始化全系统缓存，无需手动操作"""
        import threading
        import time

        def background_init():
            # 减少等待时间，加快启动
            time.sleep(0.1)

            try:
                with app.app_context():
                    app.logger.info("🚀 开始自动初始化全系统缓存...")

                    # 1. 初始化双层缓存管理器
                    try:
                        from app.cache.dual_cache_manager import get_dual_cache_manager
                        cache_manager = get_dual_cache_manager()

                        # 检查缓存状态
                        status = cache_manager.get_cache_status()
                        l1_available = status.get('l1_cache', {}).get('available', False)
                        l2_available = status.get('l2_cache', {}).get('available', False)

                        app.logger.info(f"📦 L1内存缓存: {'✅ 已启用' if l1_available else '❌ 不可用'}")
                        app.logger.info(f"🔴 L2Redis缓存: {'✅ 已启用' if l2_available else '❌ 不可用'}")

                        # 设置全局缓存管理器
                        app.cache_manager = cache_manager

                    except Exception as e:
                        app.logger.warning(f"双层缓存初始化失败: {e}")

                    # 2. 自动启动缓存调度器
                    try:
                        from app.cache.cache_scheduler import get_cache_scheduler
                        scheduler = get_cache_scheduler()
                        scheduler.start()
                        app.logger.info("⏰ 缓存调度器已自动启动")

                        # 设置全局调度器
                        app.cache_scheduler = scheduler

                    except Exception as e:
                        app.logger.warning(f"缓存调度器启动失败: {e}")

                    # 3. 自动预热关键缓存
                    time.sleep(0.5)  # 减少等待时间
                    try:
                        from app.cache.cache_warmer import get_cache_warmer
                        from app.cache.system_cache_config import SystemCacheConfig

                        warmer = get_cache_warmer()

                        # 预热高优先级缓存（减少数量，提高启动速度）
                        high_priority_items = SystemCacheConfig.get_preload_items('high')
                        app.logger.info(f"🔥 开始自动预热 {len(high_priority_items)} 个高优先级缓存...")

                        total_warmed = 0
                        for cache_type in high_priority_items[:2]:  # 减少到前2个，加快启动
                            try:
                                result = warmer.warm_cache(cache_type=cache_type)
                                warmed_count = result.get('warmed_items', 0)
                                total_warmed += warmed_count
                                if warmed_count > 0:
                                    app.logger.info(f"   ✅ {cache_type}: {warmed_count} 项")
                            except Exception as e:
                                app.logger.warning(f"   ❌ {cache_type}: {str(e)}")

                        app.logger.info(f"🎉 缓存预热完成，共预热 {total_warmed} 项数据")

                    except Exception as e:
                        app.logger.warning(f"缓存预热失败: {e}")

                    # 4. 自动注册缓存事件监听器
                    try:
                        from app.cache_invalidation import register_cache_events
                        register_cache_events()
                        app.logger.info("📡 缓存事件监听器已自动注册")
                    except Exception as e:
                        app.logger.warning(f"缓存事件监听器注册失败: {e}")

                    # 5. 标记缓存系统就绪
                    try:
                        from app.startup_manager import mark_cache_ready
                        mark_cache_ready()
                        app.logger.info("✅ 全系统缓存已就绪，自动应用到所有模块")
                    except Exception as e:
                        app.logger.warning(f"标记缓存就绪失败: {e}")

                    # 6. 数据库优化（轻量级）
                    try:
                        from app.database_optimization import DatabaseOptimizer
                        DatabaseOptimizer.create_indexes()
                        app.logger.info("🗃️ 数据库索引优化完成")
                    except Exception as e:
                        app.logger.warning(f"数据库索引优化失败: {e}")

                    # 6.1 数据库查询优化
                    try:
                        from app.database_query_optimizer import init_db_optimization
                        init_db_optimization(app)
                        app.logger.info("⚡ 数据库查询优化完成")
                    except Exception as e:
                        app.logger.warning(f"数据库查询优化失败: {e}")

                    # 7. 权限自动同步
                    try:
                        from app.utils.permission_sync import auto_sync_permissions
                        success, message = auto_sync_permissions()
                        if success:
                            app.logger.info("🔐 权限系统自动同步完成")
                        else:
                            app.logger.warning(f"权限系统同步失败: {message}")
                    except Exception as e:
                        app.logger.warning(f"权限系统同步异常: {e}")

                    # 8. 标记优化系统就绪
                    try:
                        from app.startup_manager import mark_optimization_ready
                        mark_optimization_ready()
                        app.logger.info("🚀 系统性能优化已完成")
                    except Exception as e:
                        app.logger.warning(f"标记优化就绪失败: {e}")

            except Exception as e:
                app.logger.error(f"❌ 全系统缓存初始化失败: {str(e)}")

        # 在后台线程中执行初始化
        init_thread = threading.Thread(target=background_init, daemon=True)
        init_thread.start()
        app.logger.info("🌐 全系统缓存正在后台自动初始化...")

    # 立即启动自动初始化
    init_system_cache_auto()

    # 保留原有接口以兼容CLI命令
    app.cache_init_func = lambda: app.logger.info("缓存系统已在后台初始化")

    # 优化：异步初始化服务，避免阻塞启动
    def init_services_async():
        """异步初始化各种服务"""
        import threading
        import time

        def background_service_init():
            time.sleep(0.2)  # 减少等待时间，加快服务启动

            # 初始化调度器服务
            try:
                with app.app_context():
                    from app.services.scheduler_service import scheduler_service
                    scheduler_service.init_app(app)
                    app.logger.info('调度器服务已启动')
            except Exception as e:
                app.logger.error(f'调度器服务启动失败: {e}')

            # 延迟更少时间再初始化其他服务
            time.sleep(1)

            # 初始化启动检查器
            try:
                with app.app_context():
                    from app.services.startup_checker import startup_checker
                    startup_checker.init_app(app)
                    app.logger.info('启动检查器已初始化')
            except Exception as e:
                app.logger.error(f'启动检查器初始化失败: {str(e)}')

            # 初始化持续优化服务
            try:
                with app.app_context():
                    from app.services.continuous_optimization_service import continuous_optimization_service
                    continuous_optimization_service.init_app(app)
                    app.logger.info('持续优化服务已启动')
            except Exception as e:
                app.logger.error(f'持续优化服务启动失败: {str(e)}')

            # 标记服务系统就绪
            from app.startup_manager import mark_services_ready
            mark_services_ready()

        # 在后台线程中执行
        service_thread = threading.Thread(target=background_service_init, daemon=True)
        service_thread.start()
        app.logger.info('后台服务初始化已启动')

    # 启动异步服务初始化
    init_services_async()

    # 添加请求性能监控
    @app.before_request
    def before_request():
        g.start_time = time.time()

    @app.after_request
    def after_request(response):
        try:
            from app.performance_monitor import log_request_performance
            log_request_performance()
        except:
            pass
        return response

    # 设置日志配置
    from app.logging_config import LoggingConfig
    LoggingConfig.setup_logging(app)
    
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

    # 添加moment函数到模板上下文
    @app.context_processor
    def inject_moment():
        from datetime import datetime
        def moment():
            class MomentWrapper:
                def __init__(self):
                    self.dt = datetime.now()

                def format(self, format_str):
                    # 将moment.js格式转换为Python strftime格式
                    format_map = {
                        'YYYY-MM-DD HH:mm:ss': '%Y-%m-%d %H:%M:%S',
                        'YYYY-MM-DD': '%Y-%m-%d',
                        'HH:mm:ss': '%H:%M:%S',
                        'YYYY': '%Y',
                        'MM': '%m',
                        'DD': '%d',
                        'HH': '%H',
                        'mm': '%M',
                        'ss': '%S'
                    }
                    python_format = format_map.get(format_str, format_str)
                    return self.dt.strftime(python_format)

            return MomentWrapper()

        return dict(moment=moment)

    # 添加权限检查函数到模板上下文
    @app.context_processor
    def inject_permission_functions():
        from app.utils.permission_manager import PermissionManager
        from flask_login import current_user

        def has_menu_permission(menu_code):
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

        return dict(
            has_menu_permission=has_menu_permission,
            has_page_permission=has_page_permission,
            has_operation_permission=has_operation_permission,
            has_warehouse_permission=has_warehouse_permission
        )

    # 优化：快速数据库初始化，延迟复杂操作
    def quick_db_init():
        """快速数据库初始化，只做必要操作"""
        try:
            # 基础表创建
            db.create_all()
            app.logger.info('数据库基础表创建完成')

            # 快速检查收货人信息是否存在
            from app.models import Receiver
            if Receiver.query.count() == 0:
                receivers_data = [
                    {'warehouse_name': '平湖仓', 'address': '广东省深圳市平湖物流园区A区', 'contact': '张经理 13800138001'},
                    {'warehouse_name': '昆山仓', 'address': '江苏省苏州市昆山经济开发区B区', 'contact': '李经理 13800138002'},
                    {'warehouse_name': '成都仓', 'address': '四川省成都市双流区物流中心C区', 'contact': '王经理 13800138003'},
                    {'warehouse_name': '凭祥北投仓', 'address': '广西壮族自治区崇左市凭祥市北投物流园', 'contact': '赵经理 13800138004'}
                ]
                for data in receivers_data:
                    receiver = Receiver(**data)
                    db.session.add(receiver)
                db.session.commit()
                app.logger.info('收货人信息初始化完成')

        except Exception as e:
            app.logger.error(f'快速数据库初始化失败: {e}')

    def delayed_db_optimization():
        """延迟执行的数据库优化操作"""
        import threading
        import time

        def background_db_work():
            time.sleep(0.5)  # 减少等待时间，加快数据库优化

            try:
                with app.app_context():
                    # 检查并添加ReceiveRecord表的缺失字段
                    try:
                        from sqlalchemy import text
                        inspector = db.inspect(db.engine)
                        if 'receive_records' in inspector.get_table_names():
                            columns = [col['name'] for col in inspector.get_columns('receive_records')]

                            missing_fields = [
                                ('identification_code', 'VARCHAR(100)'),
                                ('delivery_plate_number', 'VARCHAR(20)'),
                                ('inbound_plate', 'VARCHAR(20)'),
                                ('storage_location', 'VARCHAR(50)'),
                                ('export_mode', 'VARCHAR(50)'),
                                ('order_type', 'VARCHAR(50)'),
                                ('customs_broker', 'VARCHAR(100)'),
                                ('batch_total', 'INTEGER'),
                                ('batch_sequence', 'VARCHAR(20)'),
                                ('remark1', 'TEXT'),
                                ('remark2', 'TEXT')
                            ]

                            for field_name, field_type in missing_fields:
                                if field_name not in columns:
                                    try:
                                        db.session.execute(text(f'ALTER TABLE receive_records ADD COLUMN {field_name} {field_type}'))
                                        db.session.commit()
                                        app.logger.info(f"已添加字段 {field_name} 到 receive_records 表")
                                    except Exception as e:
                                        if 'duplicate column name' not in str(e).lower():
                                            app.logger.warning(f"添加字段 {field_name} 失败: {str(e)}")
                    except Exception as e:
                        app.logger.warning(f"数据库字段检查失败: {str(e)}")

                    # 检查并添加TransitCargo表的缺失字段
                    try:
                        inspector = db.inspect(db.engine)
                        if 'transit_cargo' in inspector.get_table_names():
                            columns = [col['name'] for col in inspector.get_columns('transit_cargo')]
                            transit_missing_fields = [
                                ('delivery_plate_number', 'VARCHAR(20)'),
                                ('inbound_plate', 'VARCHAR(20)')
                            ]

                            for field_name, field_type in transit_missing_fields:
                                if field_name not in columns:
                                    try:
                                        db.session.execute(text(f'ALTER TABLE transit_cargo ADD COLUMN {field_name} {field_type}'))
                                        db.session.commit()
                                        app.logger.info(f"已添加字段 {field_name} 到 transit_cargo 表")
                                    except Exception as e:
                                        if 'duplicate column name' not in str(e).lower():
                                            app.logger.warning(f"添加字段 {field_name} 失败: {str(e)}")
                    except Exception as e:
                        app.logger.warning(f"TransitCargo表字段检查失败: {str(e)}")

                    app.logger.info('数据库优化操作完成')

            except Exception as e:
                app.logger.error(f'后台数据库优化失败: {e}')

        # 在后台线程中执行
        db_thread = threading.Thread(target=background_db_work, daemon=True)
        db_thread.start()

    # 执行快速初始化和延迟优化
    with app.app_context():
        quick_db_init()
        delayed_db_optimization()

    # 会话超时检查中间件
    @app.before_request
    def check_session_timeout():
        from flask import session, request, redirect, url_for, flash
        from flask_login import current_user, logout_user
        from datetime import datetime, timedelta

        # 跳过静态文件和认证相关页面
        if (request.endpoint and
            (request.endpoint.startswith('static') or
             request.endpoint == 'auth.login' or
             request.endpoint == 'auth.logout')):
            return

        # 如果用户已登录，检查会话是否过期
        if current_user.is_authenticated:
            if 'login_time' in session:
                try:
                    login_time = datetime.fromisoformat(session['login_time'])
                    current_time = datetime.now()
                    session_duration = current_time - login_time

                    # 如果超过6小时，强制登出
                    if session_duration > timedelta(hours=app.config['SESSION_TIMEOUT_HOURS']):
                        logout_user()
                        session.clear()
                        flash('您的会话已过期，请重新登录', 'warning')
                        return redirect(url_for('auth.login'))

                except (ValueError, KeyError):
                    # 如果登录时间格式错误，重新设置登录时间
                    session['login_time'] = datetime.now().isoformat()
            else:
                # 如果没有登录时间记录，设置当前时间
                session['login_time'] = datetime.now().isoformat()

    
    # 初始化运行时性能管理器
    try:
        from app.runtime_performance_manager import init_runtime_performance
        init_runtime_performance(app)
        app.logger.info('运行时性能管理器已初始化')
    except Exception as e:
        app.logger.error(f'运行时性能管理器初始化失败: {str(e)}')

    # 延迟初始化性能监控服务（启动后5秒）
    def delayed_performance_init():
        """延迟初始化性能相关服务"""
        import threading
        import time

        def init_performance_services():
            time.sleep(1)  # 减少等待时间，加快性能服务启动

            try:
                with app.app_context():
                    # 初始化启动检查器（非阻塞模式）
                    from app.services.startup_checker import startup_checker
                    startup_checker.init_app(app)
                    app.logger.info('延迟启动检查器已初始化')
            except Exception as e:
                app.logger.error(f'延迟启动检查器初始化失败: {e}')

            try:
                with app.app_context():
                    # 初始化持续优化服务（轻量模式）
                    from app.services.continuous_optimization_service import continuous_optimization_service
                    continuous_optimization_service.init_app(app)
                    app.logger.info('延迟持续优化服务已初始化')
            except Exception as e:
                app.logger.error(f'延迟持续优化服务初始化失败: {e}')

        # 在后台线程中运行
        thread = threading.Thread(target=init_performance_services, daemon=True)
        thread.start()

    # 注册延迟初始化
    delayed_performance_init()

    return app

from app import models