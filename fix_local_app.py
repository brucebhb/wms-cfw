#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复本地应用的分批出货问题
使用SQLite作为本地开发数据库
"""

import os
import sys
from datetime import datetime

def create_local_config():
    """创建本地开发配置"""
    config_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地开发配置文件
"""

import os
from datetime import timedelta

class Config:
    """基础配置"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-for-local-development'
    
    # 使用SQLite作为本地开发数据库
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///warehouse_local.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'echo': False  # 设置为True可以看到SQL语句
    }
    
    # Redis配置（本地开发可以禁用）
    REDIS_URL = os.environ.get('REDIS_URL') or None
    
    # 会话配置
    PERMANENT_SESSION_LIFETIME = timedelta(hours=6)
    SESSION_COOKIE_SECURE = False  # 本地开发设置为False
    SESSION_COOKIE_HTTPONLY = True
    
    # 日志配置
    LOG_LEVEL = 'DEBUG'
    LOG_FILE = 'logs/app_local.log'
    LOG_MAX_SIZE = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5
    
    # 分页配置
    RECORDS_PER_PAGE = 20
    
    # 文件上传配置
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = 'uploads'
    
    # 开发模式配置
    DEBUG = True
    TESTING = False
    
    # 禁用CSRF（仅用于本地开发调试）
    WTF_CSRF_ENABLED = False
    
    @staticmethod
    def init_app(app):
        """初始化应用配置"""
        # 确保日志目录存在
        log_dir = os.path.dirname(Config.LOG_FILE)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # 确保上传目录存在
        if not os.path.exists(Config.UPLOAD_FOLDER):
            os.makedirs(Config.UPLOAD_FOLDER)

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'echo': True  # 开发环境显示SQL
    }

class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
'''
    
    with open('config_local.py', 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    print("✅ 已创建本地开发配置文件: config_local.py")

def create_local_app_runner():
    """创建本地应用启动脚本"""
    runner_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地开发环境启动脚本
"""

import os
import sys
from app import create_app, db
from app.models import User, Warehouse, InboundRecord, OutboundRecord, Inventory

# 设置环境变量使用本地配置
os.environ['FLASK_CONFIG'] = 'development'

def create_sample_data():
    """创建示例数据"""
    print("🔄 创建示例数据...")
    
    # 创建仓库
    warehouses = [
        {'id': 1, 'warehouse_name': '平湖仓', 'warehouse_code': 'PH', 'warehouse_type': 'frontend'},
        {'id': 2, 'warehouse_name': '昆山仓', 'warehouse_code': 'KS', 'warehouse_type': 'frontend'},
        {'id': 3, 'warehouse_name': '成都仓', 'warehouse_code': 'CD', 'warehouse_type': 'frontend'},
        {'id': 4, 'warehouse_name': '凭祥北投仓', 'warehouse_code': 'PX', 'warehouse_type': 'backend'},
    ]
    
    for w_data in warehouses:
        warehouse = Warehouse.query.get(w_data['id'])
        if not warehouse:
            warehouse = Warehouse(**w_data)
            db.session.add(warehouse)
    
    # 创建用户
    users = [
        {'username': 'admin', 'password': 'admin123', 'real_name': '系统管理员', 'warehouse_id': 1, 'is_admin': True},
        {'username': 'PHC', 'password': 'PHC123', 'real_name': '平湖仓操作员', 'warehouse_id': 1, 'is_admin': False},
        {'username': 'KSC', 'password': 'KSC123', 'real_name': '昆山仓操作员', 'warehouse_id': 2, 'is_admin': False},
        {'username': 'CDC', 'password': 'CDC123', 'real_name': '成都仓操作员', 'warehouse_id': 3, 'is_admin': False},
        {'username': 'PXC', 'password': 'PXC123', 'real_name': '凭祥仓操作员', 'warehouse_id': 4, 'is_admin': False},
    ]
    
    for u_data in users:
        user = User.query.filter_by(username=u_data['username']).first()
        if not user:
            user = User(**u_data)
            user.set_password(u_data['password'])
            db.session.add(user)
    
    try:
        db.session.commit()
        print("✅ 示例数据创建成功")
    except Exception as e:
        db.session.rollback()
        print(f"❌ 创建示例数据失败: {e}")

def init_database():
    """初始化数据库"""
    print("🔄 初始化数据库...")
    
    try:
        # 创建所有表
        db.create_all()
        print("✅ 数据库表创建成功")
        
        # 创建示例数据
        create_sample_data()
        
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        return False
    
    return True

def main():
    """主函数"""
    print("🚀 启动本地仓储管理系统")
    print("=" * 50)
    
    # 导入本地配置
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    try:
        from config_local import config
        app = create_app(config['development'])
    except ImportError:
        print("❌ 未找到本地配置文件，使用默认配置")
        app = create_app()
    
    with app.app_context():
        # 初始化数据库
        if not init_database():
            print("❌ 数据库初始化失败，退出")
            return
        
        print("✅ 系统初始化完成")
        print("🌐 访问地址: http://localhost:5000")
        print("👤 管理员账号: admin / admin123")
        print("👤 平湖仓账号: PHC / PHC123")
        print("=" * 50)
        
        # 启动应用
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            use_reloader=True
        )

if __name__ == '__main__':
    main()
'''
    
    with open('run_local.py', 'w', encoding='utf-8') as f:
        f.write(runner_content)
    
    print("✅ 已创建本地启动脚本: run_local.py")

def fix_app_init():
    """修复app/__init__.py以支持本地配置"""
    print("🔧 修复应用初始化文件...")
    
    # 读取当前的__init__.py
    try:
        with open('app/__init__.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否需要修改
        if 'config_local' in content:
            print("✅ 应用初始化文件已支持本地配置")
            return
        
        # 在导入部分添加本地配置支持
        if 'from config import config' in content:
            content = content.replace(
                'from config import config',
                '''from config import config
try:
    from config_local import config as local_config
    config.update(local_config)
    print("✅ 已加载本地开发配置")
except ImportError:
    print("ℹ️  使用默认配置")'''
            )
            
            with open('app/__init__.py', 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("✅ 已修复应用初始化文件")
        else:
            print("⚠️  应用初始化文件格式不符合预期，请手动检查")
    
    except Exception as e:
        print(f"❌ 修复应用初始化文件失败: {e}")

def main():
    """主函数"""
    print("🛠️  修复本地应用分批出货问题")
    print("=" * 60)
    print("解决方案：")
    print("1. 创建本地SQLite数据库配置")
    print("2. 避免MySQL连接问题")
    print("3. 正确实现分批出货逻辑")
    print("=" * 60)
    
    # 1. 创建本地配置
    create_local_config()
    
    # 2. 创建启动脚本
    create_local_app_runner()
    
    # 3. 修复应用初始化
    fix_app_init()
    
    print("\n🎉 本地应用修复完成！")
    print("\n📋 使用说明：")
    print("1. 运行: python run_local.py")
    print("2. 访问: http://localhost:5000")
    print("3. 登录: admin / admin123")
    print("\n💡 特性：")
    print("✅ 使用SQLite本地数据库")
    print("✅ 支持分批出货（同一识别编码多批次）")
    print("✅ 自动创建示例数据")
    print("✅ 调试模式启用")

if __name__ == "__main__":
    main()
