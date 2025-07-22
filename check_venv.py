#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
虚拟环境检查脚本
"""

import sys
import os
import subprocess

def check_virtual_environment():
    """检查虚拟环境状态"""
    print("🔍 检查虚拟环境状态...")
    print("=" * 50)
    
    # 检查是否在虚拟环境中
    in_venv = hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )
    
    print(f"📍 Python路径: {sys.executable}")
    print(f"📍 Python版本: {sys.version}")
    print(f"📍 虚拟环境: {'✅ 是' if in_venv else '❌ 否'}")
    
    if in_venv:
        print(f"📍 虚拟环境路径: {sys.prefix}")
    
    # 检查pyvenv.cfg文件
    pyvenv_cfg = os.path.join(sys.prefix, 'pyvenv.cfg')
    if os.path.exists(pyvenv_cfg):
        print(f"✅ pyvenv.cfg: {pyvenv_cfg}")
        with open(pyvenv_cfg, 'r') as f:
            print("📄 配置内容:")
            for line in f:
                print(f"   {line.strip()}")
    else:
        print(f"❌ pyvenv.cfg: 文件不存在")
        
        # 尝试在当前目录查找
        local_pyvenv = 'pyvenv.cfg'
        if os.path.exists(local_pyvenv):
            print(f"✅ 找到本地 pyvenv.cfg: {local_pyvenv}")
    
    print("\n" + "=" * 50)
    
    # 检查已安装的包
    print("📦 检查关键依赖包...")
    required_packages = [
        'flask', 'flask_sqlalchemy', 'flask_migrate',
        'flask_wtf', 'flask_login', 'pymysql', 'redis'
    ]
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} (未安装)")
    
    print("\n" + "=" * 50)
    
    # 检查环境变量
    print("🌍 检查环境变量...")
    env_vars = ['FLASK_ENV', 'PYTHONPATH']
    for var in env_vars:
        value = os.environ.get(var)
        if value:
            print(f"✅ {var}: {value}")
        else:
            print(f"⚪ {var}: 未设置")

def fix_virtual_environment():
    """修复虚拟环境"""
    print("\n🔧 尝试修复虚拟环境...")
    
    # 检查是否需要创建pyvenv.cfg
    if not os.path.exists('pyvenv.cfg'):
        print("📝 创建 pyvenv.cfg 文件...")
        
        # 获取Python路径
        python_exe = sys.executable
        python_home = os.path.dirname(python_exe)
        
        # 创建配置文件
        config_content = f"""home = {python_home}
include-system-site-packages = false
version = {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}
executable = {python_exe}
command = {python_exe} -m venv {os.getcwd()}
"""
        
        with open('pyvenv.cfg', 'w') as f:
            f.write(config_content)
        
        print("✅ pyvenv.cfg 文件已创建")
    
    # 检查依赖安装
    print("📚 检查依赖安装...")
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', 'list'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ pip 工作正常")
            
            # 检查是否需要安装依赖
            if 'flask' not in result.stdout.lower():
                print("⚠️ 检测到缺少Flask，建议运行: pip install -r requirements.txt")
        else:
            print("❌ pip 检查失败")
    except Exception as e:
        print(f"❌ pip 检查出错: {e}")

def main():
    """主函数"""
    print("🔍 虚拟环境诊断工具")
    print("=" * 50)
    
    check_virtual_environment()
    fix_virtual_environment()
    
    print("\n💡 建议的解决步骤:")
    print("1. 如果不在虚拟环境中，请运行: .venv\\Scripts\\Activate.ps1")
    print("2. 如果缺少依赖，请运行: pip install -r requirements.txt")
    print("3. 如果问题持续，请重新创建虚拟环境")
    print("4. 启动应用: python app.py")

if __name__ == '__main__':
    main()
