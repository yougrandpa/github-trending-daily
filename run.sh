#!/bin/bash

# GitHub Trending Daily - 启动脚本

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${GREEN}🚀 启动 GitHub Trending Daily...${NC}"
echo ""

# 检查 Python 环境
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ 错误: 未找到 python3，请先安装 Python 3.8+${NC}"
    exit 1
fi

# 创建虚拟环境（如果不存在）
VENV_DIR="$SCRIPT_DIR/venv"
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}📦 创建虚拟环境...${NC}"
    python3 -m venv "$VENV_DIR"
fi

# 激活虚拟环境
source "$VENV_DIR/bin/activate"

# 安装依赖
echo -e "${YELLOW}📦 安装依赖...${NC}"
pip install -q -r "$SCRIPT_DIR/requirements.txt"

# 检查配置文件
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    echo -e "${RED}❌ 错误: 未找到 .env 配置文件${NC}"
    echo -e "${YELLOW}请复制 .env.example 为 .env 并填写配置信息${NC}"
    echo ""
    echo "cp $SCRIPT_DIR/.env.example $SCRIPT_DIR/.env"
    echo ""
    echo "然后编辑 .env 文件，填写以下配置："
    echo "  - AI_BASE_URL: AI API 地址"
    echo "  - AI_API_KEY: AI API 密钥"
    echo "  - EMAIL_SENDER: 发件人邮箱"
    echo "  - EMAIL_PASSWORD: 发件人密码/授权码"
    echo "  - EMAIL_RECIPIENTS: 收件人邮箱（多个用逗号分隔）"
    exit 1
fi

# 检查依赖是否安装成功
if ! python3 -c "import requests, dotenv, schedule" 2>/dev/null; then
    echo -e "${RED}❌ 错误: 依赖安装失败${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ 环境检查通过！${NC}"
echo ""

# 解析命令行参数
MODE="scheduler"
HOUR=""
MINUTE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --now)
            MODE="now"
            shift
            ;;
        --hour)
            HOUR="$2"
            shift 2
            ;;
        --minute)
            MINUTE="$2"
            shift 2
            ;;
        --help|-h)
            echo "用法: ./run.sh [选项]"
            echo ""
            echo "选项:"
            echo "  --now       立即执行一次（用于测试）"
            echo "  --hour      指定执行小时（0-23）"
            echo "  --minute    指定执行分钟（0-59）"
            echo "  --help,-h   显示帮助信息"
            echo ""
            echo "示例:"
            echo "  ./run.sh                    # 启动定时调度（每天上午10点）"
            echo "  ./run.sh --now              # 立即执行一次"
            echo "  ./run.sh --hour 9 --minute 0 # 设置为每天上午9点执行"
            exit 0
            ;;
        *)
            echo -e "${RED}未知参数: $1${NC}"
            exit 1
            ;;
    esac
done

# 构建命令
CMD="python3 $SCRIPT_DIR/main.py"
if [ "$MODE" = "now" ]; then
    CMD="$CMD --now"
fi
if [ -n "$HOUR" ]; then
    CMD="$CMD --hour $HOUR"
fi
if [ -n "$MINUTE" ]; then
    CMD="$CMD --minute $MINUTE"
fi

echo -e "${YELLOW}📧 启动模式: $MODE${NC}"
if [ -n "$HOUR" ]; then
    echo -e "${YELLOW}⏰ 执行时间: 每天 ${HOUR}:${MINUTE:-00}${NC}"
fi
echo ""

# 执行
exec $CMD
