"""
Video Validator Module
视频验证器

负责视频质量、时长、格式、帧率等验证
"""

import os
import logging
from typing import Dict, Any, Optional, Tuple, List
import numpy as np
from pathlib import Path

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    logging.warning("OpenCV not available. Video validation will be limited.")

try:
    import moviepy.editor as mp
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False
    logging.warning("MoviePy not available. Advanced video analysis will be limited.")

from .validation_report import ValidationResult


class VideoValidator:
    """
    视频验证器

    提供以下验证功能：
    - 时长验证
    - 分辨率和帧率检查
    - 视频质量评估
    - 格式验证
    - 帧稳定性分析
    """

    def __init__(self, config: Dict[str, Any]):
        """
        初始化视频验证器

        Args:
            config: 视频验证配置
        """
        self.logger = logging.getLogger(__name__)
        self.config = config

        # 配置参数
        self.min_duration = config.get('min_duration', 3.0)
        self.max_duration = config.get('max_duration', 60.0)
        self.min_fps = config.get('min_fps', 12)
        self.max_fps = config.get('max_fps', 60)
        self.min_quality_score = config.get('min_quality_score', 70.0)
        self.supported_formats = config.get('supported_formats', ['mp4', 'webm', 'mov', 'avi'])
        self.quality_metrics = config.get('quality_metrics', ['resolution', 'fps', 'bitrate', 'stability'])

        self.logger.info("VideoValidator initialized")

    def validate_basic(self, video_path: str) -> ValidationResult:
        """
        基础视频验证

        Args:
            video_path: 视频文件路径

        Returns:
            ValidationResult: 验证结果
        """
        result = ValidationResult(
            item_id=os.path.basename(video_path),
            validation_type="video_basic",
            status="pending",
            score=0.0
        )

        try:
            # 检查文件存在性
            if not os.path.exists(video_path):
                result.status = "failed"
                result.details["error"] = f"File not found: {video_path}"
                return result

            # 检查文件格式
            file_ext = Path(video_path).suffix.lower().lstrip('.')
            if file_ext not in self.supported_formats:
                result.status = "failed"
                result.details["error"] = f"Unsupported format: {file_ext}"
                result.details["supported_formats"] = self.supported_formats
                return result

            # 获取视频信息
            video_info = self._get_video_info(video_path)
            if not video_info:
                result.status = "error"
                result.details["error"] = "Failed to read video information"
                return result

            # 存储视频信息
            result.details.update(video_info)

            # 时长验证
            duration_score = self._validate_duration(video_info['duration'])
            result.details['duration_score'] = duration_score

            # 分辨率验证
            resolution_score = self._validate_resolution(video_info['resolution'])
            result.details['resolution_score'] = resolution_score

            # 帧率验证
            fps_score = self._validate_fps(video_info['fps'])
            result.details['fps_score'] = fps_score

            # 质量评估
            quality_scores = self._assess_quality(video_path, video_info)
            result.details['quality_scores'] = quality_scores

            # 计算总分
            scores = [duration_score, resolution_score, fps_score]
            scores.extend(quality_scores.values())
            result.score = np.mean(scores)

            # 判断状态
            if result.score >= self.min_quality_score:
                result.status = "passed"
            else:
                result.status = "failed"
                result.details["reason"] = f"Score {result.score} below threshold {self.min_quality_score}"

        except Exception as e:
            result.status = "error"
            result.details["error"] = str(e)
            self.logger.error(f"Error validating video {video_path}: {str(e)}")

        return result

    def _get_video_info(self, video_path: str) -> Optional[Dict[str, Any]]:
        """
        获取视频基本信息

        Args:
            video_path: 视频文件路径

        Returns:
            Dict: 视频信息字典
        """
        info = {}

        try:
            # 使用OpenCV获取基本信息
            if CV2_AVAILABLE:
                cap = cv2.VideoCapture(video_path)
                if not cap.isOpened():
                    self.logger.error(f"Cannot open video: {video_path}")
                    return None

                # 获取分辨率
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                info['resolution'] = (width, height)

                # 获取帧率
                fps = cap.get(cv2.CAP_PROP_FPS)
                info['fps'] = fps

                # 获取帧数
                frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                info['frame_count'] = frame_count

                # 计算时长
                duration = frame_count / fps if fps > 0 else 0
                info['duration'] = duration

                # 获取码率（近似）
                file_size = os.path.getsize(video_path)
                bitrate = (file_size * 8) / duration if duration > 0 else 0
                info['bitrate'] = bitrate

                cap.release()

            # 使用MoviePy获取更准确的信息（如果可用）
            elif MOVIEPY_AVAILABLE:
                clip = mp.VideoFileClip(video_path)
                info['duration'] = clip.duration
                info['resolution'] = clip.size
                info['fps'] = clip.fps
                info['frame_count'] = int(clip.duration * clip.fps) if clip.fps else 0
                clip.close()

            # 添加文件信息
            info['file_size'] = os.path.getsize(video_path)
            info['format'] = Path(video_path).suffix.lower().lstrip('.')

            return info

        except Exception as e:
            self.logger.error(f"Error getting video info: {str(e)}")
            return None

    def _validate_duration(self, duration: float) -> float:
        """
        验证视频时长

        Args:
            duration: 视频时长（秒）

        Returns:
            float: 时长评分 (0-100)
        """
        if duration < self.min_duration:
            return 0.0
        elif duration > self.max_duration:
            # 超过最大时长不完全失败，但会扣分
            excess_ratio = duration / self.max_duration
            return max(0.0, 100.0 - (excess_ratio - 1.0) * 50.0)
        else:
            # 理想时长范围内
            return 100.0

    def _validate_resolution(self, resolution: Tuple[int, int]) -> float:
        """
        验证视频分辨率

        Args:
            resolution: 视频分辨率 (width, height)

        Returns:
            float: 分辨率评分 (0-100)
        """
        width, height = resolution

        # 最低分辨率要求
        min_width, min_height = 640, 480
        if width < min_width or height < min_height:
            return 0.0

        # 计算分辨率评分（基于像素数）
        pixels = width * height
        # 理想范围：640x480到1920x1080
        min_pixels = min_width * min_height
        max_pixels = 1920 * 1080

        if pixels > max_pixels:
            return 100.0  # 高分辨率不扣分
        else:
            return (pixels - min_pixels) / (max_pixels - min_pixels) * 100.0

    def _validate_fps(self, fps: float) -> float:
        """
        验证视频帧率

        Args:
            fps: 视频帧率

        Returns:
            float: 帧率评分 (0-100)
        """
        if fps < self.min_fps:
            return 0.0
        elif fps > self.max_fps:
            # 超高帧率不完全失败，但可能不必要
            return 100.0
        else:
            # 理想帧率范围内
            # 24-30fps是理想范围
            if 24 <= fps <= 30:
                return 100.0
            else:
                # 稍微偏离理想范围
                distance = min(abs(fps - 24), abs(fps - 30))
                return max(80.0, 100.0 - distance * 2.0)

    def _assess_quality(self, video_path: str, video_info: Dict[str, Any]) -> Dict[str, float]:
        """
        评估视频质量

        Args:
            video_path: 视频文件路径
            video_info: 视频基本信息

        Returns:
            Dict[str, float]: 各项质量指标评分
        """
        scores = {}

        # 码率评估
        if 'bitrate' in self.quality_metrics:
            scores['bitrate'] = self._assess_bitrate(video_info.get('bitrate', 0))

        # 帧稳定性评估
        if 'stability' in self.quality_metrics:
            scores['stability'] = self._assess_stability(video_path)

        # 运动平滑度评估
        if 'motion_smoothness' in self.quality_metrics:
            scores['motion_smoothness'] = self._assess_motion_smoothness(video_path)

        # 音频质量评估（如果有）
        if 'audio_quality' in self.quality_metrics:
            scores['audio_quality'] = self._assess_audio_quality(video_path)

        return scores

    def _assess_bitrate(self, bitrate: float) -> float:
        """
        评估视频码率

        Args:
            bitrate: 视频码率（bps）

        Returns:
            float: 码率评分 (0-100)
        """
        # 码率范围参考（bps）
        # 低质量: < 1Mbps
        # 标清: 1-5 Mbps
        # 高清: 5-10 Mbps
        # 全高清: 10-20 Mbps
        # 4K: > 20 Mbps

        if bitrate < 1000000:  # < 1Mbps
            return 30.0
        elif bitrate < 5000000:  # < 5Mbps
            return 60.0
        elif bitrate < 10000000:  # < 10Mbps
            return 80.0
        elif bitrate < 20000000:  # < 20Mbps
            return 95.0
        else:
            return 100.0

    def _assess_stability(self, video_path: str) -> float:
        """
        评估视频帧稳定性（抖动检测）

        Args:
            video_path: 视频文件路径

        Returns:
            float: 稳定性评分 (0-100，越高越稳定)
        """
        if not CV2_AVAILABLE:
            return 75.0  # 默认值

        try:
            cap = cv2.VideoCapture(video_path)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            # 采样帧进行检测（每5帧取1帧）
            sample_interval = 5
            frames = []

            for i in range(0, frame_count, sample_interval):
                cap.set(cv2.CAP_PROP_POS_FRAMES, i)
                ret, frame = cap.read()
                if ret:
                    frames.append(frame)
                if len(frames) >= 20:  # 最多检测20帧
                    break

            cap.release()

            if len(frames) < 2:
                return 75.0

            # 计算帧间运动
            motions = []
            for i in range(1, len(frames)):
                # 转换为灰度
                prev_gray = cv2.cvtColor(frames[i-1], cv2.COLOR_BGR2GRAY)
                curr_gray = cv2.cvtColor(frames[i], cv2.COLOR_BGR2GRAY)

                # 计算光流
                flow = cv2.calcOpticalFlowPyrLK(
                    prev_gray, curr_gray,
                    np.array([[100, 100]], dtype=np.float32).reshape(-1, 1, 2),
                    None
                )[0]

                # 计算全局运动幅度
                if flow is not None:
                    motion = np.mean(np.abs(flow))
                    motions.append(motion)

            if not motions:
                return 75.0

            # 评估稳定性：运动越一致越稳定
            motion_std = np.std(motions)

            # 运动标准差越小越稳定
            if motion_std < 1.0:
                return 100.0
            elif motion_std > 10.0:
                return 40.0
            else:
                return 100.0 - (motion_std - 1.0) / 9.0 * 60.0

        except Exception as e:
            self.logger.error(f"Error assessing stability: {str(e)}")
            return 75.0

    def _assess_motion_smoothness(self, video_path: str) -> float:
        """
        评估运动平滑度

        Args:
            video_path: 视频文件路径

        Returns:
            float: 运动平滑度评分 (0-100)
        """
        if not CV2_AVAILABLE:
            return 75.0

        try:
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)

            # 检测运动一致性
            prev_frame = None
            motion_scores = []

            frame_count = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                if prev_frame is not None:
                    # 计算帧差
                    diff = cv2.absdiff(prev_frame, frame)
                    motion_score = np.mean(diff)
                    motion_scores.append(motion_score)

                prev_frame = frame.copy()
                frame_count += 1

                if frame_count > 60:  # 检测前2秒（假设30fps）
                    break

            cap.release()

            if len(motion_scores) < 2:
                return 75.0

            # 评估运动平滑度：变化越平滑分数越高
            # 计算运动变化的一阶导数
            motion_diffs = np.abs(np.diff(motion_scores))
            avg_motion_diff = np.mean(motion_diffs)

            # 归一化评分
            if avg_motion_diff < 5:
                return 100.0
            elif avg_motion_diff > 50:
                return 40.0
            else:
                return 100.0 - (avg_motion_diff - 5.0) / 45.0 * 60.0

        except Exception as e:
            self.logger.error(f"Error assessing motion smoothness: {str(e)}")
            return 75.0

    def _assess_audio_quality(self, video_path: str) -> float:
        """
        评估音频质量（如果有音轨）

        Args:
            video_path: 视频文件路径

        Returns:
            float: 音频质量评分 (0-100)
        """
        try:
            if not MOVIEPY_AVAILABLE:
                return 80.0  # 默认值

            clip = mp.VideoFileClip(video_path)

            # 检查是否有音频
            if clip.audio is None:
                clip.close()
                return 80.0  # 无音频不算错误

            # 检查音频参数
            audio = clip.audio
            duration = audio.duration
            fps = audio.fps  # 采样率

            clip.close()

            # 基本评分标准
            score = 80.0

            # 采样率检查
            if fps >= 44100:  # CD质量
                score += 10.0
            elif fps >= 22050:  # 标准质量
                score += 5.0

            return min(100.0, score)

        except Exception as e:
            self.logger.error(f"Error assessing audio quality: {str(e)}")
            return 80.0