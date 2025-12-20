#!/usr/bin/env python3
"""
Data-TestId 覆盖率 CI 验证脚本

用于 CI/CD 流程中验证 data-testid 覆盖率是否达标。
"""

import sys
import json
import yaml
import argparse
from pathlib import Path
from typing import Dict, List, Any


class TestIdCoverageValidator:
    """Data-TestId 覆盖率验证器"""

    def __init__(self, config_file: str = None, report_file: str = None):
        """
        初始化验证器

        Args:
            config_file: 契约配置文件路径
            report_file: 测试报告文件路径
        """
        self.config_file = config_file or "config/required_testids.yaml"
        self.report_file = report_file
        self.required_config = self._load_required_config()
        self.test_report = self._load_test_report() if report_file else None

    def _load_required_config(self) -> Dict[str, Any]:
        """加载必需的 testid 配置"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"❌ 无法加载契约配置文件 {self.config_file}: {e}")
            sys.exit(1)

    def _load_test_report(self) -> Dict[str, Any]:
        """加载测试报告"""
        try:
            with open(self.report_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  无法加载测试报告文件 {self.report_file}: {e}")
            return None

    def validate_from_report(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        从测试报告验证覆盖率

        Args:
            report_data: 测试报告数据

        Returns:
            Dict[str, Any]: 验证结果
        """
        # 提取定位器度量数据
        locator_metrics = report_data.get('locator_metrics', {})
        if not locator_metrics:
            return self._create_failure_result("测试报告中缺少定位器度量数据")

        # 获取覆盖率数据
        required_coverage = locator_metrics.get('required_testids_coverage', {})
        data_testid_hit_rate = locator_metrics.get('data_testid_hit_rate', 0)
        fallback_rate = locator_metrics.get('fallback_rate', 0)

        # 获取 CI 门禁配置
        ci_gates = self.required_config.get('ci_gates', {})

        # 验证结果
        validation_result = {
            'passed': True,
            'failures': [],
            'warnings': [],
            'metrics': locator_metrics
        }

        # 检查整体命中率
        min_coverage = ci_gates.get('overall_coverage_min', 80)
        if data_testid_hit_rate < min_coverage:
            validation_result['passed'] = False
            validation_result['failures'].append(
                f"🔴 data-testid 命中率 {data_testid_hit_rate}% 低于要求 {min_coverage}%"
            )

        # 检查回退率
        max_fallback = ci_gates.get('fallback_rate_max', 20)
        if fallback_rate > max_fallback:
            validation_result['passed'] = False
            validation_result['failures'].append(
                f"🔴 回退率 {fallback_rate}% 超过限制 {max_fallback}%"
            )

        # 检查关键路径覆盖率
        critical_paths = ci_gates.get('critical_paths', [])
        for path in critical_paths:
            path_coverage = required_coverage.get(path, {})
            coverage_rate = path_coverage.get('coverage_rate', 0)
            covered = path_coverage.get('covered', 0)
            required = path_coverage.get('required', 0)

            if coverage_rate < 100:
                validation_result['passed'] = False
                validation_result['failures'].append(
                    f"🔴 {path} 关键路径覆盖率 {coverage_rate}% 未达标 ({covered}/{required})"
                )
            elif coverage_rate < 100:  # 即使100%也要检查是否有遗漏
                missing_count = required - covered
                if missing_count > 0:
                    validation_result['warnings'].append(
                        f"🟡 {path} 仍有 {missing_count} 个必需元素未通过 data-testid 命中"
                    )

        return validation_result

    def validate_from_direct_check(self, testid_list: List[str]) -> Dict[str, Any]:
        """
        直接从 testid 列表验证覆盖率

        Args:
            testid_list: 实际存在的 testid 列表

        Returns:
            Dict[str, Any]: 验证结果
        """
        actual_testids = set(testid_list)
        validation_result = {
            'passed': True,
            'failures': [],
            'warnings': [],
            'missing_elements': {},
            'coverage_details': {}
        }

        # 检查每个类别
        categories = ['navigation', 'text_image_flow', 'video_flow', 'ai_create_page']

        for category in categories:
            if category not in self.required_config:
                continue

            required_testids = self.required_config[category].get('required', [])
            requirement = self.required_config[category].get('coverage_requirement', 100)

            # 计算覆盖率
            covered = sum(1 for testid in required_testids if testid in actual_testids)
            total = len(required_testids)
            coverage_rate = round(covered / total * 100, 2) if total > 0 else 0

            validation_result['coverage_details'][category] = {
                'required': total,
                'covered': covered,
                'coverage_rate': coverage_rate,
                'requirement': requirement
            }

            # 检查是否满足要求
            if coverage_rate < requirement:
                validation_result['passed'] = False
                validation_result['failures'].append(
                    f"🔴 {category} 覆盖率 {coverage_rate}% 低于要求 {requirement}% ({covered}/{total})"
                )

            # 记录缺失的元素
            missing = [testid for testid in required_testids if testid not in actual_testids]
            if missing:
                validation_result['missing_elements'][category] = missing

        return validation_result

    def _create_failure_result(self, message: str) -> Dict[str, Any]:
        """创建失败结果"""
        return {
            'passed': False,
            'failures': [message],
            'warnings': [],
            'metrics': {},
            'coverage_details': {}
        }

    def generate_report(self, validation_result: Dict[str, Any]) -> str:
        """
        生成验证报告

        Args:
            validation_result: 验证结果

        Returns:
            str: 格式化的报告文本
        """
        lines = []

        # 标题
        lines.append("📊 Data-TestId 覆盖率 CI 验证报告")
        lines.append("=" * 50)
        lines.append("")

        # 验证结果
        if validation_result['passed']:
            lines.append("✅ 验证通过！所有门禁条件都满足。")
        else:
            lines.append("❌ 验证失败！存在不满足的门禁条件。")

        lines.append("")

        # 失败信息
        if validation_result['failures']:
            lines.append("🔴 失败项:")
            for failure in validation_result['failures']:
                lines.append(f"  • {failure}")
            lines.append("")

        # 警告信息
        if validation_result['warnings']:
            lines.append("🟡 警告项:")
            for warning in validation_result['warnings']:
                lines.append(f"  • {warning}")
            lines.append("")

        # 覆盖率详情
        if 'coverage_details' in validation_result:
            lines.append("📈 覆盖率详情:")
            for category, details in validation_result['coverage_details'].items():
                lines.append(f"  {category}:")
                lines.append(f"    覆盖率: {details['coverage_rate']}% "
                            f"({details['covered']}/{details['required']}) "
                            f"[要求: {details['requirement']}%]")
            lines.append("")

        # 缺失元素
        if validation_result.get('missing_elements'):
            lines.append("🔍 缺失的必需元素:")
            for category, missing in validation_result['missing_elements'].items():
                lines.append(f"  {category}:")
                for testid in missing:
                    lines.append(f"    • {testid}")
            lines.append("")

        # 修复建议
        lines.append("🛠️ 修复建议:")
        lines.append("  1. 为缺失的关键元素添加对应的 data-testid")
        lines.append("  2. 确保 data-testid 命名符合契约要求")
        lines.append("  3. 更新 required_testids.yaml 如果有新增关键流程")
        lines.append("  4. 运行本地验证确保修改有效")
        lines.append("")

        return "\n".join(lines)

    def save_validation_result(self, validation_result: Dict[str, Any], output_file: str):
        """
        保存验证结果到文件

        Args:
            validation_result: 验证结果
            output_file: 输出文件路径
        """
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(validation_result, f, indent=2, ensure_ascii=False)
            print(f"📄 验证结果已保存到: {output_file}")
        except Exception as e:
            print(f"❌ 保存验证结果失败: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Data-TestId 覆盖率 CI 验证')
    parser.add_argument('--config', default='config/required_testids.yaml',
                    help='契约配置文件路径')
    parser.add_argument('--report', help='测试报告文件路径')
    parser.add_argument('--testids', help='实际 testid 列表 (JSON格式)')
    parser.add_argument('--output', default='reports/testid_validation.json',
                    help='验证结果输出文件')
    parser.add_argument('--verbose', '-v', action='store_true',
                    help='详细输出')

    args = parser.parse_args()

    # 创建验证器
    validator = TestIdCoverageValidator(args.config, args.report)

    # 执行验证
    if args.report:
        # 从测试报告验证
        if not args.test_report:
            print(f"❌ 无法加载测试报告: {args.report}")
            sys.exit(1)

        validation_result = validator.validate_from_report(args.test_report)
    elif args.testids:
        # 从 testid 列表验证
        try:
            testid_list = json.loads(args.testids)
            validation_result = validator.validate_from_direct_check(testid_list)
        except json.JSONDecodeError as e:
            print(f"❌ 无效的 testid JSON: {e}")
            sys.exit(1)
    else:
        print("❌ 必须提供 --report 或 --testids 参数")
        parser.print_help()
        sys.exit(1)

    # 生成报告
    report_text = validator.generate_report(validation_result)
    print(report_text)

    # 保存结果
    validator.save_validation_result(validation_result, args.output)

    # 返回退出码
    if validation_result['passed']:
        print("🎉 CI 验证通过!")
        sys.exit(0)
    else:
        print("💥 CI 验证失败，请修复后重试!")
        sys.exit(1)


if __name__ == '__main__':
    main()