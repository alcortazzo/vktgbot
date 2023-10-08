import asyncio
from typing import Literal

from aiogram import Bot
from loguru import logger

from vktgbot import api_requests, tools
from vktgbot.config import Config, ConfigParameters
from vktgbot.parse_posts import parse_post
from vktgbot.send_posts import send_post


class BotInstance:
    def __init__(self, config_name: str) -> None:
        self.config_name: str = config_name

        self.config: Config
        self.config_parameters: ConfigParameters
        self.bot: Bot

    async def __aenter__(self) -> "BotInstance":
        self.__refresh_config()
        await self.__init_bot()

        logger.info("Bot instance for {self.config_name} was initialized.")

        return self

    async def __aexit__(self, *args) -> None:
        await self.__close_bot_session()
        logger.info("Bot instance was closed.")

    def __refresh_config(self) -> None:
        """Updates config and config_parameters attributes."""
        self.config = Config()
        self.config_parameters = self.config.config[self.config_name]

    async def __init_bot(self) -> None:
        self.bot = Bot(token=self.config_parameters.tg_bot_token)
        logger.debug(f"{self.config_name} - Bot was initialized.")

    async def __close_bot_session(self) -> None:
        await self.bot.session.close()
        logger.debug(f"{self.config_name} - Bot session was closed.")

    async def start(self) -> None:
        while True:
            self.__refresh_config()

            logger.info(f"{self.config_name} - Last known ID: {self.config_parameters.last_kwown_post_id}")

            posts: list[dict] = await api_requests.get_data_from_vk(self.config_parameters, self.config_name)
            if not posts:
                await self.__close_bot_session()
                logger.info(
                    f"{self.config_name} - No posts were found. Sleeping for {self.config_parameters.time_to_sleep} seconds."
                )
                await asyncio.sleep(self.config_parameters.time_to_sleep)
                continue

            if "is_pinned" in posts[0]:
                posts = posts[1:]
            logger.info(f"{self.config_name} - Got a few posts with IDs: {posts[-1]['id']} - {posts[0]['id']}.")

            new_last_id: int = posts[0]["id"]

            if new_last_id > self.config_parameters.last_kwown_post_id:
                for post in posts[::-1]:
                    if post["id"] <= self.config_parameters.last_kwown_post_id:
                        continue
                    logger.info(f"{self.config_name} - Working with post with ID: {post['id']}.")
                    if tools.blacklist_check(self.config_parameters.blacklist, post["text"]):
                        continue
                    if tools.whitelist_check(self.config_parameters.whitelist, post["text"]):
                        continue
                    if self.config_parameters.skip_ads_posts and post["marked_as_ads"]:
                        logger.info(f"{self.config_name} - Post was skipped as an advertisement.")
                        continue
                    if self.config_parameters.skip_copyrighted_posts and "copyright" in post:
                        logger.info(f"{self.config_name} - Post was skipped as an copyrighted post.")
                        continue

                    post_parts: dict[Literal["post", "repost"], dict] = {"post": post}
                    group_name: str = ""
                    repost_exists: bool = False
                    if "copy_history" in post and not self.config_parameters.skip_reposts:
                        repost_exists = True
                        post_parts["repost"] = post["copy_history"][0]
                        group_name = await api_requests.get_group_name(
                            self.config_parameters, abs(post_parts["repost"]["owner_id"]), self.config_name
                        )
                        logger.info(f"{self.config_name} - Detected repost in the post.")

                    for post_type, post_item in post_parts.items():
                        tools.prepare_folder(self.config_name, "temp")

                        logger.info(f"{self.config_name} - Starting parsing of the {post_type}")
                        parsed_post = await parse_post(
                            post=post_item,
                            repost_exists=repost_exists,
                            post_type=post_type,
                            group_name=group_name,
                            config_parameters=self.config_parameters,
                            config_name=self.config_name,
                        )
                        logger.info(f"{self.config_name} - Starting sending of the {post_type}")
                        await send_post(
                            self.bot,
                            self.config_parameters.tg_channel,
                            parsed_post["text"],
                            parsed_post["photos"],
                            parsed_post["docs"],
                            self.config_name,
                        )

            await self.__close_bot_session()

            self.config.update_last_known_id(self.config_name, new_last_id)
            logger.info(f"{self.config_name} - Last known ID was updated to {new_last_id}.")
            if not self.config_parameters.single_start:
                logger.info(f"{self.config_name} - Sleeping for {self.config_parameters.time_to_sleep} seconds.")
                await asyncio.sleep(self.config_parameters.time_to_sleep)
            else:
                break


async def start_bot_instance(config_name: str):
    async with BotInstance(config_name=config_name) as bot_instance:
        await bot_instance.start()
