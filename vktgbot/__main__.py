"""
Telegram Bot for automated reposting from VKontakte community pages
to Telegram channels.

v3.0
by @alcortazzo
"""

import time

from loguru import logger

import config
from api_requests import get_data_from_vk, get_group_name
from last_id import write_id, read_id
from parse_posts import parse_post
from send_posts import send_post
from tools import blacklist_check, whitelist_check, prepare_temp_folder


def main():
    last_known_id = read_id()
    logger.info(f"Last known ID: {last_known_id}")

    items: dict = get_data_from_vk(
        config.VK_TOKEN,
        config.REQ_VERSION,
        config.VK_DOMAIN,
        config.REQ_FILTER,
        config.REQ_COUNT,
    )

    if "is_pinned" in items[0]:
        items = items[1:]
    logger.info(f"Got a few posts with IDs: {items[-1]['id']} - {items[0]['id']}.")

    new_last_id: int = items[0]["id"]

    if new_last_id > last_known_id:
        for item in items[::-1]:
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
            if "copy_history" in item:
                item_parts["repost"] = item["copy_history"][0]
                group_name = get_group_name(
                    config.VK_TOKEN,
                    config.REQ_VERSION,
                    item["copy_history"][0]["owner_id"],
                )
                logger.info("Detected repost in the post.")

            for item_part in item_parts:
                prepare_temp_folder()
                repost_exists = True if len(item_parts) > 1 else False

                logger.info(f"Starting parsing of the {item_part}")
                parsed_post = parse_post(
                    item_parts[item_part], repost_exists, item_part, group_name
                )
                logger.info(f"Starting sending of the {item_part}")
                send_post(
                    config.TG_CHANNEL,
                    parsed_post["text"],
                    parsed_post["photos"],
                    parsed_post["docs"],
                )

        write_id(new_last_id)


if __name__ == "__main__":
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
            main()
            prepare_temp_folder()
            if config.SINGLE_START:
                logger.info("Script has successfully completed its execution")
                exit()
            else:
                logger.info(f"Script went to sleep for {config.TIME_TO_SLEEP} seconds.")
                time.sleep(config.TIME_TO_SLEEP)

        except KeyboardInterrupt:
            logger.info("Script is stopped by the user.")
            exit()
