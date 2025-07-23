#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复分批出货的数据库约束问题
识别编码保持唯一不变，通过batch_sequence实现分批出货
"""

from app import create_app, db
from app.models import OutboundRecord
from sqlalchemy import text
from datetime import datetime
import sys

def check_current_constraints():
    """检查当前数据库约束"""
    print("🔍 检查当前数据库约束...")
    
    try:
        # 查看outbound_record表的索引和约束
        result = db.session.execute(text("""
            SHOW INDEX FROM outbound_record
        """))
        
        indexes = result.fetchall()
        print("📋 当前索引和约束:")
        
        unique_constraints = []
        for index in indexes:
            index_name = index[2]  # Key_name
            column_name = index[4]  # Column_name
            non_unique = index[1]   # Non_unique (0表示唯一)
            
            if non_unique == 0:  # 唯一约束
                unique_constraints.append((index_name, column_name))
                print(f"   🔑 唯一约束: {index_name} -> {column_name}")
            else:
                print(f"   📊 普通索引: {index_name} -> {column_name}")
        
        return unique_constraints
        
    except Exception as e:
        print(f"❌ 检查约束失败: {e}")
        return []

def check_duplicate_records():
    """检查重复记录情况"""
    print("\n🔍 检查重复记录情况...")
    
    # 检查identification_code重复（不考虑batch_sequence）
    result = db.session.execute(text("""
        SELECT identification_code, COUNT(*) as count
        FROM outbound_record 
        WHERE identification_code IS NOT NULL
        GROUP BY identification_code 
        HAVING COUNT(*) > 1
        ORDER BY count DESC
        LIMIT 10
    """))
    
    duplicates = result.fetchall()
    print(f"📊 重复的识别编码: {len(duplicates)} 个")
    
    for code, count in duplicates:
        print(f"   - {code}: {count} 条记录")
        
        # 查看这些记录的batch_sequence
        detail_result = db.session.execute(text("""
            SELECT id, batch_sequence, created_at, operated_by_user_id
            FROM outbound_record 
            WHERE identification_code = :code
            ORDER BY created_at
        """), {'code': code})
        
        details = detail_result.fetchall()
        print(f"     详细信息:")
        for detail in details:
            print(f"       ID:{detail[0]}, 批次:{detail[1]}, 时间:{detail[2]}, 用户:{detail[3]}")
    
    return duplicates

def fix_batch_sequences():
    """修复batch_sequence，确保同一识别编码的记录有正确的批次序号"""
    print("\n🔧 修复batch_sequence...")
    
    # 获取所有重复的识别编码
    result = db.session.execute(text("""
        SELECT identification_code, COUNT(*) as count
        FROM outbound_record 
        WHERE identification_code IS NOT NULL
        GROUP BY identification_code 
        HAVING COUNT(*) > 1
    """))
    
    duplicates = result.fetchall()
    fixed_count = 0
    
    for code, count in duplicates:
        print(f"🔄 处理识别编码: {code} ({count} 条记录)")
        
        # 获取该识别编码的所有记录，按创建时间排序
        records = OutboundRecord.query.filter_by(
            identification_code=code
        ).order_by(OutboundRecord.created_at).all()
        
        # 重新分配batch_sequence
        for i, record in enumerate(records, start=1):
            old_sequence = record.batch_sequence
            record.batch_sequence = i
            
            if old_sequence != i:
                print(f"   ✅ 记录ID {record.id}: batch_sequence {old_sequence} -> {i}")
                fixed_count += 1
    
    try:
        db.session.commit()
        print(f"✅ 成功修复 {fixed_count} 条记录的batch_sequence")
        return True
    except Exception as e:
        db.session.rollback()
        print(f"❌ 修复失败: {e}")
        return False

def drop_wrong_constraint():
    """删除错误的唯一约束"""
    print("\n🗑️ 删除错误的唯一约束...")
    
    try:
        # 检查是否存在identification_code的唯一约束
        result = db.session.execute(text("""
            SHOW INDEX FROM outbound_record 
            WHERE Key_name LIKE '%identification%' AND Non_unique = 0
        """))
        
        wrong_constraints = result.fetchall()
        
        for constraint in wrong_constraints:
            constraint_name = constraint[2]  # Key_name
            column_name = constraint[4]      # Column_name
            
            if column_name == 'identification_code':
                print(f"🗑️ 删除错误约束: {constraint_name}")
                
                db.session.execute(text(f"""
                    ALTER TABLE outbound_record DROP INDEX {constraint_name}
                """))
                
                print(f"✅ 已删除约束: {constraint_name}")
        
        db.session.commit()
        return True
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ 删除约束失败: {e}")
        return False

def create_correct_constraint():
    """创建正确的复合唯一约束"""
    print("\n🔧 创建正确的复合唯一约束...")
    
    try:
        # 创建 (identification_code, batch_sequence) 的复合唯一约束
        db.session.execute(text("""
            ALTER TABLE outbound_record 
            ADD CONSTRAINT uk_outbound_identification_batch 
            UNIQUE (identification_code, batch_sequence)
        """))
        
        db.session.commit()
        print("✅ 已创建复合唯一约束: uk_outbound_identification_batch")
        return True
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ 创建约束失败: {e}")
        
        # 如果失败，可能是因为还有重复数据
        print("💡 可能原因：仍有重复的 (identification_code, batch_sequence) 组合")
        
        # 检查重复的组合
        result = db.session.execute(text("""
            SELECT identification_code, batch_sequence, COUNT(*) as count
            FROM outbound_record 
            GROUP BY identification_code, batch_sequence
            HAVING COUNT(*) > 1
        """))
        
        combo_duplicates = result.fetchall()
        if combo_duplicates:
            print("🔍 发现重复的组合:")
            for code, sequence, count in combo_duplicates:
                print(f"   - {code}, 批次{sequence}: {count} 条记录")
        
        return False

def verify_fix():
    """验证修复结果"""
    print("\n✅ 验证修复结果...")
    
    # 1. 检查是否还有重复的identification_code（不考虑batch_sequence）
    result = db.session.execute(text("""
        SELECT identification_code, COUNT(*) as count
        FROM outbound_record 
        WHERE identification_code IS NOT NULL
        GROUP BY identification_code 
        HAVING COUNT(*) > 1
    """))
    
    duplicates = result.fetchall()
    print(f"📊 重复的识别编码: {len(duplicates)} 个（这是正常的，因为支持分批出货）")
    
    # 2. 检查是否有重复的 (identification_code, batch_sequence) 组合
    result = db.session.execute(text("""
        SELECT identification_code, batch_sequence, COUNT(*) as count
        FROM outbound_record 
        GROUP BY identification_code, batch_sequence
        HAVING COUNT(*) > 1
    """))
    
    combo_duplicates = result.fetchall()
    print(f"📊 重复的组合: {len(combo_duplicates)} 个（应该为0）")
    
    if combo_duplicates:
        print("❌ 仍有重复组合，需要进一步处理")
        for code, sequence, count in combo_duplicates:
            print(f"   - {code}, 批次{sequence}: {count} 条记录")
        return False
    
    # 3. 检查约束是否正确创建
    result = db.session.execute(text("""
        SHOW INDEX FROM outbound_record 
        WHERE Key_name = 'uk_outbound_identification_batch'
    """))
    
    constraint_exists = result.fetchall()
    if constraint_exists:
        print("✅ 复合唯一约束已正确创建")
        return True
    else:
        print("❌ 复合唯一约束未找到")
        return False

def main():
    """主函数"""
    print("🚀 修复分批出货的数据库约束")
    print("=" * 60)
    print("业务规则：")
    print("- 识别编码唯一且不可更改")
    print("- 同一识别编码可以分批出货")
    print("- 通过batch_sequence区分批次")
    print("- 约束：(identification_code, batch_sequence) 组合唯一")
    print("=" * 60)
    
    app = create_app()
    
    with app.app_context():
        # 1. 检查当前约束
        constraints = check_current_constraints()
        
        # 2. 检查重复记录
        duplicates = check_duplicate_records()
        
        # 3. 修复batch_sequence
        if duplicates:
            if not fix_batch_sequences():
                print("❌ 修复batch_sequence失败，停止操作")
                return
        
        # 4. 删除错误的唯一约束
        if not drop_wrong_constraint():
            print("❌ 删除错误约束失败，停止操作")
            return
        
        # 5. 创建正确的复合约束
        if not create_correct_constraint():
            print("❌ 创建正确约束失败")
            return
        
        # 6. 验证修复结果
        if verify_fix():
            print("🎉 分批出货约束修复完成！")
            print("\n📋 修复总结：")
            print("✅ 删除了错误的identification_code唯一约束")
            print("✅ 修复了batch_sequence序号")
            print("✅ 创建了正确的复合唯一约束")
            print("✅ 现在支持同一识别编码的分批出货")
        else:
            print("❌ 修复验证失败，请检查问题")

if __name__ == "__main__":
    main()
