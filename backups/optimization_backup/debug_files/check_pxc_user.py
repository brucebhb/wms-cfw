#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from app import create_app, db
from app.models import User
from werkzeug.security import check_password_hash

def check_pxc_user():
    """检查PXC用户信息"""
    app = create_app()
    with app.app_context():
        # 获取PXC用户
        pxc_user = User.query.filter_by(username='PXC').first()
        if not pxc_user:
            print("未找到PXC用户")
            return
        
        print(f'PXC用户信息:')
        print(f'  用户名: {pxc_user.username}')
        print(f'  真实姓名: {pxc_user.real_name}')
        print(f'  仓库ID: {pxc_user.warehouse_id}')
        print(f'  用户类型: {pxc_user.user_type}')
        print(f'  状态: {pxc_user.status}')
        print(f'  密码哈希: {pxc_user.password_hash[:50]}...')
        
        # 测试常见密码
        common_passwords = ['123', '123456', 'password', 'admin', 'PXC', 'pxc123', 'password123']
        
        print('\n测试常见密码:')
        for password in common_passwords:
            if check_password_hash(pxc_user.password_hash, password):
                print(f'  密码 "{password}" 匹配！')
                return password
            else:
                print(f'  密码 "{password}" 不匹配')
        
        print('\n没有找到匹配的密码')
        return None

if __name__ == '__main__':
    check_pxc_user()
