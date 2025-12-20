#!/usr/bin/env python3
"""
E2E测试套件执行器
E2E Test Suite Runner

支持多种测试模式和验证策略的端到端测试执行
"""

import os
import sys
import argparse
import json
import yaml
import logging
import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.config_loader import ConfigLoader
from src.utils.timer import Timer
from src.reporter.formatter import Reporter
from src.validation.content_validator import ContentValidator


@dataclass
class E2ETestConfig:
    """E2E测试配置"""
    suite: str  # 'smoke' | 'functional' | 'regression' | 'stress'
    environment: str  # 'local' | 'staging' | 'production'
    parallel: bool
    max_workers: int
    with_validation: bool
    validation_level: str  # 'basic' | 'strict' | 'full'
    report_format: str  # 'html' | 'json' | 'junit' | 'all'
    output_dir: str
    test_data_dir: str
    config_file: str


class E2ETestSuite:
    """E2E测试套件主类"""

    def __init__(self, config: E2ETestConfig):
        self.config = config
        self.logger = self._setup_logging()
        self.base_dir = Path(__file__).parent.parent
        self.test_results = []
        self.start_time = None

        # 加载配置
        self._load_configs()

        # 初始化验证器
        if config.with_validation:
            self.validator = ContentValidator(
                config_path=self.base_dir / "config" / "validation_config.yaml"
            )
        else:
            self.validator = None

    def _setup_logging(self) -> logging.Logger:
        """设置日志"""
        log_file = Path(self.config.output_dir) / "e2e_test.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)

    def _load_configs(self):
        """加载配置文件"""
        # 加载E2E配置
        self.e2e_config = self._load_yaml(
            self.base_dir / "config" / f"{self.config.environment}_config.yaml"
        )

        # 加载测试配置
        self.test_config = self._load_yaml(
            self.base_dir / "config" / self.config.config_file
        )

        # 加载套件配置
        suite_config_path = self.base_dir / "workflows" / "e2e" / f"{self.config.suite}_suite.yaml"
        if suite_config_path.exists():
            self.suite_config = self._load_yaml(suite_config_path)
        else:
            self.suite_config = self._get_default_suite_config()

    def _load_yaml(self, path: Path) -> Dict[str, Any]:
        """加载YAML文件"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            self.logger.error(f"Failed to load config {path}: {str(e)}")
            return {}

    def _get_default_suite_config(self) -> Dict[str, Any]:
        """获取默认套件配置"""
        return {
            'test_cases': [],
            'parallel': self.config.parallel,
            'timeout': 300000,
            'retries': 2
        }

    def discover_tests(self) -> List[Path]:
        """发现测试用例"""
        test_files = []
        test_dir = self.base_dir / "workflows" / "e2e"

        if self.config.suite == "all":
            # 执行所有测试
            for yaml_file in test_dir.glob("*.yaml"):
                test_files.append(yaml_file)
        else:
            # 执行特定套件
            suite_file = test_dir / f"{self.config.suite}.yaml"
            if suite_file.exists():
                test_files.append(suite_file)

        return test_files

    def execute_test(self, test_path: Path) -> Dict[str, Any]:
        """执行单个测试用例"""
        test_name = test_path.stem
        self.logger.info(f"Executing E2E test: {test_name}")

        result = {
            'test_name': test_name,
            'test_path': str(test_path),
            'start_time': datetime.datetime.now().isoformat(),
            'status': 'running',
            'phases': [],
            'validation': None,
            'metrics': {},
            'artifacts': []
        }

        try:
            # 加载测试用例
            test_case = self._load_yaml(test_path)

            # 执行测试阶段
            with Timer() as timer:
                for phase in test_case.get('test_phases', []):
                    phase_result = self._execute_phase(phase)
                    result['phases'].append(phase_result)

                    # 如果阶段失败且配置为快速失败
                    if phase_result.get('status') == 'failed' and self.e2e_config.get('fail_fast', True):
                        result['status'] = 'failed'
                        break
                else:
                    result['status'] = 'passed'

            result['duration'] = timer.duration

            # 执行内容验证
            if self.validator and self.config.with_validation:
                result['validation'] = self._execute_validation(result)

            # 收集测试产物
            result['artifacts'] = self._collect_artifacts(test_name)

            # 收集性能指标
            result['metrics'] = self._collect_metrics(result)

        except Exception as e:
            self.logger.error(f"Test execution failed: {test_name}", exc_info=True)
            result['status'] = 'error'
            result['error'] = str(e)

        result['end_time'] = datetime.datetime.now().isoformat()
        return result

    def _execute_phase(self, phase: Dict[str, Any]) -> Dict[str, Any]:
        """执行测试阶段"""
        phase_name = phase.get('name', 'unknown')
        self.logger.info(f"Executing phase: {phase_name}")

        phase_result = {
            'name': phase_name,
            'steps': [],
            'status': 'passed',
            'start_time': datetime.datetime.now().isoformat()
        }

        # 执行步骤
        for step in phase.get('test_steps', []):
            step_result = self._execute_step(step)
            phase_result['steps'].append(step_result)

            # 如果步骤失败
            if step_result.get('status') == 'failed':
                phase_result['status'] = 'failed'
                break

        phase_result['end_time'] = datetime.datetime.now().isoformat()
        return phase_result

    def _execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """执行测试步骤"""
        # 这里需要集成实际的测试执行框架
        # 模拟执行结果
        return {
            'name': step.get('name', 'unknown'),
            'action': step.get('action', 'unknown'),
            'status': 'passed',
            'duration': 1.0,
            'details': f"Step {step.get('action', 'unknown')} executed"
        }

    def _execute_validation(self, test_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """执行内容验证"""
        if not self.validator:
            return None

        try:
            # 收集生成的内容
            content_paths = self._get_generated_content(test_result)

            if not content_paths:
                self.logger.warning("No content found for validation")
                return None

            # 执行验证
            prompt = self.test_config.get('test_prompt', '')
            context = self._get_validation_context(test_result)

            validation_report = self.validator.validate_content(
                content_paths=content_paths,
                expected_prompt=prompt,
                context=context
            )

            return {
                'status': 'passed' if validation_report.overall_score >= 70 else 'failed',
                'score': validation_report.overall_score,
                'details': validation_report.to_dict()
            }

        except Exception as e:
            self.logger.error(f"Validation failed: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }

    def _get_generated_content(self, test_result: Dict[str, Any]) -> Dict[str, List[str]]:
        """获取生成的内容路径"""
        # 这里需要从测试结果中提取生成的内容路径
        # 模拟返回
        return {
            'images': [f"output/{test_result['test_name']}_image_1.png"],
            'videos': [f"output/{test_result['test_name']}_video_1.mp4"]
        }

    def _get_validation_context(self, test_result: Dict[str, Any]) -> Dict[str, Any]:
        """获取验证上下文"""
        return {
            'test_name': test_result['test_name'],
            'environment': self.config.environment,
            'validation_level': self.config.validation_level
        }

    def _collect_artifacts(self, test_name: str) -> List[str]:
        """收集测试产物"""
        artifacts = []
        artifacts_dir = Path(self.config.output_dir) / test_name

        if artifacts_dir.exists():
            for artifact_path in artifacts_dir.rglob("*"):
                if artifact_path.is_file():
                    artifacts.append(str(artifact_path))

        return artifacts

    def _collect_metrics(self, test_result: Dict[str, Any]) -> Dict[str, Any]:
        """收集性能指标"""
        metrics = {
            'duration': test_result.get('duration', 0),
            'phases_count': len(test_result.get('phases', [])),
            'steps_count': sum(len(p.get('steps', [])) for p in test_result.get('phases', [])),
            'validation_score': None
        }

        if test_result.get('validation'):
            metrics['validation_score'] = test_result['validation'].get('score')

        return metrics

    def run(self) -> Dict[str, Any]:
        """运行E2E测试套件"""
        self.logger.info(f"Starting E2E test suite: {self.config.suite}")
        self.start_time = datetime.datetime.now()

        # 发现测试用例
        test_files = self.discover_tests()
        if not test_files:
            self.logger.warning("No test files found")
            return {'status': 'no_tests'}

        self.logger.info(f"Found {len(test_files)} test files")

        # 执行测试
        if self.config.parallel and self.config.max_workers > 1:
            results = self._run_parallel(test_files)
        else:
            results = self._run_sequential(test_files)

        self.test_results = results

        # 生成套件报告
        suite_result = {
            'suite': self.config.suite,
            'environment': self.config.environment,
            'config': self.config.__dict__,
            'start_time': self.start_time.isoformat(),
            'end_time': datetime.datetime.now().isoformat(),
            'total_tests': len(test_files),
            'results': results,
            'summary': self._generate_summary()
        }

        # 生成报告
        self._generate_reports(suite_result)

        return suite_result

    def _run_parallel(self, test_files: List[Path]) -> List[Dict[str, Any]]:
        """并行执行测试"""
        results = []

        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
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

    def _generate_summary(self) -> Dict[str, Any]:
        """生成测试摘要"""
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r.get('status') == 'passed')
        failed = sum(1 for r in self.test_results if r.get('status') == 'failed')
        errors = sum(1 for r in self.test_results if r.get('status') == 'error')

        # 计算平均验证分数
        validation_scores = [
            r.get('validation', {}).get('score')
            for r in self.test_results
            if r.get('validation') and r.get('validation').get('score') is not None
        ]
        avg_validation_score = sum(validation_scores) / len(validation_scores) if validation_scores else 0

        # 计算总执行时间
        total_duration = sum(r.get('duration', 0) for r in self.test_results)

        return {
            'total': total,
            'passed': passed,
            'failed': failed,
            'errors': errors,
            'success_rate': (passed / total * 100) if total > 0 else 0,
            'average_validation_score': avg_validation_score,
            'total_duration': total_duration,
            'validation_enabled': self.config.with_validation
        }

    def _generate_reports(self, suite_result: Dict[str, Any]):
        """生成测试报告"""
        output_dir = Path(self.config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

        # 生成JSON报告
        if self.config.report_format in ['json', 'all']:
            json_file = output_dir / f"e2e_report_{timestamp}.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(suite_result, f, indent=2, ensure_ascii=False)

        # 生成HTML报告
        if self.config.report_format in ['html', 'all']:
            html_file = output_dir / f"e2e_report_{timestamp}.html"
            self._generate_html_report(suite_result, html_file)

        # 生成JUnit报告
        if self.config.report_format in ['junit', 'all']:
            junit_file = output_dir / f"e2e_report_{timestamp}.xml"
            self._generate_junit_report(suite_result, junit_file)

        self.logger.info(f"Reports generated in {output_dir}")

    def _generate_html_report(self, suite_result: Dict[str, Any], output_path: Path):
        """生成HTML报告"""
        # 这里需要实现HTML报告生成逻辑
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>E2E测试报告 - {suite_result['suite']}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .summary {{ background: #f5f5f5; padding: 15px; border-radius: 5px; }}
                .test-result {{ margin: 10px 0; padding: 10px; border-left: 4px solid #ccc; }}
                .passed {{ border-left-color: #4CAF50; }}
                .failed {{ border-left-color: #f44336; }}
                .error {{ border-left-color: #ff9800; }}
                .metrics {{ display: flex; gap: 20px; margin: 10px 0; }}
                .metric {{ text-align: center; }}
            </style>
        </head>
        <body>
            <h1>E2E测试报告 - {suite_result['suite']}</h1>
            <div class="summary">
                <h2>测试摘要</h2>
                <div class="metrics">
                    <div class="metric">
                        <h3>{suite_result['summary']['total']}</h3>
                        <p>总计</p>
                    </div>
                    <div class="metric">
                        <h3>{suite_result['summary']['passed']}</h3>
                        <p>通过</p>
                    </div>
                    <div class="metric">
                        <h3>{suite_result['summary']['failed']}</h3>
                        <p>失败</p>
                    </div>
                    <div class="metric">
                        <h3>{suite_result['summary']['success_rate']:.2f}%</h3>
                        <p>成功率</p>
                    </div>
                    <div class="metric">
                        <h3>{suite_result['summary']['average_validation_score']:.2f}</h3>
                        <p>平均验证分</p>
                    </div>
                </div>
            </div>
            <h2>测试结果</h2>
            {self._generate_test_results_html(suite_result['results'])}
        </body>
        </html>
        """

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

    def _generate_test_results_html(self, results: List[Dict[str, Any]]) -> str:
        """生成测试结果HTML"""
        html = ""
        for result in results:
            status_class = result.get('status', 'unknown')
            html += f"""
            <div class="test-result {status_class}">
                <h3>{result.get('test_name', 'Unknown')}</h3>
                <p>状态: {result.get('status', 'Unknown')}</p>
                <p>时长: {result.get('duration', 0):.2f}秒</p>
                {f"<p>验证分数: {result.get('validation', {}).get('score', 'N/A')}</p>" if result.get('validation') else ""}
                {f"<p>错误: {result.get('error', '')}</p>" if result.get('error') else ""}
            </div>
            """
        return html

    def _generate_junit_report(self, suite_result: Dict[str, Any], output_path: Path):
        """生成JUnit XML报告"""
        # 这里需要实现JUnit XML生成逻辑
        pass


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='运行E2E测试套件')

    parser.add_argument(
        '--suite',
        choices=['smoke', 'functional', 'regression', 'stress', 'all'],
        default='smoke',
        help='测试套件类型'
    )

    parser.add_argument(
        '--environment',
        choices=['local', 'staging', 'production'],
        default='local',
        help='测试环境'
    )

    parser.add_argument(
        '--parallel',
        action='store_true',
        help='并行执行测试'
    )

    parser.add_argument(
        '--max-workers',
        type=int,
        default=4,
        help='最大工作线程数'
    )

    parser.add_argument(
        '--with-validation',
        action='store_true',
        help='启用内容验证'
    )

    parser.add_argument(
        '--validation-level',
        choices=['basic', 'strict', 'full'],
        default='basic',
        help='验证级别'
    )

    parser.add_argument(
        '--format',
        choices=['html', 'json', 'junit', 'all'],
        default='html',
        help='报告格式'
    )

    parser.add_argument(
        '--output-dir',
        default='test_artifacts/e2e',
        help='输出目录'
    )

    parser.add_argument(
        '--config',
        default='config.yaml',
        help='测试配置文件'
    )

    args = parser.parse_args()

    # 创建配置
    config = E2ETestConfig(
        suite=args.suite,
        environment=args.environment,
        parallel=args.parallel,
        max_workers=args.max_workers,
        with_validation=args.with_validation,
        validation_level=args.validation_level,
        report_format=args.format,
        output_dir=args.output_dir,
        test_data_dir='test_data',
        config_file=args.config
    )

    # 运行E2E测试
    suite = E2ETestSuite(config)
    result = suite.run()

    # 输出结果
    print(f"\nE2E测试完成:")
    print(f"  套件: {result['suite']}")
    print(f"  环境: {result['environment']}")
    print(f"  总计: {result['summary']['total']}")
    print(f"  通过: {result['summary']['passed']}")
    print(f"  失败: {result['summary']['failed']}")
    print(f"  错误: {result['summary']['errors']}")
    print(f"  成功率: {result['summary']['success_rate']:.2f}%")
    if result['summary']['validation_enabled']:
        print(f"  平均验证分: {result['summary']['average_validation_score']:.2f}")
    print(f"  总耗时: {result['summary']['total_duration']:.2f}秒")

    # 设置退出码
    if result['summary']['failed'] > 0 or result['summary']['errors'] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()