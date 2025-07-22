#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SPA处理器 - 处理单页应用请求
"""

from flask import request, g, render_template_string
from functools import wraps
import re
import time


class SPAHandler:
    """SPA请求处理器"""
    
    @staticmethod
    def is_spa_request():
        """检查是否为SPA请求"""
        return (
            request.headers.get('X-SPA-Request') == 'true' or
            request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        )
    
    @staticmethod
    def extract_content_from_html(html_content):
        """从完整HTML中提取主要内容区域"""
        
        # 定义内容区域的选择器优先级
        content_selectors = [
            r'<div[^>]*class="[^"]*main-content[^"]*"[^>]*>(.*?)</div>',
            r'<main[^>]*>(.*?)</main>',
            r'<div[^>]*id="main-content"[^>]*>(.*?)</div>',
            r'<div[^>]*class="[^"]*container-fluid[^"]*"[^>]*>(.*?)</div>',
            r'<div[^>]*class="[^"]*col-md-9[^"]*"[^>]*>(.*?)</div>',
            r'<div[^>]*class="[^"]*col-lg-10[^"]*"[^>]*>(.*?)</div>',
        ]
        
        for selector in content_selectors:
            match = re.search(selector, html_content, re.DOTALL | re.IGNORECASE)
            if match:
                content = match.group(1).strip()
                if content:  # 确保内容不为空
                    return content
        
        # 如果没有找到特定的内容区域，尝试提取body内容
        body_match = re.search(r'<body[^>]*>(.*?)</body>', html_content, re.DOTALL | re.IGNORECASE)
        if body_match:
            body_content = body_match.group(1)
            
            # 移除导航和侧边栏
            patterns_to_remove = [
                r'<nav[^>]*>.*?</nav>',
                r'<div[^>]*class="[^"]*sidebar[^"]*"[^>]*>.*?</div>',
                r'<div[^>]*id="sidebar"[^>]*>.*?</div>',
                r'<aside[^>]*>.*?</aside>',
                r'<header[^>]*>.*?</header>',
                r'<footer[^>]*>.*?</footer>',
            ]
            
            for pattern in patterns_to_remove:
                body_content = re.sub(pattern, '', body_content, flags=re.DOTALL | re.IGNORECASE)
            
            return body_content.strip()
        
        # 最后的备选方案：返回原始内容
        return html_content
    
    @staticmethod
    def process_spa_response(html_content):
        """处理SPA响应内容"""
        
        if not SPAHandler.is_spa_request():
            return html_content
        
        # 提取主要内容
        content = SPAHandler.extract_content_from_html(html_content)
        
        # 包装内容，确保脚本和样式能正确执行
        spa_wrapper = f"""
        <div class="spa-content">
            {content}
        </div>
        <script>
        // SPA内容加载完成后的处理
        (function() {{
            // 重新初始化Bootstrap组件
            if (typeof bootstrap !== 'undefined') {{
                // 初始化tooltips
                var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
                tooltipTriggerList.map(function (tooltipTriggerEl) {{
                    return new bootstrap.Tooltip(tooltipTriggerEl);
                }});
                
                // 初始化popovers
                var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
                popoverTriggerList.map(function (popoverTriggerEl) {{
                    return new bootstrap.Popover(popoverTriggerEl);
                }});
            }}
            
            // 重新初始化jQuery插件
            if (typeof $ !== 'undefined') {{
                // 重新绑定表单验证
                $('form').each(function() {{
                    // 这里可以添加表单验证逻辑
                }});
                
                // 重新初始化日期选择器
                if ($.fn.datepicker) {{
                    $('.datepicker').datepicker();
                }}
                
                // 重新初始化其他jQuery插件
                if ($.fn.select2) {{
                    $('.select2').select2();
                }}
            }}
            
            // 触发自定义事件，通知页面内容已更新
            document.dispatchEvent(new CustomEvent('spa:contentLoaded', {{
                detail: {{ timestamp: Date.now() }}
            }}));
            
            console.log('📄 SPA内容已加载并初始化');
        }})();
        </script>
        """
        
        return spa_wrapper


def spa_template_response(template_name_or_list, **context):
    """SPA模板响应装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 执行原始函数
            result = func(*args, **kwargs)
            
            # 如果不是SPA请求，直接返回原始结果
            if not SPAHandler.is_spa_request():
                return result
            
            # 如果返回的是字符串（HTML），直接处理
            if isinstance(result, str):
                return SPAHandler.process_spa_response(result)
            
            # 如果返回的是Response对象，处理其数据
            if hasattr(result, 'data'):
                processed_data = SPAHandler.process_spa_response(result.data.decode('utf-8'))
                result.data = processed_data.encode('utf-8')
                return result
            
            return result
        return wrapper
    return decorator


def spa_aware_render_template(template_name_or_list, **context):
    """SPA感知的模板渲染函数"""
    from flask import render_template
    
    # 渲染完整模板
    html_content = render_template(template_name_or_list, **context)
    
    # 如果是SPA请求，处理内容
    if SPAHandler.is_spa_request():
        return SPAHandler.process_spa_response(html_content)
    
    return html_content


# 全局模板函数
def register_spa_template_functions(app):
    """注册SPA相关的模板函数"""
    
    @app.template_global()
    def is_spa_request():
        """模板中检查是否为SPA请求"""
        return SPAHandler.is_spa_request()
    
    @app.template_global()
    def spa_content_wrapper(content):
        """SPA内容包装器"""
        if SPAHandler.is_spa_request():
            return content
        else:
            # 非SPA请求时，包装在完整的页面结构中
            return f'<div class="full-page-content">{content}</div>'
    
    @app.context_processor
    def inject_spa_context():
        """注入SPA相关的上下文变量"""
        return {
            'is_spa': SPAHandler.is_spa_request(),
            'spa_mode': 'enabled' if SPAHandler.is_spa_request() else 'disabled'
        }


# 中间件类
class SPAMiddleware:
    """SPA中间件"""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """初始化中间件"""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        
        # 注册模板函数
        register_spa_template_functions(app)
    
    def before_request(self):
        """请求前处理"""
        # 标记SPA请求
        g.is_spa_request = SPAHandler.is_spa_request()
        
        if g.is_spa_request:
            g.spa_start_time = time.time()
    
    def after_request(self, response):
        """请求后处理"""
        if hasattr(g, 'is_spa_request') and g.is_spa_request:
            # 添加SPA响应头
            response.headers['X-SPA-Response'] = 'true'
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            
            # 记录SPA请求处理时间
            if hasattr(g, 'spa_start_time'):
                processing_time = time.time() - g.spa_start_time
                response.headers['X-SPA-Processing-Time'] = str(processing_time)
        
        return response


# 便捷函数
def enable_spa_for_app(app):
    """为应用启用SPA支持"""
    spa_middleware = SPAMiddleware(app)
    app.logger.info('SPA支持已启用')
    return spa_middleware
