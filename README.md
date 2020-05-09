# <p align="center">vktgbot v0.8

<p align="center">Telegram Bot on Python for repost from VKontakte community pages (group, public page or event page) to Telegram Channels.

* [**Latest release**](https://github.com/alcortazzo/vktgbot/releases)
* [What is now implemented](#what-is-now-implemented)
* [How bot works](#how-bot-works)
* [Installation & Usage](#installation--usage)

## What is now implemented
|Type of VK post|Is implemented?|What bot will send to Telegram
|:---:|:---:|:---:|
|Text post|**Yes**|Text post
|Text post with photos|**Yes**|Text post & post with photos
|Text post with links|**Yes** |Text post with links
|Text post with YT vids|**50/50**|Text post & preview's urls > **VK-API restrictions**
|Text post with audios|**50/50**|Text post **without** audios > **VK-API [restrictions](https://vk.com/dev/audio)**
|VK reposts|**Yes**|Post with original post & repost text ([**e. g.**]([https://i.imgur.com/FRyo80A.png](https://i.imgur.com/FRyo80A.png)))
|Text post with polls|Not yet|Just text post for now

### In addition, bot can skip ads posts if  in `config.py`
```python
skipAdsPosts = True
```

## How bot works
* Bot sends and receives request from vk api [get.wall method]
* Then bot compares the id from *last_known_id.txt* with the id of the last post
* If `skipAdsPosts = True` in `config.py` bot will skip ads posts
* If id of the last post is larger than id from *last_known_id.txt* the bot will write a new id to file and call the function **sendPosts()**
 * sendPosts() checks post type and
   * if the post type is just text, it sends one text message to telegram
   * if the post type is text + photo, it sends two messages to telegram: text message + message with images
   * if the post type is text + yt video, it sends two messages to telegram: text message + video preview (because vk_api does not support youtube video links) 
   * if the post type is text + audio, it sends one text message without audio to telegram *(because vk_api [does not support](https://vk.com/dev/audio)  audio files)*
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
#### Open **last_known_id.txt** file and write in it id of the last (not pinned!) post:
* Example: if link to post is `https://vk.com/wall-22822305_1070803` id of this post will be `1070803`
* [PhotoExemple](https://i.imgur.com/eWpso0C.png)
### Launch the bot
#### Windows
```
python vktgbot.py
```
or
```
python vktgbot.py > log.txt
```
#### Linux
```
python3 vktgbot.py
```