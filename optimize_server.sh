#!/bin/bash
# 服务器优化脚本
# 适用于4核8G腾讯云服务器

echo "🚀 开始服务器优化..."

# 1. 系统优化
echo "📊 优化系统参数..."
sudo tee -a /etc/sysctl.conf << EOF
# 网络优化
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216

# 文件描述符限制
fs.file-max = 65536

# 内存优化
vm.swappiness = 10
vm.dirty_ratio = 15
vm.dirty_background_ratio = 5
EOF

# 应用系统参数
sudo sysctl -p

# 2. MySQL优化
echo "🗄️  优化MySQL配置..."
sudo tee /etc/mysql/conf.d/warehouse_optimization.cnf << EOF
[mysqld]
# 基础配置
max_connections = 50
wait_timeout = 28800
interactive_timeout = 28800

# InnoDB优化 (针对8GB内存)
innodb_buffer_pool_size = 2G
innodb_log_file_size = 256M
innodb_log_buffer_size = 16M
innodb_flush_log_at_trx_commit = 2
innodb_file_per_table = 1

# 查询缓存
query_cache_type = 1
query_cache_size = 128M
query_cache_limit = 2M

# 临时表
tmp_table_size = 64M
max_heap_table_size = 64M

# 慢查询日志
slow_query_log = 1
slow_query_log_file = /var/log/mysql/slow.log
long_query_time = 2

# 二进制日志
expire_logs_days = 7
max_binlog_size = 100M
EOF

# 3. Redis优化
echo "🔴 优化Redis配置..."
sudo tee -a /etc/redis/redis.conf << EOF

# 内存优化
maxmemory 1gb
maxmemory-policy allkeys-lru

# 持久化优化
save 900 1
save 300 10
save 60 10000

# 网络优化
tcp-keepalive 300
timeout 0
EOF

# 4. Nginx优化
echo "🌐 优化Nginx配置..."
sudo tee /etc/nginx/conf.d/warehouse_optimization.conf << EOF
# Gzip压缩
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;

# 缓存配置
location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}

# 连接优化
keepalive_timeout 65;
keepalive_requests 100;

# 缓冲区优化
client_body_buffer_size 128k;
client_max_body_size 10m;
client_header_buffer_size 1k;
large_client_header_buffers 4 4k;
EOF

# 5. 创建监控脚本
echo "📊 创建系统监控脚本..."
sudo tee /opt/warehouse/monitor_system.sh << 'EOF'
#!/bin/bash
# 系统监控脚本

LOG_FILE="/opt/warehouse/logs/system_monitor.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

# 检查系统资源
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
MEMORY_USAGE=$(free | grep Mem | awk '{printf("%.1f"), $3/$2 * 100.0}')
DISK_USAGE=$(df -h / | awk 'NR==2{print $5}' | cut -d'%' -f1)

# 检查服务状态
NGINX_STATUS=$(systemctl is-active nginx)
MYSQL_STATUS=$(systemctl is-active mysql)
REDIS_STATUS=$(systemctl is-active redis-server)

# 检查应用进程
GUNICORN_PROCESSES=$(ps aux | grep gunicorn | grep -v grep | wc -l)

# 记录日志
echo "[$DATE] CPU: ${CPU_USAGE}%, Memory: ${MEMORY_USAGE}%, Disk: ${DISK_USAGE}%" >> $LOG_FILE
echo "[$DATE] Services - Nginx: $NGINX_STATUS, MySQL: $MYSQL_STATUS, Redis: $REDIS_STATUS" >> $LOG_FILE
echo "[$DATE] Gunicorn processes: $GUNICORN_PROCESSES" >> $LOG_FILE

# 告警检查
if (( $(echo "$CPU_USAGE > 80" | bc -l) )); then
    echo "[$DATE] WARNING: High CPU usage: ${CPU_USAGE}%" >> $LOG_FILE
fi

if (( $(echo "$MEMORY_USAGE > 85" | bc -l) )); then
    echo "[$DATE] WARNING: High memory usage: ${MEMORY_USAGE}%" >> $LOG_FILE
fi

if [ "$GUNICORN_PROCESSES" -lt 4 ]; then
    echo "[$DATE] WARNING: Gunicorn processes count is low: $GUNICORN_PROCESSES" >> $LOG_FILE
fi
EOF

chmod +x /opt/warehouse/monitor_system.sh

# 6. 设置定时任务
echo "⏰ 设置定时监控任务..."
(crontab -l 2>/dev/null; echo "*/5 * * * * /opt/warehouse/monitor_system.sh") | crontab -

# 7. 创建日志轮转配置
echo "📝 配置日志轮转..."
sudo tee /etc/logrotate.d/warehouse << EOF
/opt/warehouse/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 warehouse warehouse
    postrotate
        systemctl reload nginx
    endscript
}
EOF

# 8. 重启服务
echo "🔄 重启相关服务..."
sudo systemctl restart mysql
sudo systemctl restart redis-server
sudo systemctl restart nginx

# 9. 重启应用
echo "🔄 重启仓储管理应用..."
sudo supervisorctl restart warehouse

echo "✅ 服务器优化完成！"
echo ""
echo "📊 优化项目："
echo "   ✅ 系统内核参数优化"
echo "   ✅ MySQL性能优化"
echo "   ✅ Redis缓存优化"
echo "   ✅ Nginx配置优化"
echo "   ✅ 系统监控脚本"
echo "   ✅ 定时任务配置"
echo "   ✅ 日志轮转配置"
echo ""
echo "🔍 监控命令："
echo "   查看系统监控: tail -f /opt/warehouse/logs/system_monitor.log"
echo "   查看应用日志: tail -f /opt/warehouse/logs/system.log"
echo "   查看性能状态: python3 /opt/warehouse/server_monitor.py"
echo ""
echo "🌐 访问地址: http://175.178.147.75"
