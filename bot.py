#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Made by @alcortazzo
# v1.4.4

import os
import time
import urllib
import config
import shutil
import logging
import requests
import eventlet
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
    apihelper.proxy = {'https': 'socks5://{!s}:{!s}@{!s}:{!s}'.format(config.proxyLogin, config.proxyPass,
                                                                      config.proxyIp, config.proxyPort)}


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


def sendPosts(items, last_id):
    for item in items:
        addLog('i', 'Post id: {!s}'.format(item['id']))
        cleaning('before')
        isTypePost = 'post'
        isRepost = False
        # compares id of the last post and id from the file last_known_id.txt
        if item['id'] <= last_id:
            break
        if config.skipAdsPosts:
            if item['marked_as_ads'] == 1:
                continue
        # trying to check vk post type
        try:
            if item['attachments'][0]['type'] == 'photo':
                isTypePost = 'photo'
                photos = item['attachments']
                urlsPhoto = []
                # check the size of the photo and add this photo to the URL list
                # (from large to smaller)
                # photo with type W > Z > *
                for photo in photos:
                    urls = photo['photo']['sizes']
                    if urls[-1]['type'] == 'z':
                        for url in urls:
                            if url['type'] == 'w':
                                urlsPhoto.append(url['url'])
                                break
                            elif url['type'] == 'z':
                                urlsPhoto.append(url['url'])
                                break
                    # if we did not find 'w' or 'z', we take the largest available
                    elif urls[-1]['type'] != 'z':
                        urlsPhoto.append(urls[-1]['url'])

        except Exception as ex:
            addLog('i', 'No photos in the post [post id:{!s}]'.format(item['id']))

        try:
            if item['attachments'][0]['type'] == 'video':
                isTypePost = 'video'
        except Exception as ex:
            addLog('i', 'No videos in the post [post id:{!s}]'.format(item['id']))

        try:
            if item['attachments'][0]['type'] == 'link':
                isTypePost = 'link'
                linkurl = item['attachments'][0]['link']['url']
        except Exception as ex:
            addLog('i', 'No links in the post [post id:{!s}]'.format(item['id']))

        try:
            if item['attachments'][0]['type'] == 'doc':
                isTypePost = 'doc'
                docurl = item['attachments'][0]['doc']['url']
                if item['attachments'][0]['doc']['ext'] == 'gif':
                    doc_is = 'gif'
                    docurl_gif = urllib.request.urlopen(docurl).read()
                else:
                    doc_is = 'doc'
                    doc_title = item['attachments'][0]['doc']['title']
                    docurl_img = urllib.request.urlopen(docurl).read()
                    with open(os.path.join('temp', doc_title), 'wb') as temp_file:
                        temp_file.write(docurl_img)
                        temp_file.close()
        except Exception as ex:
            addLog('i', 'No documents/gifs in the post [post id:{!s}]'.format(item['id']))

        # REPOST check
        try:
            if 'copy_history' in item:
                isRepost = True
                if item['copy_history'][0]['text'] != '':
                    textRepost = item['copy_history'][0]['text']
                else:
                    textRepost = ''
                urlOfRepost = ''
                try:
                    if item['copy_history'][0]['attachments'][0]['type'] == 'photo':
                        photoOfRepost = item['copy_history'][0]['attachments'][0]['photo']['sizes']
                        if photoOfRepost[-1]['type'] == 'z':
                            for url in photoOfRepost:
                                if url['type'] == 'w':
                                    urlOfRepost = url['url']
                                    break
                                elif url['type'] == 'z':
                                    urlOfRepost = url['url']
                                    break
                        elif photoOfRepost[-1]['type'] != 'z':
                            urlOfRepost = photoOfRepost[-1]['url']
                    elif item['copy_history'][0]['attachments'][0]['type'] == 'video':
                        isTypePost = 'video'
                except Exception as ex:
                    addLog('i', 'No photo or video of repost in the post [post id:{!s}]'.format(item['id']))
        except Exception as ex:
            addLog('e', '{!s} in sendPosts() (RepostCheck) [post id:{!s}]: {!s}'.format(
                type(ex).__name__, item['id'], str(ex)))

        # send message according to post type
        tries = 5  # attempts to send a message to telegram
        isPostSent = False
        for attempt in range(tries + 1):
            if isPostSent:
                continue
            try:
                if isTypePost == 'post':
                    if not config.parsePost:
                        addLog('i', 'Text post was skipped [post id:{!s}]'.format(item['id']))
                        isPostSent = True
                        continue
                    if not isRepost:
                        bot.send_message(config.tgChannel, item['text'])
                    elif isRepost:
                        if item['text'] != '':
                            item_text = item['text'] + '\n\n'
                        elif item['text'] == '':
                            item_text = ''
                        bot.send_message(config.tgChannel, '<a href="' + urlOfRepost + '"> </a>' + item_text +
                                         '<b>REPOST ↓</b>\n\n' + '<i>' + textRepost + '</i>',
                                         parse_mode='HTML')
                    addLog('i', 'Text post sent [post id:{!s}]'.format(item['id']))

                elif isTypePost == 'photo':
                    if not config.parsePhoto:
                        addLog('i', 'Post with photos was skipped [post id:{!s}]'.format(item['id']))
                        isPostSent = True
                        continue
                    howLong = len(item['text'])
                    listOfPhotos = []
                    # send messages with photos
                    if len(urlsPhoto) >= 2:
                        # get photos from urls
                        for urlPhoto in urlsPhoto:
                            listOfPhotos.append(types.InputMediaPhoto(urllib.request.urlopen(urlPhoto).read()))

                        if not isRepost:
                            if howLong <= 1024:
                                if item['text'] != '':
                                    listOfPhotos[0].caption = item['text']
                            elif howLong > 1024:
                                if item['text'] != '':
                                    bot.send_message(config.tgChannel, item['text'])

                        elif isRepost:
                            if item['text'] != '':
                                item_text = item['text'] + '\n\n'
                            elif item['text'] == '':
                                item_text = ''

                            if howLong <= 1004:
                                listOfPhotos[0].caption = ('<a href="' + urlOfRepost + '"> </a>'
                                                           + item_text + '<b>REPOST ↓</b>\n\n' + '<i>' +
                                                           textRepost + '</i>')
                                listOfPhotos[0].parse_mode = 'HTML'
                            elif howLong > 1004:
                                bot.send_message(config.tgChannel,
                                                 '<a href="' + urlOfRepost + '"> </a>' + item_text +
                                                 '<b>REPOST ↓</b>\n\n' + '<i>' + textRepost + '</i>',
                                                 parse_mode='HTML')

                        addLog('i', 'Text post sent [post id:{!s}]'.format(item['id']))
                        bot.send_media_group(config.tgChannel, listOfPhotos)
                        addLog('i', 'Post with photo sent [post id:{!s}]'.format(item['id']))

                    elif len(urlsPhoto) == 1:
                        Photo = urlsPhoto[0]
                        howLong = len(item['text'])
                        if not isRepost:
                            if howLong <= 1024:
                                bot.send_photo(config.tgChannel, Photo, item['text'])
                            elif howLong > 1024:
                                bot.send_message(config.tgChannel,
                                                 '<a href="' + Photo + '"> </a>' + item['text'],
                                                 parse_mode='HTML')
                        elif isRepost:
                            if item['text'] != '':
                                item_text = item['text'] + '\n\n'
                            elif item['text'] == '':
                                item_text = ''
                            bot.send_message(config.tgChannel,
                                             '<a href="' + urlOfRepost + '"> </a>' + '<a href="' + Photo + '"> </a>' +
                                             item_text + '<b>REPOST ↓</b>\n\n<i>' + textRepost + '</i>',
                                             parse_mode='HTML')
                        addLog('i', 'Post with photo sent [post id:{!s}]'.format(item['id']))

                elif isTypePost == 'video':
                    if not config.parseVideo:
                        addLog('i', 'Post with video was skipped [post id:{!s}]'.format(item['id']))
                        isPostSent = True
                        continue
                    video_url = []
                    if not isRepost:
                        videos = item['attachments']
                    if isRepost:
                        videos = item['copy_history'][0]['attachments']
                    for video in filter(lambda att: att['type'] == 'video', videos):
                        video_temp = getVideo(video['video']['owner_id'],
                                              video['video']['id'],
                                              video['video']['access_key'])
                        if video_temp == None:
                            continue
                        elif video_temp != None:
                            time.sleep(2)  # wait for a few seconds because VK can deactivate the token
                        video_url.append(video_temp)
                    if video_temp != None:
                        if not isRepost:
                            bot.send_message(config.tgChannel, item['text'] + '\n' + '\n'.join(video_url))
                        elif isRepost:
                            bot.send_message(config.tgChannel,
                                             '<a href="' + urlOfRepost + '"> </a>' +
                                             item['text'] + '\n\n<b>REPOST ↓</b>\n\n' + '<i>' + textRepost + '\n' +
                                             '\n'.join(video_url) + '</i>',
                                             parse_mode='HTML')
                        addLog('i', 'Post with video sent [post id:{!s}]'.format(item['id']))
                    else:
                        addLog('w', 'Post with video was skipped. Maybe you do not use personal token' +
                               ' or video in post is not from YouTube [post id:{!s}]'.format(item['id']))
                        videoUrlPreview = item['attachments'][0]['video']['image'][-1]['url']
                        howLong = len(item['text'])
                        if not isRepost:
                            if howLong <= 1024:
                                bot.send_photo(config.tgChannel, videoUrlPreview, item['text'])
                            elif howLong > 1024:
                                bot.send_message(config.tgChannel,
                                                 '<a href="' + videoUrlPreview + '"> </a>' + item['text'],
                                                 parse_mode='HTML')
                        elif isRepost:
                            if item['text'] != '':
                                item_text = item['text'] + '\n\n'
                            elif item['text'] == '':
                                item_text = ''
                            bot.send_message(config.tgChannel,
                                             '<a href="' + urlOfRepost + '"> </a>' + '<a href="' +
                                             videoUrlPreview + '"> </a>' + item_text +
                                             '<b>REPOST ↓</b>\n\n<i>' + textRepost + '</i>',
                                             parse_mode='HTML')
                        addLog('i', 'Post with video preview sent [post id:{!s}]'.format(item['id']))

                elif isTypePost == 'link':
                    if not config.parseLink:
                        addLog('i', 'Post with links was skipped [post id:{!s}]'.format(item['id']))
                        isPostSent = True
                        continue
                    if linkurl in item['text']:
                        linkurl = ''
                    elif linkurl not in item['text']:
                        linkurl = '\n\n' + linkurl
                    if not isRepost:
                        bot.send_message(config.tgChannel, item['text'] + linkurl)
                    elif isRepost:
                        bot.send_message(config.tgChannel,
                                         '<a href="' + urlOfRepost + '"> </a>' +
                                         item['text'] + linkurl +
                                         '\n\n<b>REPOST ↓</b>\n\n' + '<i>' + textRepost + '</i>',
                                         parse_mode='HTML')
                    addLog('i', 'Text post with link sent [post id:{!s}]'.format(item['id']))

                elif isTypePost == 'doc':
                    if not config.parseDoc:
                        addLog('i', 'Post with docs/gif was skipped [post id:{!s}]'.format(item['id']))
                        isPostSent = True
                        continue
                    howLong = len(item['text'])
                    if not isRepost:
                        if doc_is == 'gif':
                            if howLong <= 1024:
                                bot.send_video(config.tgChannel, docurl_gif, duration=None, caption=item['text'])
                            elif howLong > 1024:
                                bot.send_message(config.tgChannel, item['text'])
                                bot.send_video(config.tgChannel, docurl_gif)
                        else:
                            if howLong <= 1024:
                                with open(os.path.join('temp', doc_title), 'rb') as temp_file:
                                    bot.send_document(config.tgChannel, temp_file, reply_to_message_id=None,
                                                      caption=item['text'])
                            elif howLong > 1024:
                                bot.send_message(config.tgChannel, item['text'])
                                with open(os.path.join('temp', doc_title), 'rb') as temp_file:
                                    bot.send_document(config.tgChannel, temp_file)
                    elif isRepost:
                        if item['text'] != '':
                            item_text = item['text'] + '\n\n'
                        elif item['text'] == '':
                            item_text = ''
                        if doc_is == 'gif':
                            gif_text = item_text + '<b>REPOST ↓</b>\n\n' + '<i>' + textRepost + '</i>'
                            if len(gif_text) <= 1024:
                                bot.send_video(config.tgChannel, docurl_gif, duration=None, caption=gif_text,
                                               reply_to_message_id=None, reply_markup=None, parse_mode='HTML')
                            elif len(gif_text) > 1024:
                                bot.send_message(config.tgChannel,
                                                 item_text + '<b>REPOST ↓</b>\n\n' +
                                                 '<i>' + textRepost + '</i>',
                                                 parse_mode='HTML')
                                bot.send_video(config.tgChannel, docurl_gif)
                        else:
                            with open(os.path.join('temp', doc_title), 'rb') as temp_file:
                                doc_text = item_text + '<b>REPOST ↓</b>\n\n' + '<i>' + textRepost + '</i>'
                                if len(doc_text) <= 1024:
                                    bot.send_document(config.tgChannel, temp_file, reply_to_message_id=None,
                                                      caption=doc_text, reply_markup=None, parse_mode='HTML')
                                elif len(doc_text) > 1024:
                                    bot.send_message(config.tgChannel,
                                                     item_text + '<b>REPOST ↓</b>\n\n' +
                                                     '<i>' + textRepost + '</i>',
                                                     parse_mode='HTML')
                                    bot.send_document(config.tgChannel, temp_file)
                    addLog('i', 'Post with document/gif sent [post id:{!s}]'.format(item['id']))
                isPostSent = True
            except Exception as ex:
                isPostSent = False
                addLog('w', 'Something [{!s}] went wrong in sendPosts() [post id:{!s}] [{!s} try of {!s}]: {!s}'.format(
                    type(ex).__name__, item['id'], attempt + 1, tries, str(ex)))
                if attempt == tries - 1:
                    break
                time.sleep(10)
                continue
        cleaning('after')


def checkNewPost():
    isBotChannelAdmin(bot, config.tgChannel)
    addLog('i', '[VK] Started scanning for new posts')
    with open('last_known_id.txt', 'r') as file:
        last_id = int(file.read())
        if last_id is None:
            addLog('e', 'Could not read from storage. Skipped iteration')
            return
        addLog('i', 'Last id of vk post is {!s}'.format(last_id))
    try:
        feed = getData()
        # continue if we received data
        if feed is not None:
            entries = feed
            try:
                # if the post is pinned, skip it
                pinned = entries[0]['is_pinned']
                # and call sendPosts
                config.isPinned = True
                sendPosts(entries[1:], last_id)
            except KeyError:
                config.isPinned = False
                sendPosts(entries, last_id)
            # write new last_id to file
            with open('last_known_id.txt', 'w') as file:
                try:
                    pinned = entries[0]['is_pinned']
                    file.write(str(entries[1]['id']))
                    addLog('i', 'New last id of vk post is {!s}'.format((entries[1]['id'])))
                except KeyError:
                    file.write(str(entries[0]['id']))
                    addLog('i', 'New last id of vk post is {!s}'.format((entries[0]['id'])))
    except Exception as ex:
        addLog('e', 'Exception in type {!s} in checkNewPost(): {!s}'.format(type(ex).__name__, str(ex)))
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
        addLog('e', 'Something [{!s}] went wrong in cleaning(): {!s}'.format(type(ex).__name__, str(ex)))


# method for checking if a bot is a channel administrator
def isBotChannelAdmin(specific_bot, specific_channel):
    try:
        _ = specific_bot.get_chat_administrators(specific_channel)
    except Exception as ex:
        global isBotForLog
        isBotForLog = False
        addLog('e', 'Bot is not channel admin ({!s})\nBot was stopped!'.format(specific_channel))
        exit()


def addLog(type, text):
    global isBotForLog
    if isBotForLog:
        isBotChannelAdmin(bot_2, config.tgLogChannel)
    log_message = ''
    if type == 'w':  # WARNING
        log_message = '[WARNING] {!s}'.format(text)
        print(datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
              '| ' + log_message)
        logging.warning(log_message)
    elif type == 'i':  # INFO
        log_message = '[Bot] [Info] {!s}'.format(text)
        print(datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
              '| ' + log_message)
        logging.info(log_message)
    elif type == 'e':  # ERROR
        log_message = '[ERROR] {!s}'.format(text)
        print(datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
              '| ' + log_message)
        logging.error(log_message)
    if isBotForLog:
        sendLog(log_message)


def sendLog(log_message):
    global isBotForLog
    if isBotForLog:
        try:
            log_message_temp = '<code>' + log_message + '</code>\ntgChannel = ' + config.tgChannel + \
                               '\nvkDomain = <code>' + config.vkDomain + '</code>'
            bot_2.send_message(config.tgLogChannel, log_message_temp, parse_mode='HTML')
        except Exception as ex:
            log_message = '[ERROR] Something [{!s}] went wrong in sendLog(): {!s}'.format(
                type(ex).__name__, str(ex))
            print(datetime.now().strftime("%d-%m-%Y %H:%M:%S"), '| ' + log_message)
            logging.error(log_message)


def getVideo(owner_id, video_id, access_key):
    try:
        data = requests.get(
            f'https://api.vk.com/method/video.get?access_token={config.vkToken}&v=5.103&videos={owner_id}_{video_id}_{access_key}')
        return data.json()['response']['items'][0]['files']['external']
    except Exception:
        return None


if __name__ == '__main__':
    logging.getLogger('requests').setLevel(logging.CRITICAL)
    logging.basicConfig(format='[%(asctime)s] %(filename)s:%(lineno)d %(levelname)s - %(message)s',
                        level=logging.INFO, filename='bot.log', datefmt='%d.%m.%Y %H:%M:%S')
    if not config.singleStart:
        while True:
            checkNewPost()
            addLog('i', 'Script went to sleep for ' + str(config.timeSleep) + ' seconds\n\n')
            # pause for n minutes (timeSleep in config.py)
            time.sleep(int(config.timeSleep))
    elif config.singleStart:
        checkNewPost()
        addLog('i', 'Script exited.')
