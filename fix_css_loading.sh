#!/bin/bash

# 修复CSS加载问题 - 下载外部CSS到本地
echo "🔧 开始修复CSS加载问题..."

# 创建vendor目录
mkdir -p /opt/warehouse/app/static/vendor/css
mkdir -p /opt/warehouse/app/static/vendor/js

cd /opt/warehouse/app/static/vendor/css

echo "📥 下载Bootstrap CSS..."
curl -o bootstrap.min.css "https://cdn.bootcdn.net/ajax/libs/twitter-bootstrap/5.3.0/css/bootstrap.min.css"

echo "📥 下载FontAwesome CSS..."
curl -o fontawesome.min.css "https://cdn.bootcdn.net/ajax/libs/font-awesome/6.4.0/css/all.min.css"

echo "📥 下载DateRangePicker CSS..."
curl -o daterangepicker.css "https://cdn.jsdelivr.net/npm/daterangepicker/daterangepicker.css"

cd /opt/warehouse/app/static/vendor/js

echo "📥 下载Bootstrap JS..."
curl -o bootstrap.bundle.min.js "https://cdn.bootcdn.net/ajax/libs/twitter-bootstrap/5.3.0/js/bootstrap.bundle.min.js"

echo "📥 下载jQuery..."
curl -o jquery.min.js "https://cdn.bootcdn.net/ajax/libs/jquery/3.7.0/jquery.min.js"

echo "📥 下载DateRangePicker JS..."
curl -o daterangepicker.min.js "https://cdn.jsdelivr.net/npm/daterangepicker/daterangepicker.min.js"

echo "📥 下载Moment.js..."
curl -o moment.min.js "https://cdn.jsdelivr.net/npm/moment/moment.min.js"

# 设置权限
chown -R warehouse:warehouse /opt/warehouse/app/static/vendor/
chmod -R 644 /opt/warehouse/app/static/vendor/

echo "✅ CSS和JS文件下载完成！"

# 创建本地化的base.html模板
echo "📝 创建本地化模板..."
cat > /opt/warehouse/app/templates/base_local.html << 'EOF'
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="csrf-token" content="{{ csrf_token() }}">
    <title>{% if title %}{{ title }} - {% endif %}仓储管理系统</title>
    
    <!-- 本地Bootstrap CSS -->
    <link href="{{ url_for('static', filename='vendor/css/bootstrap.min.css') }}" rel="stylesheet">
    
    <!-- 本地FontAwesome CSS -->
    <link rel="stylesheet" href="{{ url_for('static', filename='vendor/css/fontawesome.min.css') }}">
    
    <!-- 本地DateRangePicker CSS -->
    <link rel="stylesheet" href="{{ url_for('static', filename='vendor/css/daterangepicker.css') }}">
    
    <!-- 自定义样式 -->
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/custom.css') }}">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/table-column-resizer.css') }}">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/backend-inbound-improvements.css') }}">

    <style>
        /* 固定顶部导航栏 */
        .top-navbar {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 1030;
            background-color: #198754 !important;
            border-bottom: 1px solid #dee2e6;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        /* 主体内容区域 */
        .main-content {
            margin-top: 70px;
            padding: 20px;
        }

        /* 侧边栏样式 */
        .sidebar {
            position: fixed;
            top: 70px;
            left: 0;
            width: 250px;
            height: calc(100vh - 70px);
            background-color: #2c3e50;
            overflow-y: auto;
            z-index: 1020;
        }

        /* 内容区域调整 */
        .content-wrapper {
            margin-left: 250px;
            padding: 20px;
            min-height: calc(100vh - 70px);
        }

        /* 数据卡片样式 */
        .stats-card {
            background: white;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .stats-card h3 {
            margin: 0 0 10px 0;
            font-size: 2rem;
            font-weight: bold;
            color: #198754;
        }

        .stats-card p {
            margin: 0;
            color: #6c757d;
            font-size: 0.9rem;
        }

        /* 表格样式增强 */
        .table-responsive {
            border: 1px solid #dee2e6;
            border-radius: 8px;
            overflow: hidden;
        }

        .table thead th {
            background-color: #198754;
            color: white;
            border: none;
            font-weight: 600;
        }

        /* 按钮样式 */
        .btn-primary {
            background-color: #198754;
            border-color: #198754;
        }

        .btn-primary:hover {
            background-color: #157347;
            border-color: #146c43;
        }
    </style>

    {% block head %}{% endblock %}
</head>
<body>
    <!-- 顶部导航栏 -->
    <nav class="navbar navbar-expand-lg navbar-dark top-navbar">
        <div class="container-fluid">
            <a class="navbar-brand" href="{{ url_for('main.index') }}">
                <i class="fas fa-warehouse"></i> 仓储管理系统
            </a>
            
            <div class="navbar-nav ms-auto">
                {% if current_user.is_authenticated %}
                    <span class="navbar-text me-3">
                        <i class="fas fa-user"></i> {{ current_user.username }}
                    </span>
                    <a class="nav-link" href="{{ url_for('auth.logout') }}">
                        <i class="fas fa-sign-out-alt"></i> 退出
                    </a>
                {% else %}
                    <a class="nav-link" href="{{ url_for('auth.login') }}">
                        <i class="fas fa-sign-in-alt"></i> 登录
                    </a>
                {% endif %}
            </div>
        </div>
    </nav>

    <div class="d-flex">
        <!-- 侧边栏 -->
        <div class="sidebar">
            {% block sidebar %}
            <!-- 侧边栏内容将在子模板中定义 -->
            {% endblock %}
        </div>

        <!-- 主内容区域 -->
        <div class="content-wrapper">
            {% block content %}{% endblock %}
        </div>
    </div>

    <!-- 本地JavaScript文件 -->
    <script src="{{ url_for('static', filename='vendor/js/jquery.min.js') }}"></script>
    <script src="{{ url_for('static', filename='vendor/js/bootstrap.bundle.min.js') }}"></script>
    <script src="{{ url_for('static', filename='vendor/js/moment.min.js') }}"></script>
    <script src="{{ url_for('static', filename='vendor/js/daterangepicker.min.js') }}"></script>
    
    <!-- 自定义JavaScript -->
    <script src="{{ url_for('static', filename='js/common.js') }}"></script>
    
    {% block scripts %}{% endblock %}
</body>
</html>
EOF

chown warehouse:warehouse /opt/warehouse/app/templates/base_local.html

echo "🎉 CSS修复完成！"
echo "📍 请重启应用以应用更改"
