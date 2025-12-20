"""
Content validation package
内容验证模块

Provides comprehensive content quality validation capabilities including:
- Image resolution and quality checks
- Video duration and format validation
- Character and scene consistency validation
- Content relevance scoring

遵循项目三层架构原则：
- Data Layer: 验证数据和配置
- Business Layer: 验证逻辑和规则
- Presentation Layer: 验证报告和结果输出
"""

from .content_validator import ContentValidator
from .image_validator import ImageValidator
from .video_validator import VideoValidator
from .consistency_validator import ConsistencyValidator
from .relevance_scorer import RelevanceScorer
from .validation_report import ValidationReport

__all__ = [
    'ContentValidator',
    'ImageValidator',
    'VideoValidator',
    'ConsistencyValidator',
    'RelevanceScorer',
    'ValidationReport'
]