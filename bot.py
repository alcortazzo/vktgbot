#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Made by @alcortazzo
# v2.0

import os
import sys
import time
import urllib
import config
import shutil
import logging
import requests
import eventlet
from PIL import Image
from datetime import datetime
from telebot import TeleBot, types, apihelper

bot = TeleBot(config.tgBotToken)

if (
    len(config.tgLogChannel) > 5
    and config.tgLogChannel != "@"
    and config.tgLogChannel != ""
):
    if config.tgBotForLogToken != "":
        bot_2 = TeleBot(config.tgBotForLogToken)
    else:
        bot_2 = TeleBot(config.tgBotToken)
    isBotForLog = True
else:
    isBotForLog = False

print(
    "\n\n            /$$         /$$               /$$                   /$$    \n",
    "           | $$        | $$              | $$                  | $$    \n",
    " /$$    /$$| $$   /$$ /$$$$$$    /$$$$$$ | $$$$$$$   /$$$$$$  /$$$$$$  \n",
    "|  $$  /$$/| $$  /$$/|_  $$_/   /$$__  $$| $$__  $$ /$$__  $$|_  $$_/  \n",
    " \\  $$/$$/ | $$$$$$/   | $$    | $$  \\ $$| $$  \\ $$| $$  \\ $$  | $$    \n",
    "  \\  $$$/  | $$_  $$   | $$ /$$| $$  | $$| $$  | $$| $$  | $$  | $$ /$$\n",
    "   \\  $/   | $$ \\  $$  |  $$$$/|  $$$$$$$| $$$$$$$/|  $$$$$$/  |  $$$$/\n",
    "    \\_/    |__/  \\__/   \\___/   \\____  $$|_______/  \\______/    \\___/  \n",
    "                                /$$  \\ $$                              \n",
    "                               |  $$$$$$/                              \n",
    "                                \\______/                               \n\n",
)

# enable proxy for telegram
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
    for item in items:
        if blacklist_check(item["text"]):
            addLog("i", f"[id:{item['id']}] Post was skipped due to blacklist filter")
            continue

        # cleaning("before")

        if item["id"] <= last_id:
            break
        if config.skipAdsPosts and item["marked_as_ads"] == 1:
            addLog(
                "i",
                f"[id:{item['id']}]Post was skipped because it was flagged as ad",
            )
            continue
        addLog("i", f"[id:{item['id']}] Bot is working with this post")

        def getLink(attachment):
            try:
                link_object = attachment["link"]["url"]

                if blacklist_check(link_object):
                    addLog(
                        "i",
                        f"[id:{item['id']}] Post was skipped due to blacklist filter",
                    )

                if link_object not in textOfPost:
                    return link_object
            except Exception as ex:
                addLog(
                    "e",
                    f'[id:{item["id"]}] Something [{type(ex).__name__}] went wrong in parsePosts() --> getLink(): {str(ex)}',
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
                    f'[id:{item["id"]}] Something [{type(ex).__name__}] went wrong in parsePosts() --> getVideo(): {str(ex)}',
                )

        def getPhoto(attachment):
            try:
                # check the size of the photo and add this photo to the URL list
                # (from large to smaller)
                # photo with type W > Z > *
                photo = attachment["photo"]["sizes"]
                if photo[-1]["type"] == "z":
                    for url in photo:
                        if url["type"] == "w":
                            return url["url"]
                        elif url["type"] == "z":
                            return url["url"]
                # if we did not find 'w' or 'z', we take the largest available
                elif photo[-1]["type"] != "z":
                    return photo[-1]["url"]
            except Exception as ex:
                addLog(
                    "e",
                    f'[id:{item["id"]}] Something [{type(ex).__name__}] went wrong in parsePosts() --> getPhoto(): {str(ex)}',
                )

        def getDoc(attachment):
            docurl = attachment["doc"]["url"]
            extension = attachment["doc"]["ext"]
            doc_title = attachment["doc"]["title"]
            return docurl

        """
        def getGif(attachment):
            docurl = attachment['doc']['url']
            extension = attachment['doc']['ext']
            gif_link = urllib.request.urlopen(docurl).read()
        """

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
                        photolist.append(getPhoto(attachment))
                    elif attachment["type"] == "doc":
                        if attachment["doc"]["ext"] != "gif":
                            docslist.append(getDoc(attachment))
                        # elif attachment["doc"]["ext"] == "gif":
            except Exception as ex:
                addLog(
                    "e",
                    f'[id:{item["id"]}] Something [{type(ex).__name__}] went wrong in parsePosts() --> parseAttachments(): {str(ex)}',
                )

        try:
            textOfPost = item["text"]
            links_list = []
            videos_list = []
            photo_url_list = []
            docs_list = []
            gif_link = ""

            if "attachments" in item:
                parseAttachments(
                    item, links_list, videos_list, photo_url_list, docs_list
                )
            textOfPost = compileLinksAndText(
                item["id"], textOfPost, links_list, videos_list, "post"
            )
            if "copy_history" in item and textOfPost != "":
                textOfPost = f"""{textOfPost}\n\nREPOST ↓"""
            sendPosts(
                item["id"], textOfPost, photo_url_list, docs_list, gif_link, "post"
            )
            # cleaning("after")

            if "copy_history" in item:
                # cleaning("before")

                item_repost = item["copy_history"][0]
                link_to_reposted_post = (
                    f"https://vk.com/wall{item_repost['from_id']}_{item_repost['id']}"
                )
                textOfPost_rep = item_repost["text"]
                links_list_rep = []
                videos_list_rep = []
                photo_url_list_rep = []
                docs_list_rep = []
                gif_link_rep = ""

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
                )
                sendPosts(
                    item["id"],
                    textOfPost_rep,
                    photo_url_list_rep,
                    docs_list_rep,
                    gif_link_rep,
                    "repost",
                )
                # cleaning("after")
        except Exception as ex:
            addLog(
                "e",
                f'[id:{item["id"]}] Something [{type(ex).__name__}] went wrong in parsePosts(): {str(ex)}',
            )


def sendPosts(postid, textOfPost, photo_url_list, docs_list, gif_link, *repost):
    """Checks the type of post and sends it to Telegram in a suitable method

    Args:
        postid (integer): Id of the post that is sent to Telegram. Used for better logging
        textOfPost (string): Post text with links to videos and other links from post attachments
        photo_url_list (list): Photo URL list
        docs_list (list): List of urls to docs
        gif_link ([type]): Doesnt work for now
        repost[0] (string): Used to determine if it is a post or repost
    """

    def startSending():
        try:
            if len(photo_url_list) == 0:
                addLog("i", f"[id:{postid}] Bot is trying to send text post")
                if repost[0] == "post":
                    sendTextPost("post")
                elif repost[0] == "repost":
                    sendTextPost("repost")
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
                f"[id:{postid}] Something [{type(ex).__name__}] went wrong in sendPosts() --> startSending(): {str(ex)}",
            )

    def sendTextPost(type_of_post):
        try:
            if type_of_post == "post":
                if len(textOfPost) < 4096:
                    bot.send_message(config.tgChannel, textOfPost)
                else:
                    bot.send_message(config.tgChannel, f"{textOfPost[:4090]} (...)")
                    bot.send_message(config.tgChannel, f"(...) {textOfPost[4090:]}")
            elif type_of_post == "repost":
                if len(textOfPost) < 4096:
                    bot.send_message(
                        config.tgChannel,
                        textOfPost,
                        parse_mode="HTML",
                        disable_web_page_preview=True,
                    )
                else:
                    bot.send_message(
                        config.tgChannel,
                        f"{textOfPost[:4090]} (...)",
                        parse_mode="HTML",
                        disable_web_page_preview=True,
                    )
                    bot.send_message(
                        config.tgChannel,
                        f"(...) {textOfPost[4090:]}",
                        parse_mode="HTML",
                        disable_web_page_preview=True,
                    )
            addLog("i", f"[id:{postid}] Text post sent")
        except Exception as ex:
            if type(ex).__name__ == "ConnectionError":
                addLog(
                    "w",
                    f"[id:{postid}] {type(ex).__name__} went wrong in sendPosts() --> sendTextPost(): {str(ex)}",
                )
                addLog("i", f"[id:{postid}] Bot trying to resend message to user")
                time.sleep(3)
                sendTextPost(type_of_post)
            addLog(
                "e",
                f"[id:{postid}] Something [{type(ex).__name__}] went wrong in sendPosts() --> sendTextPost(): {str(ex)}",
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
                if len(PostWithPhoto) > 1024 and len(PostWithPhoto) <= 4096:
                    bot.send_message(config.tgChannel, PostWithPhoto, parse_mode="HTML")
                elif len(PostWithPhoto) > 4096:
                    if len(textOfPost) < 4096:
                        bot.send_message(
                            config.tgChannel, textOfPost, parse_mode="HTML"
                        )
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
                    bot.send_photo(config.tgChannel, photo_url_list[0])
                addLog("i", f"[id:{postid}] Text post (>1024) with photo sent")
        except Exception as ex:
            if type(ex).__name__ == "ConnectionError":
                addLog(
                    "w",
                    f"[id:{postid}] {type(ex).__name__} went wrong in sendPosts() --> sendPhotoPost(): {str(ex)}",
                )
                addLog("i", f"[id:{postid}] Bot trying to resend message to user")
                time.sleep(3)
                sendPhotoPost()
            addLog(
                "e",
                f"[id:{postid}] Something [{type(ex).__name__}] went wrong in sendPosts() --> sendPhotoPost(): {str(ex)}",
            )

    def sendPhotosPost():
        try:
            photo_list = []
            for urlPhoto in photo_url_list:
                photo_list.append(
                    types.InputMediaPhoto(urllib.request.urlopen(urlPhoto).read())
                )

            if len(textOfPost) <= 1024 and len(textOfPost) > 0:
                photo_list[0].caption = textOfPost
            elif len(textOfPost) > 1024:
                if len(textOfPost) <= 4096:
                    bot.send_message(config.tgChannel, textOfPost, parse_mode="HTML")
                else:
                    if repost[0] == "post":
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
                    elif repost[0] == "repost":
                        bot.send_message(
                            config.tgChannel,
                            f"{textOfPost[:4086]}</i> (...)",
                            parse_mode="HTML",
                            disable_web_page_preview=True,
                        )
                        bot.send_message(
                            config.tgChannel,
                            f"(...) <i>{textOfPost[4086:]}",
                            parse_mode="HTML",
                            disable_web_page_preview=True,
                        )
            bot.send_media_group(config.tgChannel, photo_list)
            addLog("i", f"[id:{postid}] Text post with photos sent")
        except Exception as ex:
            if type(ex).__name__ == "ConnectionError":
                addLog(
                    "w",
                    f"[id:{postid}] {type(ex).__name__} went wrong in sendPosts() --> sendPhotosPost(): {str(ex)}",
                )
                addLog("i", f"[id:{postid}] Bot trying to resend message to user")
                time.sleep(3)
                sendPhotosPost()
            addLog(
                "e",
                f"[id:{postid}] Something [{type(ex).__name__}] went wrong in sendPosts() --> sendPhotosPost(): {str(ex)}",
            )

    def sendDocs():
        def sendDoc(doc):
            try:
                bot.send_document(config.tgChannel, doc)
                addLog("i", f"[id:{postid}] Document sent")
            except Exception as ex:
                if type(ex).__name__ == "ConnectionError":
                    addLog(
                        "w",
                        f"[id:{postid}] {type(ex).__name__} went wrong in sendPosts() --> sendDocs(): {str(ex)}",
                    )
                    addLog("i", f"[id:{postid}] Bot trying to resend message to user")
                    time.sleep(3)
                    sendDoc(doc)
                addLog(
                    "e",
                    f"[id:{postid}] Something [{type(ex).__name__}] went wrong in sendPosts() --> sendDocs(): {str(ex)}",
                )

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

    def addVideo():
        try:
            nonlocal first_link
            nonlocal textOfPost
            if videos_list != [] and videos_list != [None]:
                for video in videos_list:
                    if video not in textOfPost:
                        if first_link:
                            textOfPost += f"\n\n{video}"
                            first_link = False
                        elif not first_link:
                            textOfPost += f"\n{video}"
                addLog(
                    "i",
                    f"[id:{postid}] Link(s) to video(s) was(were) added to post text",
                )
        except Exception as ex:
            addLog(
                "e",
                f"[id:{postid}] Something [{type(ex).__name__}] went wrong in compileLinksAndText() --> addVideo(): {str(ex)}",
            )

    def addLink():
        try:
            nonlocal first_link
            nonlocal textOfPost
            if links_list != [] and links_list != [None]:
                for link in links_list:
                    if link not in textOfPost:
                        if first_link:
                            textOfPost += f"\n\n{link}"
                            first_link = False
                        elif not first_link:
                            textOfPost += f"\n{link}"
                addLog("i", f"[id:{postid}] Link(s) was(were) added to post text")
        except Exception as ex:
            addLog(
                "e",
                f"[id:{postid}] Something [{type(ex).__name__}] went wrong in compileLinksAndText() --> addLink(): {str(ex)}",
            )

    addVideo()
    addLink()
    if repost[0] == "repost":
        textOfPost = f'<a href="{repost[1]}"><b>REPOST ↓</b></a>\n\n<i>{textOfPost}</i>'
    return textOfPost


def checkNewPost():
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
        addLog("i", f"Got some posts [id:{feed[-1]['id']}-{feed[0]['id']}]")
        # continue if we received data
        if feed is not None:
            entries = feed
            try:
                # if the post is pinned, skip it
                pinned = entries[0]["is_pinned"]
                # and call parsePosts
                config.isPinned = True
                parsePosts(entries[1:], last_id)
            except KeyError:
                config.isPinned = False
                parsePosts(entries, last_id)
            # write new last_id to file
            with open("last_known_id.txt", "w") as file:
                try:
                    pinned = entries[0]["is_pinned"]
                    file.write(str(entries[1]["id"]))
                    addLog("i", f"New last id of vk post is {entries[1]['id']}")
                except KeyError:
                    file.write(str(entries[0]["id"]))
                    addLog("i", f"New last id of vk post is {entries[0]['id']}")
    except Exception as ex:
        addLog(
            "e", f"Exception in type {type(ex).__name__} in checkNewPost(): {str(ex)}"
        )
        pass
    addLog("i", "Scanning finished")
    return


def cleaning(when):
    """Cleaning the temp folder with files inside
    or creates an empty temp folder for future temp files inside
    """
    try:
        if when == "before":
            if "temp" in os.listdir():
                shutil.rmtree("temp")
                os.mkdir("temp")
            elif "temp" not in os.listdir():
                os.mkdir("temp")
        elif when == "after":
            shutil.rmtree("temp")
    except Exception as ex:
        addLog(
            "e", f"Something [{type(ex).__name__}] went wrong in cleaning(): {str(ex)}"
        )


# method for checking if a bot is a channel administrator
def isBotChannelAdmin(specific_bot, specific_channel):
    """Checks if the bot is a channel administrator

    Args:
        specific_bot (string): Defines which bot will be checked (config.tgBotToken / config.tgBotForLogToken)
        specific_channel (string): Defines which channel will be checked (config.tgChannel / config.tgLogChannel)
    """
    try:
        _ = specific_bot.get_chat_administrators(specific_channel)
    except Exception as ex:
        global isBotForLog
        isBotForLog = False
        addLog(
            "e",
            f"Bot is not channel admin ({specific_channel}) or Telegram Servers are down..\n",
        )
        return False


def addLog(type, text):
    """Unifies logging and makes it easier to use

    Args:
        type (string): Type of logging message (warning / info / error)
        text (string): Logging text
    """
    global isBotForLog
    if isBotForLog:
        isBotChannelAdmin(bot_2, config.tgLogChannel)
    log_message = ""
    if type == "w":  # WARNING
        log_message = f"[WARNING] {text}"
        print(datetime.now().strftime("%d-%m-%Y %H:%M:%S"), "| " + log_message)
        if config.ShouldBotLog:
            logging.warning(log_message)
    elif type == "i":  # INFO
        log_message = f"[Bot] [Info] {text}"
        print(datetime.now().strftime("%d-%m-%Y %H:%M:%S"), "| " + log_message)
        if config.ShouldBotLog:
            logging.info(log_message)
    elif type == "e":  # ERROR
        log_message = f"[ERROR] {text}"
        print(datetime.now().strftime("%d-%m-%Y %H:%M:%S"), "| " + log_message)
        if config.ShouldBotLog:
            logging.error(log_message)
    if isBotForLog:
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
            log_message = f"[ERROR] Something [{type(ex).__name__}] went wrong in sendLog(): {str(ex)}"
            print(datetime.now().strftime("%d-%m-%Y %H:%M:%S"), "| " + log_message)
            if config.ShouldBotLog:
                logging.error(log_message)


def blacklist_check(text):
    """Checks text or links for forbidden words from config.BLACKLIST

    Args:
        text (string): message text or link

    Returns:
        [bool]
    """
    isBlackWord = False
    if (
        config.BLACKLIST != []
        and config.BLACKLIST != [""]
        and config.BLACKLIST != [" "]
    ):
        for black_word in config.BLACKLIST:
            if black_word.lower() in text.lower():
                isBlackWord = True
    if isBlackWord:
        return True


def check_python_version():
    """Checks Python version.
    Will close script if Python version is lower than required
    """
    if sys.version_info[0] == 2 or sys.version_info[1] <= 5:
        print('Required python version for this bot is "3.6+"..\n')
        exit()


if __name__ == "__main__":
    check_python_version()
    if config.ShouldBotLog:
        logging.getLogger("requests").setLevel(logging.CRITICAL)
        logging.basicConfig(
            format="[%(asctime)s] %(filename)s:%(lineno)d %(levelname)s - %(message)s",
            level=logging.INFO,
            filename="bot.log",
            datefmt="%d.%m.%Y %H:%M:%S",
        )
    if not config.singleStart:
        while True:
            checkNewPost()
            addLog(
                "i",
                "Script went to sleep for " + str(config.timeSleep) + " seconds\n\n",
            )
            # pause for n minutes (timeSleep in config.py)
            time.sleep(int(config.timeSleep))
    elif config.singleStart:
        checkNewPost()
        addLog("i", "Script exited.")
