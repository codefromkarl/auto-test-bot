#!/usr/bin/env python3
"""
回归测试套件执行器
Regression Test Suite Runner

支持增量回归、全量回归、基线对比等多种测试模式
"""

import os
import sys
import argparse
import yaml
import json
import logging
import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.config_loader import ConfigLoader
from src.utils.timer import Timer
from src.reporter.formatter import Reporter


@dataclass
class RegressionConfig:
    """回归测试配置"""
    suite_type: str  # 'incremental' | 'full' | 'baseline'
    categories: List[str]
    parallel: bool
    workers: int
    baseline_version: Optional[str] = None
    update_baseline: bool = False
    output_format: str = 'both'  # 'html' | 'json' | 'both'


class RegressionSuite:
    """回归测试套件主类"""

    def __init__(self, config: RegressionConfig):
        self.config = config
        self.logger = self._setup_logging()
        self.base_dir = Path(__file__).parent.parent
        self.workflows_dir = self.base_dir / "workflows" / "rt"
        self.shared_config = self._load_shared_config()
        self.results = {}

    def _setup_logging(self) -> logging.Logger:
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('test_artifacts/regression/regression.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)

    def _load_shared_config(self) -> Dict[str, Any]:
        """加载共享配置"""
        config_path = self.workflows_dir / "shared" / "config.yaml"
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return {}

    def discover_tests(self) -> List[Path]:
        """发现测试用例"""
        tests = []

        for category in self.config.categories:
            category_dir = self.workflows_dir / category
            if not category_dir.exists():
                self.logger.warning(f"Category directory not found: {category_dir}")
                continue

            for yaml_file in category_dir.glob("*.yaml"):
                tests.append(yaml_file)

        return tests

    def load_test_case(self, test_path: Path) -> Dict[str, Any]:
        """加载测试用例"""
        with open(test_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def execute_test(self, test_path: Path) -> Dict[str, Any]:
        """执行单个测试用例"""
        test_name = test_path.stem
        self.logger.info(f"Executing test: {test_name}")

        try:
            test_case = self.load_test_case(test_path)

            # 创建测试结果结构
            result = {
                'test_name': test_name,
                'test_path': str(test_path),
                'category': test_path.parent.name,
                'start_time': datetime.datetime.now().isoformat(),
                'status': 'running',
                'steps': [],
                'metrics': {},
                'issues': []
            }

            # 执行测试步骤
            with Timer() as timer:
                for step in test_case.get('test_cases', []):
                    step_result = self._execute_step(step)
                    result['steps'].append(step_result)

                    if step_result.get('status') == 'failed':
                        result['status'] = 'failed'
                        break
                else:
                    result['status'] = 'passed'

            result['duration'] = timer.duration

            # 收集性能指标
            result['metrics'] = self._collect_metrics(test_case)

            # 检测回归
            if self.config.baseline_version:
                result['regression'] = self._detect_regression(
                    result, test_case, self.config.baseline_version
                )

            return result

        except Exception as e:
            self.logger.error(f"Test execution failed: {test_name}", exc_info=True)
            return {
                'test_name': test_name,
                'test_path': str(test_path),
                'status': 'error',
                'error': str(e),
                'start_time': datetime.datetime.now().isoformat()
            }

    def _execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """执行测试步骤"""
        # 这里需要根据实际的测试框架来实现
        # 目前返回模拟结果
        return {
            'name': step.get('name', 'unknown'),
            'action': step.get('action', 'unknown'),
            'status': 'passed',
            'duration': 1.0,
            'details': 'Step executed successfully'
        }

    def _collect_metrics(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """收集性能指标"""
        # 这里需要集成实际的性能监控
        return {
            'response_time': 2.5,
            'memory_usage': 45.2,
            'cpu_usage': 23.1
        }

    def _detect_regression(
        self,
        result: Dict[str, Any],
        test_case: Dict[str, Any],
        baseline_version: str
    ) -> Dict[str, Any]:
        """检测回归"""
        # 这里需要加载基线数据并进行对比
        return {
            'detected': False,
            'performance_regression': [],
            'functional_regression': []
        }

    def run(self) -> Dict[str, Any]:
        """运行回归测试套件"""
        self.logger.info(f"Starting regression suite: {self.config.suite_type}")

        # 发现测试用例
        test_files = self.discover_tests()
        if not test_files:
            self.logger.warning("No test files found")
            return {'status': 'no_tests'}

        self.logger.info(f"Found {len(test_files)} test files")

        # 执行测试
        if self.config.parallel and self.config.workers > 1:
            results = self._run_parallel(test_files)
        else:
            results = self._run_sequential(test_files)

        # 生成报告
        suite_result = {
            'suite_type': self.config.suite_type,
            'config': self.config.__dict__,
            'start_time': datetime.datetime.now().isoformat(),
            'total_tests': len(test_files),
            'results': results,
            'summary': self._generate_summary(results)
        }

        # 更新基线
        if self.config.update_baseline:
            self._update_baseline(results)

        # 生成报告文件
        self._generate_reports(suite_result)

        return suite_result

    def _run_parallel(self, test_files: List[Path]) -> List[Dict[str, Any]]:
        """并行执行测试"""
        results = []

        with ThreadPoolExecutor(max_workers=self.config.workers) as executor:
            future_to_file = {
                executor.submit(self.execute_test, test_file): test_file
                for test_file in test_files
            }

            for future in as_completed(future_to_file):
                test_file = future_to_file[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"Test failed: {test_file}", exc_info=True)
                    results.append({
                        'test_name': test_file.stem,
                        'test_path': str(test_file),
                        'status': 'error',
                        'error': str(e)
                    })

        return results

    def _run_sequential(self, test_files: List[Path]) -> List[Dict[str, Any]]:
        """顺序执行测试"""
        results = []

        for test_file in test_files:
            result = self.execute_test(test_file)
            results.append(result)

        return results

    def _generate_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成测试摘要"""
        total = len(results)
        passed = sum(1 for r in results if r.get('status') == 'passed')
        failed = sum(1 for r in results if r.get('status') == 'failed')
        errors = sum(1 for r in results if r.get('status') == 'error')

        return {
            'total': total,
            'passed': passed,
            'failed': failed,
            'errors': errors,
            'success_rate': (passed / total * 100) if total > 0 else 0,
            'categories': self._summarize_by_category(results)
        }

    def _summarize_by_category(self, results: List[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
        """按类别汇总"""
        categories = {}

        for result in results:
            category = result.get('category', 'unknown')
            if category not in categories:
                categories[category] = {'total': 0, 'passed': 0, 'failed': 0, 'errors': 0}

            categories[category]['total'] += 1
            status = result.get('status', 'unknown')
            if status in categories[category]:
                categories[category][status] += 1

        return categories

    def _update_baseline(self, results: List[Dict[str, Any]) -> None:
        """更新基线数据"""
        baseline_dir = Path(self.shared_config.get('baseline', {}).get('storage_path', 'test_artifacts/regression/baselines'))
        baseline_dir.mkdir(parents=True, exist_ok=True)

        version = datetime.datetime.now().strftime('%Y.%m.%d')
        baseline_file = baseline_dir / f"baseline_{version}.json"

        with open(baseline_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        self.logger.info(f"Baseline updated: {baseline_file}")

    def _generate_reports(self, suite_result: Dict[str, Any]) -> None:
        """生成测试报告"""
        output_dir = Path(self.shared_config.get('reporting', {}).get('output_dir', 'test_artifacts/regression/reports'))
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

        if self.config.output_format in ['json', 'both']:
            json_file = output_dir / f"regression_report_{timestamp}.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(suite_result, f, indent=2, ensure_ascii=False)

        if self.config.output_format in ['html', 'both']:
            html_file = output_dir / f"regression_report_{timestamp}.html"
            self._generate_html_report(suite_result, html_file)

    def _generate_html_report(self, suite_result: Dict[str, Any], output_path: Path) -> None:
        """生成HTML报告"""
        # 这里需要实现HTML报告生成逻辑
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>回归测试报告</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .summary {{ background: #f5f5f5; padding: 15px; border-radius: 5px; }}
                .test-result {{ margin: 10px 0; padding: 10px; border-left: 4px solid #ccc; }}
                .passed {{ border-left-color: #4CAF50; }}
                .failed {{ border-left-color: #f44336; }}
                .error {{ border-left-color: #ff9800; }}
            </style>
        </head>
        <body>
            <h1>回归测试报告</h1>
            <div class="summary">
                <h2>测试摘要</h2>
                <p>总计: {suite_result['summary']['total']}</p>
                <p>通过: {suite_result['summary']['passed']}</p>
                <p>失败: {suite_result['summary']['failed']}</p>
                <p>错误: {suite_result['summary']['errors']}</p>
                <p>成功率: {suite_result['summary']['success_rate']:.2f}%</p>
            </div>
        </body>
        </html>
        """

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='运行回归测试套件')

    parser.add_argument(
        '--type',
        choices=['incremental', 'full', 'baseline'],
        default='incremental',
        help='测试类型'
    )

    parser.add_argument(
        '--categories',
        nargs='+',
        default=['core', 'performance'],
        help='测试类别'
    )

    parser.add_argument(
        '--parallel',
        action='store_true',
        help='并行执行'
    )

    parser.add_argument(
        '--workers',
        type=int,
        default=4,
        help='并行工作线程数'
    )

    parser.add_argument(
        '--baseline',
        help='基线版本'
    )

    parser.add_argument(
        '--update-baseline',
        action='store_true',
        help='更新基线'
    )

    parser.add_argument(
        '--format',
        choices=['html', 'json', 'both'],
        default='both',
        help='报告格式'
    )

    args = parser.parse_args()

    # 创建配置
    config = RegressionConfig(
        suite_type=args.type,
        categories=args.categories,
        parallel=args.parallel,
        workers=args.workers,
        baseline_version=args.baseline,
        update_baseline=args.update_baseline,
        output_format=args.format
    )

    # 运行回归测试
    suite = RegressionSuite(config)
    result = suite.run()

    # 输出结果
    print(f"\n回归测试完成:")
    print(f"  总计: {result['summary']['total']}")
    print(f"  通过: {result['summary']['passed']}")
    print(f"  失败: {result['summary']['failed']}")
    print(f"  错误: {result['summary']['errors']}")
    print(f"  成功率: {result['summary']['success_rate']:.2f}%")

    # 设置退出码
    if result['summary']['failed'] > 0 or result['summary']['errors'] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()