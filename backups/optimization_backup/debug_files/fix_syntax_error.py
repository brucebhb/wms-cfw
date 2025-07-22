#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复routes.py中的语法错误
"""

import sys
import os
import re

def fix_syntax_error():
    """修复routes.py中的语法错误"""
    
    # 文件路径
    file_path = os.path.join('app', 'main', 'routes.py')
    
    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找并修复语法错误
    pattern = r'document_count=item\.get\(\'document_count\'\),\s+#.*?\n\s+documents=item\.get\(\'documents\'\)\s+#.*?\n\s+service_staff'
    replacement = r'document_count=item.get(\'document_count\'),  # 只使用前端提供的单据份数，不设默认值\n                documents=item.get(\'documents\'),  # 只使用前端提供的单据信息，不设默认值\n                service_staff'
    
    # 使用正则表达式替换
    new_content = re.sub(pattern, replacement, content)
    
    # 如果内容没有变化，尝试更精确的替换
    if new_content == content:
        print("未找到匹配的模式，尝试更精确的替换...")
        
        # 直接替换有问题的行
        lines = content.split('\n')
        for i in range(len(lines)):
            if 'documents=item.get(\'documents\')' in lines[i] and 'service_staff' in lines[i+1]:
                lines[i] = lines[i].replace('documents=item.get(\'documents\')', 'documents=item.get(\'documents\'),')
                new_content = '\n'.join(lines)
                print(f"在第 {i+1} 行找到并修复了语法错误")
                break
    
    # 如果内容仍然没有变化，尝试手动定位并替换
    if new_content == content:
        print("尝试手动定位并替换...")
        
        # 查找特定行号附近的内容
        target_line_number = 3252
        start_line = max(0, target_line_number - 10)
        end_line = min(len(content.split('\n')), target_line_number + 10)
        
        lines = content.split('\n')
        for i in range(start_line, end_line):
            if i < len(lines):
                print(f"行 {i+1}: {lines[i]}")
                if 'documents=item.get(\'documents\')' in lines[i]:
                    lines[i] = lines[i].replace('documents=item.get(\'documents\')', 'documents=item.get(\'documents\'),')
                    new_content = '\n'.join(lines)
                    print(f"在第 {i+1} 行找到并修复了语法错误")
                    break
    
    # 如果内容发生了变化，写回文件
    if new_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"✅ 成功修复了 {file_path} 中的语法错误")
        return True
    else:
        print(f"❌ 未能修复 {file_path} 中的语法错误")
        return False

if __name__ == "__main__":
    try:
        success = fix_syntax_error()
        if success:
            print("\n🎉 语法错误已成功修复！")
            print("💡 提示：现在可以重新启动应用程序了。")
        else:
            print("\n❌ 修复过程中出现错误，请手动检查文件。")
    except Exception as e:
        print(f"\n❌ 脚本执行失败: {str(e)}")
        import traceback
        traceback.print_exc()
