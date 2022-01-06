"""
Telegram Bot for automated reposting from VKontakte community pages
to Telegram channels.

v3.0
by @alcortazzo
"""

import time

from loguru import logger

from start_script import start_script
from config import SINGLE_START, TIME_TO_SLEEP
from tools import prepare_temp_folder

logger.add(
    "./logs/debug.log",
    format="{time} {level} {message}",
    level="DEBUG",
    rotation="1 week",
    compression="zip",
)

logger.info("Script is started.")

while True:
    try:
        start_script()
        prepare_temp_folder()
        if SINGLE_START:
            logger.info("Script has successfully completed its execution")
            exit()
        else:
            logger.info(f"Script went to sleep for {TIME_TO_SLEEP} seconds.")
            time.sleep(TIME_TO_SLEEP)
    except KeyboardInterrupt:
        logger.info("Script is stopped by the user.")
        exit()
