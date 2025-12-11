#!/bin/bash

# 自动化测试机器人定时任务脚本
# 用于 Cron 定时执行

# 设置脚本参数
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PYTHON_PATH="python3"
MAIN_SCRIPT="$PROJECT_DIR/src/main.py"
CONFIG_FILE="$PROJECT_DIR/config/config.yaml"
LOG_DIR="$PROJECT_DIR/logs"

# 创建日志目录
mkdir -p "$LOG_DIR"

# 获取当前时间戳
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="$LOG_DIR/cronjob_$TIMESTAMP.log"

# 输出函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 错误处理
handle_error() {
    local exit_code=$?
    log "❌ 脚本执行失败，退出码: $exit_code"
    exit $exit_code
}

# 设置错误陷阱
trap 'handle_error' ERR

log "🚀 开始执行自动化测试机器人"
log "项目目录: $PROJECT_DIR"
log "配置文件: $CONFIG_FILE"

# 检查 Python 环境
if ! command -v "$PYTHON_PATH" &> /dev/null; then
    log "❌ Python 3 未找到，请安装 Python 3"
    exit 1
fi

# 检查项目文件
if [ ! -f "$MAIN_SCRIPT" ]; then
    log "❌ 主脚本文件未找到: $MAIN_SCRIPT"
    exit 1
fi

if [ ! -f "$CONFIG_FILE" ]; then
    log "❌ 配置文件未找到: $CONFIG_FILE"
    exit 1
fi

# 切换到项目目录
cd "$PROJECT_DIR"

# 检查虚拟环境
if [ -d "venv" ]; then
    log "📦 激活虚拟环境"
    source venv/bin/activate
elif [ -d ".venv" ]; then
    log "📦 激活虚拟环境"
    source .venv/bin/activate
else
    log "⚠️  未找到虚拟环境，使用系统 Python"
fi

# 检查依赖
log "🔍 检查 Python 依赖"
if ! "$PYTHON_PATH" -c "import playwright" 2>/dev/null; then
    log "📦 安装 Python 依赖"
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        log "❌ 依赖安装失败"
        exit 1
    fi
fi

# 安装 Playwright 浏览器
log "🌐 检查 Playwright 浏览器"
if ! "$PYTHON_PATH" -m playwright install --help &>/dev/null; then
    log "📦 安装 Playwright 浏览器"
    "$PYTHON_PATH" -m playwright install
    if [ $? -ne 0 ]; then
        log "❌ Playwright 浏览器安装失败"
        exit 1
    fi
fi

# 检查 MCP 服务器（如果启用）
MCP_ENABLED=$("$PYTHON_PATH" -c "
import sys
sys.path.append('src')
from utils import MCPConfigLoader
config = MCPConfigLoader()
print('enabled' if config.is_enabled() else 'disabled')
" 2>/dev/null)

if [ "$MCP_ENABLED" = "enabled" ]; then
    log "🔧 检查 MCP 服务器"
    # 这里可以添加 MCP 服务器启动检查逻辑
    # 例如：检查端口是否可用，或者尝试连接
fi

log "▶️  开始执行自动化测试"

# 执行测试
TEST_START_TIME=$(date +%s)
"$PYTHON_PATH" "$MAIN_SCRIPT" --config "$CONFIG_FILE" 2>&1 | tee -a "$LOG_FILE"
TEST_EXIT_CODE=${PIPESTATUS[0]}
TEST_END_TIME=$(date +%s)
TEST_DURATION=$((TEST_END_TIME - TEST_START_TIME))

# 检查测试结果
if [ $TEST_EXIT_CODE -eq 0 ]; then
    log "✅ 测试成功完成，耗时: ${TEST_DURATION}秒"
else
    log "❌ 测试失败，退出码: $TEST_EXIT_CODE，耗时: ${TEST_DURATION}秒"
fi

# 清理旧日志（保留最近 7 天）
log "🧹 清理旧日志文件"
find "$LOG_DIR" -name "cronjob_*.log" -mtime +7 -delete 2>/dev/null

# 清理旧报告（保留最近 30 天）
REPORT_DIR="$PROJECT_DIR/reports"
if [ -d "$REPORT_DIR" ]; then
    find "$REPORT_DIR" -name "*.json" -o -name "*.html" -mtime +30 -delete 2>/dev/null
fi

# 清理 MCP 数据（保留最近 3 天）
MCP_DIR="$PROJECT_DIR/mcp_data"
if [ -d "$MCP_DIR" ]; then
    find "$MCP_DIR" -type f -mtime +3 -delete 2>/dev/null
    # 清理空目录
    find "$MCP_DIR" -type d -empty -delete 2>/dev/null
fi

# 检查磁盘空间
DISK_USAGE=$(du -sh "$PROJECT_DIR" | cut -f1)
log "💾 项目占用磁盘空间: $DISK_USAGE"

# 发送通知（可选）
# 这里可以添加邮件、Webhook 或其他通知方式
if command -v curl &>/dev/null && [ -n "$WEBHOOK_URL" ]; then
    log "📢 发送通知到 Webhook"
    curl -X POST "$WEBHOOK_URL" \
         -H "Content-Type: application/json" \
         -d "{\"text\":\"自动化测试完成，状态: $([ $TEST_EXIT_CODE -eq 0 ] && echo '成功' || echo '失败')\"}" \
         2>/dev/null
fi

log "🏁 自动化测试机器人执行完成"
log "📄 详细日志: $LOG_FILE"

# 返回测试退出码
exit $TEST_EXIT_CODE