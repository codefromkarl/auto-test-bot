#!/bin/bash

# Create new run record for NH-REG-001
# Usage: ./scripts/create_run.sh [spec_id] [date]

SPEC_ID=${1:-"NH-REG-001"}
DATE=${2:-$(date +%Y-%m-%d)}
RUN_DIR="runs/${DATE}"
RUN_FILE="${RUN_DIR}/${SPEC_ID}-run.md"

# Create run directory
mkdir -p "$RUN_DIR"

# Get current git commit
COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")

# Get current user
EXECUTOR=${USER:-"unknown"}

# Create run file with template
cat > "$RUN_FILE" << EOF
Spec: ${SPEC_ID}
Date: ${DATE}
Commit: ${COMMIT}
Env: local
Executor: ${EXECUTOR}

## Scope
- workflow: naohai_regression
- robot tag: naohai_smoke

## Commands
\`\`\`bash
python src/main_workflow.py --spec ${SPEC_ID}
\`\`\`

## Results

* pass:
* fail:
* report: ./report.html
* logs: ./logs.txt

## Deviations

*

EOF

echo "Created new run file: ${RUN_FILE}"
echo "Please update the Results section after test execution."