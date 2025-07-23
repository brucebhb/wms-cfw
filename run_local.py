#!/usr/bin/env python3
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
            password = u_data.pop('password')  # 移除password参数
            user = User(**u_data)
            user.set_password(password)
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
