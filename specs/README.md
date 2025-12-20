# 方案 A 实施说明

## 概述

本实施完全按照**方案 A（本地 Runbook + Git 引用）**，提供 GitHub Issues 不膨胀、Run/Evidence 不丢失、Bug 可追溯的回归测试管理体系。

## 目录结构

```
repo/
├─ specs/              # 稳定的流程规范（长期）
│  ├─ README.md        # 本说明文件
│  └─ NH-REG-001.md    # 闹海回归测试规范
├─ runs/               # 事实记录（高频）
│  └─ 2025-03-08/
│     ├─ NH-REG-001-run.md
│     ├─ report.html
│     └─ logs.txt
└─ scripts/
   └─ create_run.sh    # 辅助脚本
```

## 使用流程

### 1. 执行回归测试

#### 方法一：使用辅助脚本（推荐）
```bash
# 创建今天的 run 记录
./scripts/create_run.sh

# 手动执行测试
python src/main_workflow.py --spec NH-REG-001

# 拷贝产物到 run 目录
cp report.html runs/$(date +%Y-%m-%d)/
cp logs.txt runs/$(date +%Y-%m-%d)/

# 提交到 Git
git add runs/$(date +%Y-%m-%d)/
git commit -m "run(NH-REG-001): daily regression $(date +%Y-%m-%d)"
```

#### 方法二：手动创建
```bash
# 创建今日目录
mkdir -p runs/$(date +%Y-%m-%d)

# 复制模板并修改
cp runs/2025-03-08/NH-REG-001-run.md runs/$(date +%Y-%m-%d)/

# 更新 run.md 中的 Results 部分
```

### 2. 测试结果处理

#### ✅ 测试通过（最常见）
- 只提交到 Git，无需创建 GitHub Issue
- 运行：`git commit -m "run(NH-REG-001): daily regression $(date +%Y-%m-%d)"`

#### ❌ 测试失败
1. **先保证 Run 完整**（确保 run.md、report、logs 都已生成）
2. **创建 Bug Issue**，在 Issue 中引用：
   ```markdown
   Evidence:
   - runs/2025-03-08/NH-REG-001-run.md
   ```

## 规范说明

### 文件命名规范
- **Spec 文件**：`specs/NH-{ID}-{TYPE}.md`
- **Run 文件**：`runs/YYYY-MM-DD/NH-{ID}-{TYPE}-run.md`
- **Commit message**：`run(NH-{ID}): description YYYY-MM-DD`

### Git 使用规范
- **runs/ 目录**：不 squash、不 rebase、不 amend
- **只追加历史**：保持完整的审计轨迹
- **标准 commit**：便于后续查询历史

### Deviation 记录
在 Run 文件中的 `## Deviations` 部分记录与 Spec 的差异：
- `none`：完全符合规范
- 具体描述：记录偏差内容，用于后续 Bug 分析

## 快速参考

### 常用命令
```bash
# 创建新 run 记录
./scripts/create_run.sh NH-REG-001 2025-03-08

# 查看最近的执行历史
git log --oneline --grep="run(NH-REG-001)"

# 查找某一天的执行记录
find runs/ -name "*run.md" -path "*/2025-03-08/*"
```

### Spec 映射关系
- **Spec ID**：NH-REG-001
- **Workflow**：workflows/naohai.yml
- **Robot tags**：naohai_smoke, naohai_regression
- **Entry point**：python src/main_workflow.py

## 验证清单

每次执行回归测试后确认：
- [ ] Run 文件已创建并更新 Results
- [ ] report.html 和 logs.txt 已拷贝到同目录
- [ ] Git 已提交，使用标准 commit message
- [ ] 如有失败，Bug Issue 已引用对应 Run 文件

这个体系实现了**用 5 分钟换来了 Issues 干净、Bug 可追溯、Spec 可证明、历史不丢**的工程价值。