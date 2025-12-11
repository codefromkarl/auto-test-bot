"""
结果验证模块
验证测试步骤的执行结果并提供最终判断
"""

import logging
from typing import Dict, Any, List, Optional
from ..utils import Timer


class ValidateStep:
    """结果验证步骤"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化结果验证步骤

        Args:
            config: 配置字典
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.test_config = config.get('test', {})
        self.validation_rules = self._load_validation_rules()

    async def execute(self, step_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        执行结果验证

        Args:
            step_results: 各步骤的执行结果

        Returns:
            Dict[str, Any]: 验证结果
        """
        result = {
            'step': 'validate',
            'success': False,
            'error': None,
            'details': {},
            'metrics': {},
            'validation_summary': {},
            'step_results': step_results
        }

        timer = Timer('validate')
        timer.start()

        try:
            self.logger.info("开始执行结果验证")

            # 1. 验证必需步骤是否执行
            required_steps = self._get_required_steps()
            missing_steps = self._check_missing_steps(step_results, required_steps)
            if missing_steps:
                result['error'] = f"缺少必需的步骤: {', '.join(missing_steps)}"
                return result

            timer.checkpoint("required_steps_verified")

            # 2. 验证各步骤执行状态
            step_validation = self._validate_step_results(step_results)
            result['details']['step_validation'] = step_validation

            timer.checkpoint("step_results_validated")

            # 3. 验证生成的内容
            content_validation = self._validate_generated_content(step_results)
            result['details']['content_validation'] = content_validation

            timer.checkpoint("content_validated")

            # 4. 综合验证结果
            overall_success = self._determine_overall_success(step_validation, content_validation)
            result['success'] = overall_success

            timer.checkpoint("overall_determined")

            # 5. 生成验证摘要
            result['validation_summary'] = self._generate_validation_summary(
                step_results, step_validation, content_validation
            )

            # 6. 计算验证指标
            result['metrics']['total_time'] = timer.stop()
            result['metrics']['checkpoints'] = timer.get_checkpoints()
            result['metrics']['validation_score'] = self._calculate_validation_score(
                step_validation, content_validation
            )

            self.logger.info(f"结果验证完成，总体状态: {'成功' if overall_success else '失败'}")
            return result

        except Exception as e:
            result['error'] = str(e)
            result['metrics']['total_time'] = timer.get_elapsed_time()
            self.logger.error(f"结果验证失败: {str(e)}")
            return result

    def _get_required_steps(self) -> List[str]:
        """获取必需的步骤列表"""
        steps_config = self.test_config.get('steps', {})
        required_steps = []

        if steps_config.get('open_site', True):
            required_steps.append('open_site')

        if steps_config.get('generate_image', True):
            required_steps.append('generate_image')

        if steps_config.get('generate_video', True):
            required_steps.append('generate_video')

        return required_steps

    def _check_missing_steps(self, step_results: List[Dict[str, Any]], required_steps: List[str]) -> List[str]:
        """检查缺失的步骤"""
        executed_steps = {result.get('step') for result in step_results}
        missing_steps = []

        for required_step in required_steps:
            if required_step not in executed_steps:
                missing_steps.append(required_step)

        return missing_steps

    def _validate_step_results(self, step_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """验证步骤结果"""
        validation = {
            'total_steps': len(step_results),
            'successful_steps': 0,
            'failed_steps': 0,
            'step_details': {}
        }

        for result in step_results:
            step_name = result.get('step', 'unknown')
            step_success = result.get('success', False)
            step_error = result.get('error')

            step_info = {
                'success': step_success,
                'error': step_error,
                'duration': result.get('metrics', {}).get('total_time', 0)
            }

            # 添加特定步骤的详细信息
            if step_name == 'generate_image':
                step_info['image_url'] = result.get('generated_image_url')
            elif step_name == 'generate_video':
                step_info['video_url'] = result.get('generated_video_url')
                step_info['source_image_url'] = result.get('source_image_url')

            validation['step_details'][step_name] = step_info

            if step_success:
                validation['successful_steps'] += 1
            else:
                validation['failed_steps'] += 1

        return validation

    def _validate_generated_content(self, step_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """验证生成的内容"""
        content_validation = {
            'image_generated': False,
            'video_generated': False,
            'content_urls': {},
            'quality_checks': {}
        }

        for result in step_results:
            step_name = result.get('step')

            if step_name == 'generate_image' and result.get('success'):
                image_url = result.get('generated_image_url')
                if image_url:
                    content_validation['image_generated'] = True
                    content_validation['content_urls']['image'] = image_url
                    content_validation['quality_checks']['image_url_valid'] = self._validate_url_format(image_url)

            elif step_name == 'generate_video' and result.get('success'):
                video_url = result.get('generated_video_url')
                if video_url:
                    content_validation['video_generated'] = True
                    content_validation['content_urls']['video'] = video_url
                    content_validation['quality_checks']['video_url_valid'] = self._validate_url_format(video_url)

        return content_validation

    def _validate_url_format(self, url: str) -> bool:
        """验证 URL 格式"""
        if not url:
            return False

        valid_protocols = ['http://', 'https://', 'blob:', 'data:']
        return any(url.startswith(protocol) for protocol in valid_protocols)

    def _determine_overall_success(self, step_validation: Dict[str, Any], content_validation: Dict[str, Any]) -> bool:
        """确定总体成功状态"""
        # 基础检查：所有必需步骤必须成功
        if step_validation['failed_steps'] > 0:
            return False

        # 检查生成内容
        steps_config = self.test_config.get('steps', {})

        if steps_config.get('generate_image', True) and not content_validation['image_generated']:
            return False

        if steps_config.get('generate_video', True) and not content_validation['video_generated']:
            return False

        return True

    def _generate_validation_summary(self, step_results: List[Dict[str, Any]],
                                   step_validation: Dict[str, Any],
                                   content_validation: Dict[str, Any]) -> Dict[str, Any]:
        """生成验证摘要"""
        summary = {
            'total_execution_time': sum(result.get('metrics', {}).get('total_time', 0) for result in step_results),
            'step_success_rate': 0,
            'content_generation_status': {},
            'issues': [],
            'recommendations': []
        }

        # 计算步骤成功率
        if step_validation['total_steps'] > 0:
            summary['step_success_rate'] = (step_validation['successful_steps'] / step_validation['total_steps']) * 100

        # 内容生成状态
        summary['content_generation_status']['image'] = content_validation['image_generated']
        summary['content_generation_status']['video'] = content_validation['video_generated']

        # 识别问题
        if step_validation['failed_steps'] > 0:
            summary['issues'].append(f"{step_validation['failed_steps']} 个步骤执行失败")

        if not content_validation['image_generated']:
            summary['issues'].append("图片生成失败")

        if not content_validation['video_generated']:
            summary['issues'].append("视频生成失败")

        # 生成建议
        if summary['step_success_rate'] < 100:
            summary['recommendations'].append("检查失败步骤的错误信息并修复相关问题")

        if not content_validation['image_generated']:
            summary['recommendations'].append("验证图片生成功能和输入提示词")

        if not content_validation['video_generated']:
            summary['recommendations'].append("验证视频生成功能和图片到视频的转换流程")

        return summary

    def _calculate_validation_score(self, step_validation: Dict[str, Any],
                                   content_validation: Dict[str, Any]) -> float:
        """计算验证分数 (0-100)"""
        score = 0.0
        max_score = 100.0

        # 步骤执行分数 (60%)
        if step_validation['total_steps'] > 0:
            step_score = (step_validation['successful_steps'] / step_validation['total_steps']) * 60
            score += step_score

        # 内容生成分数 (40%)
        content_score = 0
        if content_validation['image_generated']:
            content_score += 20
        if content_validation['video_generated']:
            content_score += 20

        score += content_score

        return min(score, max_score)

    def _load_validation_rules(self) -> Dict[str, Any]:
        """加载验证规则"""
        return {
            'url_validation': {
                'allowed_protocols': ['http://', 'https://', 'blob:', 'data:'],
                'min_url_length': 10
            },
            'content_requirements': {
                'image_required': True,
                'video_required': True,
                'allow_partial_success': False
            },
            'timeout_validation': {
                'max_step_duration': 120000,  # 2 分钟
                'max_total_duration': 300000   # 5 分钟
            }
        }

    def get_step_name(self) -> str:
        """获取步骤名称"""
        return "结果验证"

    def validate_config(self) -> bool:
        """
        验证配置是否有效

        Returns:
            bool: 配置是否有效
        """
        # 检查步骤配置
        steps_config = self.test_config.get('steps', {})
        if not steps_config:
            self.logger.warning("步骤配置为空，将使用默认配置")
            return True

        # 验证步骤配置项
        valid_step_keys = ['open_site', 'generate_image', 'generate_video']
        for key in steps_config:
            if key not in valid_step_keys:
                self.logger.warning(f"未知的步骤配置项: {key}")

        return True