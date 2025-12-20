"""
Relevance Scorer Module
内容相关性评分器

负责评估生成内容与提示词的相关性
"""

import os
import logging
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from pathlib import Path

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logging.warning("PIL/Pillow not available. Image relevance scoring will be limited.")

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    logging.warning("OpenCV not available. Advanced relevance analysis will be limited.")

try:
    # 尝试导入transformers用于文本和图像的嵌入
    from transformers import pipeline, AutoTokenizer, AutoModel
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("Transformers not available. Will use basic relevance scoring.")

try:
    # 尝试导入CLIP模型
    import clip
    import torch
    CLIP_AVAILABLE = True
except ImportError:
    CLIP_AVAILABLE = False
    logging.warning("CLIP not available. Will use basic relevance scoring.")

from .validation_report import ValidationResult


class RelevanceScorer:
    """
    内容相关性评分器

    提供以下功能：
    - 图片与提示词相关性评分
    - 视频与提示词相关性评分
    - 关键词匹配分析
    - 语义相关性分析
    """

    def __init__(self, config: Dict[str, Any]):
        """
        初始化相关性评分器

        Args:
            config: 相关性评分配置
        """
        self.logger = logging.getLogger(__name__)
        self.config = config

        # 配置参数
        self.text_embedding_model = config.get('text_embedding_model', 'clip')
        self.similarity_threshold = config.get('similarity_threshold', 0.65)
        self.visual_weight = config.get('visual_weight', 0.7)
        self.semantic_weight = config.get('semantic_weight', 0.3)

        # 初始化模型
        self._initialize_models()

        self.logger.info("RelevanceScorer initialized")

    def _initialize_models(self):
        """初始化嵌入模型"""
        self.clip_model = None
        self.clip_preprocess = None
        self.device = "cpu"

        try:
            if CLIP_AVAILABLE and self.text_embedding_model == 'clip':
                # 加载CLIP模型
                self.clip_model, self.clip_preprocess = clip.load("ViT-B/32", device=self.device)
                self.logger.info("CLIP model loaded successfully")
            elif TRANSFORMERS_AVAILABLE:
                # 使用transformers的视觉语言模型
                self.logger.info("Transformers available, but CLIP preferred for relevance scoring")
            else:
                self.logger.warning("No advanced models available, using basic keyword matching")
        except Exception as e:
            self.logger.error(f"Error initializing models: {str(e)}")

    def score_image_relevance(self, image_path: str, prompt: str,
                            context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """
        评估图片与提示词的相关性

        Args:
            image_path: 图片文件路径
            prompt: 提示词
            context: 额外上下文信息

        Returns:
            ValidationResult: 相关性评分结果
        """
        result = ValidationResult(
            item_id=os.path.basename(image_path),
            validation_type="image_relevance",
            status="pending",
            score=0.0
        )

        try:
            # 检查文件存在
            if not os.path.exists(image_path):
                result.status = "failed"
                result.details["error"] = f"Image not found: {image_path}"
                return result

            # 提取关键词
            prompt_keywords = self._extract_keywords(prompt)
            context_keywords = self._extract_context_keywords(context) if context else []

            # 视觉特征分析
            visual_score = 0.0
            if self.clip_model is not None:
                # 使用CLIP计算视觉-文本相似度
                visual_score = self._calculate_clip_similarity(image_path, prompt)
            else:
                # 降级到基础分析
                visual_score = self._basic_visual_analysis(image_path, prompt_keywords)

            # 语义分析
            semantic_score = self._semantic_analysis(prompt_keywords, context_keywords, image_path)

            # 关键词匹配
            keyword_score = self._keyword_matching(image_path, prompt_keywords)

            # 综合评分
            result.score = (
                visual_score * self.visual_weight +
                semantic_score * self.semantic_weight * 0.5 +
                keyword_score * self.semantic_weight * 0.5
            ) * 100

            result.details.update({
                'visual_score': visual_score,
                'semantic_score': semantic_score,
                'keyword_score': keyword_score,
                'prompt_keywords': prompt_keywords,
                'context_keywords': context_keywords
            })

            # 判断状态
            if result.score >= self.similarity_threshold * 100:
                result.status = "passed"
            else:
                result.status = "failed"
                result.details["reason"] = f"Relevance score {result.score/100:.2f} below threshold {self.similarity_threshold}"

        except Exception as e:
            result.status = "error"
            result.details["error"] = str(e)
            self.logger.error(f"Error scoring image relevance: {str(e)}")

        return result

    def score_video_relevance(self, video_path: str, prompt: str,
                            context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """
        评估视频与提示词的相关性

        Args:
            video_path: 视频文件路径
            prompt: 提示词
            context: 额外上下文信息

        Returns:
            ValidationResult: 相关性评分结果
        """
        result = ValidationResult(
            item_id=os.path.basename(video_path),
            validation_type="video_relevance",
            status="pending",
            score=0.0
        )

        try:
            # 检查文件存在
            if not os.path.exists(video_path):
                result.status = "failed"
                result.details["error"] = f"Video not found: {video_path}"
                return result

            # 提取关键帧
            frame_paths = self._extract_video_frames(video_path, num_frames=5)
            if not frame_paths:
                result.status = "failed"
                result.details["error"] = "Failed to extract frames from video"
                return result

            # 评估每一帧的相关性
            frame_scores = []
            for frame_path in frame_paths:
                frame_result = self.score_image_relevance(frame_path, prompt, context)
                frame_scores.append(frame_result.score)

            # 计算视频总体相关性
            if frame_scores:
                # 使用中位数减少异常值影响
                avg_score = np.median(frame_scores)
                result.score = avg_score
                result.details['frame_scores'] = frame_scores
                result.details['avg_frame_score'] = avg_score
                result.details['num_frames_analyzed'] = len(frame_scores)

                # 判断状态
                if result.score >= self.similarity_threshold * 100:
                    result.status = "passed"
                else:
                    result.status = "failed"
                    result.details["reason"] = f"Video relevance {result.score/100:.2f} below threshold {self.similarity_threshold}"

                # 清理临时帧
                self._cleanup_temp_frames(frame_paths)
            else:
                result.status = "error"
                result.details["error"] = "No frame scores available"

        except Exception as e:
            result.status = "error"
            result.details["error"] = str(e)
            self.logger.error(f"Error scoring video relevance: {str(e)}")

        return result

    def _extract_keywords(self, text: str) -> List[str]:
        """
        从文本中提取关键词

        Args:
            text: 输入文本

        Returns:
            List[str]: 关键词列表
        """
        # 简单的关键词提取（实际应用中可以使用更复杂的NLP方法）
        import re

        # 移除标点符号并分词
        words = re.findall(r'\b\w+\b', text.lower())

        # 过滤停用词（简化版）
        stop_words = {'的', '是', '在', '有', '和', '一个', '这', '那', 'the', 'a', 'an', 'is', 'in', 'with'}
        keywords = [w for w in words if len(w) > 1 and w not in stop_words]

        # 去重
        keywords = list(set(keywords))

        return keywords

    def _extract_context_keywords(self, context: Dict[str, Any]) -> List[str]:
        """
        从上下文中提取关键词

        Args:
            context: 上下文字典

        Returns:
            List[str]: 关键词列表
        """
        keywords = []

        # 从角色描述中提取
        if 'characters' in context:
            for char in context['characters']:
                if isinstance(char, dict):
                    if 'name' in char:
                        keywords.append(char['name'].lower())
                    if 'description' in char:
                        keywords.extend(self._extract_keywords(char['description']))

        # 从场景描述中提取
        if 'scenes' in context:
            for scene in context['scenes']:
                if isinstance(scene, str):
                    keywords.extend(self._extract_keywords(scene))
                elif isinstance(scene, dict) and 'description' in scene:
                    keywords.extend(self._extract_keywords(scene['description']))

        # 从风格描述中提取
        if 'style' in context:
            keywords.extend(self._extract_keywords(str(context['style'])))

        return list(set(keywords))

    def _calculate_clip_similarity(self, image_path: str, text: str) -> float:
        """
        使用CLIP计算图像-文本相似度

        Args:
            image_path: 图片路径
            text: 文本描述

        Returns:
            float: 相似度分数 (0-1)
        """
        try:
            if not self.clip_model:
                return 0.5  # 默认值

            # 加载和预处理图像
            image = Image.open(image_path).convert('RGB')
            image_tensor = self.clip_preprocess(image).unsqueeze(0).to(self.device)

            # 编码文本
            text_tokens = clip.tokenize([text]).to(self.device)

            # 获取特征
            with torch.no_grad():
                image_features = self.clip_model.encode_image(image_tensor)
                text_features = self.clip_model.encode_text(text_tokens)

                # 计算相似度
                similarity = torch.cosine_similarity(image_features, text_features)
                similarity = (similarity + 1) / 2  # 归一化到0-1

            return float(similarity.cpu().numpy())

        except Exception as e:
            self.logger.error(f"Error calculating CLIP similarity: {str(e)}")
            return 0.5

    def _basic_visual_analysis(self, image_path: str, keywords: List[str]) -> float:
        """
        基础视觉分析（降级方案）

        Args:
            image_path: 图片路径
            keywords: 关键词列表

        Returns:
            float: 视觉分析分数 (0-1)
        """
        try:
            if not CV2_AVAILABLE:
                return 0.5

            # 加载图像
            img = cv2.imread(image_path)
            if img is None:
                return 0.5

            # 简单的颜色分析
            # 检查是否包含特定颜色（如天空的蓝色、草的绿色等）
            color_matches = 0

            # 转换到HSV空间进行颜色分析
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

            # 颜色范围映射
            color_ranges = {
                'blue': [(100, 50, 50), (130, 255, 255)],  # 天空
                'green': [(40, 50, 50), (80, 255, 255)],  # 草地
                'brown': [(10, 50, 50), (20, 255, 255)],  # 土地
                'white': [(0, 0, 200), (180, 30, 255)],   # 白色
                'black': [(0, 0, 0), (180, 255, 50)]      # 黑色
            }

            # 检查关键词对应的颜色
            for keyword in keywords:
                for color_name, (lower, upper) in color_ranges.items():
                    if color_name in keyword:
                        mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
                        if np.sum(mask > 0) / mask.size > 0.01:  # 至少1%的像素
                            color_matches += 1

            # 形状分析（简化）
            # 检查是否有圆形（可能是太阳、月亮等）
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 1, 20,
                                     param1=50, param2=30, minRadius=10, maxRadius=100)

            if '太阳' in keywords or 'sun' in keywords:
                if circles is not None:
                    color_matches += 1

            # 计算分数
            score = min(1.0, color_matches / max(1, len(keywords)))

            return score

        except Exception as e:
            self.logger.error(f"Error in basic visual analysis: {str(e)}")
            return 0.5

    def _semantic_analysis(self, prompt_keywords: List[str], context_keywords: List[str],
                          image_path: str) -> float:
        """
        语义分析

        Args:
            prompt_keywords: 提示词关键词
            context_keywords: 上下文关键词
            image_path: 图像路径

        Returns:
            float: 语义分析分数 (0-1)
        """
        try:
            # 如果有CLIP，使用CLIP的文本编码
            if self.clip_model is not None:
                # 合并关键词
                all_keywords = list(set(prompt_keywords + context_keywords))
                if not all_keywords:
                    return 0.5

                # 计算关键词与图像的语义相似度
                similarities = []
                for keyword in all_keywords:
                    similarity = self._calculate_clip_similarity(image_path, keyword)
                    similarities.append(similarity)

                # 返回最高相似度
                return max(similarities) if similarities else 0.5

            else:
                # 降级方案：简单的词汇匹配
                return self._basic_keyword_matching(image_path, prompt_keywords + context_keywords)

        except Exception as e:
            self.logger.error(f"Error in semantic analysis: {str(e)}")
            return 0.5

    def _keyword_matching(self, image_path: str, keywords: List[str]) -> float:
        """
        关键词匹配分析

        Args:
            image_path: 图像路径
            keywords: 关键词列表

        Returns:
            float: 匹配分数 (0-1)
        """
        # 这里可以使用OCR识别图像中的文本，然后匹配关键词
        # 或者使用对象检测来匹配关键词对应的对象
        # 简化实现，返回基础分数
        return 0.6  # 默认中等分数

    def _basic_keyword_matching(self, image_path: str, keywords: List[str]) -> float:
        """
        基础关键词匹配

        Args:
            image_path: 图像路径
            keywords: 关键词列表

        Returns:
            float: 匹配分数 (0-1)
        """
        # 极简实现：基于图像文件名和路径匹配
        image_name = os.path.basename(image_path).lower()
        matches = sum(1 for kw in keywords if kw.lower() in image_name)
        return min(1.0, matches / max(1, len(keywords)))

    def _extract_video_frames(self, video_path: str, num_frames: int = 5) -> List[str]:
        """
        从视频中提取帧

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

            temp_dir = Path('temp_relevance_frames')
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

    def _cleanup_temp_frames(self, frame_paths: List[str]):
        """
        清理临时帧文件

        Args:
            frame_paths: 帧文件路径列表
        """
        for frame_path in frame_paths:
            try:
                if os.path.exists(frame_path):
                    os.remove(frame_path)
            except Exception as e:
                self.logger.error(f"Error removing temp frame {frame_path}: {str(e)}")

        # 尝试删除临时目录
        try:
            temp_dir = Path('temp_relevance_frames')
            if temp_dir.exists() and not any(temp_dir.iterdir()):
                temp_dir.rmdir()
        except:
            pass