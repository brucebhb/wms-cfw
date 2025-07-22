#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
异步数据库操作
将同步数据库查询改造为异步处理
"""

import asyncio
import aiomysql
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from typing import List, Dict, Any, Optional
from datetime import datetime, date


class AsyncDatabaseManager:
    """异步数据库管理器"""
    
    def __init__(self, database_url: str):
        # 将同步URL转换为异步URL
        if database_url.startswith('mysql://'):
            async_url = database_url.replace('mysql://', 'mysql+aiomysql://')
        else:
            async_url = database_url
        
        self.engine = create_async_engine(async_url, echo=False)
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
    
    async def get_session(self):
        """获取异步会话"""
        async with self.async_session() as session:
            yield session


class AsyncInventoryService:
    """异步库存服务"""
    
    def __init__(self, db_manager: AsyncDatabaseManager):
        self.db = db_manager
    
    async def get_inventory_list_async(self, warehouse_id: int, page: int = 1, per_page: int = 50) -> Dict[str, Any]:
        """异步获取库存列表"""
        async with self.db.async_session() as session:
            # 使用原生SQL查询（更快）
            query = """
            SELECT id, identification_code, customer_name, 
                   package_count, pallet_count, weight, volume,
                   last_updated, operated_warehouse_id
            FROM inventory 
            WHERE operated_warehouse_id = :warehouse_id
            ORDER BY last_updated DESC
            LIMIT :limit OFFSET :offset
            """
            
            count_query = """
            SELECT COUNT(*) as total 
            FROM inventory 
            WHERE operated_warehouse_id = :warehouse_id
            """
            
            # 并发执行查询和计数
            results, count_result = await asyncio.gather(
                session.execute(query, {
                    'warehouse_id': warehouse_id,
                    'limit': per_page,
                    'offset': (page - 1) * per_page
                }),
                session.execute(count_query, {'warehouse_id': warehouse_id})
            )
            
            items = [dict(row) for row in results.fetchall()]
            total = count_result.scalar()
            
            return {
                'items': items,
                'total': total,
                'page': page,
                'per_page': per_page,
                'pages': (total + per_page - 1) // per_page
            }
    
    async def get_inventory_stats_async(self, warehouse_id: int) -> Dict[str, Any]:
        """异步获取库存统计"""
        async with self.db.async_session() as session:
            query = """
            SELECT 
                COUNT(*) as total_items,
                SUM(package_count) as total_packages,
                SUM(pallet_count) as total_pallets,
                SUM(weight) as total_weight,
                SUM(volume) as total_volume
            FROM inventory 
            WHERE operated_warehouse_id = :warehouse_id
            """
            
            result = await session.execute(query, {'warehouse_id': warehouse_id})
            row = result.fetchone()
            
            return {
                'total_items': row.total_items or 0,
                'total_packages': row.total_packages or 0,
                'total_pallets': row.total_pallets or 0,
                'total_weight': float(row.total_weight or 0),
                'total_volume': float(row.total_volume or 0)
            }


class AsyncStatisticsService:
    """异步统计服务"""
    
    def __init__(self, db_manager: AsyncDatabaseManager):
        self.db = db_manager
    
    async def get_today_stats_async(self, warehouse_id: int) -> Dict[str, Any]:
        """异步获取今日统计"""
        today = date.today()
        
        async with self.db.async_session() as session:
            # 并发查询入库和出库统计
            inbound_query = """
            SELECT COUNT(*) as count, 
                   SUM(package_count) as packages,
                   SUM(pallet_count) as pallets
            FROM inbound_records 
            WHERE operated_warehouse_id = :warehouse_id 
            AND DATE(inbound_time) = :today
            """
            
            outbound_query = """
            SELECT COUNT(*) as count,
                   SUM(package_count) as packages, 
                   SUM(pallet_count) as pallets
            FROM outbound_records 
            WHERE operated_warehouse_id = :warehouse_id 
            AND DATE(outbound_time) = :today
            """
            
            inbound_result, outbound_result = await asyncio.gather(
                session.execute(inbound_query, {'warehouse_id': warehouse_id, 'today': today}),
                session.execute(outbound_query, {'warehouse_id': warehouse_id, 'today': today})
            )
            
            inbound_row = inbound_result.fetchone()
            outbound_row = outbound_result.fetchone()
            
            return {
                'date': today.isoformat(),
                'inbound': {
                    'count': inbound_row.count or 0,
                    'packages': inbound_row.packages or 0,
                    'pallets': inbound_row.pallets or 0
                },
                'outbound': {
                    'count': outbound_row.count or 0,
                    'packages': outbound_row.packages or 0,
                    'pallets': outbound_row.pallets or 0
                }
            }
    
    async def get_dashboard_data_async(self, warehouse_id: int) -> Dict[str, Any]:
        """异步获取仪表板数据"""
        # 并发获取所有需要的数据
        today_stats, inventory_stats, week_stats = await asyncio.gather(
            self.get_today_stats_async(warehouse_id),
            AsyncInventoryService(self.db).get_inventory_stats_async(warehouse_id),
            self.get_week_stats_async(warehouse_id)
        )
        
        return {
            'today_stats': today_stats,
            'inventory_stats': inventory_stats,
            'week_stats': week_stats,
            'generated_at': datetime.now().isoformat()
        }
    
    async def get_week_stats_async(self, warehouse_id: int) -> Dict[str, Any]:
        """异步获取周统计"""
        async with self.db.async_session() as session:
            query = """
            SELECT DATE(inbound_time) as date,
                   COUNT(*) as inbound_count,
                   (SELECT COUNT(*) FROM outbound_records 
                    WHERE operated_warehouse_id = :warehouse_id 
                    AND DATE(outbound_time) = DATE(inbound_time)) as outbound_count
            FROM inbound_records 
            WHERE operated_warehouse_id = :warehouse_id 
            AND inbound_time >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
            GROUP BY DATE(inbound_time)
            ORDER BY date
            """
            
            result = await session.execute(query, {'warehouse_id': warehouse_id})
            rows = result.fetchall()
            
            return {
                'daily_stats': [
                    {
                        'date': row.date.isoformat(),
                        'inbound': row.inbound_count,
                        'outbound': row.outbound_count
                    }
                    for row in rows
                ]
            }


class AsyncTaskManager:
    """异步任务管理器"""
    
    def __init__(self):
        self.running_tasks = set()
    
    async def run_concurrent_tasks(self, tasks: List[asyncio.Task]) -> List[Any]:
        """并发运行多个任务"""
        try:
            # 添加到运行中的任务集合
            for task in tasks:
                self.running_tasks.add(task)
            
            # 等待所有任务完成
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理结果和异常
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    print(f"任务 {i} 执行失败: {result}")
                    processed_results.append(None)
                else:
                    processed_results.append(result)
            
            return processed_results
            
        finally:
            # 清理任务集合
            for task in tasks:
                self.running_tasks.discard(task)
    
    def create_task(self, coro) -> asyncio.Task:
        """创建异步任务"""
        task = asyncio.create_task(coro)
        return task
    
    async def cancel_all_tasks(self):
        """取消所有运行中的任务"""
        for task in self.running_tasks:
            task.cancel()
        
        if self.running_tasks:
            await asyncio.gather(*self.running_tasks, return_exceptions=True)
        
        self.running_tasks.clear()


# 使用示例
async def example_usage():
    """异步处理使用示例"""
    
    # 初始化异步数据库管理器
    db_manager = AsyncDatabaseManager('mysql+aiomysql://user:pass@localhost/warehouse')
    
    # 创建服务实例
    inventory_service = AsyncInventoryService(db_manager)
    stats_service = AsyncStatisticsService(db_manager)
    task_manager = AsyncTaskManager()
    
    # 并发获取多个数据
    tasks = [
        task_manager.create_task(inventory_service.get_inventory_list_async(1)),
        task_manager.create_task(stats_service.get_today_stats_async(1)),
        task_manager.create_task(inventory_service.get_inventory_stats_async(1))
    ]
    
    # 等待所有任务完成
    results = await task_manager.run_concurrent_tasks(tasks)
    
    inventory_list, today_stats, inventory_stats = results
    
    return {
        'inventory_list': inventory_list,
        'today_stats': today_stats,
        'inventory_stats': inventory_stats
    }


# 在Flask中使用异步
def run_async_in_flask(async_func, *args, **kwargs):
    """在Flask中运行异步函数"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(async_func(*args, **kwargs))
    finally:
        loop.close()
