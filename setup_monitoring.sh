#!/bin/bash
# 仓储管理系统监控和维护配置脚本
# 第三阶段：配置监控、备份和维护

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

APP_DIR="/opt/warehouse"
APP_USER="warehouse"

echo -e "${GREEN}🔧 配置系统监控和维护...${NC}"

# 1. 创建系统监控脚本
echo -e "${YELLOW}📊 创建系统监控脚本...${NC}"
cat > /usr/local/bin/warehouse_monitor.sh << 'EOF'
#!/bin/bash
# 仓储管理系统监控脚本

LOG_FILE="/var/log/warehouse/monitor.log"
APP_DIR="/opt/warehouse"

# 记录日志函数
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> $LOG_FILE
}

# 检查应用服务
check_app_service() {
    if supervisorctl status warehouse | grep -q "RUNNING"; then
        log_message "✅ 应用服务运行正常"
        return 0
    else
        log_message "❌ 应用服务异常，尝试重启"
        supervisorctl restart warehouse
        sleep 10
        if supervisorctl status warehouse | grep -q "RUNNING"; then
            log_message "✅ 应用服务重启成功"
        else
            log_message "❌ 应用服务重启失败"
            # 发送告警（可配置邮件或短信）
        fi
        return 1
    fi
}

# 检查Nginx
check_nginx() {
    if systemctl is-active --quiet nginx; then
        log_message "✅ Nginx运行正常"
        return 0
    else
        log_message "❌ Nginx异常，尝试重启"
        systemctl restart nginx
        if systemctl is-active --quiet nginx; then
            log_message "✅ Nginx重启成功"
        else
            log_message "❌ Nginx重启失败"
        fi
        return 1
    fi
}

# 检查MySQL
check_mysql() {
    if systemctl is-active --quiet mysql; then
        log_message "✅ MySQL运行正常"
        return 0
    else
        log_message "❌ MySQL异常，尝试重启"
        systemctl restart mysql
        sleep 15
        if systemctl is-active --quiet mysql; then
            log_message "✅ MySQL重启成功"
        else
            log_message "❌ MySQL重启失败"
        fi
        return 1
    fi
}

# 检查Redis
check_redis() {
    if systemctl is-active --quiet redis-server; then
        log_message "✅ Redis运行正常"
        return 0
    else
        log_message "❌ Redis异常，尝试重启"
        systemctl restart redis-server
        if systemctl is-active --quiet redis-server; then
            log_message "✅ Redis重启成功"
        else
            log_message "❌ Redis重启失败"
        fi
        return 1
    fi
}

# 检查磁盘空间
check_disk_space() {
    DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ $DISK_USAGE -gt 85 ]; then
        log_message "⚠️ 磁盘使用率过高: ${DISK_USAGE}%"
        # 清理日志文件
        find /var/log -name "*.log" -mtime +7 -exec rm {} \;
        find /tmp -type f -mtime +3 -exec rm {} \;
    else
        log_message "✅ 磁盘使用率正常: ${DISK_USAGE}%"
    fi
}

# 检查内存使用
check_memory() {
    MEM_USAGE=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
    if [ $MEM_USAGE -gt 90 ]; then
        log_message "⚠️ 内存使用率过高: ${MEM_USAGE}%"
        # 清理缓存
        echo 1 > /proc/sys/vm/drop_caches
    else
        log_message "✅ 内存使用率正常: ${MEM_USAGE}%"
    fi
}

# 检查应用健康状态
check_app_health() {
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/health || echo "000")
    if [ "$HTTP_CODE" = "200" ]; then
        log_message "✅ 应用健康检查通过"
        return 0
    else
        log_message "❌ 应用健康检查失败，HTTP状态码: $HTTP_CODE"
        return 1
    fi
}

# 主监控流程
main() {
    log_message "🔍 开始系统监控检查"
    
    check_app_service
    check_nginx
    check_mysql
    check_redis
    check_disk_space
    check_memory
    check_app_health
    
    log_message "✅ 监控检查完成"
}

# 执行监控
main
EOF

chmod +x /usr/local/bin/warehouse_monitor.sh

# 2. 创建备份脚本
echo -e "${YELLOW}💾 创建备份脚本...${NC}"
cat > /usr/local/bin/warehouse_backup.sh << 'EOF'
#!/bin/bash
# 仓储管理系统备份脚本

BACKUP_DIR="/var/backups/warehouse"
APP_DIR="/opt/warehouse"
MYSQL_USER="warehouse_user"
MYSQL_PASSWORD="warehouse_secure_2024"
MYSQL_DATABASE="warehouse_production"
RETENTION_DAYS=30

# 创建备份目录
mkdir -p $BACKUP_DIR

# 生成时间戳
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "🔄 开始备份 - $TIMESTAMP"

# 1. 备份MySQL数据库
echo "📊 备份MySQL数据库..."
mysqldump -u $MYSQL_USER -p$MYSQL_PASSWORD $MYSQL_DATABASE | gzip > $BACKUP_DIR/mysql_backup_$TIMESTAMP.sql.gz

# 2. 备份应用代码和配置
echo "📁 备份应用代码..."
tar -czf $BACKUP_DIR/app_backup_$TIMESTAMP.tar.gz -C $APP_DIR . --exclude=venv --exclude=__pycache__ --exclude=*.pyc

# 3. 备份日志文件
echo "📝 备份日志文件..."
tar -czf $BACKUP_DIR/logs_backup_$TIMESTAMP.tar.gz -C /var/log warehouse

# 4. 创建备份信息文件
cat > $BACKUP_DIR/backup_info_$TIMESTAMP.json << EOF
{
    "timestamp": "$TIMESTAMP",
    "date": "$(date)",
    "mysql_backup": "mysql_backup_$TIMESTAMP.sql.gz",
    "app_backup": "app_backup_$TIMESTAMP.tar.gz",
    "logs_backup": "logs_backup_$TIMESTAMP.tar.gz",
    "mysql_size": "$(stat -c%s $BACKUP_DIR/mysql_backup_$TIMESTAMP.sql.gz)",
    "app_size": "$(stat -c%s $BACKUP_DIR/app_backup_$TIMESTAMP.tar.gz)",
    "logs_size": "$(stat -c%s $BACKUP_DIR/logs_backup_$TIMESTAMP.tar.gz)"
}
EOF

# 5. 清理旧备份
echo "🧹 清理旧备份..."
find $BACKUP_DIR -name "*backup_*" -mtime +$RETENTION_DAYS -delete

echo "✅ 备份完成 - $TIMESTAMP"
echo "📍 备份位置: $BACKUP_DIR"
ls -lh $BACKUP_DIR/*$TIMESTAMP*
EOF

chmod +x /usr/local/bin/warehouse_backup.sh

# 3. 创建日志轮转配置
echo -e "${YELLOW}📋 配置日志轮转...${NC}"
cat > /etc/logrotate.d/warehouse << 'EOF'
/var/log/warehouse/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 warehouse warehouse
    postrotate
        supervisorctl restart warehouse > /dev/null 2>&1 || true
    endscript
}

/var/log/nginx/warehouse_*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
    postrotate
        systemctl reload nginx > /dev/null 2>&1 || true
    endscript
}
EOF

# 4. 配置定时任务
echo -e "${YELLOW}⏰ 配置定时任务...${NC}"
cat > /etc/cron.d/warehouse << 'EOF'
# 仓储管理系统定时任务

# 每5分钟检查系统状态
*/5 * * * * root /usr/local/bin/warehouse_monitor.sh

# 每天凌晨2点备份
0 2 * * * root /usr/local/bin/warehouse_backup.sh

# 每天凌晨3点清理临时文件
0 3 * * * root find /tmp -type f -mtime +1 -delete

# 每周日凌晨4点重启服务（维护窗口）
0 4 * * 0 root supervisorctl restart warehouse && systemctl restart nginx

# 每月1号清理旧日志
0 1 1 * * root find /var/log -name "*.log.*" -mtime +30 -delete
EOF

# 5. 创建性能优化脚本
echo -e "${YELLOW}⚡ 创建性能优化脚本...${NC}"
cat > /usr/local/bin/warehouse_optimize.sh << 'EOF'
#!/bin/bash
# 仓储管理系统性能优化脚本

echo "🚀 开始性能优化..."

# 1. 优化MySQL
echo "🗄️ 优化MySQL..."
mysql -u root -pwarehouse_root_2024 -e "
OPTIMIZE TABLE warehouse_production.inbound_records;
OPTIMIZE TABLE warehouse_production.outbound_records;
OPTIMIZE TABLE warehouse_production.inventory;
ANALYZE TABLE warehouse_production.inbound_records;
ANALYZE TABLE warehouse_production.outbound_records;
ANALYZE TABLE warehouse_production.inventory;
"

# 2. 清理Redis缓存
echo "🔴 清理Redis缓存..."
redis-cli FLUSHDB

# 3. 清理系统缓存
echo "💾 清理系统缓存..."
echo 1 > /proc/sys/vm/drop_caches
echo 2 > /proc/sys/vm/drop_caches
echo 3 > /proc/sys/vm/drop_caches

# 4. 重启应用服务
echo "🔄 重启应用服务..."
supervisorctl restart warehouse

echo "✅ 性能优化完成"
EOF

chmod +x /usr/local/bin/warehouse_optimize.sh

# 6. 创建系统状态检查脚本
echo -e "${YELLOW}📈 创建系统状态脚本...${NC}"
cat > /usr/local/bin/warehouse_status.sh << 'EOF'
#!/bin/bash
# 系统状态检查脚本

echo "📊 仓储管理系统状态报告"
echo "================================"
echo "🕐 检查时间: $(date)"
echo ""

# 系统信息
echo "💻 系统信息:"
echo "   CPU核心数: $(nproc)"
echo "   内存总量: $(free -h | awk 'NR==2{print $2}')"
echo "   磁盘使用: $(df -h / | awk 'NR==2{print $5}')"
echo "   系统负载: $(uptime | awk -F'load average:' '{print $2}')"
echo ""

# 服务状态
echo "🔧 服务状态:"
echo "   应用服务: $(supervisorctl status warehouse | awk '{print $2}')"
echo "   Nginx: $(systemctl is-active nginx)"
echo "   MySQL: $(systemctl is-active mysql)"
echo "   Redis: $(systemctl is-active redis-server)"
echo ""

# 网络连接
echo "🌐 网络连接:"
echo "   HTTP连接数: $(netstat -an | grep :80 | wc -l)"
echo "   MySQL连接数: $(netstat -an | grep :3306 | wc -l)"
echo ""

# 应用健康检查
echo "🏥 应用健康:"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/health || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    echo "   健康检查: ✅ 正常"
else
    echo "   健康检查: ❌ 异常 (HTTP $HTTP_CODE)"
fi

# 最近的错误日志
echo ""
echo "📝 最近错误 (最近10条):"
tail -10 /var/log/warehouse/gunicorn_error.log 2>/dev/null || echo "   无错误日志"
EOF

chmod +x /usr/local/bin/warehouse_status.sh

# 7. 设置权限
chown -R $APP_USER:$APP_USER /var/log/warehouse
chown -R $APP_USER:$APP_USER /var/backups/warehouse

# 8. 启动定时任务
systemctl enable cron
systemctl start cron

echo -e "${GREEN}✅ 监控和维护配置完成！${NC}"
echo -e "${BLUE}📋 可用命令:${NC}"
echo -e "   warehouse_monitor.sh  - 系统监控"
echo -e "   warehouse_backup.sh   - 手动备份"
echo -e "   warehouse_optimize.sh - 性能优化"
echo -e "   warehouse_status.sh   - 状态检查"

echo -e "${BLUE}📊 定时任务:${NC}"
echo -e "   每5分钟: 系统监控"
echo -e "   每天2点: 自动备份"
echo -e "   每天3点: 清理临时文件"
echo -e "   每周日4点: 服务重启"

echo -e "${GREEN}🎉 监控系统已就绪！${NC}"
