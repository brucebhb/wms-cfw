#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复PHC用户的货量报表仪表板访问权限
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User, UserPagePermission, OperationPermission
from datetime import datetime

def fix_dashboard_permissions():
    """修复PHC用户的仪表板权限"""
    app = create_app()
    
    with app.app_context():
        # 查找PHC用户
        phc_user = User.query.filter_by(username='PHC').first()
        if not phc_user:
            print("❌ 未找到PHC用户")
            return
        
        print(f"🔧 修复PHC用户 (ID: {phc_user.id}) 的货量报表仪表板权限")
        print()
        
        # 1. 只授予CARGO_VOLUME_DASHBOARD页面权限
        existing_page_perm = UserPagePermission.query.filter_by(
            user_id=phc_user.id,
            page_code='CARGO_VOLUME_DASHBOARD'
        ).first()
        
        if existing_page_perm:
            existing_page_perm.is_granted = True
            existing_page_perm.granted_at = datetime.now()
            print("✅ 更新CARGO_VOLUME_DASHBOARD页面权限")
        else:
            new_page_perm = UserPagePermission(
                user_id=phc_user.id,
                page_code='CARGO_VOLUME_DASHBOARD',
                is_granted=True,
                granted_by=1,  # admin用户ID
                granted_at=datetime.now()
            )
            db.session.add(new_page_perm)
            print("✅ 新增CARGO_VOLUME_DASHBOARD页面权限")
        
        # 2. 检查系统中存在的操作权限
        print("\n🔍 检查系统中存在的操作权限:")
        all_operations = OperationPermission.query.all()
        for op in all_operations:
            print(f"   - {op.operation_code}: {op.operation_name}")
        
        # 提交更改
        try:
            db.session.commit()
            print()
            print("🎉 页面权限授予成功！")
            print()
            print("📝 下一步操作：")
            print("   1. 重新登录PHC用户")
            print("   2. 访问 http://127.0.0.1:5000/reports/cargo_volume_dashboard")
            print("   3. 如果API调用失败，需要临时禁用API权限检查")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ 权限授予失败: {e}")

if __name__ == '__main__':
    fix_dashboard_permissions()
