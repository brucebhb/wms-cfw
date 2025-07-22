def strip_whitespace(value):
    """
    去除字符串中的所有空格
    
    Args:
        value: 输入值，可以是字符串或其他类型
        
    Returns:
        如果输入是字符串，返回去除空格后的字符串；否则原样返回
    """
    if isinstance(value, str):
        return value.strip()
    return value
    
def clean_dict_whitespace(data):
    """
    清理字典中所有字符串值的空格
    
    Args:
        data: 包含键值对的字典
        
    Returns:
        处理后的字典，所有字符串值都去除了首尾空格
    """
    if not isinstance(data, dict):
        return data
        
    result = {}
    for key, value in data.items():
        if isinstance(value, str):
            result[key] = value.strip()
        elif isinstance(value, dict):
            result[key] = clean_dict_whitespace(value)
        elif isinstance(value, list):
            result[key] = [clean_dict_whitespace(item) if isinstance(item, dict) 
                          else strip_whitespace(item) for item in value]
        else:
            result[key] = value
    return result

import sqlite3
from flask import current_app, request, render_template
from functools import wraps

def get_db_connection():
    """
    获取数据库连接

    Returns:
        SQLite数据库连接对象
    """
    conn = sqlite3.connect(current_app.config['DATABASE_URI'])
    conn.row_factory = sqlite3.Row
    return conn


def render_ajax_aware(template_name, **context):
    """
    智能渲染函数，根据请求类型选择合适的模板

    Args:
        template_name: 基础模板名称
        **context: 模板上下文
    """
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # AJAX请求，尝试使用AJAX版本的模板
        ajax_template_name = template_name.replace('.html', '_ajax.html')
        try:
            return render_template(ajax_template_name, **context)
        except:
            # 如果AJAX模板不存在，使用普通模板
            pass

    # 普通请求或AJAX模板不存在，使用普通模板
    return render_template(template_name, **context)