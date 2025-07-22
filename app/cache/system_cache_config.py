#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全系统缓存配置
整合现有Redis实现，扩展到全系统模块
"""

from typing import Dict, Any, Optional
from datetime import timedelta


class SystemCacheConfig:
    """全系统缓存配置"""
    
    # ==================== 全系统缓存策略配置 ====================
    CACHE_STRATEGIES = {
        # ==================== 仪表板模块 ====================
        'dashboard_summary': {
            'l1_ttl': 300,      # 5分钟
            'l2_ttl': 1800,     # 30分钟
            'priority': 'high',
            'auto_refresh': True,
            'preload': True
        },
        'today_stats': {
            'l1_ttl': 60,       # 1分钟
            'l2_ttl': 300,      # 5分钟
            'priority': 'high',
            'auto_refresh': True,
            'preload': True
        },
        'realtime_metrics': {
            'l1_ttl': 30,       # 30秒
            'l2_ttl': 120,      # 2分钟
            'priority': 'critical',
            'auto_refresh': True,
            'preload': False
        },
        
        # ==================== 库存管理模块 ====================
        'inventory_list': {
            'l1_ttl': 180,      # 3分钟
            'l2_ttl': 900,      # 15分钟
            'priority': 'high',
            'auto_refresh': False,
            'preload': True,
            'invalidate_on': ['inventory_change', 'inbound_change', 'outbound_change']
        },
        'inventory_overview': {
            'l1_ttl': 120,      # 2分钟
            'l2_ttl': 600,      # 10分钟
            'priority': 'high',
            'auto_refresh': True,
            'preload': True
        },
        'inventory_search': {
            'l1_ttl': 300,      # 5分钟
            'l2_ttl': 1800,     # 30分钟
            'priority': 'medium',
            'auto_refresh': False,
            'preload': False
        },
        'inventory_stats': {
            'l1_ttl': 600,      # 10分钟
            'l2_ttl': 3600,     # 1小时
            'priority': 'medium',
            'auto_refresh': True,
            'preload': False
        },
        'aggregated_inventory': {
            'l1_ttl': 300,      # 5分钟
            'l2_ttl': 1800,     # 30分钟
            'priority': 'high',
            'auto_refresh': True,
            'preload': True
        },
        
        # ==================== 入库管理模块 ====================
        'inbound_list': {
            'l1_ttl': 120,      # 2分钟
            'l2_ttl': 600,      # 10分钟
            'priority': 'high',
            'auto_refresh': False,
            'preload': False
        },
        'inbound_batch': {
            'l1_ttl': 60,       # 1分钟
            'l2_ttl': 300,      # 5分钟
            'priority': 'high',
            'auto_refresh': False,
            'preload': False
        },
        'inbound_stats': {
            'l1_ttl': 300,      # 5分钟
            'l2_ttl': 1800,     # 30分钟
            'priority': 'medium',
            'auto_refresh': True,
            'preload': False
        },
        
        # ==================== 出库管理模块 ====================
        'outbound_list': {
            'l1_ttl': 120,      # 2分钟
            'l2_ttl': 600,      # 10分钟
            'priority': 'high',
            'auto_refresh': False,
            'preload': False
        },
        'outbound_batch': {
            'l1_ttl': 60,       # 1分钟
            'l2_ttl': 300,      # 5分钟
            'priority': 'high',
            'auto_refresh': False,
            'preload': False
        },
        'outbound_stats': {
            'l1_ttl': 300,      # 5分钟
            'l2_ttl': 1800,     # 30分钟
            'priority': 'medium',
            'auto_refresh': True,
            'preload': False
        },
        
        # ==================== 在途货物模块 ====================
        'transit_list': {
            'l1_ttl': 180,      # 3分钟
            'l2_ttl': 900,      # 15分钟
            'priority': 'high',
            'auto_refresh': False,
            'preload': False
        },
        'transit_overview': {
            'l1_ttl': 180,      # 3分钟
            'l2_ttl': 900,      # 15分钟
            'priority': 'high',
            'auto_refresh': True,
            'preload': True
        },
        'transit_batch': {
            'l1_ttl': 120,      # 2分钟
            'l2_ttl': 600,      # 10分钟
            'priority': 'medium',
            'auto_refresh': False,
            'preload': False
        },
        
        # ==================== 收货管理模块 ====================
        'receive_list': {
            'l1_ttl': 120,      # 2分钟
            'l2_ttl': 600,      # 10分钟
            'priority': 'high',
            'auto_refresh': False,
            'preload': False
        },
        'receive_batch': {
            'l1_ttl': 60,       # 1分钟
            'l2_ttl': 300,      # 5分钟
            'priority': 'high',
            'auto_refresh': False,
            'preload': False
        },
        
        # ==================== 用户权限模块 ====================
        'user_list': {
            'l1_ttl': 600,      # 10分钟
            'l2_ttl': 3600,     # 1小时
            'priority': 'medium',
            'auto_refresh': False,
            'preload': False
        },
        'user_info': {
            'l1_ttl': 1800,     # 30分钟
            'l2_ttl': 7200,     # 2小时
            'priority': 'medium',
            'auto_refresh': False,
            'preload': True,
            'invalidate_on': ['user_change']
        },
        'user_permissions': {
            'l1_ttl': 1800,     # 30分钟
            'l2_ttl': 7200,     # 2小时
            'priority': 'high',
            'auto_refresh': False,
            'preload': True,
            'invalidate_on': ['user_change', 'permission_change']
        },
        'warehouse_users': {
            'l1_ttl': 900,      # 15分钟
            'l2_ttl': 3600,     # 1小时
            'priority': 'medium',
            'auto_refresh': False,
            'preload': False
        },
        
        # ==================== 客户数据模块 ====================
        'customer_list': {
            'l1_ttl': 900,      # 15分钟
            'l2_ttl': 3600,     # 1小时
            'priority': 'medium',
            'auto_refresh': False,
            'preload': False
        },
        'customer_ranking': {
            'l1_ttl': 900,      # 15分钟
            'l2_ttl': 7200,     # 2小时
            'priority': 'medium',
            'auto_refresh': True,
            'preload': True
        },
        'customer_stats': {
            'l1_ttl': 1800,     # 30分钟
            'l2_ttl': 7200,     # 2小时
            'priority': 'low',
            'auto_refresh': True,
            'preload': False
        },
        
        # ==================== 仓库数据模块 ====================
        'warehouse_list': {
            'l1_ttl': 1800,     # 30分钟
            'l2_ttl': 7200,     # 2小时
            'priority': 'medium',
            'auto_refresh': False,
            'preload': True,
            'invalidate_on': ['warehouse_change']
        },
        'warehouse_info': {
            'l1_ttl': 3600,     # 1小时
            'l2_ttl': 86400,    # 24小时
            'priority': 'medium',
            'auto_refresh': False,
            'preload': True
        },
        'warehouse_summary': {
            'l1_ttl': 600,      # 10分钟
            'l2_ttl': 3600,     # 1小时
            'priority': 'high',
            'auto_refresh': True,
            'preload': True
        },
        'warehouse_stats': {
            'l1_ttl': 900,      # 15分钟
            'l2_ttl': 3600,     # 1小时
            'priority': 'medium',
            'auto_refresh': True,
            'preload': False
        },
        
        # ==================== 报表模块 ====================
        'daily_report': {
            'l1_ttl': 1800,     # 30分钟
            'l2_ttl': 7200,     # 2小时
            'priority': 'medium',
            'auto_refresh': True,
            'preload': False
        },
        'weekly_report': {
            'l1_ttl': 3600,     # 1小时
            'l2_ttl': 21600,    # 6小时
            'priority': 'low',
            'auto_refresh': True,
            'preload': False
        },
        'monthly_report': {
            'l1_ttl': 3600,     # 1小时
            'l2_ttl': 86400,    # 24小时
            'priority': 'low',
            'auto_refresh': True,
            'preload': False
        },
        'historical_stats': {
            'l1_ttl': 1800,     # 30分钟
            'l2_ttl': 21600,    # 6小时
            'priority': 'low',
            'auto_refresh': False,
            'preload': False
        },
        'statistics': {
            'l1_ttl': 900,      # 15分钟
            'l2_ttl': 3600,     # 1小时
            'priority': 'medium',
            'auto_refresh': True,
            'preload': False
        },
        
        # ==================== 打印模块 ====================
        'print_templates': {
            'l1_ttl': 3600,     # 1小时
            'l2_ttl': 86400,    # 24小时
            'priority': 'low',
            'auto_refresh': False,
            'preload': False
        },
        'print_queue': {
            'l1_ttl': 60,       # 1分钟
            'l2_ttl': 300,      # 5分钟
            'priority': 'high',
            'auto_refresh': False,
            'preload': False
        },
        
        # ==================== 系统配置模块 ====================
        'system_config': {
            'l1_ttl': 3600,     # 1小时
            'l2_ttl': 86400,    # 24小时
            'priority': 'medium',
            'auto_refresh': False,
            'preload': True
        },
        'menu_permissions': {
            'l1_ttl': 1800,     # 30分钟
            'l2_ttl': 7200,     # 2小时
            'priority': 'high',
            'auto_refresh': False,
            'preload': True,
            'invalidate_on': ['permission_change']
        },
        
        # ==================== 搜索结果模块 ====================
        'search_results': {
            'l1_ttl': 180,      # 3分钟
            'l2_ttl': 900,      # 15分钟
            'priority': 'medium',
            'auto_refresh': False,
            'preload': False
        },
        
        # ==================== 默认配置 ====================
        'default': {
            'l1_ttl': 300,      # 5分钟
            'l2_ttl': 1800,     # 30分钟
            'priority': 'medium',
            'auto_refresh': False,
            'preload': False
        }
    }
    
    # ==================== 缓存失效映射 ====================
    INVALIDATION_MAPPING = {
        'inventory_change': [
            'inventory_list', 'inventory_overview', 'inventory_stats',
            'aggregated_inventory', 'dashboard_summary', 'warehouse_summary'
        ],
        'inbound_change': [
            'inbound_list', 'inbound_batch', 'inbound_stats',
            'inventory_list', 'inventory_overview', 'dashboard_summary'
        ],
        'outbound_change': [
            'outbound_list', 'outbound_batch', 'outbound_stats',
            'inventory_list', 'inventory_overview', 'dashboard_summary'
        ],
        'user_change': [
            'user_info', 'user_permissions', 'warehouse_users'
        ],
        'warehouse_change': [
            'warehouse_list', 'warehouse_info', 'warehouse_summary'
        ],
        'permission_change': [
            'user_permissions', 'menu_permissions'
        ],
        'customer_change': [
            'customer_list', 'customer_ranking', 'customer_stats'
        ]
    }
    
    # ==================== 预加载优先级 ====================
    PRELOAD_PRIORITIES = {
        'critical': ['realtime_metrics'],
        'high': [
            'dashboard_summary', 'today_stats', 'inventory_overview',
            'warehouse_summary', 'user_permissions', 'menu_permissions'
        ],
        'medium': [
            'inventory_list', 'warehouse_list', 'user_info', 'system_config'
        ],
        'low': []
    }
    
    @classmethod
    def get_cache_config(cls, cache_type: str) -> Dict[str, Any]:
        """获取缓存配置"""
        return cls.CACHE_STRATEGIES.get(cache_type, cls.CACHE_STRATEGIES['default'])
    
    @classmethod
    def get_invalidation_targets(cls, event_type: str) -> list:
        """获取需要失效的缓存类型"""
        return cls.INVALIDATION_MAPPING.get(event_type, [])
    
    @classmethod
    def get_preload_items(cls, priority: str = 'high') -> list:
        """获取需要预加载的缓存类型"""
        items = []
        for p in ['critical', 'high', 'medium', 'low']:
            items.extend(cls.PRELOAD_PRIORITIES.get(p, []))
            if p == priority:
                break
        return items
    
    @classmethod
    def should_auto_refresh(cls, cache_type: str) -> bool:
        """检查是否需要自动刷新"""
        config = cls.get_cache_config(cache_type)
        return config.get('auto_refresh', False)
    
    @classmethod
    def should_preload(cls, cache_type: str) -> bool:
        """检查是否需要预加载"""
        config = cls.get_cache_config(cache_type)
        return config.get('preload', False)
