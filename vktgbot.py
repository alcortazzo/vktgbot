#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Made by @alcortazzo
v0.2
'''

import config
import requests
import telebot
import eventlet
import time
from datetime import datetime

bot = telebot.TeleBot(config.tgBotToken)


def getData():
    timeout = eventlet.Timeout(20)
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
              '| [ERROR] Got Timeout while retrieving VK JSON data. Cancelling...')
        return None
    finally:
        timeout.cancel()


def sendPosts(items, last_id):
    isTypePost = 'post'
    # posts = items
    for item in items:
        if item['id'] <= last_id:
            break
        post = item
        try:
            if post['attachments'][0]['type'] == 'photo':
                isTypePost = 'photo'
                photos = post['attachments']
                urlsPhoto = []
                for photo in photos:
                    urls = photo['photo']['sizes']
                    for url in urls:
                        if url['type'] == 'w':
                            urlsPhoto.append(url['url'])
                            break
                        elif url['type'] == 'z':
                            urlsPhoto.append(url['url'])
                            break
        except Exception as ex:
            print(datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
                  '| [Bot] [Info] Photos from the post has been added to the message',
                  'or the post did not have photos {!s} in sendPosts(): {!s}'.format(
                      type(ex).__name__, str(ex)))

        try:
            if post['attachments'][0]['type'] == 'video':
                isTypePost = 'video'
                videoUrlPreview = post['attachments'][0]['video']['image'][-1]['url']
                print(videoUrlPreview)
        except Exception as ex:
            print(datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
                  '| [Bot] [Info] The post did not have videos {!s} in sendPosts(): {!s}'.format(
                      type(ex).__name__, str(ex)))

        try:
            if post['attachments'][0]['type'] == 'link':
                isTypePost = 'link'
                linkurl = post['attachments'][0]['link']['url']
                print(linkurl)
        except Exception as ex:
            print(datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
                  '| [Bot] [Info] The post did not have links {!s} in sendPosts(): {!s}'.format(
                      type(ex).__name__, str(ex)))

        if isTypePost == 'post':
            tgPost = '{!s}{!s}'.format(item['text'])
            bot.send_message(config.tgChannel, tgPost)
            print(datetime.now().strftime("%d-%m-%Y %H:%M:%S"), '| [Bot] Text post without photo/video sent')

        elif isTypePost == 'photo':
            x = ''
            for urlPhoto in urlsPhoto:
                x += urlPhoto + '\n'
            print(x)
            tgPost = '{!s}{!s}'.format(item['text'], '\n\n' + x)
            bot.send_message(config.tgChannel, tgPost)
            print(datetime.now().strftime("%d-%m-%Y %H:%M:%S"), '| [Bot] Text post with photos sent')

        elif isTypePost == 'video':
            tgPost = '{!s}{!s}'.format(item['text'], '\n\n' + videoUrlPreview)
            bot.send_message(config.tgChannel, tgPost)
            print(datetime.now().strftime("%d-%m-%Y %H:%M:%S"), '| [Bot] Text post with video sent')

        elif isTypePost == 'link':
            tgPost = '{!s}{!s}'.format(item['text'], '\n\n' + linkurl)
            bot.send_message(config.tgChannel, tgPost)
            print(datetime.now().strftime("%d-%m-%Y %H:%M:%S"), '| [Bot] Text post with links sent')


def checkNewPost():
    print(datetime.now().strftime("%d-%m-%Y %H:%M:%S"), '| [VK] Started scanning for new posts')
    with open('last_known_id.txt', 'r') as file:
        last_id = int(file.read())
        if last_id is None:
            print(datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
                  '| [ERROR] Could not read from storage. Skipped iteration')
            return
        print(datetime.now().strftime("%d-%m-%Y %H:%M:%S"), '| [Info] Last id of vk post is {!s}'.format(last_id))
    try:
        feed = getData()
        if feed is not None:
            entries = feed
            try:
                pinned = entries[0]['is_pinned']
                config.isPinned = True
                sendPosts(entries[1:], last_id)
            except KeyError:
                config.isPinned = False
                sendPosts(entries, last_id)
            with open('last_known_id.txt', 'w') as file:
                try:
                    pinned = entries[0]['is_pinned']
                    file.write(str(entries[1]['id']))
                    print(datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
                          '| [Info] New Last id (VK) is {!s}'.format((entries[1]['id'])))
                except KeyError:
                    file.write(str(entries[0]['id']))
                    print(datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
                          '| [Info] New Last id (VK) is {!s}'.format((entries[0]['id'])))
    except Exception as ex:
        print(datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
              '| Excepion in type {!s} in checkNewPost(): {!s}'.format(type(ex).__name__, str(ex)))
        pass
    print(datetime.now().strftime("%d-%m-%Y %H:%M:%S"), '| [VK] Finished scanning')
    return


if __name__ == '__main__':
    if not config.singleStart:
        while True:
            checkNewPost()
            print(datetime.now().strftime("%d-%m-%Y %H:%M:%S"), '| [Bot] Script went to sleep for', config.timeSleep,
                  'seconds\n\n')
            time.sleep(int(config.timeSleep))
    elif config.singleStart:
        checkNewPost()
        print(datetime.now().strftime("%d-%m-%Y %H:%M:%S"), '| [Bot] Script exited.\n')
