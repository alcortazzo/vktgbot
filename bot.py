#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Made by @alcortazzo
# v2.0-beta4

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

if len(config.tgLogChannel) > 5 and config.tgLogChannel != '@' and config.tgLogChannel != '':
    bot_2 = TeleBot(config.tgBotToken)
    isBotForLog = True
else:
    isBotForLog = False

print('\n\n            /$$         /$$               /$$                   /$$    \n',
      '           | $$        | $$              | $$                  | $$    \n',
      ' /$$    /$$| $$   /$$ /$$$$$$    /$$$$$$ | $$$$$$$   /$$$$$$  /$$$$$$  \n',
      '|  $$  /$$/| $$  /$$/|_  $$_/   /$$__  $$| $$__  $$ /$$__  $$|_  $$_/  \n',
      ' \\  $$/$$/ | $$$$$$/   | $$    | $$  \\ $$| $$  \\ $$| $$  \\ $$  | $$    \n',
      '  \\  $$$/  | $$_  $$   | $$ /$$| $$  | $$| $$  | $$| $$  | $$  | $$ /$$\n',
      '   \\  $/   | $$ \\  $$  |  $$$$/|  $$$$$$$| $$$$$$$/|  $$$$$$/  |  $$$$/\n',
      '    \\_/    |__/  \\__/   \\___/   \\____  $$|_______/  \\______/    \\___/  \n',
      '                                /$$  \\ $$                              \n',
      '                               |  $$$$$$/                              \n',
      '                                \\______/                               \n\n')

# enable proxy for telegram
if config.proxyEnable:
    apihelper.proxy = {
        'https': f'socks5://{config.proxyLogin}:{config.proxyPass}@{config.proxyIp}:{config.proxyPort}'}


def getData():
    timeout = eventlet.Timeout(20)
    # trying to request data from vk_api
    try:
        data = requests.get('https://api.vk.com/method/wall.get',
                            params={'access_token': config.vkToken,
                                    'v': config.reqVer,
                                    'domain': config.vkDomain,
                                    'filter': config.reqFilter,
                                    'count': config.reqCount})
        return data.json()['response']['items']
    except eventlet.timeout.Timeout:
        addLog('w', 'Got Timeout while retrieving VK JSON data. Cancelling...')
        return None
    finally:
        timeout.cancel()


def parsePosts(items, last_id):
    for item in items:
        if blacklist_check(item['text']):
            addLog(
                'i', f"Post was skipped due to blacklist filter [post id:{item['id']}]")
            continue
        addLog('i', f"Post id: {item['id']}")

        cleaning('before')
        
        if item['id'] <= last_id:
            break
        if config.skipAdsPosts and item['marked_as_ads'] == 1:
            continue

        textOfPost = item['text']
        links_list = []
        videos_list = []
        photo_url_list = []
        docs_exist = False
        gif_link = ''
        
        def getLink(attachment):
            link_object = attachment['link']['url']
            
            if blacklist_check(link_object):
                addLog(
                    'i', f"Post was skipped due to blacklist filter [post id:{item['id']}]")
                #return True
#            if not config.parseLink:
#                addLog(
#                    'i', f"Post with links was skipped [post id:{item['id']}]")
#                #return True
            
            if link_object not in textOfPost:
                links_list.append(link_object)
        
        def getVideo(attachment):
            def getVideoUrl(owner_id, video_id, access_key):
                try:
                    data = requests.get(
                        f'https://api.vk.com/method/video.get?access_token={config.vkToken}&v=5.103&videos={owner_id}_{video_id}_{access_key}')
                    return data.json()['response']['items'][0]['files']['external']
                except Exception:
                    return None
            
#            if not config.parseVideo:
#                addLog(
#                    'i', f"Post with video was skipped [post id:{item['id']}]")
#                #return True
            
            # wait for a few seconds because VK can deactivate the access token due to frequent requests
            time.sleep(2)
            video = getVideoUrl(attachment['video']['owner_id'],
                            attachment['video']['id'],
                            attachment['video']['access_key'])
            if video != None:
                videos_list.append(video)
        
        def getPhoto(attachment):
#            if not config.parsePhoto:
#                addLog(
#                    'i', f"Post with photos was skipped [post id:{item['id']}]")
#                isPostSent = True
#                #return True
            
            # check the size of the photo and add this photo to the URL list
            # (from large to smaller)
            # photo with type W > Z > *
            photo = attachment['photo']['sizes']
            if photo[-1]['type'] == 'z':
                for url in photo:
                    if url['type'] == 'w':
                        photo_url_list.append(url['url'])
                        break
                    elif url['type'] == 'z':
                        photo_url_list.append(url['url'])
                        break
            # if we did not find 'w' or 'z', we take the largest available
            elif photo[-1]['type'] != 'z':
                photo_url_list.append(photo[-1]['url'])
        
        def getDoc(attachment): 
#            if not config.parseDoc:
#                addLog(
#                    'i', f"Post with docs was skipped [post id:{item['id']}]")
#                #return True
            
            docurl = attachment['doc']['url']
            extension = attachment['doc']['ext']
            doc_title = attachment['doc']['title']
            try:
                docurl_img = urllib.request.urlopen(docurl).read()
            except Exception as ex:
                print(ex)
            with open(os.path.join('temp', doc_title), 'wb') as temp_file:
                        temp_file.write(docurl_img)
                        temp_file.close()
            docs_exist = True
        
        def getGif(attachment):
#            if not config.parseGif:
#                addLog(
#                    'i', f"Post with gif was skipped [post id:{item['id']}]")
#                #return True
            
            docurl = attachment['doc']['url']
            extension = attachment['doc']['ext']
            gif_link = urllib.request.urlopen(docurl).read()
        
        for attachment in item['attachments']:
            if attachment['type'] == 'link':
                getLink(attachment)
            elif attachment['type'] == 'video':
                getVideo(attachment)
            elif attachment['type'] == 'photo':
                getPhoto(attachment)
#           elif attachment['type'] == 'doc':           doesnt work for now
#               if attachment['doc']['ext'] == 'gif':   doesnt work for now
#                   getGif(attachment)                  doesnt work for now
#               else:                                   doesnt work for now
#                   getDoc(attachment)                  doesnt work for now
        
        
        textOfPost = compileLinksAndText(textOfPost, links_list, videos_list)
        sendPosts(textOfPost, photo_url_list, docs_exist, gif_link)
        cleaning('after')

def sendPosts(textOfPost, photo_url_list, docs_exist, gif_link):
    def startSending():
        if len(photo_url_list) == 0:
            sendTextPost()
        elif len(photo_url_list) == 1:
            sendPhotoPost()
        elif len(photo_url_list) >= 2:
            sendPhotosPost()

    # поставить try except

    def sendTextPost():
        if len(textOfPost) < 4096:
            bot.send_message(config.tgChannel, textOfPost)
        else:
            bot.send_message(config.tgChannel, f'{textOfPost[:4090]} (...)')
            bot.send_message(config.tgChannel, f'(...) {textOfPost[4090:]}')
    
    def sendPhotoPost():
        if len(textOfPost) <= 1024:
            bot.send_photo(config.tgChannel, photo_url_list[0], textOfPost)
        else:
            PostWithPhoto = f'<a href="{photo_url_list[0]}"> </a>{textOfPost}'
            if len(PostWithPhoto) > 1024 and len(PostWithPhoto) <= 4096:
                bot.send_message(config.tgChannel, PostWithPhoto, parse_mode='HTML')
            elif len(PostWithPhoto) > 4096: # если >4096 - делить на два
                if len(textOfPost) < 4096:
                    bot.send_message(config.tgChannel, textOfPost)
                else:
                    bot.send_message(config.tgChannel, f'{textOfPost[:4090]} (...)')
                    bot.send_message(config.tgChannel, f'(...) {textOfPost[4090:]}')
                bot.send_photo(config.tgChannel, photo_url_list[0])
                
    def sendPhotosPost():
        photo_list = []
        for urlPhoto in photo_url_list:
            photo_list.append(types.InputMediaPhoto(urllib.request.urlopen(urlPhoto).read()))
        
        if len(textOfPost) <= 1024 and len(textOfPost) > 0:
            photo_list[0].caption = textOfPost
        elif len(textOfPost) > 1024 and len(textOfPost) <= 4096:
            bot.send_message(config.tgChannel, textOfPost)
            
        bot.send_media_group(config.tgChannel, photo_list)
    
    startSending()


def compileLinksAndText(textOfPost, links_list, videos_list):
    first_link = True
    def addVideo():
        nonlocal first_link
        nonlocal textOfPost
        if videos_list != []:
            for video in videos_list:
                if video not in textOfPost:
                    if first_link:
                        textOfPost += f'\n\n{video}'
                        first_link = False
                    elif not first_link:
                        textOfPost += f'\n{video}'
    
    def addLink():
        nonlocal first_link
        nonlocal textOfPost
        if links_list != []:
            for link in links_list:
                if link not in textOfPost:
                    if first_link:
                        textOfPost += f'\n\n{link}'
                        first_link = False
                    elif not first_link:
                        textOfPost += f'\n{link}'
                        
    addVideo()
    addLink()
    return textOfPost

def checkNewPost():
    if not isBotChannelAdmin(bot, config.tgChannel):
        pass
    addLog('i', '[VK] Started scanning for new posts')
    with open('last_known_id.txt', 'r') as file:
        last_id = int(file.read())
        if last_id is None:
            addLog('e', 'Could not read from storage. Skipped iteration')
            return
        addLog('i', f"Last id of vk post is {last_id}")
    try:
        feed = getData()
        # continue if we received data
        if feed is not None:
            entries = feed
            try:
                # if the post is pinned, skip it
                pinned = entries[0]['is_pinned']
                # and call parsePosts
                config.isPinned = True
                parsePosts(entries[1:], last_id)
            except KeyError:
                config.isPinned = False
                parsePosts(entries, last_id)
            # write new last_id to file
            with open('last_known_id.txt', 'w') as file:
                try:
                    pinned = entries[0]['is_pinned']
                    file.write(str(entries[1]['id']))
                    addLog(
                        'i', f"New last id of vk post is {entries[1]['id']}")
                except KeyError:
                    file.write(str(entries[0]['id']))
                    addLog(
                        'i', f"New last id of vk post is {entries[0]['id']}")
    except Exception as ex:
        addLog(
            'e', f'Exception in type {type(ex).__name__} in checkNewPost(): {str(ex)}')
        pass
    addLog('i', '[VK] Finished scanning')
    return


def cleaning(when):
    try:
        if when == 'before':
            if 'temp' in os.listdir():
                shutil.rmtree('temp')
                os.mkdir('temp')
            elif 'temp' not in os.listdir():
                os.mkdir('temp')
        elif when == 'after':
            shutil.rmtree('temp')
    except Exception as ex:
        addLog(
            'e', f'Something [{type(ex).__name__}] went wrong in cleaning(): {str(ex)}')


# method for checking if a bot is a channel administrator
def isBotChannelAdmin(specific_bot, specific_channel):
    try:
        _ = specific_bot.get_chat_administrators(specific_channel)
    except Exception as ex:
        global isBotForLog
        isBotForLog = False
        addLog(
            'e', f'Bot is not channel admin ({specific_channel}) or Telegram Servers are down..\n')
        return False


def addLog(type, text):
    global isBotForLog
    if isBotForLog:
        isBotChannelAdmin(bot_2, config.tgLogChannel)
    log_message = ''
    if type == 'w':  # WARNING
        log_message = f'[WARNING] {text}'
        print(datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
              '| ' + log_message)
        if config.ShouldBotLog:
            logging.warning(log_message)
    elif type == 'i':  # INFO
        log_message = f'[Bot] [Info] {text}'
        print(datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
              '| ' + log_message)
        if config.ShouldBotLog:
            logging.info(log_message)
    elif type == 'e':  # ERROR
        log_message = f'[ERROR] {text}'
        print(datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
              '| ' + log_message)
        if config.ShouldBotLog:
            logging.error(log_message)
    if isBotForLog:
        sendLog(log_message)


def sendLog(log_message):
    global isBotForLog
    if isBotForLog:
        try:
            log_message_temp = '<code>' + log_message + '</code>\ntgChannel = ' + config.tgChannel + \
                               '\nvkDomain = <code>' + config.vkDomain + '</code>'
            bot_2.send_message(config.tgLogChannel,
                               log_message_temp, parse_mode='HTML')
        except Exception as ex:
            log_message = f'[ERROR] Something [{type(ex).__name__}] went wrong in sendLog(): {str(ex)}'
            print(datetime.now().strftime(
                "%d-%m-%Y %H:%M:%S"), '| ' + log_message)
            if config.ShouldBotLog:
                logging.error(log_message)


def blacklist_check(text):
    # global isBlackWord
    isBlackWord = False
    if config.BLACKLIST != [] and config.BLACKLIST != [''] and config.BLACKLIST != [' ']:
        for black_word in config.BLACKLIST:
            if black_word.lower() in text.lower():
                isBlackWord = True
    if isBlackWord:
        return True


def check_python_version():
    if sys.version_info[0] == 2 or sys.version_info[1] <= 5:
        print('Required python version for this bot is "3.6+"..\n')
        exit()


if __name__ == '__main__':
    check_python_version()
    if config.ShouldBotLog:
        logging.getLogger('requests').setLevel(logging.CRITICAL)
        logging.basicConfig(format='[%(asctime)s] %(filename)s:%(lineno)d %(levelname)s - %(message)s',
                            level=logging.INFO, filename='bot.log', datefmt='%d.%m.%Y %H:%M:%S')
    if not config.singleStart:
        while True:
            checkNewPost()
            addLog('i', 'Script went to sleep for ' +
                   str(config.timeSleep) + ' seconds\n\n')
            # pause for n minutes (timeSleep in config.py)
            time.sleep(int(config.timeSleep))
    elif config.singleStart:
        checkNewPost()
        addLog('i', 'Script exited.')
