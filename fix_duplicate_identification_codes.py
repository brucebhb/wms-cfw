#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复识别编码重复问题
"""

from app import create_app, db
from app.models import InboundRecord, OutboundRecord, Inventory
from sqlalchemy import func, text
from datetime import datetime
import sys

def check_duplicate_identification_codes():
    """检查重复的识别编码"""
    print("🔍 检查重复的识别编码...")
    
    # 检查入库记录重复
    inbound_duplicates = db.session.query(
        InboundRecord.identification_code,
        func.count(InboundRecord.id).label('count')
    ).group_by(InboundRecord.identification_code).having(
        func.count(InboundRecord.id) > 1
    ).all()
    
    print(f"📊 入库记录重复识别编码: {len(inbound_duplicates)} 个")
    for code, count in inbound_duplicates[:5]:  # 只显示前5个
        print(f"   - {code}: {count} 条记录")
    
    # 检查出库记录重复
    outbound_duplicates = db.session.query(
        OutboundRecord.identification_code,
        func.count(OutboundRecord.id).label('count')
    ).group_by(OutboundRecord.identification_code).having(
        func.count(OutboundRecord.id) > 1
    ).all()
    
    print(f"📊 出库记录重复识别编码: {len(outbound_duplicates)} 个")
    for code, count in outbound_duplicates[:5]:  # 只显示前5个
        print(f"   - {code}: {count} 条记录")
    
    # 检查库存记录重复
    inventory_duplicates = db.session.query(
        Inventory.identification_code,
        func.count(Inventory.id).label('count')
    ).group_by(Inventory.identification_code).having(
        func.count(Inventory.id) > 1
    ).all()
    
    print(f"📊 库存记录重复识别编码: {len(inventory_duplicates)} 个")
    for code, count in inventory_duplicates[:5]:  # 只显示前5个
        print(f"   - {code}: {count} 条记录")
    
    return {
        'inbound': inbound_duplicates,
        'outbound': outbound_duplicates,
        'inventory': inventory_duplicates
    }

def fix_outbound_duplicates():
    """修复出库记录重复问题"""
    print("\n🔧 修复出库记录重复问题...")
    
    # 查找重复的出库记录
    duplicates = db.session.query(
        OutboundRecord.identification_code,
        func.count(OutboundRecord.id).label('count')
    ).group_by(OutboundRecord.identification_code).having(
        func.count(OutboundRecord.id) > 1
    ).all()
    
    fixed_count = 0
    
    for code, count in duplicates:
        print(f"🔄 处理重复识别编码: {code} ({count} 条记录)")
        
        # 获取所有重复记录，按创建时间排序
        records = OutboundRecord.query.filter_by(
            identification_code=code
        ).order_by(OutboundRecord.created_at).all()
        
        # 保留第一条记录，修改其他记录的识别编码
        for i, record in enumerate(records[1:], start=2):
            # 生成新的识别编码，添加批次后缀
            new_code = f"{code}-{i}"
            
            # 检查新编码是否已存在
            existing = OutboundRecord.query.filter_by(
                identification_code=new_code
            ).first()
            
            if not existing:
                old_code = record.identification_code
                record.identification_code = new_code
                record.batch_sequence = i
                print(f"   ✅ 更新: {old_code} -> {new_code}")
                fixed_count += 1
            else:
                # 如果新编码也存在，使用时间戳
                timestamp = record.created_at.strftime("%H%M%S")
                new_code = f"{code}-{timestamp}"
                record.identification_code = new_code
                print(f"   ✅ 更新: {old_code} -> {new_code}")
                fixed_count += 1
    
    try:
        db.session.commit()
        print(f"✅ 成功修复 {fixed_count} 条出库记录")
    except Exception as e:
        db.session.rollback()
        print(f"❌ 修复失败: {e}")
        return False
    
    return True

def fix_inventory_duplicates():
    """修复库存记录重复问题"""
    print("\n🔧 修复库存记录重复问题...")
    
    # 查找重复的库存记录
    duplicates = db.session.query(
        Inventory.identification_code,
        func.count(Inventory.id).label('count')
    ).group_by(Inventory.identification_code).having(
        func.count(Inventory.id) > 1
    ).all()
    
    fixed_count = 0
    
    for code, count in duplicates:
        print(f"🔄 处理重复库存识别编码: {code} ({count} 条记录)")
        
        # 获取所有重复记录
        records = Inventory.query.filter_by(
            identification_code=code
        ).order_by(Inventory.last_updated.desc()).all()
        
        # 合并库存数量到最新记录
        latest_record = records[0]
        total_pallet = 0
        total_package = 0
        total_weight = 0
        total_volume = 0
        
        for record in records:
            total_pallet += record.pallet_count or 0
            total_package += record.package_count or 0
            total_weight += record.weight or 0
            total_volume += record.volume or 0
        
        # 更新最新记录
        latest_record.pallet_count = total_pallet
        latest_record.package_count = total_package
        latest_record.weight = total_weight
        latest_record.volume = total_volume
        latest_record.last_updated = datetime.now()
        
        # 删除其他重复记录
        for record in records[1:]:
            db.session.delete(record)
            fixed_count += 1
        
        print(f"   ✅ 合并库存: 板数={total_pallet}, 件数={total_package}")
    
    try:
        db.session.commit()
        print(f"✅ 成功合并 {fixed_count} 条重复库存记录")
    except Exception as e:
        db.session.rollback()
        print(f"❌ 修复失败: {e}")
        return False
    
    return True

def check_database_constraints():
    """检查数据库约束"""
    print("\n🔍 检查数据库约束...")
    
    try:
        # 检查出库记录表的唯一约束
        result = db.session.execute(text("""
            SHOW INDEX FROM outbound_record WHERE Key_name LIKE '%identification%'
        """))
        
        constraints = result.fetchall()
        print("📋 出库记录表约束:")
        for constraint in constraints:
            print(f"   - {constraint}")
            
    except Exception as e:
        print(f"❌ 检查约束失败: {e}")

def backup_before_fix():
    """修复前备份数据"""
    print("💾 创建修复前备份...")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    try:
        # 备份重复的出库记录
        duplicates = db.session.execute(text("""
            SELECT identification_code, COUNT(*) as count 
            FROM outbound_record 
            GROUP BY identification_code 
            HAVING COUNT(*) > 1
        """)).fetchall()
        
        with open(f'duplicate_outbound_backup_{timestamp}.txt', 'w', encoding='utf-8') as f:
            f.write("重复出库记录备份\n")
            f.write(f"备份时间: {datetime.now()}\n")
            f.write("=" * 50 + "\n")
            
            for code, count in duplicates:
                f.write(f"{code}: {count} 条记录\n")
        
        print(f"✅ 备份完成: duplicate_outbound_backup_{timestamp}.txt")
        return True
        
    except Exception as e:
        print(f"❌ 备份失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 开始修复识别编码重复问题")
    print("=" * 60)
    
    app = create_app()
    
    with app.app_context():
        # 1. 检查重复情况
        duplicates = check_duplicate_identification_codes()
        
        # 2. 如果有重复，询问是否修复
        total_duplicates = (len(duplicates['inbound']) + 
                          len(duplicates['outbound']) + 
                          len(duplicates['inventory']))
        
        if total_duplicates == 0:
            print("✅ 没有发现重复的识别编码")
            return
        
        print(f"\n⚠️  发现 {total_duplicates} 个重复问题")
        
        # 3. 创建备份
        if not backup_before_fix():
            print("❌ 备份失败，停止修复")
            return
        
        # 4. 修复出库记录重复
        if duplicates['outbound']:
            if fix_outbound_duplicates():
                print("✅ 出库记录重复问题已修复")
            else:
                print("❌ 出库记录修复失败")
                return
        
        # 5. 修复库存记录重复
        if duplicates['inventory']:
            if fix_inventory_duplicates():
                print("✅ 库存记录重复问题已修复")
            else:
                print("❌ 库存记录修复失败")
                return
        
        # 6. 再次检查
        print("\n🔍 修复后检查...")
        final_check = check_duplicate_identification_codes()
        
        final_total = (len(final_check['inbound']) + 
                      len(final_check['outbound']) + 
                      len(final_check['inventory']))
        
        if final_total == 0:
            print("🎉 所有重复问题已解决！")
        else:
            print(f"⚠️  仍有 {final_total} 个重复问题需要手动处理")

if __name__ == "__main__":
    main()
