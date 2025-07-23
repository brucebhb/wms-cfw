from app import create_app, db
from app.models import (InboundRecord, OutboundRecord, Inventory,
                       Warehouse, Role, Permission, User, UserRole,
                       RolePermission, UserLoginLog, AuditLog)
import click
import os

# 根据环境变量选择配置
env = os.environ.get('FLASK_ENV', 'production')
if env == 'production':
    from config_production import ProductionConfig
    app = create_app(ProductionConfig)
else:
    app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'InboundRecord': InboundRecord,
        'OutboundRecord': OutboundRecord,
        'Inventory': Inventory,
        'Warehouse': Warehouse,
        'Role': Role,
        'Permission': Permission,
        'User': User,
        'UserRole': UserRole,
        'RolePermission': RolePermission,
        'UserLoginLog': UserLoginLog,
        'AuditLog': AuditLog
    }

@app.cli.command()
def init_db():
    """初始化数据库"""
    db.create_all()
    click.echo('数据库表已创建。')

@app.cli.command()
def add_sample_data():
    """添加示例数据"""
    from datetime import datetime
    import random

    # 客户名称示例
    customers = ['上海物流有限公司', '广州贸易集团', '深圳进出口有限公司', 
                '北京国际货运代理', '天津港口物流公司']
    
    # 车牌示例
    plates = ['沪A12345', '粤B67890', '京C13579', '津D24680', '苏E98765']
    
    # 报关行示例
    brokers = ['中国外运', '华贸物流', '港中旅华贸', '海程邦达', '嘉里大通']
    
    # 出境模式
    modes = ['公路运输', '铁路运输', '海运', '空运', '多式联运']
    
    # 生成10条示例数据
    for i in range(10):
        record = InboundRecord(
            plate_number=random.choice(plates),
            customer_name=random.choice(customers),
            pallet_count=random.randint(5, 30),
            package_count=random.randint(50, 500),
            weight=round(random.uniform(100, 5000), 2),
            volume=round(random.uniform(5, 50), 2),
            export_mode=random.choice(modes),
            customs_broker=random.choice(brokers),
            identification_code=f"TEST{i+1:03d}",
            batch_no=f"BATCH{i+1:03d}",
            record_type='direct'
        )
        db.session.add(record)
    
    db.session.commit()
    click.echo('已添加10条示例数据。')

# 打印所有已注册路由
@app.cli.command('routes')
def routes():
    """显示所有已注册的路由"""
    rules = []
    for rule in app.url_map.iter_rules():
        methods = ','.join(sorted(rule.methods)) if rule.methods else 'N/A'
        rules.append((rule.endpoint, methods, str(rule)))

    sort_by_rule = False
    if sort_by_rule:
        rules.sort(key=lambda x: x[2])
    else:
        rules.sort(key=lambda x: x[0])

    for endpoint, methods, rule in rules:
        print(f"{endpoint} - {methods} - {rule}")

@app.cli.command('log-status')
def log_status():
    """显示日志文件状态"""
    from app.logging_config import get_log_file_sizes

    print("=== 日志文件状态 ===")
    log_info = get_log_file_sizes()

    total_size = 0
    for log_file, info in log_info.items():
        if 'error' in info:
            print(f"{log_file}: 错误 - {info['error']}")
        else:
            print(f"{log_file}: {info['size_mb']} MB (修改时间: {info['modified']})")
            total_size += info['size_mb']

    print(f"\n总日志大小: {total_size:.2f} MB")

@app.cli.command('log-cleanup')
@click.option('--days', default=30, help='删除多少天前的日志文件')
def log_cleanup(days):
    """清理旧的日志文件"""
    from app.logging_config import cleanup_old_logs

    print(f"开始清理 {days} 天前的日志文件...")
    cleanup_old_logs(days)
    print("日志清理完成")

@app.cli.command('log-rotate')
def log_rotate():
    """手动轮转日志文件"""
    from app.logging_config import rotate_logs_manually

    print("开始手动轮转日志文件...")
    rotate_logs_manually()
    print("日志轮转完成")

@app.cli.command('performance-optimize')
@click.option('--type', default='comprehensive', help='优化类型: quick/comprehensive')
def performance_optimize(type):
    """运行性能优化"""
    from app.integrated_performance_optimizer import integrated_optimizer

    print(f"🚀 开始执行{type}性能优化...")

    if type == 'quick':
        # 快速优化
        from app.cache_config import get_cache_manager
        cache_manager = get_cache_manager()
        cleared = cache_manager.delete_pattern('search_results*')
        print(f"✅ 快速优化完成，清理了 {cleared} 个缓存项")
    else:
        # 综合优化
        result = integrated_optimizer.run_comprehensive_optimization()

        print("📊 优化结果:")
        print(f"  数据库优化: {result.get('database_optimization', {}).get('status', 'unknown')}")
        print(f"  缓存优化: {result.get('cache_optimization', {}).get('status', 'unknown')}")
        print(f"  日志优化: {result.get('log_optimization', {}).get('status', 'unknown')}")
        print(f"  系统清理: {result.get('system_cleanup', {}).get('status', 'unknown')}")

        # 显示性能报告
        performance_report = result.get('performance_report', {})
        if performance_report.get('alerts'):
            print(f"⚠️  发现 {len(performance_report['alerts'])} 个性能告警")
            for alert in performance_report['alerts'][:3]:  # 只显示前3个
                print(f"   - {alert.get('message', 'N/A')}")

        if performance_report.get('recommendations'):
            print(f"💡 优化建议:")
            for rec in performance_report['recommendations'][:3]:  # 只显示前3个
                print(f"   - [{rec.get('priority', 'medium').upper()}] {rec.get('message', 'N/A')}")

    print("✨ 性能优化完成!")

@app.cli.command('performance-status')
def performance_status():
    """查看性能状态"""
    from app.integrated_performance_optimizer import integrated_optimizer

    print("📈 系统性能状态:")
    print("-" * 50)

    status = integrated_optimizer.get_quick_status()

    print(f"缓存命中率: {status.get('cache_hit_rate', 0)}%")
    print(f"平均查询时间: {status.get('avg_query_time', 0):.3f}秒")
    print(f"慢查询数量: {status.get('slow_queries_count', 0)}")
    print(f"Redis可用: {'✅ 是' if status.get('redis_available') else '❌ 否'}")
    print(f"内存使用率: {status.get('system_memory_percent', 0)}%")
    print(f"检查时间: {status.get('timestamp', 'N/A')}")

    # 性能建议
    suggestions = []
    cache_hit_rate = float(status.get('cache_hit_rate', 100))
    avg_query_time = float(status.get('avg_query_time', 0))
    memory_percent = float(status.get('system_memory_percent', 0))

    if cache_hit_rate < 70:
        suggestions.append("缓存命中率偏低，建议执行快速优化")
    if avg_query_time > 2:
        suggestions.append("查询速度偏慢，建议执行综合优化")
    if memory_percent > 85:
        suggestions.append("内存使用率过高，建议重启应用")

    if suggestions:
        print("\n💡 优化建议:")
        for suggestion in suggestions:
            print(f"   - {suggestion}")
    else:
        print("\n✅ 系统性能良好")

@app.cli.command('cache-status')
def cache_status():
    """查看双层缓存状态"""
    from app.cache.dual_cache_manager import DualCacheManager

    print("🚀 双层缓存系统状态:")
    print("-" * 50)

    try:
        cache_manager = DualCacheManager()
        status = cache_manager.get_cache_status()

        # L1 内存缓存状态
        l1_status = status.get('l1_cache', {})
        print(f"📦 L1内存缓存:")
        print(f"   状态: {'✅ 正常' if l1_status.get('available') else '❌ 异常'}")
        print(f"   命中率: {l1_status.get('hit_rate', 0):.1f}%")
        print(f"   键数量: {l1_status.get('key_count', 0)}")
        print(f"   内存使用: {l1_status.get('memory_usage', 0):.1f}MB")

        # L2 Redis缓存状态
        l2_status = status.get('l2_cache', {})
        print(f"\n🔴 L2Redis缓存:")
        print(f"   状态: {'✅ 正常' if l2_status.get('available') else '❌ 异常'}")
        print(f"   命中率: {l2_status.get('hit_rate', 0):.1f}%")
        print(f"   键数量: {l2_status.get('key_count', 0)}")
        print(f"   内存使用: {l2_status.get('memory_usage', 0):.1f}MB")
        print(f"   连接数: {l2_status.get('connections', 0)}")

        # 整体性能指标
        overall = status.get('overall', {})
        print(f"\n📊 整体性能:")
        print(f"   总命中率: {overall.get('hit_rate', 0):.1f}%")
        print(f"   平均响应时间: {overall.get('avg_response_time', 0):.2f}ms")
        print(f"   请求总数: {overall.get('total_requests', 0)}")
        print(f"   错误率: {overall.get('error_rate', 0):.2f}%")

    except Exception as e:
        print(f"❌ 获取缓存状态失败: {str(e)}")

@app.cli.command('cache-clear')
@click.option('--level', default='all', help='清理级别: l1/l2/all')
@click.option('--pattern', default='*', help='清理模式匹配')
def cache_clear(level, pattern):
    """清理缓存数据"""
    from app.cache.dual_cache_manager import DualCacheManager

    print(f"🧹 开始清理缓存 (级别: {level}, 模式: {pattern})")

    try:
        cache_manager = DualCacheManager()
        result = cache_manager.clear_cache(level=level, pattern=pattern)

        print(f"✅ 缓存清理完成:")
        if level in ['l1', 'all']:
            print(f"   L1内存缓存: 清理了 {result.get('l1_cleared', 0)} 个键")
        if level in ['l2', 'all']:
            print(f"   L2Redis缓存: 清理了 {result.get('l2_cleared', 0)} 个键")
        print(f"   总计清理: {result.get('total_cleared', 0)} 个键")

    except Exception as e:
        print(f"❌ 清理缓存失败: {str(e)}")

@app.cli.command('cache-warm')
@click.option('--type', default='dashboard', help='预热类型: dashboard/inventory/all/system')
@click.option('--priority', default='high', help='预热优先级: critical/high/medium/low')
def cache_warm(type, priority):
    """缓存预热"""
    from app.cache.cache_warmer import CacheWarmer
    from app.cache.system_cache_config import SystemCacheConfig

    print(f"🔥 开始缓存预热 (类型: {type}, 优先级: {priority})")

    try:
        warmer = CacheWarmer()

        if type == 'system':
            # 全系统预热
            preload_items = SystemCacheConfig.get_preload_items(priority)
            print(f"📋 系统预热项目: {len(preload_items)} 个")

            total_warmed = 0
            total_errors = []

            for cache_type in preload_items:
                try:
                    result = warmer.warm_cache(cache_type=cache_type)
                    total_warmed += result.get('warmed_items', 0)
                    total_errors.extend(result.get('errors', []))
                    print(f"   ✅ {cache_type}: {result.get('warmed_items', 0)} 项")
                except Exception as e:
                    total_errors.append(f"{cache_type}: {str(e)}")
                    print(f"   ❌ {cache_type}: {str(e)}")

            print(f"\n🎉 系统预热完成:")
            print(f"   总预热项目: {total_warmed}")
            print(f"   错误数量: {len(total_errors)}")

        else:
            # 单模块预热
            result = warmer.warm_cache(cache_type=type)

            print(f"✅ 缓存预热完成:")
            print(f"   预热数据项: {result.get('warmed_items', 0)}")
            print(f"   耗时: {result.get('duration', 0):.2f}秒")
            print(f"   成功率: {result.get('success_rate', 0):.1f}%")

            if result.get('errors'):
                print(f"⚠️  预热过程中的错误:")
                for error in result['errors'][:3]:  # 只显示前3个错误
                    print(f"   - {error}")

    except Exception as e:
        print(f"❌ 缓存预热失败: {str(e)}")

@app.cli.command('system-cache-status')
def system_cache_status():
    """查看全系统缓存状态"""
    from app.cache.dual_cache_manager import DualCacheManager
    from app.cache.system_cache_config import SystemCacheConfig

    print("🌐 全系统缓存状态:")
    print("=" * 60)

    try:
        cache_manager = DualCacheManager()
        status = cache_manager.get_cache_status()

        # 双层缓存状态
        print("📦 双层缓存系统:")
        l1_status = status.get('l1_cache', {})
        l2_status = status.get('l2_cache', {})

        print(f"   L1内存缓存: {'✅ 正常' if l1_status.get('available') else '❌ 异常'}")
        print(f"   - 命中率: {l1_status.get('hit_rate', 0):.1f}%")
        print(f"   - 键数量: {l1_status.get('key_count', 0)}")
        print(f"   - 内存使用: {l1_status.get('memory_usage', 0):.1f}MB")

        print(f"   L2Redis缓存: {'✅ 正常' if l2_status.get('available') else '❌ 异常'}")
        print(f"   - 命中率: {l2_status.get('hit_rate', 0):.1f}%")
        print(f"   - 键数量: {l2_status.get('key_count', 0)}")
        print(f"   - 内存使用: {l2_status.get('memory_usage', 0):.1f}MB")

        # 整体性能
        overall = status.get('overall', {})
        print(f"\n📊 整体性能:")
        print(f"   总命中率: {overall.get('hit_rate', 0):.1f}%")
        print(f"   总请求数: {overall.get('total_requests', 0)}")
        print(f"   错误率: {overall.get('error_rate', 0):.2f}%")

        # 系统配置概览
        print(f"\n⚙️  系统配置:")
        cache_types = list(SystemCacheConfig.CACHE_STRATEGIES.keys())
        print(f"   配置的缓存类型: {len(cache_types)} 个")

        # 按优先级分组
        priorities = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        for cache_type in cache_types:
            config = SystemCacheConfig.get_cache_config(cache_type)
            priority = config.get('priority', 'medium')
            priorities[priority] += 1

        for priority, count in priorities.items():
            if count > 0:
                print(f"   - {priority.capitalize()}: {count} 个")

        # 现有Redis状态
        try:
            from app.cache_config import get_cache_manager
            legacy_manager = get_cache_manager()
            legacy_stats = legacy_manager.get_cache_stats()

            print(f"\n🔄 现有Redis缓存:")
            print(f"   Redis版本: {legacy_stats.get('redis_version', 'N/A')}")
            print(f"   内存使用: {legacy_stats.get('used_memory', 'N/A')}")
            print(f"   连接客户端: {legacy_stats.get('connected_clients', 0)}")
            print(f"   现有缓存键: {legacy_stats.get('our_cache_keys', 0)}")
            print(f"   命中率: {legacy_stats.get('hit_rate', 0)}%")

        except Exception as e:
            print(f"\n⚠️  现有Redis缓存状态获取失败: {e}")

    except Exception as e:
        print(f"❌ 获取系统缓存状态失败: {str(e)}")

@app.cli.command('migrate-cache')
@click.option('--dry-run', is_flag=True, help='仅显示迁移计划，不执行实际迁移')
def migrate_cache(dry_run):
    """迁移现有缓存到新系统"""
    print("🔄 开始缓存系统迁移...")

    if dry_run:
        print("📋 迁移计划 (预览模式):")
        print("=" * 50)

        # 显示迁移计划
        migration_plan = [
            "1. 备份现有Redis缓存数据",
            "2. 初始化双层缓存系统",
            "3. 迁移库存相关缓存",
            "4. 迁移用户权限缓存",
            "5. 迁移统计数据缓存",
            "6. 验证迁移结果",
            "7. 清理旧缓存数据"
        ]

        for step in migration_plan:
            print(f"   {step}")

        print(f"\n💡 执行迁移请运行: flask migrate-cache")
        return

    try:
        # 实际迁移逻辑
        from app.cache.dual_cache_manager import get_dual_cache_manager
        from app.cache_config import get_cache_manager

        print("1️⃣ 初始化双层缓存系统...")
        dual_cache = get_dual_cache_manager()

        print("2️⃣ 检查现有缓存...")
        legacy_cache = get_cache_manager()
        legacy_stats = legacy_cache.get_cache_stats()

        print(f"   发现现有缓存键: {legacy_stats.get('our_cache_keys', 0)} 个")

        print("3️⃣ 预热新缓存系统...")
        from app.cache.cache_warmer import get_cache_warmer
        warmer = get_cache_warmer()
        result = warmer.warm_cache('all')

        print(f"   预热完成: {result.get('warmed_items', 0)} 项")

        print("✅ 缓存迁移完成!")
        print("💡 建议运行 'flask system-cache-status' 检查系统状态")

    except Exception as e:
        print(f"❌ 缓存迁移失败: {str(e)}")

# 健康检查端点（用于Docker健康检查）
@app.route('/health')
def health_check():
    """健康检查端点"""
    try:
        from datetime import datetime

        # 检查数据库连接
        from app import db
        with db.engine.connect() as conn:
            conn.execute(db.text('SELECT 1'))

        # 检查缓存连接
        try:
            from app.cache.dual_cache_manager import get_dual_cache_manager
            cache_manager = get_dual_cache_manager()
            cache_status = cache_manager.get_cache_status()
            cache_ok = cache_status.get('l1_cache', {}).get('available', False)
        except:
            cache_ok = False

        return {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'database': 'ok',
            'cache': 'ok' if cache_ok else 'degraded',
            'version': '2.0.0'
        }, 200

    except Exception as e:
        from datetime import datetime
        return {
            'status': 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'error': str(e),
            'version': '2.0.0'
        }, 503

if __name__ == '__main__':
    # 根据环境决定启动方式
    env = os.environ.get('FLASK_ENV', 'production')

    if env == 'production':
        print("🚀 启动仓储管理系统 (生产环境)...")
        print("⚠️  生产环境建议使用 Gunicorn 启动")
        print("📍 访问地址: http://0.0.0.0:5000")
        print("🔧 生产环境配置已加载")
        print("-" * 50)

        # 生产环境配置
        app.run(
            debug=False,
            host='0.0.0.0',
            port=5000,
            threaded=True,
            use_reloader=False,
            processes=1
        )
    else:
        print("🚀 启动仓储管理系统 (开发环境)...")
        print("📍 访问地址: http://127.0.0.1:5000")
        print("⏹️  按 Ctrl+C 停止服务器")
        print("🔧 启动优化: 异步初始化已启用")
        print("-" * 50)

        # 调试：打印admin API路由
        print("\n=== Admin API 路由 ===")
        for rule in app.url_map.iter_rules():
            if 'admin/api' in rule.rule:
                print(f"{rule.rule} -> {rule.endpoint}")
        print("=====================\n")

        # 开发环境配置
        # 可以通过环境变量控制是否使用多进程测试
        dev_processes = int(os.environ.get('DEV_PROCESSES', 1))

        if dev_processes > 1:
            print(f"🔄 开发环境多进程模式: {dev_processes} 个进程")
            print("⚠️  多进程模式下调试功能受限")

        app.run(
            debug=True,
            host='127.0.0.1',
            port=5000,
            threaded=True if dev_processes == 1 else False,  # 多进程时关闭多线程
            use_reloader=False,
            processes=dev_processes  # 支持通过环境变量控制
        )