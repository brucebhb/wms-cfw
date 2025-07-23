#!/bin/bash

# 修复nginx配置脚本
echo "开始修复nginx配置..."

# 备份原配置
sudo cp /etc/nginx/sites-available/warehouse /etc/nginx/sites-available/warehouse.backup

# 创建新的nginx配置
sudo tee /etc/nginx/sites-available/warehouse > /dev/null << 'EOF'
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;

    client_max_body_size 16M;

    # 静态文件处理 - 关键修复！
    location /static/ {
        alias /opt/warehouse/app/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # 主应用代理
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 30s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        proxy_buffering off;
    }
}
EOF

# 测试配置
echo "测试nginx配置..."
sudo nginx -t

if [ $? -eq 0 ]; then
    echo "配置测试通过，重新加载nginx..."
    sudo systemctl reload nginx
    echo "nginx重新加载完成！"
    
    # 测试静态文件访问
    echo "测试静态文件访问..."
    curl -I http://127.0.0.1/static/css/style.css
    
    echo "修复完成！请访问 http://175.178.147.75 测试"
else
    echo "nginx配置测试失败，恢复备份..."
    sudo cp /etc/nginx/sites-available/warehouse.backup /etc/nginx/sites-available/warehouse
fi
