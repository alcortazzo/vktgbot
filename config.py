#!/usr/bin/env python
# -*- coding: utf-8 -*-

ShouldBotLog = True  # If False bot will not create and keep bot.log file
BLACKLIST = ['']  # You can add words to the blacklist. If a post contains a blacklisted word, the post will be skipped
# BLACKLIST = ['ExAmPlE', 'etc', '123456789'] <== That's an example. But be careful. Do not add just one symbol to the list.

tgChannel = '@aaaa'  # link to channel in telegram !!! you must add bot to this channel as an administrator
tgBotToken = '1234567890:AAA-AaA1aaa1AAaaAa1a1AAAAA-a1aa1-Aa'  # your token from t.me/BotFather
vkToken = '00a0a0ab00f0a0ab00f0a6ab0c00000b0f000f000f0a0ab0a00b000000dd00000000de0'  # your token from https://vk.com/dev/authcode_flow_user
vkDomain = 'bbbb'  # domain of vk channel (vk.com/>>>>aaaaaaaa<<<<)

tgLogChannel = '@cccc'  # link to another channel in telegram if you want to get bot's log message
                        # !!! you must add bot to this channel as an administrator
                        # yes, you can use the same bot as for the main task

reqVer = 5.103  # version of VK API [wall.get method]
reqCount = 3  # number of posts to return (2 - 100)
reqFilter = 'owner'  # Filter to apply: owner — posts by the wall owner; others — posts by someone else;
                     # all — posts by the wall owner and others (default)
                     # postponed — timed posts (only available for calls with an access_token)
                     # suggests — suggested posts on a community wall

singleStart = False
timeSleep = 60 * 2  # time in seconds
isPinned = False
skipAdsPosts = True

#parsePost = True   # bot will skip just text posts if the value is False
#parsePhoto = True  # bot will skip photo posts if the value is False
#parseVideo = True  # bot will skip video posts if the value is False
#parseLink = True   # bot will skip posts with link if the value is False
#parseDoc = True    # bot will skip posts with docs if the value is False
#parseGif = True    # bot will skip posts with gifs if the value is False

proxyEnable = False  # Set True if telegram is not available in your country
proxyLogin = "bot"  # Login for Socks5 proxy
proxyPass = "12345"  # Password for Socks5 proxy
proxyIp = "myproxy.com"  # Socks5 proxy ip
proxyPort = "1234"  # Socks5 proxy port
