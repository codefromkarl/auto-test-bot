# Workflow DSL v1

## 约束
- 线性执行
- 无条件分支 / 并行
- Action 原子化

## 示例
```yaml
workflow:
  name: nowhi_text_to_video
  phases:
    - name: navigation
      steps:
        - open_page:
            url: http://example.com
        - click:
            selector: "text=AI创作"
```
