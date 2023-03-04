import asyncio

from aiogram import Bot, types
from aiogram.utils import exceptions
from loguru import logger

from tools import split_text


async def send_post(bot: Bot, tg_channel: str, text: str, photos: list, docs: list, config_name: str) -> None:
    """Send post to Telegram channel.

    Args:
        bot (Bot): Bot instance.
        tg_channel (str): Unique identifier for the target chat or username of the target channel.
        text (str): Post text.
        photos (list): List of photos.
        docs (list): List of documents.
        config_name (str): Name of config.
    """
    num_tries = 1
    while num_tries <= 5:
        num_tries += 1
        try:
            if len(photos) == 0:
                await send_text_post(bot, tg_channel, text, config_name)
            elif len(photos) == 1:
                await send_photo_post(bot, tg_channel, text, photos, config_name)
            elif len(photos) >= 2:
                await send_photos_post(bot, tg_channel, text, photos, config_name)
            if docs:
                await send_docs_post(bot, tg_channel, docs, config_name)
            break
        except exceptions.RetryAfter as ex:
            logger.warning(
                f"{config_name} - Flood limit is exceeded. Sleep {ex.timeout + 10} seconds. Try: {num_tries - 1}."
            )
            await asyncio.sleep(ex.timeout + 10)
        except exceptions.BadRequest as ex:
            logger.warning(f"{config_name} - Bad request. Wait 60 seconds. Try: {num_tries}. {ex}")
            await asyncio.sleep(60)
        if num_tries > 5:
            logger.error(f"{config_name} - Post was not sent to Telegram. Too many tries.")


async def send_text_post(bot: Bot, tg_channel: str, text: str, config_name: str) -> None:
    """Send text post to Telegram channel."""
    if not text:
        return

    if len(text) < 4096:
        await bot.send_message(tg_channel, text, parse_mode=types.ParseMode.HTML)
    else:
        text_parts = split_text(text, 4084)
        prepared_text_parts = (
            [text_parts[0] + " (...)"]
            + ["(...) " + part + " (...)" for part in text_parts[1:-1]]
            + ["(...) " + text_parts[-1]]
        )

        for part in prepared_text_parts:
            await bot.send_message(tg_channel, part, parse_mode=types.ParseMode.HTML)
            await asyncio.sleep(0.5)
    logger.info(f"{config_name} - Text post sent to Telegram.")


async def send_photo_post(bot: Bot, tg_channel: str, text: str, photos: list, config_name: str) -> None:
    """Send post with one photo to Telegram channel."""
    if len(text) <= 1024:
        await bot.send_photo(tg_channel, photos[0], text, parse_mode=types.ParseMode.HTML)
        logger.info(f"{config_name} - Text post (<=1024) with photo sent to Telegram.")
    else:
        prepared_text = f'<a href="{photos[0]}"> </a>{text}'
        if len(prepared_text) <= 4096:
            await bot.send_message(tg_channel, prepared_text, parse_mode=types.ParseMode.HTML)
        else:
            await send_text_post(bot, tg_channel, text, config_name)
            await bot.send_photo(tg_channel, photos[0])
        logger.info(f"{config_name} - Text post (>1024) with photo sent to Telegram.")


async def send_photos_post(bot: Bot, tg_channel: str, text: str, photos: list, config_name: str) -> None:
    """Send post with multiple photos to Telegram channel."""
    media = types.MediaGroup()
    for photo in photos:
        media.attach_photo(types.InputMediaPhoto(photo))

    if (len(text) > 0) and (len(text) <= 1024):
        media.media[0].caption = text
        media.media[0].parse_mode = types.ParseMode.HTML
    elif len(text) > 1024:
        await send_text_post(bot, tg_channel, text, config_name)
    await bot.send_media_group(tg_channel, media)
    logger.info(f"{config_name} - Text post with photos sent to Telegram.")


async def send_docs_post(bot: Bot, tg_channel: str, docs: list, config_name: str) -> None:
    """Send documents to Telegram channel."""
    media = types.MediaGroup()
    for doc in docs:
        media.attach_document(types.InputMediaDocument(open(f"./temp/{config_name}/{doc['title']}", "rb")))
    await bot.send_media_group(tg_channel, media)
    logger.info(f"{config_name} - Documents sent to Telegram.")
