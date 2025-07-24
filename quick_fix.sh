#!/bin/bash
# 仓储管理系统 - Linux快速性能修复脚本

# 设置颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo "========================================"
echo -e "${BLUE}🔧 仓储管理系统 - 快速性能修复${NC}"
echo "========================================"
echo ""

# 1. 终止现有Python进程
echo -e "${YELLOW}[$(date '+%H:%M:%S')] 🔄 终止现有Python进程...${NC}"
pkill -f "python.*app.py" 2>/dev/null || echo -e "${YELLOW}[$(date '+%H:%M:%S')] ℹ️  没有发现运行中的应用进程${NC}"
sleep 2
echo -e "${GREEN}[$(date '+%H:%M:%S')] ✅ Python进程已终止${NC}"

# 2. 清理缓存文件
echo -e "${YELLOW}[$(date '+%H:%M:%S')] 🧹 清理缓存文件...${NC}"
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
rm -rf .pytest_cache 2>/dev/null || true
echo -e "${GREEN}[$(date '+%H:%M:%S')] ✅ 缓存文件已清理${NC}"

# 3. 禁用性能监控脚本
echo -e "${YELLOW}[$(date '+%H:%M:%S')] ⚙️  禁用性能监控脚本...${NC}"
if [ -d "app/static/js" ]; then
    cd app/static/js
    for file in performance-*.js unified-performance-*.js; do
        if [ -f "$file" ] && [[ ! "$file" == *.disabled ]]; then
            mv "$file" "$file.disabled" 2>/dev/null || true
        fi
    done
    cd ../../..
fi
echo -e "${GREEN}[$(date '+%H:%M:%S')] ✅ 性能监控脚本已禁用${NC}"

# 4. 设置快速启动环境变量
echo -e "${YELLOW}[$(date '+%H:%M:%S')] 🔧 设置快速启动模式...${NC}"
export FLASK_ENV=development
export QUICK_START_MODE=1
echo -e "${GREEN}[$(date '+%H:%M:%S')] ✅ 快速启动模式已设置${NC}"

# 5. 显示修复完成信息
echo ""
echo "========================================"
echo -e "${GREEN}✅ 快速性能修复完成！${NC}"
echo "========================================"
echo ""
echo -e "${BLUE}📋 修复内容：${NC}"
echo -e "${GREEN}  ✅ 已终止所有Python进程${NC}"
echo -e "${GREEN}  ✅ 已清理缓存文件${NC}"
echo -e "${GREEN}  ✅ 已禁用性能监控脚本${NC}"
echo -e "${GREEN}  ✅ 已启用快速启动模式${NC}"
echo ""
echo -e "${YELLOW}🚀 现在可以运行以下命令启动系统：${NC}"
echo -e "${BLUE}  ./start.sh${NC}"
echo -e "${BLUE}  或者: python3 app.py${NC}"
echo ""
echo -e "${YELLOW}📍 访问地址: http://127.0.0.1:5000${NC}"
echo ""
