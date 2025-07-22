#!/usr/bin/env python3
"""
权限清理脚本
用于清理重复的菜单权限和页面权限
"""

from app import create_app, db
from app.models import MenuPermission, PagePermission, UserMenuPermission, UserPagePermission

def clean_duplicate_permissions():
    """清理重复的权限"""
    app = create_app()
    with app.app_context():
        print("🧹 开始清理重复权限...")
        
        # 清理重复的菜单权限
        clean_duplicate_menu_permissions()
        
        # 清理重复的页面权限
        clean_duplicate_page_permissions()
        
        print("✅ 权限清理完成！")

def clean_duplicate_menu_permissions():
    """清理重复的菜单权限"""
    print("\n📁 检查菜单权限重复...")
    
    menus = MenuPermission.query.all()
    menu_codes = {}
    duplicates_to_delete = []
    
    for menu in menus:
        if menu.menu_code in menu_codes:
            # 发现重复，保留ID较小的（较早创建的）
            existing_menu = menu_codes[menu.menu_code]
            if menu.id < existing_menu.id:
                duplicates_to_delete.append(existing_menu)
                menu_codes[menu.menu_code] = menu
            else:
                duplicates_to_delete.append(menu)
        else:
            menu_codes[menu.menu_code] = menu
    
    if duplicates_to_delete:
        print(f"发现 {len(duplicates_to_delete)} 个重复菜单权限，正在删除...")
        for menu in duplicates_to_delete:
            # 删除用户菜单权限关联
            UserMenuPermission.query.filter_by(menu_code=menu.menu_code).delete()
            # 删除菜单权限
            db.session.delete(menu)
            print(f"  删除: {menu.menu_code} - {menu.menu_name}")
        
        db.session.commit()
        print(f"✅ 成功删除 {len(duplicates_to_delete)} 个重复菜单权限")
    else:
        print("✅ 没有发现重复的菜单权限")

def clean_duplicate_page_permissions():
    """清理重复的页面权限"""
    print("\n📄 检查页面权限重复...")
    
    pages = PagePermission.query.all()
    page_codes = {}
    duplicates_to_delete = []
    
    for page in pages:
        if page.page_code in page_codes:
            # 发现重复，保留ID较小的（较早创建的）
            existing_page = page_codes[page.page_code]
            if page.id < existing_page.id:
                duplicates_to_delete.append(existing_page)
                page_codes[page.page_code] = page
            else:
                duplicates_to_delete.append(page)
        else:
            page_codes[page.page_code] = page
    
    if duplicates_to_delete:
        print(f"发现 {len(duplicates_to_delete)} 个重复页面权限，正在删除...")
        for page in duplicates_to_delete:
            # 删除用户页面权限关联
            UserPagePermission.query.filter_by(page_code=page.page_code).delete()
            # 删除页面权限
            db.session.delete(page)
            print(f"  删除: {page.page_code} - {page.page_name}")
        
        db.session.commit()
        print(f"✅ 成功删除 {len(duplicates_to_delete)} 个重复页面权限")
    else:
        print("✅ 没有发现重复的页面权限")

def verify_permissions():
    """验证权限完整性"""
    app = create_app()
    with app.app_context():
        print("\n🔍 验证权限完整性...")
        
        menus = MenuPermission.query.all()
        pages = PagePermission.query.all()
        
        menu_codes = [m.menu_code for m in menus]
        page_codes = [p.page_code for p in pages]
        
        menu_duplicates = [code for code in set(menu_codes) if menu_codes.count(code) > 1]
        page_duplicates = [code for code in set(page_codes) if page_codes.count(code) > 1]
        
        print(f"📊 统计信息:")
        print(f"  菜单权限总数: {len(menus)}")
        print(f"  页面权限总数: {len(pages)}")
        
        if menu_duplicates:
            print(f"⚠️ 仍有重复菜单权限: {menu_duplicates}")
            return False
        else:
            print("✅ 菜单权限无重复")
            
        if page_duplicates:
            print(f"⚠️ 仍有重复页面权限: {page_duplicates}")
            return False
        else:
            print("✅ 页面权限无重复")
        
        return True

if __name__ == "__main__":
    clean_duplicate_permissions()
    verify_permissions()
