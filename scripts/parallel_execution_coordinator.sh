#!/bin/bash

# 闹海测试工作流 - 并行执行协调脚本
# UI/前端测试 -> Gemini, 功能/逻辑测试 -> Codex, Claude 协调

set -e

# 配置参数
PROJECT_DIR="/home/yuanzhi/Develop/NowHi/auto-test-bot"
LOGS_DIR="${PROJECT_DIR}/logs/parallel_execution"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# 创建日志目录
mkdir -p "${LOGS_DIR}"

echo "=== 闹海测试工作流 - 并行任务分配执行 ==="
echo "开始时间: $(date)"
echo "项目目录: ${PROJECT_DIR}"
echo "日志目录: ${LOGS_DIR}"
echo ""

# 任务1: UI/前端测试 - Gemini负责
echo "🎨 任务组1: UI/前端测试 (Gemini)"
echo "包含内容:"
echo "  - FC-NH-051到060: UI元素存在性和可见性验证"
echo "  - 页面加载和渲染测试"
echo "  - DOM结构验证"
echo "  - 前端样式检查"
echo ""

# 任务2: 核心功能测试 - Codex负责
echo "⚙️ 任务组2: 核心功能测试 (Codex)"
echo "包含内容:"
echo "  - FC-NH-002到050: 功能逻辑测试"
echo "  - 剧本管理、分集管理、角色管理等"
echo "  - 资源绑定、视频制作功能"
echo ""

# 任务3: 端到端测试 - Codex负责
echo "🔄 任务组3: 端到端业务流程 (Codex)"
echo "包含内容:"
echo "  - E2E黄金路径测试: 7阶段完整业务流程"
echo "  - 从剧本创建到视频导出的用户旅程"
echo ""

# 函数: 执行Gemini任务
execute_gemini_tasks() {
    echo "🚀 启动Gemini UI测试任务..."
    cd "${PROJECT_DIR}"

    # 使用Gemini执行UI测试任务
    gemini -p "
PURPOSE: 执行闹海项目UI和前端测试验证
TASK:
• 执行FC-NH-051到060系列UI元素验证测试
• 验证页面加载和DOM结构完整性
• 检查前端样式和页面渲染效果
• 生成详细的UI测试报告，包含截图和元素状态
MODE: write
CONTEXT: @workflows/fc/naohai_FC_NH_05*.yaml @workflows/fc/naohai_FC_NH_06*.yaml @config/config.yaml
EXPECTED: 完整的UI测试执行报告，包含元素存在性验证、页面截图、测试通过率统计
RULES: $(cat ~/.claude/workflows/cli-templates/prompts/analysis/02-analyze-code-patterns.txt) | 专注于UI元素验证和前端分析 | write=CREATE/MODIFY/DELETE
" --approval-mode yolo > "${LOGS_DIR}/gemini_ui_tasks_${TIMESTAMP}.log" 2>&1 &

    GEMINI_PID=$!
    echo "Gemini任务 PID: ${GEMINI_PID}"
    echo "${GEMINI_PID}" > "${LOGS_DIR}/gemini.pid"
}

# 函数: 执行Codex功能测试任务
execute_codex_functional_tasks() {
    echo "⚙️ 启动Codex功能测试任务..."
    cd "${PROJECT_DIR}"

    # 使用Codex执行功能测试
    codex -C "${PROJECT_DIR}" --full-auto exec "
PURPOSE: 执行闹海项目核心功能和业务逻辑测试
TASK:
• 执行FC-NH-002到050系列功能测试用例
• 覆盖剧本管理、分集管理、角色管理、场景管理等核心功能
• 测试分镜管理、资源绑定、视频制作等关键业务流程
• 验证数据操作、API调用、错误处理等逻辑正确性
MODE: auto
CONTEXT: @workflows/fc/naohai_FC_NH_0[2-4][0-9].yaml @workflows/fc/naohai_FC_NH_05[0].yaml @config/config.yaml @src/
EXPECTED: 详细的功能测试报告，包含各模块测试结果、业务流程验证状态、错误处理验证
RULES: $(cat ~/.claude/workflows/cli-templates/prompts/development/02-implement-feature.txt) | 专注于功能逻辑和业务流程验证 | auto=FULL operations
" --skip-git-repo-check -s danger-full-access > "${LOGS_DIR}/codex_functional_${TIMESTAMP}.log" 2>&1 &

    CODEX_FUNC_PID=$!
    echo "Codex功能测试 PID: ${CODEX_FUNC_PID}"
    echo "${CODEX_FUNC_PID}" > "${LOGS_DIR}/codex_functional.pid"
}

# 函数: 执行Codex E2E测试任务
execute_codex_e2e_tasks() {
    echo "🔄 启动Codex E2E测试任务..."
    cd "${PROJECT_DIR}"

    # 使用Codex执行E2E测试
    codex -C "${PROJECT_DIR}" --full-auto exec "
PURPOSE: 执行闹海项目端到端业务流程测试
TASK:
• 执行E2E黄金路径测试，验证完整的7阶段业务流程
• 测试从剧本创建到视频导出的完整用户旅程
• 验证各阶段间的数据流转和状态一致性
• 测试性能表现和错误恢复机制
MODE: auto
CONTEXT: @workflows/e2e/naohai_E2E_GoldenPath.yaml @config/e2e_config.yaml @config/config.yaml @src/
EXPECTED: 完整的E2E测试报告，包含各阶段执行结果、性能数据、业务流程完整性验证
RULES: $(cat ~/.claude/workflows/cli-templates/prompts/development/02-implement-feature.txt) | 专注于端到端业务流程和用户体验验证 | auto=FULL operations
" --skip-git-repo-check -s danger-full-access > "${LOGS_DIR}/codex_e2e_${TIMESTAMP}.log" 2>&1 &

    CODEX_E2E_PID=$!
    echo "Codex E2E测试 PID: ${CODEX_E2E_PID}"
    echo "${CODEX_E2E_PID}" > "${LOGS_DIR}/codex_e2e.pid"
}

# 函数: 监控任务状态
monitor_tasks() {
    echo "📊 开始监控任务执行状态..."

    while true; do
        all_finished=true

        # 检查Gemini任务
        if [ -f "${LOGS_DIR}/gemini.pid" ]; then
            gemini_pid=$(cat "${LOGS_DIR}/gemini.pid")
            if ps -p $gemini_pid > /dev/null 2>&1; then
                echo "🎨 Gemini UI测试: 执行中 (PID: $gemini_pid)"
                all_finished=false
            else
                echo "✅ Gemini UI测试: 已完成"
            fi
        fi

        # 检查Codex功能测试任务
        if [ -f "${LOGS_DIR}/codex_functional.pid" ]; then
            codex_func_pid=$(cat "${LOGS_DIR}/codex_functional.pid")
            if ps -p $codex_func_pid > /dev/null 2>&1; then
                echo "⚙️ Codex功能测试: 执行中 (PID: $codex_func_pid)"
                all_finished=false
            else
                echo "✅ Codex功能测试: 已完成"
            fi
        fi

        # 检查Codex E2E测试任务
        if [ -f "${LOGS_DIR}/codex_e2e.pid" ]; then
            codex_e2e_pid=$(cat "${LOGS_DIR}/codex_e2e.pid")
            if ps -p $codex_e2e_pid > /dev/null 2>&1; then
                echo "🔄 Codex E2E测试: 执行中 (PID: $codex_e2e_pid)"
                all_finished=false
            else
                echo "✅ Codex E2E测试: 已完成"
            fi
        fi

        if [ "$all_finished" = true ]; then
            echo ""
            echo "🎉 所有任务执行完成!"
            break
        fi

        echo "--- $(date) ---"
        sleep 30  # 每30秒检查一次
    done
}

# 函数: 生成最终报告
generate_final_report() {
    echo ""
    echo "📋 生成最终执行报告..."

    REPORT_FILE="${LOGS_DIR}/final_report_${TIMESTAMP}.md"

    cat > "${REPORT_FILE}" << EOF
# 闹海测试工作流 - 并行执行报告

## 执行概要
- **开始时间**: $(date)
- **项目目录**: ${PROJECT_DIR}
- **执行方式**: 并行任务分配 (Gemini + Codex + Claude协调)

## 任务分配详情

### 🎨 任务组1: UI/前端测试 (Gemini负责)
- **测试范围**: FC-NH-051到060系列UI验证
- **执行日志**: ${LOGS_DIR}/gemini_ui_tasks_${TIMESTAMP}.log
- **状态**: $([ -f "${LOGS_DIR}/gemini.pid" ] && (ps -p $(cat "${LOGS_DIR}/gemini.pid") > /dev/null 2>&1 && echo "执行中" || echo "已完成") || echo "未启动")

### ⚙️ 任务组2: 核心功能测试 (Codex负责)
- **测试范围**: FC-NH-002到050功能逻辑测试
- **执行日志**: ${LOGS_DIR}/codex_functional_${TIMESTAMP}.log
- **状态**: $([ -f "${LOGS_DIR}/codex_functional.pid" ] && (ps -p $(cat "${LOGS_DIR}/codex_functional.pid") > /dev/null 2>&1 && echo "执行中" || echo "已完成") || echo "未启动")

### 🔄 任务组3: 端到端测试 (Codex负责)
- **测试范围**: E2E黄金路径7阶段业务流程
- **执行日志**: ${LOGS_DIR}/codex_e2e_${TIMESTAMP}.log
- **状态**: $([ -f "${LOGS_DIR}/codex_e2e.pid" ] && (ps -p $(cat "${LOGS_DIR}/codex_e2e.pid") > /dev/null 2>&1 && echo "执行中" || echo "已完成") || echo "未启动")

## 执行日志摘要
$(find "${LOGS_DIR}" -name "*_${TIMESTAMP}.log" -exec basename {} \; | sed 's/^/- /')

## 后续行动
1. 检查各任务组的详细执行日志
2. 分析测试结果和失败案例
3. 汇总测试覆盖率和质量指标
4. 生成测试趋势报告

---

*报告生成时间: $(date)*
EOF

    echo "📄 最终报告已生成: ${REPORT_FILE}"
}

# 主执行流程
main() {
    echo "开始执行闹海测试工作流..."

    # 启动所有并行任务
    execute_gemini_tasks &
    sleep 5  # 错开启动时间

    execute_codex_functional_tasks &
    sleep 5

    execute_codex_e2e_tasks &
    sleep 5

    echo ""
    echo "🎯 所有任务已启动，开始监控执行状态..."

    # 监控任务执行
    monitor_tasks

    # 生成最终报告
    generate_final_report

    echo ""
    echo "🏁 闹海测试工作流执行完成!"
    echo "详细日志位置: ${LOGS_DIR}"
}

# 执行主函数
main