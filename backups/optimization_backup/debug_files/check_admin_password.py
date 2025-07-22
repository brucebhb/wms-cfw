#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from app import create_app, db
from app.models import User
from werkzeug.security import check_password_hash

def check_admin_password():
    """检查admin用户密码"""
    app = create_app()
    with app.app_context():
        # 获取admin用户
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            print("未找到admin用户")
            return
        
        print(f'Admin用户信息:')
        print(f'  用户名: {admin_user.username}')
        print(f'  密码哈希: {admin_user.password_hash[:50]}...')
        
        # 测试常见密码
        common_passwords = ['admin123', 'admin', '123456', 'password', '123']
        
        print('\n测试常见密码:')
        for password in common_passwords:
            if check_password_hash(admin_user.password_hash, password):
                print(f'  密码 "{password}" 匹配！')
                return password
            else:
                print(f'  密码 "{password}" 不匹配')
        
        print('\n没有找到匹配的密码')
        return None

if __name__ == '__main__':
    check_admin_password()
