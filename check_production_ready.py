#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生产环境就绪检查脚本
检查系统是否准备好部署到生产环境
"""

import os
import sys
import subprocess
import importlib.util
from pathlib import Path

def check_file_exists(filepath, description):
    """检查文件是否存在"""
    if os.path.exists(filepath):
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description}: {filepath} (缺失)")
        return False

def check_directory_exists(dirpath, description):
    """检查目录是否存在"""
    if os.path.exists(dirpath) and os.path.isdir(dirpath):
        print(f"✅ {description}: {dirpath}")
        return True
    else:
        print(f"❌ {description}: {dirpath} (缺失)")
        return False

def check_python_module(module_name):
    """检查Python模块是否可导入"""
    try:
        importlib.import_module(module_name)
        print(f"✅ Python模块: {module_name}")
        return True
    except ImportError:
        print(f"❌ Python模块: {module_name} (缺失)")
        return False

def check_environment_variables():
    """检查环境变量配置"""
    print("\n🔍 检查环境变量配置...")
    
    # 检查.env.production文件
    env_file = '.env.production'
    if not os.path.exists(env_file):
        print(f"❌ 环境变量文件: {env_file} (缺失)")
        return False
    
    # 读取环境变量
    from dotenv import load_dotenv
    load_dotenv(env_file)
    
    required_vars = [
        'SECRET_KEY',
        'MYSQL_HOST',
        'MYSQL_USER',
        'MYSQL_PASSWORD', 
        'MYSQL_DATABASE',
        'REDIS_HOST',
        'REDIS_PORT'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.environ.get(var)
        if value:
            # 隐藏敏感信息
            if 'PASSWORD' in var or 'SECRET' in var:
                display_value = '*' * len(value)
            else:
                display_value = value
            print(f"✅ {var}: {display_value}")
        else:
            print(f"❌ {var}: (未设置)")
            missing_vars.append(var)
    
    return len(missing_vars) == 0

def check_database_connection():
    """检查数据库连接"""
    print("\n🗄️ 检查数据库连接...")
    
    try:
        from dotenv import load_dotenv
        load_dotenv('.env.production')
        
        from config_production import ProductionConfig
        from app import create_app, db
        
        app = create_app(ProductionConfig)
        with app.app_context():
            with db.engine.connect() as conn:
                result = conn.execute(db.text('SELECT VERSION()'))
                version = result.fetchone()[0]
                print(f"✅ MySQL连接成功: {version}")
                return True
                
    except Exception as e:
        print(f"❌ MySQL连接失败: {str(e)}")
        return False

def check_redis_connection():
    """检查Redis连接"""
    print("\n🔴 检查Redis连接...")
    
    try:
        import redis
        from dotenv import load_dotenv
        load_dotenv('.env.production')
        
        redis_host = os.environ.get('REDIS_HOST', 'localhost')
        redis_port = int(os.environ.get('REDIS_PORT', 6379))
        redis_db = int(os.environ.get('REDIS_DB', 0))
        
        r = redis.Redis(host=redis_host, port=redis_port, db=redis_db)
        info = r.info()
        print(f"✅ Redis连接成功: {info['redis_version']}")
        return True
        
    except Exception as e:
        print(f"⚠️ Redis连接失败: {str(e)}")
        print("💡 Redis不可用时系统将使用内存缓存")
        return False

def check_system_requirements():
    """检查系统要求"""
    print("\n💻 检查系统要求...")
    
    # 检查Python版本
    python_version = sys.version_info
    if python_version >= (3, 8):
        print(f"✅ Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    else:
        print(f"❌ Python版本过低: {python_version.major}.{python_version.minor}.{python_version.micro} (需要3.8+)")
        return False
    
    # 检查磁盘空间
    try:
        import shutil
        total, used, free = shutil.disk_usage('.')
        free_gb = free // (1024**3)
        if free_gb >= 5:
            print(f"✅ 磁盘空间: {free_gb}GB 可用")
        else:
            print(f"⚠️ 磁盘空间不足: {free_gb}GB 可用 (建议至少5GB)")
    except:
        print("⚠️ 无法检查磁盘空间")
    
    # 检查内存
    try:
        import psutil
        memory = psutil.virtual_memory()
        memory_gb = memory.total // (1024**3)
        if memory_gb >= 4:
            print(f"✅ 系统内存: {memory_gb}GB")
        else:
            print(f"⚠️ 内存可能不足: {memory_gb}GB (建议至少4GB)")
    except:
        print("⚠️ 无法检查系统内存")
    
    return True

def check_security_configuration():
    """检查安全配置"""
    print("\n🔒 检查安全配置...")
    
    # 检查SECRET_KEY
    from dotenv import load_dotenv
    load_dotenv('.env.production')
    
    secret_key = os.environ.get('SECRET_KEY')
    if secret_key and len(secret_key) >= 32:
        print("✅ SECRET_KEY: 长度足够")
    else:
        print("❌ SECRET_KEY: 长度不足或未设置 (建议至少32字符)")
        return False
    
    # 检查文件权限
    sensitive_files = ['.env.production']
    for file in sensitive_files:
        if os.path.exists(file):
            stat = os.stat(file)
            mode = oct(stat.st_mode)[-3:]
            if mode in ['600', '640']:
                print(f"✅ 文件权限: {file} ({mode})")
            else:
                print(f"⚠️ 文件权限: {file} ({mode}) - 建议设为600")
    
    return True

def main():
    """主检查函数"""
    print("🔍 仓储管理系统生产环境就绪检查")
    print("=" * 60)
    
    all_checks_passed = True
    
    # 1. 检查核心文件
    print("\n📁 检查核心文件...")
    core_files = [
        ('app.py', '应用入口文件'),
        ('config_production.py', '生产环境配置'),
        ('requirements.txt', 'Python依赖列表'),
        ('gunicorn_production.py', 'Gunicorn配置'),
        ('.env.example', '环境变量模板')
    ]
    
    for filepath, description in core_files:
        if not check_file_exists(filepath, description):
            all_checks_passed = False
    
    # 2. 检查目录结构
    print("\n📂 检查目录结构...")
    core_dirs = [
        ('app', '应用目录'),
        ('app/templates', '模板目录'),
        ('app/static', '静态文件目录')
    ]
    
    for dirpath, description in core_dirs:
        if not check_directory_exists(dirpath, description):
            all_checks_passed = False
    
    # 3. 检查Python依赖
    print("\n📚 检查Python依赖...")
    required_modules = [
        'flask', 'flask_sqlalchemy', 'flask_migrate',
        'flask_wtf', 'flask_login', 'pymysql', 'redis',
        'gunicorn', 'gevent', 'dotenv'
    ]
    
    for module in required_modules:
        if not check_python_module(module):
            all_checks_passed = False
    
    # 4. 检查环境变量
    if not check_environment_variables():
        all_checks_passed = False
    
    # 5. 检查数据库连接
    if not check_database_connection():
        all_checks_passed = False
    
    # 6. 检查Redis连接（可选）
    check_redis_connection()  # Redis失败不影响整体检查
    
    # 7. 检查系统要求
    if not check_system_requirements():
        all_checks_passed = False
    
    # 8. 检查安全配置
    if not check_security_configuration():
        all_checks_passed = False
    
    # 总结
    print("\n" + "=" * 60)
    if all_checks_passed:
        print("✅ 所有检查通过！系统已准备好部署到生产环境")
        print("\n🚀 建议的部署步骤:")
        print("1. 运行: chmod +x start_production.sh")
        print("2. 运行: ./start_production.sh")
        print("3. 或使用Gunicorn: gunicorn -c gunicorn_production.py app:app")
        return 0
    else:
        print("❌ 检查失败！请修复上述问题后重试")
        print("\n💡 常见解决方案:")
        print("1. 复制 .env.example 为 .env.production 并配置")
        print("2. 安装依赖: pip install -r requirements.txt")
        print("3. 检查MySQL和Redis服务是否运行")
        return 1

if __name__ == '__main__':
    sys.exit(main())
