#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
仓储管理系统生产环境启动脚本
适用于腾讯云服务器部署
"""

import os
import sys
import logging
from datetime import datetime

def setup_production_environment():
    """设置生产环境变量"""
    # 设置环境变量
    os.environ['FLASK_ENV'] = 'production'
    os.environ['PYTHONPATH'] = os.path.dirname(os.path.abspath(__file__))
    
    # 确保日志目录存在
    log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 确保备份目录存在
    backup_dir = os.path.join(os.path.dirname(__file__), 'backups')
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

def check_environment():
    """检查生产环境配置"""
    print("🔍 检查生产环境配置...")
    
    # 检查必要的环境变量文件
    env_file = '.env.production'
    if not os.path.exists(env_file):
        print(f"❌ 缺少环境变量文件: {env_file}")
        print("💡 请复制 .env.example 为 .env.production 并配置正确的值")
        return False
    
    # 检查生产配置文件
    if not os.path.exists('config_production.py'):
        print("❌ 缺少生产环境配置文件: config_production.py")
        return False
    
    # 检查数据库配置
    from dotenv import load_dotenv
    load_dotenv(env_file)
    
    required_vars = [
        'SECRET_KEY',
        'MYSQL_HOST',
        'MYSQL_USER', 
        'MYSQL_PASSWORD',
        'MYSQL_DATABASE'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ 缺少必要的环境变量: {', '.join(missing_vars)}")
        return False
    
    print("✅ 环境配置检查通过")
    return True

def test_database_connection():
    """测试数据库连接"""
    print("🗄️ 测试数据库连接...")
    
    try:
        from config_production import ProductionConfig
        from app import create_app, db
        
        app = create_app(ProductionConfig)
        with app.app_context():
            # 测试数据库连接
            with db.engine.connect() as conn:
                result = conn.execute(db.text('SELECT 1'))
                result.fetchone()
            
        print("✅ 数据库连接正常")
        return True
        
    except Exception as e:
        print(f"❌ 数据库连接失败: {str(e)}")
        return False

def test_redis_connection():
    """测试Redis连接"""
    print("🔴 测试Redis连接...")
    
    try:
        import redis
        from dotenv import load_dotenv
        
        load_dotenv('.env.production')
        
        redis_host = os.environ.get('REDIS_HOST', 'localhost')
        redis_port = int(os.environ.get('REDIS_PORT', 6379))
        redis_db = int(os.environ.get('REDIS_DB', 0))
        
        r = redis.Redis(host=redis_host, port=redis_port, db=redis_db)
        r.ping()
        
        print("✅ Redis连接正常")
        return True
        
    except Exception as e:
        print(f"⚠️ Redis连接失败: {str(e)}")
        print("💡 Redis不可用时系统将使用内存缓存")
        return False

def initialize_database():
    """初始化数据库"""
    print("🔧 初始化数据库...")
    
    try:
        from config_production import ProductionConfig
        from app import create_app, db
        from app.models import User, Warehouse
        
        app = create_app(ProductionConfig)
        with app.app_context():
            # 创建所有表
            db.create_all()
            
            # 检查是否需要创建初始数据
            if Warehouse.query.count() == 0:
                print("📦 创建初始仓库数据...")
                warehouses = [
                    {'warehouse_code': 'PH', 'warehouse_name': '平湖仓', 'warehouse_type': 'frontend'},
                    {'warehouse_code': 'KS', 'warehouse_name': '昆山仓', 'warehouse_type': 'frontend'},
                    {'warehouse_code': 'CD', 'warehouse_name': '成都仓', 'warehouse_type': 'frontend'},
                    {'warehouse_code': 'PX', 'warehouse_name': '凭祥北投仓', 'warehouse_type': 'backend'}
                ]
                
                for wh_data in warehouses:
                    warehouse = Warehouse(**wh_data)
                    db.session.add(warehouse)
                
                db.session.commit()
                print("✅ 初始仓库数据创建完成")
            
            # 检查管理员用户
            if not User.query.filter_by(username='admin').first():
                print("👑 创建管理员用户...")
                admin = User(
                    username='admin',
                    real_name='系统管理员',
                    email='admin@warehouse.com',
                    user_type='admin',
                    is_admin=True,
                    status='active'
                )
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
                print("✅ 管理员用户创建完成 (admin/admin123)")
        
        print("✅ 数据库初始化完成")
        return True
        
    except Exception as e:
        print(f"❌ 数据库初始化失败: {str(e)}")
        return False

def start_application():
    """启动应用程序"""
    print("🚀 启动仓储管理系统...")
    print("=" * 60)
    print(f"🕐 启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🌐 环境模式: 生产环境")
    print("📍 访问地址: http://your_server_ip")
    print("👤 管理员账号: admin / admin123")
    print("=" * 60)
    
    try:
        from config_production import ProductionConfig
        from app import create_app
        
        app = create_app(ProductionConfig)
        
        # 生产环境启动配置
        app.run(
            debug=False,
            host='0.0.0.0',
            port=5000,
            threaded=True,
            use_reloader=False
        )
        
    except KeyboardInterrupt:
        print("\n⏹️ 服务器已停止")
    except Exception as e:
        print(f"❌ 启动失败: {str(e)}")
        sys.exit(1)

def main():
    """主函数"""
    print("🏭 仓储管理系统生产环境启动器")
    print("=" * 60)
    
    # 设置生产环境
    setup_production_environment()
    
    # 检查环境配置
    if not check_environment():
        print("\n❌ 环境检查失败，请修复配置后重试")
        sys.exit(1)
    
    # 测试数据库连接
    if not test_database_connection():
        print("\n❌ 数据库连接失败，请检查配置")
        sys.exit(1)
    
    # 测试Redis连接（可选）
    test_redis_connection()
    
    # 初始化数据库
    if not initialize_database():
        print("\n❌ 数据库初始化失败")
        sys.exit(1)
    
    print("\n✅ 所有检查通过，准备启动应用...")
    print("💡 生产环境建议使用 Gunicorn 或 uWSGI 启动")
    print("💡 当前使用 Flask 内置服务器（仅用于测试）")
    
    # 询问是否继续
    try:
        response = input("\n是否继续启动？(y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            print("⏹️ 启动已取消")
            sys.exit(0)
    except KeyboardInterrupt:
        print("\n⏹️ 启动已取消")
        sys.exit(0)
    
    # 启动应用
    start_application()

if __name__ == '__main__':
    main()
