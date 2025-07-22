#!/bin/bash
# 仓储管理系统性能测试脚本
# 针对15用户并发和200条/日记录进行压力测试

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置变量
SERVER_URL="http://localhost"
CONCURRENT_USERS=15
TOTAL_REQUESTS=1000
TEST_DURATION=300  # 5分钟

echo -e "${GREEN}🚀 仓储管理系统性能测试${NC}"
echo -e "${BLUE}📋 测试配置:${NC}"
echo -e "   服务器: $SERVER_URL"
echo -e "   并发用户: $CONCURRENT_USERS"
echo -e "   总请求数: $TOTAL_REQUESTS"
echo -e "   测试时长: ${TEST_DURATION}秒"
echo ""

# 1. 检查测试工具
echo -e "${YELLOW}🔧 检查测试工具...${NC}"
if ! command -v ab &> /dev/null; then
    echo "安装Apache Bench..."
    apt update && apt install -y apache2-utils
fi

if ! command -v curl &> /dev/null; then
    echo "安装curl..."
    apt install -y curl
fi

# 2. 基础连通性测试
echo -e "${YELLOW}🌐 基础连通性测试...${NC}"
if curl -s -o /dev/null -w "%{http_code}" $SERVER_URL | grep -q "200"; then
    echo -e "${GREEN}✅ 服务器连接正常${NC}"
else
    echo -e "${RED}❌ 服务器连接失败${NC}"
    exit 1
fi

# 3. 健康检查测试
echo -e "${YELLOW}🏥 健康检查测试...${NC}"
HEALTH_CODE=$(curl -s -o /dev/null -w "%{http_code}" $SERVER_URL/health)
if [ "$HEALTH_CODE" = "200" ]; then
    echo -e "${GREEN}✅ 应用健康检查通过${NC}"
else
    echo -e "${RED}❌ 应用健康检查失败 (HTTP $HEALTH_CODE)${NC}"
fi

# 4. 静态资源测试
echo -e "${YELLOW}📁 静态资源性能测试...${NC}"
ab -n 100 -c 10 $SERVER_URL/static/css/style.css > /tmp/static_test.log 2>&1
STATIC_RPS=$(grep "Requests per second" /tmp/static_test.log | awk '{print $4}')
echo -e "   静态资源RPS: $STATIC_RPS"

# 5. 主页面并发测试
echo -e "${YELLOW}🏠 主页面并发测试...${NC}"
ab -n $TOTAL_REQUESTS -c $CONCURRENT_USERS $SERVER_URL/ > /tmp/homepage_test.log 2>&1

# 解析结果
HOMEPAGE_RPS=$(grep "Requests per second" /tmp/homepage_test.log | awk '{print $4}')
HOMEPAGE_TIME=$(grep "Time per request" /tmp/homepage_test.log | head -1 | awk '{print $4}')
HOMEPAGE_FAILED=$(grep "Failed requests" /tmp/homepage_test.log | awk '{print $3}')

echo -e "   主页RPS: $HOMEPAGE_RPS"
echo -e "   平均响应时间: ${HOMEPAGE_TIME}ms"
echo -e "   失败请求: $HOMEPAGE_FAILED"

# 6. 登录页面测试
echo -e "${YELLOW}🔐 登录页面测试...${NC}"
ab -n 500 -c $CONCURRENT_USERS $SERVER_URL/auth/login > /tmp/login_test.log 2>&1
LOGIN_RPS=$(grep "Requests per second" /tmp/login_test.log | awk '{print $4}')
echo -e "   登录页RPS: $LOGIN_RPS"

# 7. API接口测试（如果有公开API）
echo -e "${YELLOW}🔌 API接口测试...${NC}"
if curl -s $SERVER_URL/api/health &> /dev/null; then
    ab -n 300 -c 10 $SERVER_URL/api/health > /tmp/api_test.log 2>&1
    API_RPS=$(grep "Requests per second" /tmp/api_test.log | awk '{print $4}')
    echo -e "   API RPS: $API_RPS"
else
    echo -e "   API接口不可用，跳过测试"
fi

# 8. 数据库连接测试
echo -e "${YELLOW}🗄️ 数据库性能测试...${NC}"
DB_START_TIME=$(date +%s.%N)
mysql -u warehouse_user -pwarehouse_secure_2024 warehouse_production -e "SELECT COUNT(*) FROM information_schema.tables;" > /dev/null 2>&1
DB_END_TIME=$(date +%s.%N)
DB_RESPONSE_TIME=$(echo "$DB_END_TIME - $DB_START_TIME" | bc)
echo -e "   数据库响应时间: ${DB_RESPONSE_TIME}秒"

# 9. Redis性能测试
echo -e "${YELLOW}🔴 Redis性能测试...${NC}"
REDIS_START_TIME=$(date +%s.%N)
redis-cli ping > /dev/null 2>&1
REDIS_END_TIME=$(date +%s.%N)
REDIS_RESPONSE_TIME=$(echo "$REDIS_END_TIME - $REDIS_START_TIME" | bc)
echo -e "   Redis响应时间: ${REDIS_RESPONSE_TIME}秒"

# 10. 系统资源监控
echo -e "${YELLOW}📊 系统资源监控...${NC}"

# CPU使用率
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//')
echo -e "   CPU使用率: ${CPU_USAGE}%"

# 内存使用率
MEM_USAGE=$(free | awk 'NR==2{printf "%.1f", $3*100/$2}')
echo -e "   内存使用率: ${MEM_USAGE}%"

# 磁盘使用率
DISK_USAGE=$(df / | awk 'NR==2 {print $5}')
echo -e "   磁盘使用率: $DISK_USAGE"

# 网络连接数
HTTP_CONNECTIONS=$(netstat -an | grep :80 | wc -l)
echo -e "   HTTP连接数: $HTTP_CONNECTIONS"

# 11. 长时间压力测试
echo -e "${YELLOW}⏱️ 长时间压力测试 (${TEST_DURATION}秒)...${NC}"
timeout $TEST_DURATION ab -n 999999 -c $CONCURRENT_USERS $SERVER_URL/ > /tmp/stress_test.log 2>&1 &
STRESS_PID=$!

# 监控资源使用
for i in {1..10}; do
    sleep $(($TEST_DURATION / 10))
    CPU_NOW=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//')
    MEM_NOW=$(free | awk 'NR==2{printf "%.1f", $3*100/$2}')
    echo -e "   第${i}次检查 - CPU: ${CPU_NOW}%, 内存: ${MEM_NOW}%"
done

wait $STRESS_PID 2>/dev/null || true

# 12. 生成测试报告
echo -e "${YELLOW}📋 生成测试报告...${NC}"
REPORT_FILE="/tmp/performance_report_$(date +%Y%m%d_%H%M%S).txt"

cat > $REPORT_FILE << EOF
仓储管理系统性能测试报告
================================
测试时间: $(date)
服务器配置: 4核8G, Ubuntu 22.04
测试配置: ${CONCURRENT_USERS}并发用户, ${TOTAL_REQUESTS}总请求

测试结果:
--------
主页面性能:
  - RPS: $HOMEPAGE_RPS
  - 平均响应时间: ${HOMEPAGE_TIME}ms
  - 失败请求: $HOMEPAGE_FAILED

静态资源性能:
  - RPS: $STATIC_RPS

登录页面性能:
  - RPS: $LOGIN_RPS

数据库性能:
  - 响应时间: ${DB_RESPONSE_TIME}秒

Redis性能:
  - 响应时间: ${REDIS_RESPONSE_TIME}秒

系统资源:
  - CPU使用率: ${CPU_USAGE}%
  - 内存使用率: ${MEM_USAGE}%
  - 磁盘使用率: $DISK_USAGE
  - HTTP连接数: $HTTP_CONNECTIONS

性能评估:
--------
EOF

# 性能评估
if (( $(echo "$HOMEPAGE_RPS > 50" | bc -l) )); then
    echo "✅ 主页面性能: 优秀 (RPS > 50)" >> $REPORT_FILE
elif (( $(echo "$HOMEPAGE_RPS > 20" | bc -l) )); then
    echo "⚠️ 主页面性能: 良好 (RPS > 20)" >> $REPORT_FILE
else
    echo "❌ 主页面性能: 需要优化 (RPS < 20)" >> $REPORT_FILE
fi

if (( $(echo "$HOMEPAGE_TIME < 1000" | bc -l) )); then
    echo "✅ 响应时间: 优秀 (< 1秒)" >> $REPORT_FILE
elif (( $(echo "$HOMEPAGE_TIME < 3000" | bc -l) )); then
    echo "⚠️ 响应时间: 良好 (< 3秒)" >> $REPORT_FILE
else
    echo "❌ 响应时间: 需要优化 (> 3秒)" >> $REPORT_FILE
fi

if [ "$HOMEPAGE_FAILED" = "0" ]; then
    echo "✅ 稳定性: 优秀 (无失败请求)" >> $REPORT_FILE
else
    echo "⚠️ 稳定性: 有 $HOMEPAGE_FAILED 个失败请求" >> $REPORT_FILE
fi

echo "" >> $REPORT_FILE
echo "建议:" >> $REPORT_FILE
echo "- 针对15用户并发，当前配置应该能够满足需求" >> $REPORT_FILE
echo "- 建议定期监控系统资源使用情况" >> $REPORT_FILE
echo "- 如性能不足，可考虑增加Gunicorn worker数量" >> $REPORT_FILE

# 显示报告
echo ""
echo -e "${GREEN}📊 测试完成！报告已生成：${NC}"
echo -e "${BLUE}$REPORT_FILE${NC}"
echo ""
cat $REPORT_FILE

echo ""
echo -e "${GREEN}🎉 性能测试完成！${NC}"
echo -e "${BLUE}💡 优化建议：${NC}"
echo -e "   1. 如果RPS < 20，考虑增加Gunicorn worker数量"
echo -e "   2. 如果响应时间 > 3秒，检查数据库查询优化"
echo -e "   3. 如果内存使用率 > 80%，考虑增加Redis缓存"
echo -e "   4. 定期运行此测试脚本监控性能变化"
