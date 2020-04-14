#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Made by @alcortazzo
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
    posts = items
    for item in items:
        if item['id'] <= last_id:
            break
        # item = getData()
        for post in posts:
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
                                #wwwwwwwwwwww
                                break
                            elif url['type'] == 'z':
                                urlsPhoto.append(url['url'])
                                #zzzzzzzzzzzz
                                break
                            #elif url['type'] == 'y':
                            #    urlsPhoto.append(url['url'])
                            #    #yyyyyyyyyyyy
                            #    break
                    print(urlsPhoto)
            except Exception as ex:
                print(datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
                      '| [Bot] [Info] Excepion in type {!s} in sendPosts(): {!s}'.format( ########################################
                          type(ex).__name__, str(ex)))
            #try:
            #    if post['attachments'][0]['type'] == 'video':
            #        isTypePost = 'video'
            #        videoUrlPreview = post['attachments'][0]['video']['image'][-1]['url']
            #        print(videoUrlPreview)
            #except Exception as ex:
            #    print(datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
            #          '| [Bot] [Info] [No Video in post] Excepion in type {!s} in sendPosts(): {!s}'.format(
            #              type(ex).__name__, str(ex)))


        # gPostType = '{!s}{!s}'.format(img)
    if isTypePost == 'post':
        tgPost = '{!s}{!s}'.format(item['text'], '\n\n@thedrzj_tg')
        bot.send_message(config.tgChannel, tgPost)
        print(datetime.now().strftime("%d-%m-%Y %H:%M:%S"), '| [Bot] Post sent')

    elif isTypePost == 'photo':
        tgPost = '{!s}{!s}'.format(item['text'], '\n\n@thedrzj_tg')
        bot.send_message(config.tgChannel, tgPost)
        print(datetime.now().strftime("%d-%m-%Y %H:%M:%S"), '| [Bot] Post sent')

        bot.send_message(config.tgChannel, str(urlsPhoto))
        print(datetime.now().strftime("%d-%m-%Y %H:%M:%S"), '| [Bot] Photo(s) sent')
        time.sleep(1)
    elif isTypePost == 'video':
        bot.send_message(config.tgChannel, '')
        print(datetime.now().strftime("%d-%m-%Y %H:%M:%S"), '| [Bot] Video sent')
        time.sleep(1)
    return


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
