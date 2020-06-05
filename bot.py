#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Made by @alcortazzo
v1.0.2
'''

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

if config.proxyEnable:
    apihelper.proxy = {'https': f'socks5://{config.proxyLogin}:{config.proxyPass}@{config.proxyIp}:{config.proxyPort}'}

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
            print(datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
                  '| [Bot] [Info] No photos in the post [post id:{!s}]'.format(item['id']))
            logging.info('[Bot] [Info] No photos in the post [post id:{!s}]'.format(item['id']))

        try:
            if item['attachments'][0]['type'] == 'video':
                isTypePost = 'video'
                videoUrlPreview = item['attachments'][0]['video']['image'][-1]['url']
        except Exception as ex:
            print(datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
                  '| [Bot] [Info] No videos in the post [post id:{!s}]'.format(item['id']))
            logging.info('[Bot] [Info] No videos in the post [post id:{!s}]'.format(item['id']))

        try:
            if item['attachments'][0]['type'] == 'link':
                isTypePost = 'link'
                linkurl = item['attachments'][0]['link']['url']
        except Exception as ex:
            print(datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
                  '| [Bot] [Info] No links in the post [post id:{!s}]'.format(item['id']))
            logging.info('[Bot] [Info] No links in the post [post id:{!s}]'.format(item['id']))

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
            print(datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
                  '| [Bot] [Info] No documents/gifs in the post [post id:{!s}]'.format(item['id']))
            logging.info('[Bot] [Info] No documents/gifs in the post [post id:{!s}]'.format(item['id']))

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
            # send messages with photos
            if len(urlsPhoto) >= 2:
                # get photos from urls
                for urlPhoto in urlsPhoto:
                    listOfPhotos.append(types.InputMediaPhoto(urllib.request.urlopen(urlPhoto).read()))

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
            elif len(urlsPhoto) == 1:
                Photo = urlsPhoto[0]
                howLong = len(item['text'])
                if not isRepost:
                    if howLong <= 1024:
                        bot.send_photo(config.tgChannel, Photo, item['text'])
                    elif howLong > 1024:
                        bot.send_message(config.tgChannel, '[ ](' + Photo + ')' + item['text'], parse_mode='Markdown')
                elif isRepost:
                    bot.send_message(config.tgChannel,
                                     '[ ](' + Photo + ')' + item['text'] + '\n\n*REPOST ↓*\n\n_' + textRepost + '_',
                                     parse_mode='Markdown')
                print(datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
                      '| [Bot] Post with photo sent [post id:{!s}]'.format(item['id']))
                logging.info('[Bot] Post with photo sent [post id:{!s}]'.format(item['id']))

        elif isTypePost == 'video':
            howLong = len(item['text'])
            # send messages with video preview
            if not isRepost:
                if howLong <= 1024:
                    bot.send_photo(config.tgChannel, videoUrlPreview, item['text'])
                elif howLong > 1024:
                    bot.send_message(config.tgChannel, '[ ](' + videoUrlPreview + ')' + item['text'],
                                     parse_mode='Markdown')
            elif isRepost:
                bot.send_message(
                    config.tgChannel,
                    '[ ](' + videoUrlPreview + ')' + item['text'] + '\n\n*REPOST ↓*\n\n_' + textRepost + '_',
                    parse_mode='Markdown')
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
                  '| [Bot] Text post with link sent [post id:{!s}]'.format(item['id']))
            logging.info('[Bot] Text post with link sent [post id:{!s}]'.format(item['id']))

        elif isTypePost == 'doc':
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
            if isRepost:
                if doc_is == 'gif':
                    gif_text = item['text'] + '\n\n*REPOST ↓*\n\n' + '_' + textRepost + '_'
                    if len(gif_text) <= 1024:
                        bot.send_video(config.tgChannel, docurl_gif, duration=None, caption=gif_text,
                                       reply_to_message_id=None, reply_markup=None, parse_mode='Markdown')
                    elif len(gif_text) > 1024:
                        bot.send_message(config.tgChannel, item['text'] + '\n\n*REPOST ↓*\n\n' + '_' + textRepost + '_',
                                         parse_mode='Markdown')
                        bot.send_video(config.tgChannel, docurl_gif)
                else:
                    with open(os.path.join('temp', doc_title), 'rb') as temp_file:
                        doc_text = item['text'] + '\n\n*REPOST ↓*\n\n' + '_' + textRepost + '_'
                        if len(doc_text) <= 1024:
                            bot.send_document(config.tgChannel, temp_file, reply_to_message_id=None, caption=doc_text,
                                              reply_markup=None, parse_mode='Markdown')
                        elif len(doc_text) > 1024:
                            bot.send_message(config.tgChannel,
                                             item['text'] + '\n\n*REPOST ↓*\n\n' + '_' + textRepost + '_',
                                             parse_mode='Markdown')
                            bot.send_document(config.tgChannel, temp_file)
            print(datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
                  '| [Bot] Post with document/gif sent [post id:{!s}]'.format(item['id']))
            logging.info('[Bot] Post with document/gif sent [post id:{!s}]'.format(item['id']))
        cleaning('after')


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


def cleaning(when):
    if when == 'before':
        if 'temp' in os.listdir():
            shutil.rmtree('temp')
            os.mkdir('temp')
        elif 'temp' not in os.listdir():
            os.mkdir('temp')
    elif when == 'after':
        shutil.rmtree('temp')


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
