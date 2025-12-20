"""
Image Validator Module
图片验证器

负责图片质量、分辨率、格式等验证
"""

import os
import logging
from typing import Dict, Any, Optional, Tuple
import numpy as np
from pathlib import Path

try:
    from PIL import Image, ImageStat
    from PIL.ExifTags import TAGS
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logging.warning("PIL/Pillow not available. Image validation will be limited.")

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    logging.warning("OpenCV not available. Advanced image analysis will be limited.")

from .validation_report import ValidationResult


class ImageValidator:
    """
    图片验证器

    提供以下验证功能：
    - 分辨率检查
    - 图片质量评估（清晰度、对比度、亮度等）
    - 格式验证
    - 文件完整性检查
    """

    def __init__(self, config: Dict[str, Any]):
        """
        初始化图片验证器

        Args:
            config: 图片验证配置
        """
        self.logger = logging.getLogger(__name__)
        self.config = config

        # 配置参数
        self.min_resolution = tuple(config.get('min_resolution', [512, 512]))
        self.max_resolution = tuple(config.get('max_resolution', [4096, 4096]))
        self.min_quality_score = config.get('min_quality_score', 70.0)
        self.supported_formats = config.get('supported_formats', ['jpg', 'jpeg', 'png', 'webp'])
        self.quality_metrics = config.get('quality_metrics', ['sharpness', 'contrast', 'brightness'])

        self.logger.info("ImageValidator initialized")

    def validate_basic(self, image_path: str) -> ValidationResult:
        """
        基础图片验证

        Args:
            image_path: 图片文件路径

        Returns:
            ValidationResult: 验证结果
        """
        result = ValidationResult(
            item_id=os.path.basename(image_path),
            validation_type="image_basic",
            status="pending",
            score=0.0
        )

        try:
            # 检查文件存在性
            if not os.path.exists(image_path):
                result.status = "failed"
                result.details["error"] = f"File not found: {image_path}"
                return result

            # 检查文件格式
            file_ext = Path(image_path).suffix.lower().lstrip('.')
            if file_ext not in self.supported_formats:
                result.status = "failed"
                result.details["error"] = f"Unsupported format: {file_ext}"
                result.details["supported_formats"] = self.supported_formats
                return result

            # 加载图片
            if PIL_AVAILABLE:
                with Image.open(image_path) as img:
                    # 基础信息
                    result.details.update({
                        'format': img.format,
                        'mode': img.mode,
                        'size': img.size,
                        'file_size': os.path.getsize(image_path)
                    })

                    # 分辨率验证
                    resolution_score = self._validate_resolution(img.size)
                    result.details['resolution_score'] = resolution_score

                    # 质量评估
                    quality_scores = self._assess_quality(img)
                    result.details['quality_scores'] = quality_scores

                    # 计算总分
                    result.score = min(resolution_score, np.mean(list(quality_scores.values())))

                    # 判断状态
                    if result.score >= self.min_quality_score:
                        result.status = "passed"
                    else:
                        result.status = "failed"
                        result.details["reason"] = f"Score {result.score} below threshold {self.min_quality_score}"

            else:
                # 降级处理：仅检查文件
                result.status = "warning"
                result.details["message"] = "PIL not available, limited validation performed"
                result.score = 50.0

        except Exception as e:
            result.status = "error"
            result.details["error"] = str(e)
            self.logger.error(f"Error validating image {image_path}: {str(e)}")

        return result

    def _validate_resolution(self, size: Tuple[int, int]) -> float:
        """
        验证图片分辨率

        Args:
            size: 图片尺寸 (width, height)

        Returns:
            float: 分辨率评分 (0-100)
        """
        width, height = size

        # 检查最小分辨率
        min_width, min_height = self.min_resolution
        if width < min_width or height < min_height:
            return 0.0

        # 检查最大分辨率
        max_width, max_height = self.max_resolution
        if width > max_width or height > max_height:
            # 超过最大分辨率不完全失败，但会扣分
            excess_ratio = max(width/max_width, height/max_height)
            return max(0.0, 100.0 - (excess_ratio - 1.0) * 50.0)

        # 理想分辨率范围内
        return 100.0

    def _assess_quality(self, img: Image.Image) -> Dict[str, float]:
        """
        评估图片质量

        Args:
            img: PIL Image对象

        Returns:
            Dict[str, float]: 各项质量指标评分
        """
        scores = {}

        # 转换为RGB模式（如果不是）
        if img.mode != 'RGB':
            img = img.convert('RGB')

        # 转换为numpy数组
        img_array = np.array(img)

        # 清晰度评估
        if 'sharpness' in self.quality_metrics:
            scores['sharpness'] = self._calculate_sharpness(img_array)

        # 对比度评估
        if 'contrast' in self.quality_metrics:
            scores['contrast'] = self._calculate_contrast(img_array)

        # 亮度评估
        if 'brightness' in self.quality_metrics:
            scores['brightness'] = self._calculate_brightness(img_array)

        # 色彩平衡评估
        if 'color_balance' in self.quality_metrics:
            scores['color_balance'] = self._calculate_color_balance(img_array)

        # 噪声评估（如果OpenCV可用）
        if CV2_AVAILABLE and 'noise' in self.quality_metrics:
            scores['noise'] = self._calculate_noise(img_array)

        return scores

    def _calculate_sharpness(self, img_array: np.ndarray) -> float:
        """
        计算图片清晰度（使用拉普拉斯方差）

        Args:
            img_array: 图片numpy数组

        Returns:
            float: 清晰度评分 (0-100)
        """
        try:
            # 转换为灰度
            if len(img_array.shape) == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY) if CV2_AVAILABLE else np.mean(img_array, axis=2)
            else:
                gray = img_array

            # 计算拉普拉斯方差
            if CV2_AVAILABLE:
                laplacian = cv2.Laplacian(gray, cv2.CV_64F)
                variance = laplacian.var()
            else:
                # 使用Sobel算子近似
                from scipy import ndimage
                sobel_x = ndimage.sobel(gray, axis=1)
                sobel_y = ndimage.sobel(gray, axis=0)
                variance = np.var(sobel_x) + np.var(sobel_y)

            # 归一化到0-100
            # 典型值范围：100-1000，理想值约300-700
            if variance < 100:
                return 0.0
            elif variance > 1000:
                return 100.0
            else:
                return min(100.0, (variance - 100) / 900 * 100)

        except Exception as e:
            self.logger.error(f"Error calculating sharpness: {str(e)}")
            return 50.0

    def _calculate_contrast(self, img_array: np.ndarray) -> float:
        """
        计算对比度（使用标准差）

        Args:
            img_array: 图片numpy数组

        Returns:
            float: 对比度评分 (0-100)
        """
        try:
            if len(img_array.shape) == 3:
                # 对每个通道分别计算
                contrasts = []
                for channel in range(img_array.shape[2]):
                    contrasts.append(np.std(img_array[:, :, channel]))
                avg_contrast = np.mean(contrasts)
            else:
                avg_contrast = np.std(img_array)

            # 归一化到0-100
            # 标准差范围：0-128，理想值约40-80
            if avg_contrast < 20:
                return avg_contrast * 2.5
            elif avg_contrast > 80:
                return 100.0
            else:
                return min(100.0, (avg_contrast - 20) / 60 * 50 + 50)

        except Exception as e:
            self.logger.error(f"Error calculating contrast: {str(e)}")
            return 50.0

    def _calculate_brightness(self, img_array: np.ndarray) -> float:
        """
        计算亮度评分

        Args:
            img_array: 图片numpy数组

        Returns:
            float: 亮度评分 (0-100)
        """
        try:
            # 计算平均亮度
            if len(img_array.shape) == 3:
                brightness = np.mean(img_array)
            else:
                brightness = np.mean(img_array)

            # 理想亮度范围：100-180（0-255范围）
            if brightness < 50:
                return brightness * 2.0
            elif brightness > 200:
                return max(0.0, 100.0 - (brightness - 200) * 0.5)
            else:
                return 100.0

        except Exception as e:
            self.logger.error(f"Error calculating brightness: {str(e)}")
            return 50.0

    def _calculate_color_balance(self, img_array: np.ndarray) -> float:
        """
        计算色彩平衡评分

        Args:
            img_array: 图片numpy数组

        Returns:
            float: 色彩平衡评分 (0-100)
        """
        try:
            if len(img_array.shape) != 3:
                return 100.0  # 灰度图

            # 计算各通道均值
            means = [np.mean(img_array[:, :, i]) for i in range(3)]

            # 计算标准差（越小越平衡）
            balance = 100.0 - np.std(means) / 255.0 * 100.0

            return max(0.0, balance)

        except Exception as e:
            self.logger.error(f"Error calculating color balance: {str(e)}")
            return 50.0

    def _calculate_noise(self, img_array: np.ndarray) -> float:
        """
        计算噪声水平（需要OpenCV）

        Args:
            img_array: 图片numpy数组

        Returns:
            float: 噪声评分 (0-100，越高噪声越少)
        """
        try:
            if not CV2_AVAILABLE:
                return 75.0  # 默认值

            # 转换为灰度
            if len(img_array.shape) == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_array

            # 使用高斯模糊计算噪声
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            noise = np.mean(np.abs(gray.astype(float) - blurred.astype(float)))

            # 归一化：噪声越小分数越高
            # 典型噪声范围：0-30
            if noise > 30:
                return 0.0
            else:
                return 100.0 - (noise / 30.0 * 100.0)

        except Exception as e:
            self.logger.error(f"Error calculating noise: {str(e)}")
            return 75.0