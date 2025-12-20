"""
Consistency Validator Module
一致性验证器

负责角色、场景、风格等一致性验证
"""

import os
import logging
from typing import Dict, Any, List, Union, Tuple, Optional
import numpy as np
from pathlib import Path

try:
    from PIL import Image, ImageChops
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logging.warning("PIL/Pillow not available. Consistency validation will be limited.")

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    logging.warning("OpenCV not available. Advanced consistency analysis will be limited.")

try:
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.feature_extraction.text import TfidfVectorizer
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning("Scikit-learn not available. Advanced similarity analysis will be limited.")

from .validation_report import ValidationResult


class ConsistencyValidator:
    """
    一致性验证器

    提供以下验证功能：
    - 角色一致性验证（多图片/视频中的人物特征一致性）
    - 场景一致性验证（背景、环境的连贯性）
    - 风格一致性验证（视觉风格、色调、构图等）
    - 跨帧一致性验证（视频的帧间稳定性）
    """

    def __init__(self, config: Dict[str, Any]):
        """
        初始化一致性验证器

        Args:
            config: 一致性验证配置
        """
        self.logger = logging.getLogger(__name__)
        self.config = config

        # 配置参数
        self.character_similarity_threshold = config.get('character_similarity_threshold', 0.75)
        self.scene_similarity_threshold = config.get('scene_similarity_threshold', 0.70)
        self.style_consistency_threshold = config.get('style_consistency_threshold', 0.75)
        self.enable_cross_frame_analysis = config.get('enable_cross_frame_analysis', True)

        self.logger.info("ConsistencyValidator initialized")

    def validate_character_consistency(self, content_paths: Dict[str, Union[str, List[str]]],
                                     expected_characters: List[Dict[str, Any]]) -> ValidationResult:
        """
        验证角色一致性

        Args:
            content_paths: 内容路径字典（图片/视频）
            expected_characters: 期望的角色特征列表
                [{'name': str, 'features': dict}, ...]

        Returns:
            ValidationResult: 验证结果
        """
        result = ValidationResult(
            item_id="character_consistency",
            validation_type="character_consistency",
            status="pending",
            score=0.0
        )

        try:
            # 收集所有内容帧
            frames = self._extract_frames(content_paths)
            if not frames:
                result.status = "failed"
                result.details["error"] = "No valid frames found"
                return result

            # 分析每个角色的出现和一致性
            character_results = []
            for char in expected_characters:
                char_name = char.get('name', 'unknown')
                char_features = char.get('features', {})

                # 检测角色在所有帧中的出现
                char_detections = []
                for frame_path in frames:
                    detection = self._detect_character_in_frame(frame_path, char_features)
                    char_detections.append(detection)

                # 计算角色一致性分数
                if char_detections:
                    consistency_score = self._calculate_character_consistency(char_detections)
                    character_results.append({
                        'name': char_name,
                        'consistency_score': consistency_score,
                        'detection_rate': sum(1 for d in char_detections if d['detected']) / len(char_detections)
                    })

            # 计算总体角色一致性
            if character_results:
                avg_consistency = np.mean([r['consistency_score'] for r in character_results])
                result.score = avg_consistency * 100
                result.details['character_results'] = character_results

                # 判断状态
                if result.score >= self.character_similarity_threshold * 100:
                    result.status = "passed"
                else:
                    result.status = "failed"
                    result.details["reason"] = f"Character consistency {result.score/100:.2f} below threshold {self.character_similarity_threshold}"
            else:
                result.status = "failed"
                result.details["error"] = "No character consistency data available"

        except Exception as e:
            result.status = "error"
            result.details["error"] = str(e)
            self.logger.error(f"Error validating character consistency: {str(e)}")

        return result

    def validate_scene_consistency(self, content_paths: Dict[str, Union[str, List[str]]],
                                 expected_scenes: List[Dict[str, Any]]) -> ValidationResult:
        """
        验证场景一致性

        Args:
            content_paths: 内容路径字典
            expected_scenes: 期望的场景特征列表
                [{'name': str, 'elements': list}, ...]

        Returns:
            ValidationResult: 验证结果
        """
        result = ValidationResult(
            item_id="scene_consistency",
            validation_type="scene_consistency",
            status="pending",
            score=0.0
        )

        try:
            # 收集所有内容帧
            frames = self._extract_frames(content_paths)
            if not frames:
                result.status = "failed"
                result.details["error"] = "No valid frames found"
                return result

            # 分析场景特征
            scene_features = []
            for frame_path in frames:
                features = self._extract_scene_features(frame_path)
                scene_features.append(features)

            # 计算场景一致性
            if len(scene_features) > 1:
                similarity_scores = []
                for i in range(len(scene_features) - 1):
                    for j in range(i + 1, len(scene_features)):
                        similarity = self._calculate_scene_similarity(
                            scene_features[i], scene_features[j]
                        )
                        similarity_scores.append(similarity)

                avg_similarity = np.mean(similarity_scores)
                result.score = avg_similarity * 100
                result.details['similarity_scores'] = similarity_scores
                result.details['scene_features_count'] = len(scene_features)

                # 判断状态
                if result.score >= self.scene_similarity_threshold * 100:
                    result.status = "passed"
                else:
                    result.status = "failed"
                    result.details["reason"] = f"Scene consistency {result.score/100:.2f} below threshold {self.scene_similarity_threshold}"
            else:
                result.status = "passed"  # 单帧自动通过
                result.score = 100.0
                result.details["message"] = "Single frame - consistency automatically passed"

        except Exception as e:
            result.status = "error"
            result.details["error"] = str(e)
            self.logger.error(f"Error validating scene consistency: {str(e)}")

        return result

    def validate_style_consistency(self, content_paths: Dict[str, Union[str, List[str]]]) -> ValidationResult:
        """
        验证风格一致性

        Args:
            content_paths: 内容路径字典

        Returns:
            ValidationResult: 验证结果
        """
        result = ValidationResult(
            item_id="style_consistency",
            validation_type="style_consistency",
            status="pending",
            score=0.0
        )

        try:
            # 收集所有内容帧
            frames = self._extract_frames(content_paths)
            if not frames:
                result.status = "failed"
                result.details["error"] = "No valid frames found"
                return result

            # 分析风格特征
            style_features = []
            for frame_path in frames:
                features = self._extract_style_features(frame_path)
                style_features.append(features)

            # 计算风格一致性
            if len(style_features) > 1:
                consistency_scores = []
                for metric in ['color_palette', 'brightness', 'contrast', 'composition']:
                    metric_values = [sf.get(metric, 0) for sf in style_features]
                    if metric_values:
                        metric_std = np.std(metric_values)
                        # 标准差越小越一致
                        metric_score = max(0, 1 - metric_std / np.mean(metric_values))
                        consistency_scores.append(metric_score)

                avg_consistency = np.mean(consistency_scores) if consistency_scores else 0
                result.score = avg_consistency * 100
                result.details['style_metrics'] = {
                    metric: [sf.get(metric, 0) for sf in style_features]
                    for metric in ['color_palette', 'brightness', 'contrast', 'composition']
                }

                # 判断状态
                if result.score >= self.style_consistency_threshold * 100:
                    result.status = "passed"
                else:
                    result.status = "failed"
                    result.details["reason"] = f"Style consistency {result.score/100:.2f} below threshold {self.style_consistency_threshold}"
            else:
                result.status = "passed"
                result.score = 100.0
                result.details["message"] = "Single frame - style consistency automatically passed"

        except Exception as e:
            result.status = "error"
            result.details["error"] = str(e)
            self.logger.error(f"Error validating style consistency: {str(e)}")

        return result

    def _extract_frames(self, content_paths: Dict[str, Union[str, List[str]]]) -> List[str]:
        """
        从内容中提取帧

        Args:
            content_paths: 内容路径字典

        Returns:
            List[str]: 帧文件路径列表
        """
        frames = []

        # 处理图片
        if 'images' in content_paths:
            image_paths = content_paths['images']
            if isinstance(image_paths, str):
                image_paths = [image_paths]
            frames.extend(image_paths)

        # 处理视频（提取关键帧）
        if 'videos' in content_paths:
            video_paths = content_paths['videos']
            if isinstance(video_paths, str):
                video_paths = [video_paths]

            for video_path in video_paths:
                video_frames = self._extract_video_frames(video_path)
                frames.extend(video_frames)

        return frames

    def _extract_video_frames(self, video_path: str, num_frames: int = 5) -> List[str]:
        """
        从视频中提取关键帧

        Args:
            video_path: 视频路径
            num_frames: 提取帧数

        Returns:
            List[str]: 临时帧文件路径列表
        """
        if not CV2_AVAILABLE:
            return []

        frames = []
        try:
            cap = cv2.VideoCapture(video_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            if total_frames == 0:
                cap.release()
                return []

            # 均匀选择帧
            frame_indices = np.linspace(0, total_frames - 1, num_frames, dtype=int)

            temp_dir = Path('temp_video_frames')
            temp_dir.mkdir(exist_ok=True)

            for idx, frame_idx in enumerate(frame_indices):
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                if ret:
                    frame_path = temp_dir / f"frame_{Path(video_path).stem}_{idx}.jpg"
                    cv2.imwrite(str(frame_path), frame)
                    frames.append(str(frame_path))

            cap.release()

        except Exception as e:
            self.logger.error(f"Error extracting video frames: {str(e)}")

        return frames

    def _detect_character_in_frame(self, frame_path: str, character_features: Dict[str, Any]) -> Dict[str, Any]:
        """
        在帧中检测特定角色

        Args:
            frame_path: 帧文件路径
            character_features: 角色特征描述

        Returns:
            Dict: 检测结果
        """
        result = {
            'detected': False,
            'confidence': 0.0,
            'features': {}
        }

        try:
            if not CV2_AVAILABLE:
                return result

            # 加载图像
            img = cv2.imread(frame_path)
            if img is None:
                return result

            # 基础特征检测（颜色、位置等）
            if 'color' in character_features:
                # 颜色匹配
                target_color = np.array(character_features['color'])
                # 简化处理：检查图像中是否存在目标颜色
                color_mask = cv2.inRange(img, target_color - 20, target_color + 20)
                color_ratio = np.sum(color_mask > 0) / (img.shape[0] * img.shape[1])
                result['features']['color_match'] = color_ratio

            if 'position' in character_features:
                # 位置分析（简化处理）
                target_pos = character_features['position']
                # 这里可以使用目标检测或特征匹配
                result['features']['position'] = target_pos

            # 简单的置信度计算
            confidence = 0.0
            if 'color_match' in result['features']:
                confidence += result['features']['color_match'] * 0.5

            result['confidence'] = min(confidence, 1.0)
            result['detected'] = result['confidence'] > 0.3

        except Exception as e:
            self.logger.error(f"Error detecting character in frame: {str(e)}")

        return result

    def _calculate_character_consistency(self, detections: List[Dict[str, Any]]) -> float:
        """
        计算角色一致性分数

        Args:
            detections: 检测结果列表

        Returns:
            float: 一致性分数 (0-1)
        """
        if not detections:
            return 0.0

        # 计算检测的一致性
        detected_frames = [d for d in detections if d['detected']]
        if not detected_frames:
            return 0.0

        # 检测率一致性
        detection_rate = len(detected_frames) / len(detections)

        # 置信度一致性
        confidences = [d['confidence'] for d in detected_frames]
        confidence_consistency = 1.0 - np.std(confidences) if confidences else 0.0

        # 综合分数
        consistency = (detection_rate * 0.6 + confidence_consistency * 0.4)

        return min(1.0, consistency)

    def _extract_scene_features(self, frame_path: str) -> Dict[str, Any]:
        """
        提取场景特征

        Args:
            frame_path: 帧文件路径

        Returns:
            Dict: 场景特征
        """
        features = {}

        try:
            if not PIL_AVAILABLE:
                return features

            with Image.open(frame_path) as img:
                # 颜色直方图
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                histogram = img.histogram()
                features['histogram'] = histogram[:256]  # 仅使用一个通道

                # 边缘特征
                if CV2_AVAILABLE:
                    img_cv = cv2.imread(frame_path)
                    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
                    edges = cv2.Canny(gray, 50, 150)
                    features['edge_density'] = np.sum(edges > 0) / edges.size

                # 纹理特征（简化）
                features['texture_variance'] = np.var(np.array(img))

        except Exception as e:
            self.logger.error(f"Error extracting scene features: {str(e)}")

        return features

    def _calculate_scene_similarity(self, features1: Dict[str, Any], features2: Dict[str, Any]) -> float:
        """
        计算场景相似度

        Args:
            features1: 场景特征1
            features2: 场景特征2

        Returns:
            float: 相似度分数 (0-1)
        """
        similarity = 0.0
        count = 0

        # 直方图相似度
        if 'histogram' in features1 and 'histogram' in features2:
            hist1 = np.array(features1['histogram'])
            hist2 = np.array(features2['histogram'])
            hist_sim = 1.0 - np.abs(hist1 - hist2).sum() / hist1.sum()
            similarity += hist_sim
            count += 1

        # 边缘密度相似度
        if 'edge_density' in features1 and 'edge_density' in features2:
            edge_sim = 1.0 - abs(features1['edge_density'] - features2['edge_density'])
            similarity += edge_sim
            count += 1

        # 纹理相似度
        if 'texture_variance' in features1 and 'texture_variance' in features2:
            tex_sim = 1.0 - abs(features1['texture_variance'] - features2['texture_variance']) / max(features1['texture_variance'], features2['texture_variance'])
            similarity += tex_sim
            count += 1

        return similarity / count if count > 0 else 0.0

    def _extract_style_features(self, frame_path: str) -> Dict[str, Any]:
        """
        提取风格特征

        Args:
            frame_path: 帧文件路径

        Returns:
            Dict: 风格特征
        """
        features = {}

        try:
            if not PIL_AVAILABLE:
                return features

            with Image.open(frame_path) as img:
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                # 亮度
                img_array = np.array(img)
                features['brightness'] = np.mean(img_array)

                # 对比度
                features['contrast'] = np.std(img_array)

                # 颜色分布（简化）
                features['color_palette'] = np.mean(img_array, axis=(0, 1))

                # 构图特征（简化：重心位置）
                h, w = img_array.shape[:2]
                y_coords, x_coords = np.mgrid[:h, :w]
                total_intensity = np.sum(img_array)
                if total_intensity > 0:
                    center_y = np.sum(y_coords * np.mean(img_array, axis=2)) / total_intensity
                    center_x = np.sum(x_coords * np.mean(img_array, axis=2)) / total_intensity
                    features['composition'] = (center_x / w, center_y / h)
                else:
                    features['composition'] = (0.5, 0.5)

        except Exception as e:
            self.logger.error(f"Error extracting style features: {str(e)}")

        return features