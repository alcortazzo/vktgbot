#!/usr/bin/env python
# -*- coding: utf-8 -*-

tgChannel = '@aaaa' # link to channel in telegram !!! you must add bot to this channel as an administrator
tgBotToken = '1234567890:AAA-AaA1aaa1AAaaAa1a1AAAAA-a1aa1-Aa' # your token from t.me/BotFather
vkToken = '00a0a0ab00f0a0ab00f0a6ab0c00000b0f000f000f0a0ab0a00b000000dd00000000de0' # your token from https://vk.com/dev/authcode_flow_user
vkDomain = 'aaaaaaaa' # domain of vk channel (vk.com/>>>>aaaaaaaa<<<<)

reqVer = 5.103  # version of VK API [wall.get method]
reqCount = 2 # number of posts to return (maximum 100)
reqFilter = 'owner'  # Filter to apply: owner — posts by the wall owner; others — posts by someone else;
                     # all — posts by the wall owner and others (default)
                     # postponed — timed posts (only available for calls with an access_token)
                     # suggests — suggested posts on a community wall

singleStart = False
timeSleep = 60 * 3  # time in seconds
isPinned = False
skipAdsPosts = True
