from typing import Union

from aiogram import Bot, Dispatcher
from aiogram.utils import executor
from loguru import logger

import config
from api_requests import get_data_from_vk, get_group_name
from last_id import read_id, write_id
from parse_posts import parse_post
from send_posts import send_post
from tools import blacklist_check, prepare_temp_folder, whitelist_check


def start_script():
    bot = Bot(token=config.TG_BOT_TOKEN)
    dp = Dispatcher(bot)

    last_known_id = read_id()
    logger.info(f"Last known ID: {last_known_id}")

    items: Union[dict, None] = get_data_from_vk(
        config.VK_TOKEN,
        config.REQ_VERSION,
        config.VK_DOMAIN,
        config.REQ_FILTER,
        config.REQ_COUNT,
    )
    if not items:
        return

    if "is_pinned" in items[0]:
        items = items[1:]
    logger.info(f"Got a few posts with IDs: {items[-1]['id']} - {items[0]['id']}.")

    new_last_id: int = items[0]["id"]

    if new_last_id > last_known_id:
        for item in items[::-1]:
            item: dict
            if item["id"] <= last_known_id:
                continue
            logger.info(f"Working with post with ID: {item['id']}.")
            if blacklist_check(config.BLACKLIST, item["text"]):
                continue
            if whitelist_check(config.WHITELIST, item["text"]):
                continue
            if config.SKIP_ADS_POSTS and item["marked_as_ads"]:
                logger.info("Post was skipped as an advertisement.")
                continue
            if config.SKIP_COPYRIGHTED_POST and "copyright" in item:
                logger.info("Post was skipped as an copyrighted post.")
                continue

            item_parts = {"post": item}
            group_name = ""
            if "copy_history" in item and not config.SKIP_REPOSTS:
                item_parts["repost"] = item["copy_history"][0]
                group_name = get_group_name(
                    config.VK_TOKEN,
                    config.REQ_VERSION,
                    abs(item_parts["repost"]["owner_id"]),
                )
                logger.info("Detected repost in the post.")

            for item_part in item_parts:
                prepare_temp_folder()
                repost_exists: bool = True if len(item_parts) > 1 else False

                logger.info(f"Starting parsing of the {item_part}")
                parsed_post = parse_post(item_parts[item_part], repost_exists, item_part, group_name)
                logger.info(f"Starting sending of the {item_part}")
                executor.start(
                    dp,
                    send_post(
                        bot,
                        config.TG_CHANNEL,
                        parsed_post["text"],
                        parsed_post["photos"],
                        parsed_post["docs"],
                    ),
                )

        write_id(new_last_id)
