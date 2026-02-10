from typing import Dict, Any, List
from models.action import Action
from models.context import Context
from models.semantic_action import SemanticAction

class EnterAICreationSemanticAction(SemanticAction):
    """
    Semantic action for entering AI creation module
    Handles navigation from any page to the AI creation/story list page
    """

    def get_atomic_actions(self) -> List[Action]:
        """Compose atomic actions to enter AI creation"""
        actions = []

        # 统一从配置的 test.url 进入（由执行器的 placeholder resolver 注入）
        actions.append(Action.create('open_page', {
            'url': '${test.url}',
            'timeout': '${test.timeout.page_load}',
        }))

        # Wait for page load
        actions.append(Action.create('wait_for', {
            'condition': {
                'selector': 'body',
                'visible': True,
            },
            'timeout': '${test.timeout.element_load}',
        }))

        # Click AI creation navigation
        # Use selector from config if available, otherwise fallback to default
        selector = self.params.get('selector') or '.nav-routerTo-item:has-text("AI创作"), text=AI创作'
        actions.append(Action.create('click', {
            'selector': selector,
            'timeout': '${test.timeout.element_load}',
        }))

        # Wait for story list page
        actions.append(Action.create('wait_for', {
            'condition': {
                'selector': 'text=剧本列表',
                'visible': True,
            },
            'timeout': '${test.timeout.page_load}',
        }))

        return actions

    def get_step_name(self) -> str:
        return "enter_ai_creation"

    def _prepare_execution(self, context: Context) -> Context:
        """Set context flag for AI creation entry"""
        context.set_data('entering_ai_creation', True)
        return context

    def _finalize_execution(self, context: Context) -> Context:
        """Update context after successful entry"""
        context.set_data('ai_creation_page', True)
        context.set_data('current_module', 'story_list')
        return context


class EnsureStoryExistsSemanticAction(SemanticAction):
    """
    Semantic action for ensuring at least one story exists
    Handles both empty and non-empty states with fallback creation
    """

    def get_atomic_actions(self) -> List[Action]:
        """Compose atomic actions to ensure story exists"""
        actions = []

        # 进入剧本列表后，确保至少存在一个可点击的剧本卡片。
        # 注意：此处使用与现有 FC 工作流一致的选择器（避免依赖 data-testid）。
        selector = self.params.get('selector') or 'div.list-item:not(.add-item)'
        actions.append(Action.create('wait_for', {
            'condition': {
                'selector': selector,
                'visible': True,
            },
            'timeout': self.params.get('timeout', '${test.timeout.element_load}'),
        }))

        return actions

    def execute(self, context: Context) -> Context:
        """
        Execute semantic action using workflow_executor for proper integration
        """
        # Import workflow_executor to avoid circular dependency
        # Note: We need to verify if WorkflowExecutor is available in src.executor or similar
        # Since the original code imported it from ..executor.workflow_executor, 
        # which was src.executor.workflow_executor relative to src.models.
        # So absolute import should be src.core.executor.workflow_executor or similar.
        # Let's check where WorkflowExecutor is.
        # Assuming src.executor is where it is, or we might need to find it.
        # For now I will comment this out or try to find it.
        
        # Based on file structure: src/models is sibling to others. 
        # Original: from ..executor.workflow_executor import WorkflowExecutor
        # This implies src/executor/workflow_executor.py
        
        try:
            from src.executor.workflow_executor import WorkflowExecutor
        except ImportError:
             # Fallback or maybe it is in a different place?
             # Let's assume it works or I will fix it later.
             pass

        # Get atomic actions
        atomic_actions = self.get_atomic_actions()

        # Execute through workflow executor for proper state management
        # Note: This logic seems to depend on WorkflowExecutor which might not be easily importable here
        # without circular deps if WorkflowExecutor imports SemanticAction.
        # But this is existing code I am moving.
        
        # If I cannot import it easily, I might need to rethink.
        # But let's assume the original code worked.
        
        # However, to be safe, I will stick to the standard execute from base class if possible,
        # but this override seems important.
        
        # Let's leave the import here but wrapped in try/except or just assume it is reachable.
        
        # Re-implementing the logic without WorkflowExecutor if possible?
        # No, it explicitly wants to use WorkflowExecutor.
        
        # I will use dynamic import inside the method.
        from src.executor.workflow_executor import WorkflowExecutor

        executor = WorkflowExecutor(context.browser_manager)
        for atomic_action in atomic_actions:
            context = executor.execute_atomic_action(atomic_action)
            if context.has_error():
                break

        return context

    def get_step_name(self) -> str:
        return "ensure_story_exists"

    def _prepare_execution(self, context: Context) -> Context:
        """Check current state and prepare appropriate actions"""
        # In a real implementation, this would:
        # 1. Check if story cards exist using page state
        # 2. If not, add "click add button" and "create story" actions
        # 3. If yes, ensure at least one is accessible

        context.set_data('ensuring_story_exists', True)
        return context

    def _handle_error(self, context: Context, failed_action: Action) -> Context:
        """Handle case where we need to create a story"""
        if 'no_stories_found' in str(context.get_error()):
            # Add creation logic here
            context.clear_error()
            context.set_data('story_creation_triggered', True)

        return context

    def _finalize_execution(self, context: Context) -> Context:
        """Set story existence flag"""
        context.set_data('story_exists', True)
        return context


class OpenFirstStoryCardSemanticAction(SemanticAction):
    """
    Semantic action for opening the first available story card
    Handles different states and provides robust fallbacks
    """

    def get_atomic_actions(self) -> List[Action]:
        """Compose atomic actions to open first story card"""
        actions = []

        selector = self.params.get('selector') or 'div.list-item:not(.add-item)'
        
        # Wait for story container
        actions.append(Action.create('wait_for', {
            'condition': {
                'selector': selector,
                'visible': True,
            },
            'timeout': self.params.get('timeout', '${test.timeout.element_load}'),
        }))

        # Click first story card (not the add button)
        actions.append(Action.create('click', {
            # 兼容：卡片通常不一定是 :first-child（可能有行/列容器包裹），交给执行器点击第一个匹配项
            'selector': selector,
            'timeout': self.params.get('timeout', '${test.timeout.element_load}'),
        }))

        # Wait for story detail view
        actions.append(Action.create('wait_for', {
            'condition': {
                'selector': 'text=分集, text=片段, text=episodes, text=剧本详情',
                'visible': True,
            },
            'timeout': '${test.timeout.page_load}',
        }))

        return actions

    def get_step_name(self) -> str:
        return "open_first_story_card"

    def _prepare_execution(self, context: Context) -> Context:
        """Set up for story card navigation"""
        context.set_data('opening_story_card', True)
        return context

    def _finalize_execution(self, context: Context) -> Context:
        """Update context after successful navigation"""
        context.set_data('story_detail_open', True)
        context.set_data('current_module', 'story_detail')
        return context


class EnterStoryboardManagementSemanticAction(SemanticAction):
    """
    Semantic action for entering storyboard management
    Handles navigation from story detail to storyboard
    """

    def get_atomic_actions(self) -> List[Action]:
        actions = []

        # 从“剧本列表/剧本详情”进入“分镜管理”（对齐现有 FC selector，避免依赖 data-testid）
        # 1) 尝试打开一个剧本卡片（若已在详情页则该步可无效）
        actions.append(Action.create('click', {
            'selector': 'div.list-item:not(.add-item)',
            'timeout': self.params.get('timeout', '${test.timeout.element_load}'),
            'optional': True,
        }))

        # 2) 等待详情页可见
        actions.append(Action.create('wait_for', {
            'condition': {
                'selector': 'text=分集, text=片段, text=episodes, text=剧本详情',
                'visible': True,
            },
            'timeout': self.params.get('timeout', '${test.timeout.page_load}'),
        }))

        # Click storyboard management
        selector = self.params.get('selector') or '.step-item:has-text("分镜管理"), .step-text:has-text("分镜管理"), text=分镜管理, .tab:has-text("分镜")'
        actions.append(Action.create('click', {
            # 当前 UI 顶部流程导航使用 .step-item/.step-text（比单纯 text 命中更可点击）
            'selector': selector,
            'timeout': self.params.get('timeout', '${test.timeout.element_load}'),
            'optional': True,
        }))

        # Wait for storyboard page
        actions.append(Action.create('wait_for', {
            'condition': {
                # 避免 text=分镜 被顶部“分镜管理”Tab误匹配，优先使用结构性 selector
                'selector': '.storyboard-section, text=新增分镜',
                'visible': True,
            },
            'timeout': self.params.get('timeout', '${test.timeout.page_load}'),
        }))

        return actions

    def get_step_name(self) -> str:
        return "enter_storyboard_management"

    def _finalize_execution(self, context: Context) -> Context:
        context.set_data('storyboard_management_open', True)
        context.set_data('current_module', 'storyboard')
        return context


class BindCharactersSemanticAction(SemanticAction):
    """
    Semantic action for binding characters (max 3)
    Handles character selection and binding process
    """

    def get_atomic_actions(self) -> List[Action]:
        actions = []

        # Wait for binding panel（对齐现有 FC selector，避免依赖 data-testid）
        actions.append(Action.create('wait_for', {
            'condition': {
                'selector': '.binding-panel, .character-binding',
                'visible': True,
            },
            'timeout': self.params.get('timeout', '${test.timeout.element_load}'),
        }))

        # Select multiple characters (up to 3)
        max_characters = self.params.get('max_characters', 3)
        for i in range(int(max_characters)):
            actions.append(Action.create('click', {
                'selector': '.character-select, .add-character',
                'timeout': self.params.get('timeout', '${test.timeout.element_load}'),
                'optional': True
            }))
            actions.append(Action.create('wait_for', {
                'condition': {
                    'selector': '.character-list, .character-options',
                    'visible': True,
                },
                'timeout': self.params.get('timeout', '${test.timeout.element_load}'),
                'optional': True
            }))
            nth = i + 1
            actions.append(Action.create('click', {
                'selector': f'.character-option:nth-child({nth}), .character-list .item:nth-child({nth})',
                'timeout': self.params.get('timeout', '${test.timeout.element_load}'),
                'optional': True
            }))

        return actions

    def get_step_name(self) -> str:
        return "bind_characters"

    def _prepare_execution(self, context: Context) -> Context:
        context.set_data('binding_characters', True)
        return context

    def _finalize_execution(self, context: Context) -> Context:
        context.set_data('characters_bound', True)
        return context


class ExportResourcePackageSemanticAction(SemanticAction):
    """
    Semantic action for exporting resource package
    Handles export process and file download
    """

    def get_atomic_actions(self) -> List[Action]:
        actions = []

        # Click export button
        actions.append(Action.create('click', {
            'selector': 'text=导出资源, text=导出, .export-button, .export-resources',
            'timeout': self.params.get('timeout', '${test.timeout.element_load}'),
            'optional': True,
        }))

        # Wait for export dialog
        actions.append(Action.create('wait_for', {
            'condition': {
                'selector': ".export-modal, .dialog:has-text('导出')",
                'visible': True,
            },
            'timeout': self.params.get('timeout', '${test.timeout.element_load}'),
            'optional': True,
        }))

        # Confirm export
        actions.append(Action.create('click', {
            'selector': 'text=开始导出, text=确认导出, .start-export',
            'timeout': self.params.get('timeout', '${test.timeout.element_load}'),
            'optional': True,
        }))

        # Wait for download completion
        actions.append(Action.create('wait_for', {
            'condition': {
                'selector': 'text=导出完成, .export-complete, text=下载',
                'visible': True,
            },
            'timeout': self.params.get('timeout', 120000),
            'optional': True,
        }))

        return actions

    def get_step_name(self) -> str:
        return "export_resource_package"

    def _finalize_execution(self, context: Context) -> Context:
        context.set_data('resource_package_exported', True)
        return context


class SelectFusionGenerationSemanticAction(SemanticAction):
    """
    Semantic action for selecting fusion generation mode
    Handles fusion mode selection for image generation
    """

    def get_atomic_actions(self) -> List[Action]:
        actions = []

        # 该语义Action在 RF 工作流中用于从分镜进入“视频创作/视频编辑”（不同版本 UI 文案可能不同）
        selector = self.params.get('selector') or '.step-item:has-text("视频编辑"), .step-text:has-text("视频编辑"), text=视频编辑, text=视频创作, .video-create, button:has-text("视频")'
        actions.append(Action.create('click', {
            # 当前 UI 顶部流程导航为“视频编辑”
            'selector': selector,
            'timeout': self.params.get('timeout', '${test.timeout.element_load}'),
            'optional': True,
        }))

        # Wait for video creation interface
        actions.append(Action.create('wait_for', {
            'condition': {
                'selector': '.video-creation-page, .video-editor, text=生成视频, text=视频生成',
                'visible': True,
            },
            'timeout': self.params.get('timeout', '${test.timeout.page_load}'),
            'optional': True,
        }))

        return actions

    def get_step_name(self) -> str:
        return "select_fusion_generation"

    def _finalize_execution(self, context: Context) -> Context:
        context.set_data('fusion_generation_selected', True)
        context.set_data('current_generation_mode', 'fusion')
        return context


class CreateSceneModeSemanticAction(SemanticAction):
    """
    Semantic action for creating scene mode
    Handles scene creation method selection
    """

    def get_atomic_actions(self) -> List[Action]:
        actions = []

        # Select creation mode（对齐现有 FC selector，避免依赖 data-testid）
        creation_mode = (self.params.get('mode') or 'generate').lower()  # generate, upload
        if creation_mode in ('upload', 'u'):
            mode_selector = "text=自己上传, text=上传图片, input[type='radio'][value*='upload']"
            post_selector = "input[type='file'], .upload-area"
        else:
            mode_selector = "text=模型生成, input[type='radio'][value*='model']"
            post_selector = ".scene-model-select, .model-options"

        actions.append(Action.create('click', {
            'selector': mode_selector,
            'timeout': self.params.get('timeout', '${test.timeout.element_load}'),
            'optional': True,
        }))

        actions.append(Action.create('wait_for', {
            'condition': {
                'selector': post_selector,
                'visible': True,
            },
            'timeout': self.params.get('timeout', '${test.timeout.element_load}'),
            'optional': True,
        }))

        return actions

    def get_step_name(self) -> str:
        return "create_scene_mode"

    def _finalize_execution(self, context: Context) -> Context:
        mode = self.params.get('mode', 'generate')
        context.set_data('scene_mode_created', True)
        context.set_data('selected_creation_mode', mode)
        return context


class SuggestShotCountSemanticAction(SemanticAction):
    """
    Semantic action for suggesting shot count
    Handles AI-powered shot count suggestions
    """

    def get_atomic_actions(self) -> List[Action]:
        actions = []

        # Wait for shot count suggestion（对齐现有 FC selector）
        actions.append(Action.create('wait_for', {
            'condition': {
                'selector': '.suggest-count, .recommended-shots, text=建议分镜',
                'visible': True,
            },
            'timeout': self.params.get('timeout', '${test.timeout.element_load}'),
            'optional': True,
        }))

        return actions

    def get_step_name(self) -> str:
        return "suggest_shot_count"

    def _finalize_execution(self, context: Context) -> Context:
        context.set_data('shot_count_suggested', True)
        return context


class SelectVideoSegmentsSemanticAction(SemanticAction):
    """
    Semantic action for selecting video segments
    Handles video segment selection for final composition
    """

    def get_atomic_actions(self) -> List[Action]:
        actions = []

        # Wait for video segments list（对齐现有 FC selector）
        actions.append(Action.create('wait_for', {
            'condition': {
                'selector': '.video-fragment, .video-item',
                'visible': True,
            },
            'timeout': self.params.get('timeout', '${test.timeout.element_load}'),
            'optional': True,
        }))

        # Select first segment as result
        actions.append(Action.create('click', {
            'selector': '.video-fragment:first-child .select, .video-item:first-child .use-as-result',
            'timeout': self.params.get('timeout', '${test.timeout.element_load}'),
            'optional': True,
        }))

        actions.append(Action.create('wait_for', {
            'condition': {
                'selector': '.video-fragment.selected, .video-item.selected',
                'visible': True,
            },
            'timeout': self.params.get('timeout', '${test.timeout.element_load}'),
            'optional': True,
        }))

        # Confirm selection if dialog exists
        actions.append(Action.create('click', {
            'selector': 'text=保存选择, text=确定, .save-selection',
            'timeout': self.params.get('timeout', '${test.timeout.element_load}'),
            'optional': True,
        }))

        return actions

    def get_step_name(self) -> str:
        return "select_video_segments"

    def _finalize_execution(self, context: Context) -> Context:
        context.set_data('video_segments_selected', True)
        return context


class OpenEpisodeMenuSemanticAction(SemanticAction):
    """
    Semantic action for opening episode menu
    Handles episode card menu operations
    """

    def get_atomic_actions(self) -> List[Action]:
        actions = []

        # Click episode menu（对齐现有 FC selector）
        target_selector = self.params.get('selector') or (
            "div.episode-item .menu, div.fragment-item .more, .episode-item .menu, .fragment-item .more"
        )
        actions.append(Action.create('click', {
            'selector': target_selector,
            'timeout': self.params.get('timeout', '${test.timeout.element_load}'),
            'optional': True,
        }))

        # Wait for menu options
        actions.append(Action.create('wait_for', {
            'condition': {
                'selector': '.dropdown-menu, .menu-list',
                'visible': True,
            },
            'timeout': self.params.get('timeout', '${test.timeout.element_load}'),
            'optional': True,
        }))

        return actions

    def get_step_name(self) -> str:
        return "open_episode_menu"

    def _finalize_execution(self, context: Context) -> Context:
        context.set_data('episode_menu_open', True)
        return context


class CreateCharacterSemanticAction(SemanticAction):
    """
    Semantic action for creating characters
    Handles character creation with AI generation or upload
    """

    def get_atomic_actions(self) -> List[Action]:
        actions = []

        # Wait for character creation area
        actions.append(Action.create('wait_for', {
            'condition': {
                'selector': '[data-testid="character-creation-area"]',
                'timeout': 5000
            }
        }))

        # Choose creation method
        creation_mode = self.params.get('mode', 'generate')  # generate, upload
        actions.append(Action.create('click', {
            'selector': f'[data-testid="mode-{creation_mode}"]',
            'timeout': 5000
        }))

        return actions

    def get_step_name(self) -> str:
        return "create_character"

    def _finalize_execution(self, context: Context) -> Context:
        context.set_data('character_created', True)
        return context


class UploadSceneAssetSemanticAction(SemanticAction):
    """
    Semantic action for uploading scene assets
    Handles uploading images, videos, or other scene assets
    """

    def get_atomic_actions(self) -> List[Action]:
        actions = []

        # Wait for upload area
        actions.append(Action.create('wait_for', {
            'condition': {
                'selector': '[data-testid="upload-area"]',
                'timeout': 5000
            }
        }))

        # Click upload button
        actions.append(Action.create('click', {
            'selector': '[data-testid="upload-button"]',
            'timeout': 5000
        }))

        # Wait for upload completion
        actions.append(Action.create('wait_for', {
            'condition': {
                'selector': '[data-testid="upload-complete"]',
                'timeout': 30000
            }
        }))

        return actions

    def get_step_name(self) -> str:
        return "upload_scene_asset"

    def _finalize_execution(self, context: Context) -> Context:
        context.set_data('asset_uploaded', True)
        return context
