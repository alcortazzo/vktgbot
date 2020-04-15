

# vktgbot v0.1

## Overview
Telegram Bot on Python for repost from VKontakte community pages (group, public page or event page) to Telegram Channels.

## What is now implemented
|Type|Is implemented?|When was added|
|:---:|:---:|:---:|
|Text from posts|Yes|14-Apr-2020|
|Images from posts|Only image's urls for now|~|
|Links to YouTube vids|Not yet|~
|Polls|Not yet|~

## How bot works [for now]
* Bot sends and receives request from vk api [get.wall method]
* Then bot compares the id from *last_known_id.txt* with the id of the last post
* If id of the last post is less than id from *last_known_id.txt* the bot will write a new id to file and call the function **sendPosts()**
 * sendPosts() checks post type and
   * if the post type is just text, it sends one text message to telegram
   * if the post type is text + photo, it sends two messages to telegram: text message + message with urls to images [i will fix that]
* Then bot waits for the period set by the user and starts again

## Installation & Usage
### Python 3
#### Windows
```
pip install -r requirements.txt
```
#### Linux
```
pip3 install -r requirements.txt
```
### Open **config** file and update the following variables:
```python
tgChannel = '@aaaa'
tgBotToken = '1234567890:AAA-AaA1aaa1AAaaAa1a1AAAAA-a1aa1-Aa'
vkToken = '00a0a0ab00f0a0ab00f0a6ab0c00000b0f000f000f0a0ab0a00b000000dd00000000de0'
vkDomain = 'aaaaaaaa'
```
* `tgChannel` is the link to channel in telegram `t.me/>>aaaa<<`. **You must add bot to this channel as an administrator**
* `tgBotToken` is the bot token from [BotFather](t.me/BotFather)
* `vkToken` is vk service token. [HowToGet](https://youtu.be/oGS683RYmg8)
* `vkDomain` is the link to vk public `vk.com/>>aaaaaaaa<<`
### Launch the bot
#### Windows
```
python vktgbot.py
```
#### Linux
```
python3 vktgbot.py
```
