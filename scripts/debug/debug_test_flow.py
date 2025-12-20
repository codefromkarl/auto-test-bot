#!/usr/bin/env python3
"""
调试测试流程
"""

import asyncio
import logging
import sys
import os

# 添加src目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from main import AutoTestBot

# 设置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def debug_test_flow():
    """调试测试流程"""
    config_file = 'config/config.yaml'

    try:
        # 创建测试机器人
        bot = AutoTestBot(config_file)
        logger.info("测试机器人创建成功")

        # 初始化
        if not await bot.initialize():
            logger.error("初始化失败")
            return

        logger.info("初始化成功，开始测试")

        # 执行测试
        result = await bot.run_test()

        logger.info(f"测试完成，结果: {result}")

        # 输出结果
        if result.get('overall_success'):
            logger.info("✅ 测试成功完成")
        else:
            error = result.get('error', 'Unknown error')
            logger.error(f"❌ 测试失败: {error}")

    except Exception as e:
        logger.error(f"测试过程中出现异常: {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        # 确保清理资源
        try:
            if 'bot' in locals():
                await bot.cleanup()
                logger.info("资源清理完成")
        except Exception as e:
            logger.error(f"资源清理失败: {e}")

if __name__ == "__main__":
    asyncio.run(debug_test_flow())