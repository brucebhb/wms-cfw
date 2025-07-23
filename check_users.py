#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
sys.path.append('/opt/warehouse')

from app import create_app, db
from app.models import User
from config_production import ProductionConfig
from werkzeug.security import check_password_hash, generate_password_hash

# 设置环境变量
os.environ['FLASK_ENV'] = 'production'

# 创建应用
app = create_app(ProductionConfig)

with app.app_context():
    try:
        print("🔍 检查用户数据...")
        
        # 检查所有用户
        users = User.query.all()
        print(f"用户总数: {len(users)}")
        
        for user in users:
            print(f"  - {user.username}: active={user.is_active}")
        
        # 检查admin用户
        admin = User.query.filter_by(username='admin').first()
        if admin:
            print(f"\n✅ 找到admin用户")
            print(f"   用户名: {admin.username}")
            print(f"   激活状态: {admin.is_active}")
            print(f"   密码哈希: {admin.password_hash[:50]}...")
            
            # 测试密码验证
            result = check_password_hash(admin.password_hash, 'admin123')
            print(f"   密码验证结果: {result}")
            
            if not result:
                print("❌ 密码验证失败，重新设置密码...")
                admin.password_hash = generate_password_hash('admin123')
                db.session.commit()
                print("✅ 密码重新设置完成")
                
                # 再次验证
                result = check_password_hash(admin.password_hash, 'admin123')
                print(f"   新密码验证结果: {result}")
        else:
            print("❌ 未找到admin用户，创建新用户...")
            admin = User(
                username='admin',
                password_hash=generate_password_hash('admin123'),
                is_active=True
            )
            db.session.add(admin)
            db.session.commit()
            print("✅ admin用户创建完成")
            
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()
