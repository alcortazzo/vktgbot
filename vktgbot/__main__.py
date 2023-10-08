"""
Telegram Bot for automated reposting from VKontakte community pages
to Telegram channels.

v4.0
by @alcortazzo
"""

import asyncio
from asyncio import CancelledError, Task

from loguru import logger

from vktgbot import tools
from vktgbot.config import Config
from vktgbot.start_script import start_bot_instance

logger.add(
    "./logs/debug.log",
    format="{time} {level} {message}",
    level="DEBUG",
    rotation="1 week",
    retention="1 month",
    compression="zip",
)

logger.info("Script is started.")


@logger.catch(reraise=True)
async def main():
    """
    Main function that creates tasks of start_script
    function for each section in config.
    """
    try:
        config = Config()
        tools.prepare_folder("temp")
        async_tasks: list[Task] = []

        # Create tasks for each section in config
        for config_name in config.config.keys():
            logger.info(f"Bot '{config_name}' is started.")
            async_task = asyncio.create_task(coro=start_bot_instance(config_name), name=config_name)
            async_tasks.append(async_task)

        # Wait for tasks to finish and remove them from the list.
        # Some tasks will never finish because they are infinite loops.
        while True:
            await asyncio.sleep(1)
            if not len(async_tasks):
                break

            for async_task in async_tasks[:]:
                if async_task.done():
                    async_task.result()
                    logger.info(f"Bot '{async_task.get_name()}' is stopped.")
                    async_tasks.remove(async_task)

    except (KeyboardInterrupt, CancelledError):
        logger.info("Script is stopped by user.")
    logger.info("Script is stopped.")


if __name__ == "__main__":
    asyncio.run(main())
