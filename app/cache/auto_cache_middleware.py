#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动缓存中间件
无需手动操作，自动为所有请求应用缓存优化
"""

import time
import functools
from flask import request, g, current_app
from flask_login import current_user

from .dual_cache_manager import get_dual_cache_manager
from .system_cache_config import SystemCacheConfig


class AutoCacheMiddleware:
    """自动缓存中间件"""
    
    def __init__(self, app=None):
        self.app = app
        self.cache_manager = None
        self.enabled = True
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """初始化应用"""
        self.app = app
        
        # 注册请求钩子
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        
        # 获取缓存管理器
        try:
            self.cache_manager = get_dual_cache_manager()
            app.logger.info("🔄 自动缓存中间件已启用")
        except Exception as e:
            app.logger.warning(f"自动缓存中间件初始化失败: {e}")
            self.enabled = False
    
    def before_request(self):
        """请求前处理"""
        if not self.enabled or not self.cache_manager:
            return
        
        # 记录请求开始时间
        g.request_start_time = time.time()
        
        # 分析请求类型，决定缓存策略
        cache_info = self._analyze_request()
        g.cache_info = cache_info
        
        if cache_info and cache_info.get('cacheable'):
            # 尝试从缓存获取响应
            cached_response = self._get_cached_response(cache_info)
            if cached_response:
                g.cache_hit = True
                return cached_response
        
        g.cache_hit = False
    
    def after_request(self, response):
        """请求后处理"""
        if not self.enabled or not self.cache_manager:
            return response
        
        # 计算请求耗时
        if hasattr(g, 'request_start_time'):
            duration = time.time() - g.request_start_time
            g.request_duration = duration
        
        # 如果是可缓存的请求且未命中缓存，则缓存响应
        cache_info = getattr(g, 'cache_info', None)
        cache_hit = getattr(g, 'cache_hit', False)
        
        if (cache_info and 
            cache_info.get('cacheable') and 
            not cache_hit and 
            response.status_code == 200):
            
            self._cache_response(cache_info, response)
        
        # 添加缓存头信息
        self._add_cache_headers(response, cache_info, cache_hit)
        
        return response
    
    def _analyze_request(self):
        """分析请求，确定缓存策略"""
        path = request.path
        method = request.method
        
        # 只缓存GET请求
        if method != 'GET':
            return {'cacheable': False, 'reason': 'non_get_method'}
        
        # 分析路径，确定缓存类型
        cache_type = self._determine_cache_type(path)
        if not cache_type:
            return {'cacheable': False, 'reason': 'unsupported_path'}
        
        # 生成缓存键
        cache_key = self._generate_cache_key(path, cache_type)
        
        # 获取缓存配置
        cache_config = SystemCacheConfig.get_cache_config(cache_type)
        
        return {
            'cacheable': True,
            'cache_type': cache_type,
            'cache_key': cache_key,
            'config': cache_config,
            'path': path
        }
    
    def _determine_cache_type(self, path):
        """根据路径确定缓存类型"""
        path_mappings = {
            # API路径映射
            '/api/inventory/list': 'inventory_list',
            '/api/inventory/search': 'inventory_search',
            '/api/inventory/statistics': 'inventory_stats',
            '/reports/api/dashboard_data': 'dashboard_summary',
            '/reports/api/realtime_stats': 'realtime_metrics',
            '/reports/api/inventory_overview': 'inventory_overview',
            '/api/users/list': 'user_list',
            '/api/users/permissions': 'user_permissions',
            '/api/warehouses/list': 'warehouse_list',
            '/api/customers/list': 'customer_list',
            
            # 页面路径映射
            '/inventory': 'inventory_list',
            '/reports/dashboard': 'dashboard_summary',
            '/users': 'user_list',
            '/warehouses': 'warehouse_list',
            '/customers': 'customer_list',
        }
        
        # 精确匹配
        if path in path_mappings:
            return path_mappings[path]
        
        # 模式匹配
        if path.startswith('/api/inventory/'):
            return 'inventory_list'
        elif path.startswith('/api/inbound/'):
            return 'inbound_list'
        elif path.startswith('/api/outbound/'):
            return 'outbound_list'
        elif path.startswith('/api/transit/'):
            return 'transit_list'
        elif path.startswith('/api/receive/'):
            return 'receive_list'
        elif path.startswith('/reports/api/'):
            return 'statistics'
        elif path.startswith('/api/users/'):
            return 'user_info'
        elif path.startswith('/api/warehouses/'):
            return 'warehouse_info'
        elif path.startswith('/api/customers/'):
            return 'customer_list'
        
        return None
    
    def _generate_cache_key(self, path, cache_type):
        """生成缓存键"""
        key_parts = ['auto_cache', cache_type, path]
        
        # 添加用户信息
        try:
            if current_user and current_user.is_authenticated:
                key_parts.append(f"user:{current_user.id}")
                if hasattr(current_user, 'warehouse_id') and current_user.warehouse_id:
                    key_parts.append(f"warehouse:{current_user.warehouse_id}")
        except:
            pass
        
        # 添加查询参数
        if request.args:
            # 排序参数确保一致性
            sorted_args = sorted(request.args.items())
            args_str = '&'.join(f"{k}={v}" for k, v in sorted_args)
            key_parts.append(f"args:{args_str}")
        
        return ':'.join(key_parts)
    
    def _get_cached_response(self, cache_info):
        """从缓存获取响应"""
        try:
            cache_key = cache_info['cache_key']
            cached_data = self.cache_manager.get(cache_key)
            
            if cached_data:
                current_app.logger.debug(f"缓存命中: {cache_key}")
                
                # 构建响应
                from flask import jsonify, make_response
                
                if isinstance(cached_data, dict):
                    response = make_response(jsonify(cached_data))
                else:
                    response = make_response(cached_data)
                
                response.headers['X-Cache'] = 'HIT'
                return response
            
        except Exception as e:
            current_app.logger.warning(f"获取缓存响应失败: {e}")
        
        return None
    
    def _cache_response(self, cache_info, response):
        """缓存响应"""
        try:
            cache_key = cache_info['cache_key']
            cache_type = cache_info['cache_type']
            
            # 只缓存JSON响应
            if response.content_type and 'application/json' in response.content_type:
                response_data = response.get_json()
                
                if response_data:
                    # 添加缓存元数据
                    response_data['_cache_meta'] = {
                        'cached_at': time.time(),
                        'cache_type': cache_type,
                        'ttl': cache_info['config'].get('l1_ttl', 300)
                    }
                    
                    # 存储到缓存
                    self.cache_manager.set(
                        cache_key, 
                        response_data, 
                        cache_type=cache_type
                    )
                    
                    current_app.logger.debug(f"响应已缓存: {cache_key}")
            
        except Exception as e:
            current_app.logger.warning(f"缓存响应失败: {e}")
    
    def _add_cache_headers(self, response, cache_info, cache_hit):
        """添加缓存头信息"""
        try:
            if cache_hit:
                response.headers['X-Cache'] = 'HIT'
                response.headers['X-Cache-Type'] = cache_info.get('cache_type', 'unknown')
            else:
                response.headers['X-Cache'] = 'MISS'
            
            # 添加性能信息
            if hasattr(g, 'request_duration'):
                response.headers['X-Response-Time'] = f"{g.request_duration:.3f}s"
            
            # 添加缓存控制头
            if cache_info and cache_info.get('cacheable'):
                config = cache_info.get('config', {})
                max_age = config.get('l1_ttl', 300)
                response.headers['Cache-Control'] = f'public, max-age={max_age}'
            
        except Exception as e:
            current_app.logger.warning(f"添加缓存头失败: {e}")


# 全局中间件实例
auto_cache_middleware = AutoCacheMiddleware()


def init_auto_cache_middleware(app):
    """初始化自动缓存中间件"""
    auto_cache_middleware.init_app(app)
    return auto_cache_middleware
