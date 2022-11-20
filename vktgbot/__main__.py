"""
Telegram Bot for automated reposting from VKontakte community pages
to Telegram channels.

v4.0
by @alcortazzo
"""

import asyncio
from asyncio import Task

from loguru import logger

from config import Config
from start_script import start_script
from tools import prepare_folder


logger.add(
    "./logs/debug.log",
    format="{time} {level} {message}",
    level="DEBUG",
    rotation="1 week",
    compression="zip",
)

logger.info("Script is started.")


@logger.catch(reraise=True)
async def main():
    try:
        config = Config()
        prepare_folder("temp")
        async_tasks: dict[str, Task] = {}

        for config_name in config.config.keys():
            logger.info(f"Bot '{config_name}' is started.")
            async_task = asyncio.create_task(start_script(config_name))
            async_tasks[config_name] = async_task

        while True:
            await asyncio.sleep(1)
            if not len(async_tasks):
                break
            async_tasks_to_remove: list[str] = []

            for config_name, async_task in async_tasks.items():
                if async_task.done():
                    async_task.result()
                    logger.info(f"Bot '{config_name}' is stopped.")
                    async_tasks_to_remove.append(config_name)

            for config_name in async_tasks_to_remove:
                async_tasks.pop(config_name)
    except KeyboardInterrupt:
        logger.info("Script is stopped by user.")
    logger.info("Script is stopped.")


asyncio.run(main())
