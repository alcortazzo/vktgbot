# Made by @alcortazzo
# v2.4

import os
import re
import sys
import time
import urllib
import config
import shutil
import logging
import requests
import eventlet
from telebot import TeleBot, types, apihelper
from logging.handlers import TimedRotatingFileHandler

bot = TeleBot(config.tgBotToken)

if len(str(config.tgLogChannel)) > 5:
    if config.tgBotForLogToken != "":
        bot_2 = TeleBot(config.tgBotForLogToken)
    else:
        bot_2 = TeleBot(config.tgBotToken)
    isBotForLog = True
else:
    isBotForLog = False


if config.proxyEnable:
    apihelper.proxy = {
        "https": f"socks5://{config.proxyLogin}:{config.proxyPass}@{config.proxyIp}:{config.proxyPort}"
    }


def getData():
    """Trying to request data from VK using vk_api

    Returns:
        List of N posts from vk.com/xxx, where
            N = config.reqCount
            xxx = config.vkDomain
    """
    timeout = eventlet.Timeout(20)
    try:
        data = requests.get(
            "https://api.vk.com/method/wall.get",
            params={
                "access_token": config.vkToken,
                "v": config.reqVer,
                "domain": config.vkDomain,
                "filter": config.reqFilter,
                "count": config.reqCount,
            },
        )
        return data.json()["response"]["items"]
    except eventlet.timeout.Timeout:
        addLog("w", "Got Timeout while retrieving VK JSON data. Cancelling...")
        return None
    finally:
        timeout.cancel()


def parsePosts(items, last_id):
    """For each post in the received posts list:
        * Сhecks post id to make sure it is larger than the one written in the last_known_id.txt
        * Parses all attachments of post or repost
        * Calls 'compileLinksAndText()' to compile links to videos and other links from post to post text
        * Calls 'sendPosts()' to send post to Telegram channel (config.tgChannel)

    Args:
        items (list): List of posts received from VK
        last_id (integer): The current value in the last_known_id.txt
                           (must be less than id of the new post)
    """
    for item in items[::-1]:
        if item["id"] <= last_id:
            continue

        if blacklist_check(item["text"]):
            addLog("i", f"[id:{item['id']}] Post was skipped due to blacklist filter")
            continue

        if whitelist_check(item["text"]):
            addLog("i", f"[id:{item['id']}] Post was skipped due to whitelist filter")
            continue

        if config.skipAdsPosts and item["marked_as_ads"] == 1:
            addLog(
                "i",
                f"[id:{item['id']}] Post was skipped because it was flagged as ad",
            )
            continue
        if config.skipPostsWithCopyright and "copyright" in item:
            addLog(
                "i",
                f"[id:{item['id']}] Post was skipped because it has copyright",
            )
            continue
        addLog("i", f"[id:{item['id']}] Bot is working with this post")

        def getLink(attachment):
            try:
                link_object = attachment["link"]["url"]

                if link_object not in textOfPost:
                    return link_object
            except Exception as ex:
                addLog(
                    "e",
                    f'[id:{item["id"]}] [{type(ex).__name__}] in getLink(): {str(ex)}',
                )

        def getVideo(attachment):
            def getVideoUrl(owner_id, video_id, access_key):
                try:
                    data = requests.get(
                        f"https://api.vk.com/method/video.get?access_token={config.vkToken}&v=5.103&videos={owner_id}_{video_id}_{access_key}"
                    )
                    return data.json()["response"]["items"][0]["files"]["external"]
                except Exception:
                    return None

            try:
                video = getVideoUrl(
                    attachment["video"]["owner_id"],
                    attachment["video"]["id"],
                    attachment["video"]["access_key"],
                )
                # wait for a few seconds because VK can deactivate the access token due to frequent requests
                time.sleep(2)
                if video != None:
                    return video
                else:
                    return f"https://vk.com/video{attachment['video']['owner_id']}_{attachment['video']['id']}"
            except Exception as ex:
                addLog(
                    "e",
                    f'[id:{item["id"]}] [{type(ex).__name__}] in getVideo(): {str(ex)}',
                )

        def getPhoto(attachment):
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
                addLog(
                    "e",
                    f'[id:{item["id"]}] [{type(ex).__name__}] in getPhoto(): {str(ex)}',
                )

        def getDoc(attachment):
            docurl = attachment["doc"]["url"]
            extension = attachment["doc"]["ext"]
            doc_title = attachment["doc"]["title"]
            return docurl

        def getPublicNameById(id):
            try:
                data = requests.get(
                    f"https://api.vk.com/method/groups.getById?access_token={config.vkToken}&v=5.103&group_id={id}"
                )
                return data.json()["response"][0]["name"]
            except Exception as ex:
                addLog(
                    "e",
                    f'[id:{item["id"]}] [{type(ex).__name__}] in getPublicNameById(): {str(ex)}',
                )
                return ""

        def parseAttachments(item, linklist, vidlist, photolist, docslist):
            try:
                for attachment in item["attachments"]:
                    if attachment["type"] == "link":
                        linklist.append(getLink(attachment))
                    elif attachment["type"] == "video":
                        temp_vid = getVideo(attachment)
                        if temp_vid != None:
                            vidlist.append(temp_vid)
                    elif attachment["type"] == "photo":
                        photolist.append(
                            re.sub(
                                "&([a-zA-Z]+(_[a-zA-Z]+)+)=([a-zA-Z0-9-_]+)",
                                "",
                                getPhoto(attachment),
                            )
                        )
                    elif attachment["type"] == "doc":
                        docslist.append(getDoc(attachment))
            except Exception as ex:
                addLog(
                    "e",
                    f'[id:{item["id"]}] [{type(ex).__name__}] in parseAttachments(): {str(ex)}',
                )

        try:
            textOfPost = ready_for_html(item["text"])
            links_list = []
            videos_list = []
            photo_url_list = []
            docs_list = []

            if "attachments" in item:
                parseAttachments(
                    item, links_list, videos_list, photo_url_list, docs_list
                )
            textOfPost = compileLinksAndText(
                item["id"],
                textOfPost,
                links_list,
                videos_list,
                "post",
            )
            if "copy_history" in item and textOfPost != "":
                groupName = getPublicNameById(abs(item["copy_history"][0]["owner_id"]))
                textOfPost = f"""{textOfPost}\n\nREPOST ↓ {groupName}"""
            sendPosts(item["id"], textOfPost, photo_url_list, docs_list)

            if "copy_history" in item:
                item_repost = item["copy_history"][0]
                link_to_reposted_post = (
                    f"https://vk.com/wall{item_repost['from_id']}_{item_repost['id']}"
                )
                textOfPost_rep = ready_for_html(item_repost["text"])
                links_list_rep = []
                videos_list_rep = []
                photo_url_list_rep = []
                docs_list_rep = []
                group_id = abs(item_repost["owner_id"])
                group_name = getPublicNameById(group_id)

                if "attachments" in item_repost:
                    parseAttachments(
                        item_repost,
                        links_list_rep,
                        videos_list_rep,
                        photo_url_list_rep,
                        docs_list_rep,
                    )
                textOfPost_rep = compileLinksAndText(
                    item["id"],
                    textOfPost_rep,
                    links_list_rep,
                    videos_list_rep,
                    "repost",
                    link_to_reposted_post,
                    group_name,
                )
                sendPosts(
                    item["id"],
                    textOfPost_rep,
                    photo_url_list_rep,
                    docs_list_rep,
                )
        except Exception as ex:
            addLog(
                "e",
                f'[id:{item["id"]}] [{type(ex).__name__}] in parsePosts(): {str(ex)}',
            )


def sendPosts(postid, textOfPost, photo_url_list, docs_list):
    """Checks the type of post and sends it to Telegram in a suitable method

    Args:
        postid (integer): Id of the post that is sent to Telegram. Used for better logging
        textOfPost (string): Post text with links to videos and other links from post attachments
        photo_url_list (list): Photo URL list
        docs_list (list): List of urls to docs
    """

    def startSending():
        try:
            if len(photo_url_list) == 0:
                addLog("i", f"[id:{postid}] Bot is trying to send text post")
                sendTextPost()
            elif len(photo_url_list) == 1:
                addLog("i", f"[id:{postid}] Bot is trying to send post with photo")
                sendPhotoPost()
            elif len(photo_url_list) >= 2:
                addLog("i", f"[id:{postid}] Bot is trying to send post with photos")
                sendPhotosPost()

            if docs_list != []:
                sendDocs()
        except Exception as ex:
            addLog(
                "e",
                f"[id:{postid}] [{type(ex).__name__}] in startSending(): {str(ex)}",
            )

    def sendTextPost():
        try:
            if textOfPost:
                if len(textOfPost) < 4096:
                    bot.send_message(config.tgChannel, textOfPost, parse_mode="HTML")
                else:
                    bot.send_message(
                        config.tgChannel,
                        f"{textOfPost[:4090]} (...)",
                        parse_mode="HTML",
                    )
                    bot.send_message(
                        config.tgChannel,
                        f"(...) {textOfPost[4090:]}",
                        parse_mode="HTML",
                    )
                addLog("i", f"[id:{postid}] Text post sent")
            else:
                addLog("i", f"[id:{postid}] Text post skipped because it is empty")
        except Exception as ex:
            if type(ex).__name__ == "ConnectionError":
                addLog(
                    "w",
                    f"[id:{postid}] [{type(ex).__name__}] in sendTextPost(): {str(ex)}",
                )
                addLog("i", f"[id:{postid}] Bot trying to resend message to user")
                time.sleep(3)
                sendTextPost()
            addLog(
                "e",
                f"[id:{postid}] [{type(ex).__name__}] in sendTextPost(): {str(ex)}",
            )

    def sendPhotoPost():
        try:
            if len(textOfPost) <= 1024:
                bot.send_photo(
                    config.tgChannel, photo_url_list[0], textOfPost, parse_mode="HTML"
                )
                addLog("i", f"[id:{postid}] Text post (≤1024) with photo sent")
            else:
                PostWithPhoto = f'<a href="{photo_url_list[0]}"> </a>{textOfPost}'
                if len(PostWithPhoto) <= 4096:
                    bot.send_message(config.tgChannel, PostWithPhoto, parse_mode="HTML")
                else:
                    sendTextPost()
                    bot.send_photo(config.tgChannel, photo_url_list[0])
                addLog("i", f"[id:{postid}] Text post (>1024) with photo sent")
        except Exception as ex:
            addLog(
                "e",
                f"[id:{postid}] [{type(ex).__name__}] in sendPhotoPost(): {str(ex)}",
            )
            if type(ex).__name__ == "ConnectionError":
                addLog("i", f"[id:{postid}] Bot trying to resend message to user")
                time.sleep(3)
                sendPhotoPost()

    def sendPhotosPost():
        try:
            photo_list = []
            for urlPhoto in photo_url_list:
                photo_list.append(
                    types.InputMediaPhoto(urllib.request.urlopen(urlPhoto).read())
                )

            if len(textOfPost) <= 1024 and len(textOfPost) > 0:
                photo_list[0].caption = textOfPost
                photo_list[0].parse_mode = "HTML"
            elif len(textOfPost) > 1024:
                sendTextPost()
            bot.send_media_group(config.tgChannel, photo_list)
            addLog("i", f"[id:{postid}] Text post with photos sent")
        except Exception as ex:
            addLog(
                "e",
                f"[id:{postid}] [{type(ex).__name__}] in sendPhotosPost(): {str(ex)}",
            )
            if type(ex).__name__ == "ConnectionError":
                addLog("i", f"[id:{postid}] Bot trying to resend message to user")
                time.sleep(3)
                sendPhotosPost()

    def sendDocs():
        def sendDoc(doc):
            try:
                bot.send_document(config.tgChannel, doc)
                addLog("i", f"[id:{postid}] Document sent")
            except Exception as ex:
                addLog(
                    "e",
                    f"[id:{postid}] [{type(ex).__name__}] in sendDocs(): {str(ex)}",
                )
                if type(ex).__name__ == "ConnectionError":
                    addLog("i", f"[id:{postid}] Bot trying to resend message to user")
                    time.sleep(3)
                    sendDoc(doc)

        for doc in docs_list:
            sendDoc(doc)

    startSending()


def compileLinksAndText(postid, textOfPost, links_list, videos_list, *repost):
    """Compiles links to videos and other links with post text

    Args:
        postid (integer): Id of the post that is sent to Telegram. Used for better logging
        textOfPost (string): Just a post text
        links_list (list): link(s) from post attachments
        videos_list (list): link(s) to video(s) from post attachments

    Returns:
        textOfPost (string): Post text with links to videos and other links from post attachments
    """
    first_link = True

    def addLinks(links):
        nonlocal first_link
        nonlocal textOfPost
        if links and links != [None]:
            for link in links:
                if link not in textOfPost:
                    if textOfPost:
                        if first_link:
                            textOfPost = f'<a href="{link}"> </a>{textOfPost}\n'
                            first_link = False
                        textOfPost += f"\n{link}"
                    else:
                        if first_link:
                            textOfPost += link
                            first_link = False
                        else:
                            textOfPost += f"\n{link}"

    if repost[0] == "repost":
        textOfPost = (
            f'<a href="{repost[1]}"><b>REPOST ↓ {repost[2]}</b></a>\n\n{textOfPost}'
        )
    try:
        addLinks(videos_list)
        addLinks(links_list)
        addLog("i", f"[id:{postid}] Link(s) was(were) added to post text")
    except Exception as ex:
        addLog(
            "e",
            f"[id:{postid}] [{type(ex).__name__}] in compileLinksAndText(): {str(ex)}",
        )
    return textOfPost


def checkNewPost():
    """Gets list of posts from getData(),
    compares post's id with id from the last_known_id.txt file.
    Sends list of posts to parsePosts(), writes new last id into file"""
    if not isBotChannelAdmin(bot, config.tgChannel):
        pass
    addLog("i", "Scanning for new posts")
    with open("last_known_id.txt", "r") as file:
        last_id = int(file.read())
        if last_id is None:
            addLog("e", "Could not read from storage. Skipped iteration")
            return
        addLog("i", f"Last id of vk post is {last_id}")
    try:
        feed = getData()
        if feed is not None:
            if "is_pinned" in feed[0]:
                addLog("i", f"Got some posts [id:{feed[-1]['id']}-{feed[1]['id']}]")
                config.isPinned = True
                parsePosts(feed[1:], last_id)
            else:
                addLog("i", f"Got some posts [id:{feed[-1]['id']}-{feed[0]['id']}]")
                config.isPinned = False
                parsePosts(feed, last_id)
            with open("last_known_id.txt", "w") as file:
                if "is_pinned" in feed[0]:
                    file.write(str(feed[1]["id"]))
                    addLog("i", f"New last id of vk post is {feed[1]['id']}")
                else:
                    file.write(str(feed[0]["id"]))
                    addLog("i", f"New last id of vk post is {feed[0]['id']}")
    except Exception as ex:
        addLog("e", f"[{type(ex).__name__}] in checkNewPost(): {str(ex)}")
    addLog("i", "Scanning finished")


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


def isBotChannelAdmin(specific_bot, specific_channel):
    """Checks if the bot is a channel administrator

    Args:
        specific_bot (string): Defines which bot will be checked (config.tgBotToken / config.tgBotForLogToken)
        specific_channel (string): Defines which channel will be checked (config.tgChannel / config.tgLogChannel)
    """
    try:
        _ = specific_bot.get_chat_administrators(specific_channel)
        return True
    except Exception as ex:
        global isBotForLog
        isBotForLog = False
        addLog(
            "e",
            f"Bot is not channel admin ({specific_channel}) or Telegram Servers are down..\n",
        )
        return False


def addLog(type_of_log, text):
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

    global isBotForLog
    if isBotForLog and isBotChannelAdmin(bot_2, config.tgLogChannel):
        time.sleep(1)
        sendLog(log_message)


def sendLog(log_message):
    """Sends logs to config.tgLogChannel channel

    Args:
        log_message (string): Logging text
    """
    global isBotForLog
    if isBotForLog:
        try:
            log_message_temp = (
                "<code>"
                + log_message
                + "</code>\ntgChannel = "
                + config.tgChannel
                + "\nvkDomain = <code>"
                + config.vkDomain
                + "</code>"
            )
            bot_2.send_message(config.tgLogChannel, log_message_temp, parse_mode="HTML")
        except Exception as ex:
            global logger
            logger.error(f"[{type(ex).__name__}] in sendLog(): {str(ex)}")


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

    if not os.path.exists(f"./{config.logFolderName}"):
        os.makedirs(f"./{config.logFolderName}")

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "[%(asctime)s] %(filename)s:%(lineno)d %(levelname)s - %(message)s"
    )

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)

    tr_file_handler = TimedRotatingFileHandler(
        f"./{config.logFolderName}/{config.logFileName}", "midnight", interval=1
    )
    tr_file_handler.suffix = "%Y%m%d"
    tr_file_handler.setLevel(logging.INFO)
    tr_file_handler.setFormatter(formatter)

    logger.addHandler(stream_handler)
    logger.addHandler(tr_file_handler)

    if not config.singleStart:
        while True:
            checkNewPost()
            addLog(
                "i",
                f"Script went to sleep for {config.timeSleep} seconds\n\n",
            )
            time.sleep(int(config.timeSleep))
    elif config.singleStart:
        checkNewPost()
        addLog("i", "Script exited.")
