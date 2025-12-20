#!/bin/bash
# 自动复制Codex和Gemini技能脚本到当前项目
# 解决跨项目使用技能脚本的路径问题

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}正在设置Codex/Gemini技能脚本...${NC}"

PROJECT_DIR=$(pwd)
CODEX_SRC="/home/yuanzhi/.claude/skills/collaborating-with-codex/scripts/codex_bridge.py"
GEMINI_SRC="/home/yuanzhi/.claude/skills/collaborating-with-gemini/scripts/gemini_bridge.py"

# 检查源文件是否存在
if [[ ! -f "$CODEX_SRC" ]]; then
    echo -e "${RED}错误: Codex脚本不存在: $CODEX_SRC${NC}"
    exit 1
fi

if [[ ! -f "$GEMINI_SRC" ]]; then
    echo -e "${RED}错误: Gemini脚本不存在: $GEMINI_SRC${NC}"
    exit 1
fi

# 创建scripts目录
mkdir -p "$PROJECT_DIR/scripts"

# 复制脚本
cp "$CODEX_SRC" "$PROJECT_DIR/scripts/"
cp "$GEMINI_SRC" "$PROJECT_DIR/scripts/"

# 设置执行权限
chmod +x "$PROJECT_DIR/scripts/codex_bridge.py"
chmod +x "$PROJECT_DIR/scripts/gemini_bridge.py"

echo -e "${GREEN}✓ 技能脚本已复制到 $PROJECT_DIR/scripts/${NC}"
echo -e "${GREEN}✓ Codex Bridge: $PROJECT_DIR/scripts/codex_bridge.py${NC}"
echo -e "${GREEN}✓ Gemini Bridge: $PROJECT_DIR/scripts/gemini_bridge.py${NC}"
echo ""
echo -e "${YELLOW}使用示例:${NC}"
echo "codex: python scripts/codex_bridge.py --cd \"$PROJECT_DIR\" --PROMPT \"你的任务\""
echo "gemini: python scripts/gemini_bridge.py --cd \"$PROJECT_DIR\" --PROMPT \"你的任务\""