#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Made by @alcortazzo
v0.8
'''

import time
import urllib
import config
import logging
import requests
import eventlet
from datetime import datetime
from telebot import TeleBot, types

bot = TeleBot(config.tgBotToken)

print('\n\n            /$$         /$$               /$$                   /$$    \n',
      '           | $$        | $$              | $$                  | $$    \n',
      ' /$$    /$$| $$   /$$ /$$$$$$    /$$$$$$ | $$$$$$$   /$$$$$$  /$$$$$$  \n',
      '|  $$  /$$/| $$  /$$/|_  $$_/   /$$__  $$| $$__  $$ /$$__  $$|_  $$_/  \n',
      ' \  $$/$$/ | $$$$$$/   | $$    | $$  \ $$| $$  \ $$| $$  \ $$  | $$    \n',
      '  \  $$$/  | $$_  $$   | $$ /$$| $$  | $$| $$  | $$| $$  | $$  | $$ /$$\n',
      '   \  $/   | $$ \  $$  |  $$$$/|  $$$$$$$| $$$$$$$/|  $$$$$$/  |  $$$$/\n',
      '    \_/    |__/  \__/   \___/   \____  $$|_______/  \______/    \___/  \n',
      '                                /$$  \ $$                              \n',
      '                               |  $$$$$$/                              \n',
      '                                \______/                               \n\n')

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
        print(datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
              '| [WARNING] Got Timeout while retrieving VK JSON data. Cancelling...')
        logging.warning('[WARNING] Got Timeout while retrieving VK JSON data. Cancelling...')
        return None
    finally:
        timeout.cancel()


def sendPosts(items, last_id):
    for item in items:
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
            print(datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
                  '| [Bot] [Info] No photos in the post [post id:{!s}].'.format(item['id']))
            logging.info('[Bot] [Info] No photos in the post [post id:{!s}].'.format(item['id']))

        try:
            if item['attachments'][0]['type'] == 'video':
                isTypePost = 'video'
                videoUrlPreview = item['attachments'][0]['video']['image'][-1]['url']
        except Exception as ex:
            print(datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
                  '| [Bot] [Info] No videos in the post [post id:{!s}].'.format(item['id']))
            logging.info('[Bot] [Info] No videos in the post [post id:{!s}].'.format(item['id']))

        try:
            if item['attachments'][0]['type'] == 'link':
                isTypePost = 'link'
                linkurl = item['attachments'][0]['link']['url']
        except Exception as ex:
            print(datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
                  '| [Bot] [Info] No links in the post [post id:{!s}]'.format(item['id']))
            logging.info('[Bot] [Info] No links in the post [post id:{!s}]'.format(item['id']))

        # REPOST check
        try:
            if 'copy_history' in item:
                isRepost = True
                if item['copy_history'][0]['text'] != '':
                    textRepost = item['copy_history'][0]['text']
        except Exception as ex:
            print(datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
                  '[ERROR] {!s} in sendPosts() (RepostCheck) [post id:{!s}]: {!s}'.format(
                      type(ex).__name__, item['id'], str(ex)))
            logging.error('[ERROR] {!s} in sendPosts() (RepostCheck) [post id:{!s}]: {!s}'.format(
                type(ex).__name__, item['id'], str(ex)))

        # send message according to post type
        if isTypePost == 'post':
            if not isRepost:
                bot.send_message(config.tgChannel, item['text'])
            elif isRepost:
                bot.send_message(config.tgChannel, item['text'] + '\n\n*REPOST ↓*\n\n' + '_' + textRepost + '_',
                                 parse_mode='Markdown')
            print(datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
                  '| [Bot] Text post sent [post id:{!s}]'.format(item['id']))
            logging.info('[Bot] Text post sent [post id:{!s}]'.format(item['id']))

        elif isTypePost == 'photo':
            listOfPhotos = []
            # get photos from urls
            for urlPhoto in urlsPhoto:
                listOfPhotos.append(types.InputMediaPhoto(urllib.request.urlopen(urlPhoto).read()))
            # send messages with photos
            if not isRepost:
                if item['text'] != '':
                    bot.send_message(config.tgChannel, item['text'])
            elif isRepost:
                bot.send_message(config.tgChannel, item['text'] + '\n\n*REPOST ↓*\n\n' + '_' + textRepost + '_',
                                 parse_mode='Markdown')
            print(datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
                  '| [Bot] Text post sent [post id:{!s}]'.format(item['id']))
            logging.info('[Bot] Text post sent [post id:{!s}]'.format(item['id']))
            bot.send_media_group(config.tgChannel, listOfPhotos)
            print(datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
                  '| [Bot] Post with photo sent [post id:{!s}]'.format(item['id']))
            logging.info('[Bot] Post with photo sent [post id:{!s}]'.format(item['id']))

        elif isTypePost == 'video':
            # get preview from youtube video
            listOfPreviews = []
            listOfPreviews.append(types.InputMediaPhoto(urllib.request.urlopen(videoUrlPreview).read()))
            # send messages with video preview
            if not isRepost:
                if item['text'] != '':
                    bot.send_message(config.tgChannel, item['text'])
            elif isRepost:
                bot.send_message(config.tgChannel, item['text'] + '\n\n*REPOST ↓*\n\n' + '_' + textRepost + '_',
                                 parse_mode='Markdown')
            print(datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
                  '| [Bot] Text post sent [post id:{!s}]'.format(item['id']))
            logging.info('[Bot] Text post sent [post id:{!s}]'.format(item['id']))
            bot.send_media_group(config.tgChannel, listOfPreviews)
            print(datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
                  '| [Bot] Post with video preview sent [post id:{!s}]'.format(item['id']))
            logging.info('[Bot] Post with video preview sent [post id:{!s}]'.format(item['id']))

        elif isTypePost == 'link':
            if not isRepost:
                bot.send_message(config.tgChannel, item['text'] + '\n\n' + linkurl)
            elif isRepost:
                bot.send_message(config.tgChannel,
                                 item['text'] + '\n\n' + linkurl + '\n\n*REPOST ↓*\n\n' + '_' + textRepost + '_',
                                 parse_mode='Markdown')
            print(datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
                  '| [Bot] Text post sent [post id:{!s}]'.format(item['id']))
            logging.info('[Bot] Text post sent [post id:{!s}]'.format(item['id']))


def checkNewPost():
    print(datetime.now().strftime("%d-%m-%Y %H:%M:%S"), '| [VK] Started scanning for new posts')
    logging.info('[VK] Started scanning for new posts')
    with open('last_known_id.txt', 'r') as file:
        last_id = int(file.read())
        if last_id is None:
            print(datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
                  '| [ERROR] Could not read from storage. Skipped iteration')
            logging.warning('[VK] Could not read from storage. Skipped iteration')
            return
        print(datetime.now().strftime("%d-%m-%Y %H:%M:%S"), '| [Info] Last id of vk post is {!s}'.format(last_id))
        logging.info('[Info] Last id of vk post is {!s}'.format(last_id))
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
                    print(datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
                          '| [Info] New last id of vk post is {!s}'.format((entries[1]['id'])))
                    logging.info('[Info] New last id of vk post is {!s}'.format((entries[1]['id'])))
                except KeyError:
                    file.write(str(entries[0]['id']))
                    print(datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
                          '| [Info] New last id of vk post is {!s}'.format((entries[0]['id'])))
                    logging.info('[Info] New last id of vk post is {!s}'.format((entries[0]['id'])))
    except Exception as ex:
        print(datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
              '| Excepion in type {!s} in checkNewPost(): {!s}'.format(type(ex).__name__, str(ex)))
        logging.error('Exception of type {!s} in checkNewPost(): {!s}'.format(type(ex).__name__, str(ex)))
        pass
    print(datetime.now().strftime("%d-%m-%Y %H:%M:%S"), '| [VK] Finished scanning')
    logging.info('[VK] Finished scanning')
    return


if __name__ == '__main__':
    logging.getLogger('requests').setLevel(logging.CRITICAL)
    logging.basicConfig(format='[%(asctime)s] %(filename)s:%(lineno)d %(levelname)s - %(message)s',
                        level=logging.INFO, filename='bot.log', datefmt='%d.%m.%Y %H:%M:%S')
    if not config.singleStart:
        while True:
            checkNewPost()
            print(datetime.now().strftime("%d-%m-%Y %H:%M:%S"), '| [Bot] Script went to sleep for', config.timeSleep,
                  'seconds\n\n')
            logging.info('[Bot] Script went to sleep.\n\n')
            # pause for n minutes (timeSleep in config.py)
            time.sleep(int(config.timeSleep))
    elif config.singleStart:
        checkNewPost()
        print(datetime.now().strftime("%d-%m-%Y %H:%M:%S"), '| [Bot] Script exited.\n')
        logging.info('[Bot] Script exited.\n')
