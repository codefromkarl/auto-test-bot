import yaml
import sys

try:
    with open("config/config.yaml", 'r', encoding='utf-8') as f:
        content = f.read()
        print(f"File length: {len(content)}")
        yaml.safe_load(content)
    print("YAML is valid.")
except yaml.YAMLError as exc:
    print(f"YAML Error: {exc}")
    if hasattr(exc, 'problem_mark'):
        mark = exc.problem_mark
        print(f"Error position: line {mark.line+1}, column {mark.column+1}")
        
        # Print context
        lines = content.splitlines()
        start = max(0, mark.line - 5)
        end = min(len(lines), mark.line + 5)
        for i in range(start, end):
            prefix = ">> " if i == mark.line else "   "
            print(f"{prefix}{i+1}: {lines[i]}")
