#!/bin/bash
# 仓储管理系统 - Linux启动脚本

# 设置颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo "========================================"
echo -e "${BLUE}🚀 仓储管理系统 - 快速启动模式${NC}"
echo "========================================"
echo ""

# 设置快速启动环境变量
export FLASK_APP=app.py
export FLASK_ENV=development
export QUICK_START_MODE=1

echo -e "${GREEN}🚀 快速启动模式已启用${NC}"
echo -e "${GREEN}  ✅ 跳过后台任务初始化${NC}"
echo -e "${GREEN}  ✅ 禁用性能监控${NC}"
echo -e "${GREEN}  ✅ 优化页面加载速度${NC}"
echo ""

echo -e "${YELLOW}🚀 启动应用程序...${NC}"
echo -e "${YELLOW}📍 访问地址: http://127.0.0.1:5000${NC}"
echo -e "${YELLOW}⏹️  按 Ctrl+C 停止服务器${NC}"
echo ""

# 检查Python是否可用
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo -e "${RED}❌ Python未找到，请先安装Python${NC}"
        exit 1
    else
        python app.py
    fi
else
    python3 app.py
fi

echo ""
echo -e "${YELLOW}👋 应用程序已停止${NC}"
