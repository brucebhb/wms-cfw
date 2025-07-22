#!/usr/bin/env python3
"""
维护服务模块
集成到Flask应用中的自动维护功能
"""
import os
import glob
import logging
from datetime import datetime, timedelta
from flask import current_app
from app import db
from app.models import InboundRecord, OutboundRecord, ReceiveRecord, Inventory
from sqlalchemy import text

class MaintenanceService:
    """维护服务类"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def clean_logs(self, max_size_mb=50, keep_days=7):
        """清理日志文件"""
        try:
            log_dir = os.path.join(current_app.root_path, '..', 'logs')
            if not os.path.exists(log_dir):
                return {'success': True, 'message': '日志目录不存在', 'cleaned_count': 0}
            
            max_size_bytes = max_size_mb * 1024 * 1024
            cutoff_time = datetime.now() - timedelta(days=keep_days)
            cleaned_count = 0
            
            for log_file in glob.glob(os.path.join(log_dir, "*.log*")):
                try:
                    file_size = os.path.getsize(log_file)
                    file_time = datetime.fromtimestamp(os.path.getmtime(log_file))
                    
                    # 删除过大或过期的文件
                    if file_size > max_size_bytes or file_time < cutoff_time:
                        # 备份重要日志
                        if 'error' in log_file.lower():
                            backup_name = f"{log_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                            os.rename(log_file, backup_name)
                            self.logger.info(f"重要日志已备份: {backup_name}")
                        else:
                            os.remove(log_file)
                            self.logger.info(f"删除日志文件: {os.path.basename(log_file)} ({file_size/1024/1024:.1f}MB)")
                        cleaned_count += 1
                except Exception as e:
                    self.logger.error(f"处理日志文件失败 {log_file}: {e}")
            
            return {
                'success': True,
                'message': f'日志清理完成，清理了 {cleaned_count} 个文件',
                'cleaned_count': cleaned_count
            }
            
        except Exception as e:
            self.logger.error(f"日志清理失败: {e}")
            return {'success': False, 'message': f'日志清理失败: {e}', 'cleaned_count': 0}
    
    def optimize_database(self):
        """优化数据库"""
        try:
            # 获取表统计信息
            stats = self._get_table_stats()

            # 清理测试数据
            cleaned_records = self._cleanup_test_data()

            # 执行数据库优化 - 兼容MySQL和SQLite
            try:
                # 检测数据库类型
                db_url = str(db.engine.url)

                if 'mysql' in db_url.lower():
                    # MySQL优化命令
                    self.logger.info("执行MySQL数据库优化")

                    # 获取所有表名
                    tables_result = db.session.execute(text("SHOW TABLES"))
                    tables = [row[0] for row in tables_result]

                    # 优化每个表
                    for table in tables:
                        try:
                            db.session.execute(text(f"OPTIMIZE TABLE `{table}`"))
                            self.logger.info(f"优化表: {table}")
                        except Exception as e:
                            self.logger.warning(f"优化表 {table} 失败: {e}")

                    # 分析表统计信息
                    for table in tables:
                        try:
                            db.session.execute(text(f"ANALYZE TABLE `{table}`"))
                        except Exception as e:
                            self.logger.warning(f"分析表 {table} 失败: {e}")

                elif 'sqlite' in db_url.lower():
                    # SQLite优化命令
                    self.logger.info("执行SQLite数据库优化")
                    db.session.execute(text('VACUUM;'))
                    db.session.execute(text('ANALYZE;'))
                else:
                    # PostgreSQL或其他数据库
                    self.logger.info("执行通用数据库优化")
                    db.session.execute(text('ANALYZE;'))

                db.session.commit()

            except Exception as e:
                self.logger.warning(f"数据库优化命令执行失败: {e}")

            self.logger.info("数据库优化完成")

            return {
                'success': True,
                'message': f'数据库优化完成，清理了 {cleaned_records} 条测试记录',
                'stats': stats,
                'cleaned_records': cleaned_records
            }

        except Exception as e:
            db.session.rollback()
            self.logger.error(f"数据库优化失败: {e}")
            return {'success': False, 'message': f'数据库优化失败: {e}'}
    
    def _get_table_stats(self):
        """获取表统计信息"""
        try:
            stats = {}
            tables = {
                'InboundRecord': InboundRecord,
                'OutboundRecord': OutboundRecord,
                'ReceiveRecord': ReceiveRecord,
                'Inventory': Inventory
            }
            
            for table_name, model in tables.items():
                count = model.query.count()
                stats[table_name] = count
                
            return stats
        except Exception as e:
            self.logger.error(f"获取表统计失败: {e}")
            return {}
    
    def _cleanup_test_data(self, days_to_keep=90):
        """清理测试数据"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            cleaned_count = 0
            
            # 清理旧的测试入库记录
            test_records = InboundRecord.query.filter(
                InboundRecord.created_at < cutoff_date
            ).filter(
                InboundRecord.customer_name.like('%测试%') |
                InboundRecord.customer_name.like('%test%') |
                InboundRecord.customer_name.like('%temp%')
            ).all()
            
            for record in test_records:
                db.session.delete(record)
                cleaned_count += 1
            
            # 清理旧的测试接收记录
            test_receive_records = ReceiveRecord.query.filter(
                ReceiveRecord.receive_time < cutoff_date
            ).filter(
                ReceiveRecord.customer_name.like('%测试%') |
                ReceiveRecord.customer_name.like('%test%') |
                ReceiveRecord.customer_name.like('%temp%')
            ).all()
            
            for record in test_receive_records:
                db.session.delete(record)
                cleaned_count += 1
            
            db.session.commit()
            return cleaned_count
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"清理测试数据失败: {e}")
            return 0
    
    def check_system_health(self):
        """检查系统健康状态"""
        try:
            health_info = {
                'database_size': self._get_database_size(),
                'log_files_count': self._count_log_files(),
                'large_log_files': self._get_large_log_files(),
                'table_stats': self._get_table_stats(),
                'timestamp': datetime.now().isoformat()
            }
            
            # 生成健康建议
            recommendations = self._generate_health_recommendations(health_info)
            health_info['recommendations'] = recommendations
            
            return {
                'success': True,
                'health_info': health_info
            }
            
        except Exception as e:
            self.logger.error(f"系统健康检查失败: {e}")
            return {'success': False, 'message': f'系统健康检查失败: {e}'}
    
    def _get_database_size(self):
        """获取数据库大小"""
        try:
            db_url = str(db.engine.url)

            if 'mysql' in db_url.lower():
                # MySQL数据库大小查询
                try:
                    # 获取数据库名
                    db_name = db.engine.url.database

                    # 查询数据库大小
                    result = db.session.execute(text("""
                        SELECT ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) as size_mb
                        FROM information_schema.tables
                        WHERE table_schema = :db_name
                    """), {'db_name': db_name})

                    size = result.scalar()
                    return float(size) if size else 0

                except Exception as e:
                    self.logger.warning(f"获取MySQL数据库大小失败: {e}")
                    return 0

            elif 'sqlite' in db_url.lower():
                # SQLite数据库大小
                db_path = os.path.join(current_app.instance_path, 'warehouse.db')
                if os.path.exists(db_path):
                    return os.path.getsize(db_path) / 1024 / 1024  # MB
                return 0

            else:
                # PostgreSQL或其他数据库
                try:
                    result = db.session.execute(text("""
                        SELECT pg_size_pretty(pg_database_size(current_database()))
                    """))
                    size_str = result.scalar()
                    # 简单解析，返回估算值
                    return 50.0  # 默认估算值
                except Exception:
                    return 0

        except Exception as e:
            self.logger.warning(f"获取数据库大小失败: {e}")
            return 0
    
    def _count_log_files(self):
        """统计日志文件数量"""
        try:
            log_dir = os.path.join(current_app.root_path, '..', 'logs')
            if os.path.exists(log_dir):
                return len([f for f in os.listdir(log_dir) if f.endswith('.log') or '.log.' in f])
            return 0
        except Exception:
            return 0
    
    def _get_large_log_files(self, size_threshold_mb=10):
        """获取大日志文件列表"""
        try:
            log_dir = os.path.join(current_app.root_path, '..', 'logs')
            large_files = []
            
            if os.path.exists(log_dir):
                for filename in os.listdir(log_dir):
                    if filename.endswith('.log') or '.log.' in filename:
                        filepath = os.path.join(log_dir, filename)
                        size_mb = os.path.getsize(filepath) / 1024 / 1024
                        if size_mb > size_threshold_mb:
                            large_files.append({
                                'filename': filename,
                                'size_mb': round(size_mb, 2)
                            })
            
            return large_files
        except Exception:
            return []
    
    def _generate_health_recommendations(self, health_info):
        """生成健康建议"""
        recommendations = []
        
        # 数据库大小检查
        if health_info['database_size'] > 500:  # 500MB
            recommendations.append("数据库文件较大，建议执行优化")
        
        # 日志文件检查
        if len(health_info['large_log_files']) > 0:
            recommendations.append(f"发现 {len(health_info['large_log_files'])} 个大日志文件，建议清理")
        
        # 记录数量检查
        total_records = sum(health_info['table_stats'].values())
        if total_records > 10000:
            recommendations.append("数据记录较多，建议定期清理测试数据")
        
        if not recommendations:
            recommendations.append("系统运行正常")

        return recommendations

    def check_inventory_consistency(self):
        """检查库存一致性"""
        try:
            from app.models import Inventory, InboundRecord, OutboundRecord, Warehouse
            from app import db

            self.logger.info("开始检查库存一致性...")

            # 获取所有仓库
            warehouses = Warehouse.query.all()
            total_checked = 0
            total_fixed = 0
            problems_found = []

            for warehouse in warehouses:
                warehouse_ids = [warehouse.id]

                # 获取该仓库的库存记录
                inventory_records = Inventory.query.filter_by(
                    operated_warehouse_id=warehouse.id
                ).all()

                for inv in inventory_records:
                    if not inv.identification_code:
                        continue

                    total_checked += 1

                    # 查找对应的入库记录
                    inbound_record = InboundRecord.query.filter_by(
                        identification_code=inv.identification_code
                    ).first()

                    if not inbound_record:
                        continue

                    # 查找对应的出库记录
                    outbound_records = OutboundRecord.query.filter_by(
                        identification_code=inv.identification_code
                    ).filter(
                        OutboundRecord.operated_warehouse_id.in_(warehouse_ids)
                    ).all()

                    # 计算理论库存
                    original_pallet = inbound_record.pallet_count or 0
                    original_package = inbound_record.package_count or 0

                    total_out_pallet = sum(rec.pallet_count or 0 for rec in outbound_records)
                    total_out_package = sum(rec.package_count or 0 for rec in outbound_records)

                    theoretical_pallet = max(0, original_pallet - total_out_pallet)
                    theoretical_package = max(0, original_package - total_out_package)

                    current_pallet = inv.pallet_count or 0
                    current_package = inv.package_count or 0

                    # 检查是否需要修复
                    if (current_pallet != theoretical_pallet or
                        current_package != theoretical_package):

                        problems_found.append({
                            'warehouse': warehouse.warehouse_name,
                            'identification_code': inv.identification_code,
                            'customer_name': inv.customer_name,
                            'current_pallet': current_pallet,
                            'current_package': current_package,
                            'theoretical_pallet': theoretical_pallet,
                            'theoretical_package': theoretical_package
                        })

                        # 自动修复
                        inv.pallet_count = theoretical_pallet
                        inv.package_count = theoretical_package
                        inv.last_updated = datetime.now()
                        total_fixed += 1

                        self.logger.info(f"修复库存不一致: {warehouse.warehouse_name} - {inv.identification_code}")

            # 提交修复
            if total_fixed > 0:
                db.session.commit()
                self.logger.info(f"库存一致性检查完成，修复了 {total_fixed} 条记录")
            else:
                self.logger.info("库存一致性检查完成，未发现问题")

            return {
                'success': True,
                'message': f'检查了 {total_checked} 条记录，修复了 {total_fixed} 条不一致记录',
                'total_checked': total_checked,
                'total_fixed': total_fixed,
                'problems_found': len(problems_found),
                'details': problems_found[:5] if problems_found else []  # 只返回前5条详情
            }

        except Exception as e:
            self.logger.error(f"库存一致性检查失败: {e}")
            return {
                'success': False,
                'message': f'库存一致性检查失败: {e}'
            }
    
    def run_full_maintenance(self):
        """执行完整维护"""
        try:
            self.logger.info("开始执行自动维护")
            
            results = {
                'start_time': datetime.now().isoformat(),
                'tasks': {}
            }
            
            # 1. 系统健康检查
            health_result = self.check_system_health()
            results['tasks']['health_check'] = health_result
            
            # 2. 日志清理
            log_result = self.clean_logs()
            results['tasks']['log_cleanup'] = log_result
            
            # 3. 库存一致性检查
            inventory_result = self.check_inventory_consistency()
            results['tasks']['inventory_consistency'] = inventory_result

            # 4. 数据库优化（仅在需要时执行）
            if health_result.get('success') and health_result.get('health_info', {}).get('database_size', 0) > 100:
                db_result = self.optimize_database()
                results['tasks']['database_optimization'] = db_result
            else:
                results['tasks']['database_optimization'] = {
                    'success': True,
                    'message': '数据库大小正常，跳过优化',
                    'skipped': True
                }
            
            results['end_time'] = datetime.now().isoformat()
            results['success'] = all(task.get('success', False) for task in results['tasks'].values())
            
            self.logger.info(f"自动维护完成，成功: {results['success']}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"自动维护失败: {e}")
            return {
                'success': False,
                'message': f'自动维护失败: {e}',
                'timestamp': datetime.now().isoformat()
            }

# 全局维护服务实例
maintenance_service = MaintenanceService()
