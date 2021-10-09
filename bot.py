# Made by @alcortazzo
# v2.4

import os
import re
import sys
import time
import urllib
import config
import logging
import requests
import eventlet
from telebot import TeleBot, types, apihelper
from logging.handlers import TimedRotatingFileHandler

bot = TeleBot(config.tg_bot_token)

if len(str(config.tg_log_channel)) > 5:
    if config.tg_bot_for_log_token != "":
        bot_2 = TeleBot(config.tg_bot_for_log_token)
    else:
        bot_2 = TeleBot(config.tg_bot_token)
    is_bot_for_log = True
else:
    is_bot_for_log = False


if config.proxy_enable:
    apihelper.proxy = {
        "https": f"socks5://{config.proxy_login}:{config.proxy_pass}@{config.proxy_ip}:{config.proxy_port}"
    }


def get_data():
    """Trying to request data from VK using vk_api

    Returns:
        List of N posts from vk.com/xxx, where
            N = config.req_count
            xxx = config.vk_domain
    """
    timeout = eventlet.Timeout(20)
    try:
        data = requests.get(
            "https://api.vk.com/method/wall.get",
            params={
                "access_token": config.vk_token,
                "v": config.reqVer,
                "domain": config.vk_domain,
                "filter": config.req_filter,
                "count": config.req_count,
            },
        )
        return data.json()["response"]["items"]
    except eventlet.timeout.Timeout:
        add_log("w", "Got Timeout while retrieving VK JSON data. Cancelling...")
        return None
    finally:
        timeout.cancel()


def parse_posts(items, last_id):
    """For each post in the received posts list:
        * Сhecks post id to make sure it is larger than the one written in the last_known_id.txt
        * Parses all attachments of post or repost
        * Calls 'compile_links_and_text()' to compile links to videos and other links from post to post text
        * Calls 'send_posts()' to send post to Telegram channel (config.tg_channel)

    Args:
        items (list): List of posts received from VK
        last_id (integer): The current value in the last_known_id.txt
                           (must be less than id of the new post)
    """
    for item in items[::-1]:
        if item["id"] <= last_id:
            continue

        if blacklist_check(item["text"]):
            add_log("i", f"[id:{item['id']}] Post was skipped due to blacklist filter")
            continue

        if whitelist_check(item["text"]):
            add_log("i", f"[id:{item['id']}] Post was skipped due to whitelist filter")
            continue

        if config.skip_ads_posts and item["marked_as_ads"] == 1:
            add_log(
                "i",
                f"[id:{item['id']}] Post was skipped because it was flagged as ad",
            )
            continue
        if config.skip_copyrighted_post and "copyright" in item:
            add_log(
                "i",
                f"[id:{item['id']}] Post was skipped because it has copyright",
            )
            continue
        add_log("i", f"[id:{item['id']}] Bot is working with this post")

        def get_link(attachment):
            try:
                link_object = attachment["link"]["url"]

                if link_object not in text_of_post:
                    return link_object
            except Exception as ex:
                add_log(
                    "e",
                    f'[id:{item["id"]}] [{type(ex).__name__}] in get_link(): {str(ex)}',
                )

        def get_video(attachment):
            def get_video_url(owner_id, video_id, access_key):
                try:
                    data = requests.get(
                        f"https://api.vk.com/method/video.get?"
                        f"access_token={config.vk_token}&"
                        f"v={config.reqVer}&"
                        f"videos={owner_id}_{video_id}_{access_key}"
                    )
                    return data.json()["response"]["items"][0]["files"]["external"]
                except Exception:
                    return None

            try:
                video = get_video_url(
                    attachment["video"]["owner_id"],
                    attachment["video"]["id"],
                    attachment["video"]["access_key"],
                )
                # wait for a few seconds because VK can deactivate the access token due to frequent requests
                time.sleep(2)
                if video is not None:
                    return video
                else:
                    return f"https://vk.com/video{attachment['video']['owner_id']}_{attachment['video']['id']}"
            except Exception as ex:
                add_log(
                    "e",
                    f'[id:{item["id"]}] [{type(ex).__name__}] in get_video(): {str(ex)}',
                )

        def get_photo(attachment):
            try:
                # check the size of the photo and add this photo to the URL list
                # (from large to smaller)
                # photo with type W > Z > Y > X > (...)
                photo_sizes = attachment["photo"]["sizes"]
                photo_types = ["w", "z", "y", "x", "r", "q", "p", "o", "m", "s"]
                for photo_type in photo_types:
                    if next(
                        (item for item in photo_sizes if item["type"] == photo_type),
                        False,
                    ):
                        return next(
                            (
                                item
                                for item in photo_sizes
                                if item["type"] == photo_type
                            ),
                            False,
                        )["url"]
            except Exception as ex:
                add_log(
                    "e",
                    f'[id:{item["id"]}] [{type(ex).__name__}] in get_photo(): {str(ex)}',
                )

        def get_doc(attachment):
            docurl = attachment["doc"]["url"]
            extension = attachment["doc"]["ext"]
            doc_title = attachment["doc"]["title"]
            return docurl

        def get_public_name_by_id(id):
            try:
                data = requests.get(
                    f"https://api.vk.com/method/groups.getById?access_token={config.vk_token}&v=5.103&group_id={id}"
                )
                return data.json()["response"][0]["name"]
            except Exception as ex:
                add_log(
                    "e",
                    f'[id:{item["id"]}] [{type(ex).__name__}] in get_public_name_by_id(): {str(ex)}',
                )
                return ""

        def parse_attachments(item, linklist, vidlist, photolist, docslist):
            try:
                for attachment in item["attachments"]:
                    if attachment["type"] == "link":
                        linklist.append(get_link(attachment))
                    elif attachment["type"] == "video":
                        temp_vid = get_video(attachment)
                        if temp_vid is not None:
                            vidlist.append(temp_vid)
                    elif attachment["type"] == "photo":
                        photolist.append(
                            re.sub(
                                "&([a-zA-Z]+(_[a-zA-Z]+)+)=([a-zA-Z0-9-_]+)",
                                "",
                                get_photo(attachment),
                            )
                        )
                    elif attachment["type"] == "doc":
                        docslist.append(get_doc(attachment))
            except Exception as ex:
                add_log(
                    "e",
                    f'[id:{item["id"]}] [{type(ex).__name__}] in parse_attachments(): {str(ex)}',
                )

        try:
            text_of_post = ready_for_html(item["text"])
            links_list = []
            videos_list = []
            photo_url_list = []
            docs_list = []

            if "attachments" in item:
                parse_attachments(
                    item, links_list, videos_list, photo_url_list, docs_list
                )
            text_of_post = compile_links_and_text(
                item["id"],
                text_of_post,
                links_list,
                videos_list,
                "post",
            )
            if "copy_history" in item and text_of_post != "":
                group_name = get_public_name_by_id(
                    abs(item["copy_history"][0]["owner_id"])
                )
                text_of_post = f"""{text_of_post}\n\nREPOST ↓ {group_name}"""
            send_posts(item["id"], text_of_post, photo_url_list, docs_list)

            if "copy_history" in item:
                item_repost = item["copy_history"][0]
                link_to_reposted_post = (
                    f"https://vk.com/wall{item_repost['from_id']}_{item_repost['id']}"
                )
                text_of_post_rep = ready_for_html(item_repost["text"])
                links_list_rep = []
                videos_list_rep = []
                photo_url_list_rep = []
                docs_list_rep = []
                group_id = abs(item_repost["owner_id"])
                group_name = get_public_name_by_id(group_id)

                if "attachments" in item_repost:
                    parse_attachments(
                        item_repost,
                        links_list_rep,
                        videos_list_rep,
                        photo_url_list_rep,
                        docs_list_rep,
                    )
                text_of_post_rep = compile_links_and_text(
                    item["id"],
                    text_of_post_rep,
                    links_list_rep,
                    videos_list_rep,
                    "repost",
                    link_to_reposted_post,
                    group_name,
                )
                send_posts(
                    item["id"],
                    text_of_post_rep,
                    photo_url_list_rep,
                    docs_list_rep,
                )
        except Exception as ex:
            add_log(
                "e",
                f'[id:{item["id"]}] [{type(ex).__name__}] in parse_posts(): {str(ex)}',
            )


def send_posts(postid, text_of_post, photo_url_list, docs_list):
    """Checks the type of post and sends it to Telegram in a suitable method

    Args:
        postid (integer): Id of the post that is sent to Telegram. Used for better logging
        text_of_post (string): Post text with links to videos and other links from post attachments
        photo_url_list (list): Photo URL list
        docs_list (list): List of urls to docs
    """

    def start_sending():
        try:
            if len(photo_url_list) == 0:
                add_log("i", f"[id:{postid}] Bot is trying to send text post")
                send_text_post()
            elif len(photo_url_list) == 1:
                add_log("i", f"[id:{postid}] Bot is trying to send post with photo")
                send_photo_post()
            elif len(photo_url_list) >= 2:
                add_log("i", f"[id:{postid}] Bot is trying to send post with photos")
                send_photos_post()

            if docs_list != []:
                send_docs()
        except Exception as ex:
            add_log(
                "e",
                f"[id:{postid}] [{type(ex).__name__}] in start_sending(): {str(ex)}",
            )

    def send_text_post():
        try:
            if text_of_post:
                if len(text_of_post) < 4096:
                    bot.send_message(config.tg_channel, text_of_post, parse_mode="HTML")
                else:
                    bot.send_message(
                        config.tg_channel,
                        f"{text_of_post[:4090]} (...)",
                        parse_mode="HTML",
                    )
                    bot.send_message(
                        config.tg_channel,
                        f"(...) {text_of_post[4090:]}",
                        parse_mode="HTML",
                    )
                add_log("i", f"[id:{postid}] Text post sent")
            else:
                add_log("i", f"[id:{postid}] Text post skipped because it is empty")
        except Exception as ex:
            if type(ex).__name__ == "ConnectionError":
                add_log(
                    "w",
                    f"[id:{postid}] [{type(ex).__name__}] in send_text_post(): {str(ex)}",
                )
                add_log("i", f"[id:{postid}] Bot trying to resend message to user")
                time.sleep(3)
                send_text_post()
            add_log(
                "e",
                f"[id:{postid}] [{type(ex).__name__}] in send_text_post(): {str(ex)}",
            )

    def send_photo_post():
        try:
            if len(text_of_post) <= 1024:
                bot.send_photo(
                    config.tg_channel,
                    photo_url_list[0],
                    text_of_post,
                    parse_mode="HTML",
                )
                add_log("i", f"[id:{postid}] Text post (≤1024) with photo sent")
            else:
                post_with_photo = f'<a href="{photo_url_list[0]}"> </a>{text_of_post}'
                if len(post_with_photo) <= 4096:
                    bot.send_message(
                        config.tg_channel, post_with_photo, parse_mode="HTML"
                    )
                else:
                    send_text_post()
                    bot.send_photo(config.tg_channel, photo_url_list[0])
                add_log("i", f"[id:{postid}] Text post (>1024) with photo sent")
        except Exception as ex:
            add_log(
                "e",
                f"[id:{postid}] [{type(ex).__name__}] in send_photo_post(): {str(ex)}",
            )
            if type(ex).__name__ == "ConnectionError":
                add_log("i", f"[id:{postid}] Bot trying to resend message to user")
                time.sleep(3)
                send_photo_post()

    def send_photos_post():
        try:
            photo_list = []
            for url_photo in photo_url_list:
                photo_list.append(
                    types.InputMediaPhoto(urllib.request.urlopen(url_photo).read())
                )

            if len(text_of_post) <= 1024 and len(text_of_post) > 0:
                photo_list[0].caption = text_of_post
                photo_list[0].parse_mode = "HTML"
            elif len(text_of_post) > 1024:
                send_text_post()
            bot.send_media_group(config.tg_channel, photo_list)
            add_log("i", f"[id:{postid}] Text post with photos sent")
        except Exception as ex:
            add_log(
                "e",
                f"[id:{postid}] [{type(ex).__name__}] in send_photos_post(): {str(ex)}",
            )
            if type(ex).__name__ == "ConnectionError":
                add_log("i", f"[id:{postid}] Bot trying to resend message to user")
                time.sleep(3)
                send_photos_post()

    def send_docs():
        def send_doc(doc):
            try:
                bot.send_document(config.tg_channel, doc)
                add_log("i", f"[id:{postid}] Document sent")
            except Exception as ex:
                add_log(
                    "e",
                    f"[id:{postid}] [{type(ex).__name__}] in send_docs(): {str(ex)}",
                )
                if type(ex).__name__ == "ConnectionError":
                    add_log("i", f"[id:{postid}] Bot trying to resend message to user")
                    time.sleep(3)
                    send_doc(doc)

        for doc in docs_list:
            send_doc(doc)

    start_sending()


def compile_links_and_text(postid, text_of_post, links_list, videos_list, *repost):
    """Compiles links to videos and other links with post text

    Args:
        postid (integer): Id of the post that is sent to Telegram. Used for better logging
        text_of_post (string): Just a post text
        links_list (list): link(s) from post attachments
        videos_list (list): link(s) to video(s) from post attachments

    Returns:
        text_of_post (string): Post text with links to videos and other links from post attachments
    """
    first_link = True

    def add_links(links):
        nonlocal first_link
        nonlocal text_of_post
        if links and links != [None]:
            for link in links:
                if link not in text_of_post:
                    if text_of_post:
                        if first_link:
                            text_of_post = f'<a href="{link}"> </a>{text_of_post}\n'
                            first_link = False
                        text_of_post += f"\n{link}"
                    else:
                        if first_link:
                            text_of_post += link
                            first_link = False
                        else:
                            text_of_post += f"\n{link}"

    if repost[0] == "repost":
        text_of_post = (
            f'<a href="{repost[1]}"><b>REPOST ↓ {repost[2]}</b></a>\n\n{text_of_post}'
        )
    try:
        add_links(videos_list)
        add_links(links_list)
        add_log("i", f"[id:{postid}] Link(s) was(were) added to post text")
    except Exception as ex:
        add_log(
            "e",
            f"[id:{postid}] [{type(ex).__name__}] in compile_links_and_text(): {str(ex)}",
        )
    return text_of_post


def check_new_post():
    """Gets list of posts from get_data(),
    compares post's id with id from the last_known_id.txt file.
    Sends list of posts to parse_posts(), writes new last id into file"""
    if not check_admin_status(bot, config.tg_channel):
        pass
    add_log("i", "Scanning for new posts")
    with open("last_known_id.txt", "r") as file:
        last_id = int(file.read())
        if last_id is None:
            add_log("e", "Could not read from storage. Skipped iteration")
            return
        add_log("i", f"Last id of vk post is {last_id}")
    try:
        feed = get_data()
        if feed is not None:
            if "is_pinned" in feed[0]:
                add_log("i", f"Got some posts [id:{feed[-1]['id']}-{feed[1]['id']}]")
                config._is_pinned_post = True
                parse_posts(feed[1:], last_id)
                new_last_id = feed[1]["id"]
            else:
                add_log("i", f"Got some posts [id:{feed[-1]['id']}-{feed[0]['id']}]")
                config._is_pinned_post = False
                parse_posts(feed, last_id)
                new_last_id = feed[0]["id"]
            if new_last_id > last_id:
                with open("last_known_id.txt", "w") as file:
                    file.write(str(new_last_id))
                add_log("i", f"New last id of vk post is {new_last_id}")
            else:
                add_log("i", f"Last id remains {new_last_id}")
    except Exception as ex:
        add_log("e", f"[{type(ex).__name__}] in check_new_post(): {str(ex)}")
    add_log("i", "Scanning finished")


def ready_for_html(text):
    """All '<', '>' and '&' symbols that are not a part
    of a tag or an HTML entity must be replaced with the
    corresponding HTML entities:
    ('<' with '&lt;', '>' with '&gt;' and '&' with '&amp;')
    https://core.telegram.org/bots/api#html-style

    Args:
        text (str): Post text before replacing characters

    Returns:
        str: Text from Args, but with characters replaced
    """
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def check_admin_status(specific_bot, specific_channel):
    """Checks if the bot is a channel administrator

    Args:
        specific_bot (string): Defines which bot will be checked (config.tg_bot_token / config.tg_bot_for_log_token)
        specific_channel (string): Defines which channel will be checked (config.tg_channel / config.tg_log_channel)
    """
    try:
        _ = specific_bot.get_chat_administrators(specific_channel)
        return True
    except Exception:
        global is_bot_for_log
        is_bot_for_log = False
        add_log(
            "e",
            f"Bot is not channel admin ({specific_channel}) or Telegram Servers are down..\n",
        )
        return False


def add_log(type_of_log, text):
    """Unifies logging and makes it easier to use

    Args:
        type (string): Type of logging message (warning / info / error)
        text (string): Logging text
    """
    types = {"w": "WARNING", "i": "INFO", "e": "ERROR"}
    log_message = f"[{types[type_of_log]}] {text}"
    if type_of_log == "w":  # WARNING
        logger.warning(text)
    elif type_of_log == "i":  # INFO
        logger.info(text)
    elif type_of_log == "e":  # ERROR
        logger.error(text)

    global is_bot_for_log
    if is_bot_for_log and check_admin_status(bot_2, config.tg_log_channel):
        time.sleep(1)
        send_log(log_message)


def send_log(log_message):
    """Sends logs to config.tg_log_channel channel

    Args:
        log_message (string): Logging text
    """
    global is_bot_for_log
    if is_bot_for_log:
        try:
            log_message_temp = (
                "<code>"
                + log_message
                + "</code>\ntg_channel = "
                + config.tg_channel
                + "\nvk_domain = <code>"
                + config.vk_domain
                + "</code>"
            )
            bot_2.send_message(
                config.tg_log_channel, log_message_temp, parse_mode="HTML"
            )
        except Exception as ex:
            global logger
            logger.error(f"[{type(ex).__name__}] in send_log(): {str(ex)}")


def blacklist_check(text):
    """Checks text or links for forbidden words from config.BLACKLIST

    Args:
        text (string): message text or link

    Returns:
        [bool]
    """
    if config.BLACKLIST:
        text_lower = text.lower()
        for black_word in config.BLACKLIST:
            if black_word.lower() in text_lower:
                return True

    return False


def whitelist_check(text):
    """Checks text or links for filter words from config.WHITELIST

    Args:
        text (string): message text or link

    Returns:
        [bool]
    """
    if config.WHITELIST:
        text_lower = text.lower()
        for white_word in config.WHITELIST:
            if white_word.lower() in text_lower:
                return False
        return True

    return False


def check_python_version():
    """Checks Python version.
    Will close script if Python version is lower than required
    """
    if sys.version_info[0] == 2 or sys.version_info[1] <= 5:
        print('Required python version for this bot is "3.6+"..\n')
        exit()


if __name__ == "__main__":
    check_python_version()

    if not os.path.exists(f"./{config.log_folder}"):
        os.makedirs(f"./{config.log_folder}")

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "[%(asctime)s] %(filename)s:%(lineno)d %(levelname)s - %(message)s"
    )

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)

    tr_file_handler = TimedRotatingFileHandler(
        f"./{config.log_folder}/{config.log_file}", "midnight", interval=1
    )
    tr_file_handler.suffix = "%Y%m%d"
    tr_file_handler.setLevel(logging.INFO)
    tr_file_handler.setFormatter(formatter)

    logger.addHandler(stream_handler)
    logger.addHandler(tr_file_handler)

    if not config.single_start:
        while True:
            check_new_post()
            add_log(
                "i",
                f"Script went to sleep for {config.time_to_sleep} seconds\n\n",
            )
            time.sleep(int(config.time_to_sleep))
    else:
        check_new_post()
        add_log("i", "Script exited.")
