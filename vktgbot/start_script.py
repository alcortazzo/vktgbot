import asyncio

from aiogram import Bot
from loguru import logger

from api_requests import get_data_from_vk, get_group_name
from config import Config, ConfigParameters
from parse_posts import parse_post
from send_posts import send_post
from tools import blacklist_check, prepare_folder, whitelist_check


async def start_script(config_name: str):
    while True:
        prepare_folder(config_name, "temp")
        config_cls = Config()
        config: ConfigParameters = config_cls.config[config_name]
        logger.info(f"{config_name} - Last known ID: {config.last_kwown_post_id}")

        items: list[dict] = await get_data_from_vk(config, config_name)
        if not items:
            logger.info(f"{config_name} - No posts were found. Sleeping for {config.time_to_sleep} seconds.")
            await asyncio.sleep(config.time_to_sleep)
            continue

        if "is_pinned" in items[0]:
            items = items[1:]
        logger.info(f"{config_name} - Got a few posts with IDs: {items[-1]['id']} - {items[0]['id']}.")

        new_last_id: int = items[0]["id"]

        if new_last_id > config.last_kwown_post_id:
            bot = Bot(token=config.tg_bot_token)

            for item in items[::-1]:
                if item["id"] <= config.last_kwown_post_id:
                    continue
                logger.info(f"{config_name} - Working with post with ID: {item['id']}.")
                if blacklist_check(config.blacklist, item["text"]):
                    continue
                if whitelist_check(config.whitelist, item["text"]):
                    continue
                if config.skip_ads_posts and item["marked_as_ads"]:
                    logger.info(f"{config_name} - Post was skipped as an advertisement.")
                    continue
                if config.skip_copyrighted_posts and "copyright" in item:
                    logger.info(f"{config_name} - Post was skipped as an copyrighted post.")
                    continue

                item_parts = {"post": item}
                group_name = ""
                if "copy_history" in item and not config.skip_reposts:
                    item_parts["repost"] = item["copy_history"][0]
                    group_name = await get_group_name(config, abs(item_parts["repost"]["owner_id"]), config_name)
                    logger.info(f"{config_name} - Detected repost in the post.")

                for item_part in item_parts:
                    prepare_folder(config_name, "temp")
                    repost_exists: bool = True if len(item_parts) > 1 else False

                    logger.info(f"{config_name} - Starting parsing of the {item_part}")
                    parsed_post = await parse_post(
                        item_parts[item_part], repost_exists, item_part, group_name, config, config_name
                    )
                    logger.info(f"{config_name} - Starting sending of the {item_part}")
                    await send_post(
                        bot,
                        config.tg_channel,
                        parsed_post["text"],
                        parsed_post["photos"],
                        parsed_post["docs"],
                        config_name,
                    )
            await bot.close()

        config_cls.update_last_known_id(config_name, new_last_id)
        logger.info(f"{config_name} - Last known ID was updated to {new_last_id}.")
        if not config.single_start:
            logger.info(f"{config_name} - Sleeping for {config.time_to_sleep} seconds.")
            await asyncio.sleep(config.time_to_sleep)
        else:
            break
