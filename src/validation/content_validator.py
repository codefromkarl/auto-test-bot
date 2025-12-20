"""
Content Validator Module
内容验证器核心模块

综合性内容质量验证，整合图片、视频、一致性和相关性验证
"""

import os
import logging
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import json

from .image_validator import ImageValidator
from .video_validator import VideoValidator
from .consistency_validator import ConsistencyValidator
from .relevance_scorer import RelevanceScorer
from .validation_report import ValidationReport, ValidationResult
from ..utils.config_loader import ConfigLoader


class ContentValidator:
    """
    内容质量验证器

    负责协调各类验证任务，生成综合验证报告

    Architecture: Business Layer (业务层)
    - 整合各专门验证器
    - 协调验证流程
    - 聚合验证结果
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化内容验证器

        Args:
            config_path: 配置文件路径，默认使用项目主配置
        """
        self.logger = logging.getLogger(__name__)

        # 加载配置
        if config_path is None:
            config_path = os.path.join(os.getcwd(), "config", "config.yaml")
        self.config_loader = ConfigLoader(config_path)
        self.config = self.config_loader.load_config()
        self.validation_config = self.config.get('validation', self._get_default_validation_config())

        # 初始化各验证器
        self.image_validator = ImageValidator(self.validation_config.get('image', {}))
        self.video_validator = VideoValidator(self.validation_config.get('video', {}))
        self.consistency_validator = ConsistencyValidator(self.validation_config.get('consistency', {}))
        self.relevance_scorer = RelevanceScorer(self.validation_config.get('relevance', {}))

        self.logger.info("ContentValidator initialized")

    def validate_content(self, content_paths: Dict[str, Union[str, List[str]]],
                        expected_prompt: Optional[str] = None,
                        context: Optional[Dict[str, Any]] = None) -> ValidationReport:
        """
        验证内容质量

        Args:
            content_paths: 内容路径字典
                - 'images': 图片路径或列表
                - 'videos': 视频路径或列表
            expected_prompt: 期望的提示词（用于相关性验证）
            context: 额外上下文信息（如角色、场景描述等）

        Returns:
            ValidationReport: 综合验证报告
        """
        self.logger.info(f"Starting content validation for: {content_paths}")

        # 创建验证报告
        report = ValidationReport()
        report.context = context or {}

        # 验证图片
        if 'images' in content_paths:
            image_results = self._validate_images(content_paths['images'], expected_prompt, context)
            report.add_results('images', image_results)

        # 验证视频
        if 'videos' in content_paths:
            video_results = self._validate_videos(content_paths['videos'], expected_prompt, context)
            report.add_results('videos', video_results)

        # 一致性验证（需要多个内容）
        if len(content_paths) > 1 or any(isinstance(v, list) and len(v) > 1
                                       for v in content_paths.values()):
            consistency_results = self._validate_consistency(content_paths, context)
            report.add_results('consistency', consistency_results)

        # 计算总体评分
        report.calculate_overall_score()

        # 保存报告
        self._save_report(report)

        self.logger.info(f"Content validation completed. Overall score: {report.overall_score}")
        return report

    def _validate_images(self, image_paths: Union[str, List[str]],
                        expected_prompt: Optional[str] = None,
                        context: Optional[Dict[str, Any]] = None) -> List[ValidationResult]:
        """验证图片内容"""
        paths = image_paths if isinstance(image_paths, list) else [image_paths]
        results = []

        for i, path in enumerate(paths):
            try:
                # 基础验证
                basic_result = self.image_validator.validate_basic(path)
                basic_result.item_id = f"image_{i}"
                results.append(basic_result)

                # 相关性评分
                if expected_prompt:
                    relevance_result = self.relevance_scorer.score_image_relevance(
                        path, expected_prompt, context
                    )
                    relevance_result.item_id = f"image_{i}_relevance"
                    results.append(relevance_result)

            except Exception as e:
                error_result = ValidationResult(
                    item_id=f"image_{i}",
                    validation_type="image",
                    status="error",
                    score=0.0,
                    details={"error": str(e)}
                )
                results.append(error_result)
                self.logger.error(f"Error validating image {path}: {str(e)}")

        return results

    def _validate_videos(self, video_paths: Union[str, List[str]],
                        expected_prompt: Optional[str] = None,
                        context: Optional[Dict[str, Any]] = None) -> List[ValidationResult]:
        """验证视频内容"""
        paths = video_paths if isinstance(video_paths, list) else [video_paths]
        results = []

        for i, path in enumerate(paths):
            try:
                # 基础验证
                basic_result = self.video_validator.validate_basic(path)
                basic_result.item_id = f"video_{i}"
                results.append(basic_result)

                # 相关性评分
                if expected_prompt:
                    relevance_result = self.relevance_scorer.score_video_relevance(
                        path, expected_prompt, context
                    )
                    relevance_result.item_id = f"video_{i}_relevance"
                    results.append(relevance_result)

            except Exception as e:
                error_result = ValidationResult(
                    item_id=f"video_{i}",
                    validation_type="video",
                    status="error",
                    score=0.0,
                    details={"error": str(e)}
                )
                results.append(error_result)
                self.logger.error(f"Error validating video {path}: {str(e)}")

        return results

    def _validate_consistency(self, content_paths: Dict[str, Union[str, List[str]]],
                             context: Optional[Dict[str, Any]] = None) -> List[ValidationResult]:
        """验证内容一致性"""
        results = []

        try:
            # 角色一致性
            if context and 'characters' in context:
                character_result = self.consistency_validator.validate_character_consistency(
                    content_paths, context['characters']
                )
                character_result.item_id = "character_consistency"
                results.append(character_result)

            # 场景一致性
            if context and 'scenes' in context:
                scene_result = self.consistency_validator.validate_scene_consistency(
                    content_paths, context['scenes']
                )
                scene_result.item_id = "scene_consistency"
                results.append(scene_result)

            # 风格一致性
            style_result = self.consistency_validator.validate_style_consistency(content_paths)
            style_result.item_id = "style_consistency"
            results.append(style_result)

        except Exception as e:
            error_result = ValidationResult(
                item_id="consistency",
                validation_type="consistency",
                status="error",
                score=0.0,
                details={"error": str(e)}
            )
            results.append(error_result)
            self.logger.error(f"Error validating consistency: {str(e)}")

        return results

    def _get_default_validation_config(self) -> Dict[str, Any]:
        """获取默认验证配置"""
        return {
            'enabled': True,
            'output_dir': 'validation_reports',

            'image': {
                'min_resolution': {'width': 512, 'height': 512},
                'max_resolution': {'width': 4096, 'height': 4096},
                'min_quality_score': 70.0,
                'supported_formats': ['jpg', 'jpeg', 'png', 'webp'],
                'quality_metrics': ['sharpness', 'contrast', 'brightness', 'color_balance']
            },

            'video': {
                'min_duration': 3.0,  # seconds
                'max_duration': 60.0,
                'min_fps': 12,
                'max_fps': 60,
                'min_quality_score': 70.0,
                'supported_formats': ['mp4', 'webm', 'mov', 'avi'],
                'quality_metrics': ['resolution', 'fps', 'bitrate', 'stability']
            },

            'consistency': {
                'character_similarity_threshold': 0.75,
                'scene_similarity_threshold': 0.70,
                'style_consistency_threshold': 0.75,
                'enable_cross_frame_analysis': True
            },

            'relevance': {
                'text_embedding_model': 'clip',
                'similarity_threshold': 0.65,
                'visual_weight': 0.7,
                'semantic_weight': 0.3
            },

            'reporting': {
                'include_thumbnails': True,
                'thumbnail_size': [200, 200],
                'save_detailed_metrics': True,
                'export_formats': ['json', 'html']
            }
        }

    def _save_report(self, report: ValidationReport):
        """保存验证报告"""
        try:
            output_dir = Path(self.validation_config.get('output_dir', 'validation_reports'))
            output_dir.mkdir(exist_ok=True)

            # 生成时间戳
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # 保存JSON格式报告
            json_path = output_dir / f"validation_report_{timestamp}.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(report.to_dict(), f, ensure_ascii=False, indent=2)

            # 保存HTML格式报告（如果启用）
            if 'html' in self.validation_config.get('reporting', {}).get('export_formats', []):
                html_path = output_dir / f"validation_report_{timestamp}.html"
                report.save_html(html_path)

            self.logger.info(f"Validation report saved to {json_path}")

        except Exception as e:
            self.logger.error(f"Failed to save validation report: {str(e)}")

    def get_validation_summary(self, report: ValidationReport) -> Dict[str, Any]:
        """获取验证摘要（用于日志或通知）"""
        return {
            'timestamp': report.timestamp,
            'overall_score': report.overall_score,
            'status': report.status,
            'total_items': len(report.results),
            'passed_items': len([r for r in report.results if r.status == 'passed']),
            'failed_items': len([r for r in report.results if r.status == 'failed']),
            'errors': len([r for r in report.results if r.status == 'error']),
            'key_issues': report.get_key_issues()
        }