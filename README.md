# <p align="center">vktgbot v0.4

<p align="center">Telegram Bot on Python for repost from VKontakte community pages (group, public page or event page) to Telegram Channels.

* [What is now implemented](#what-is-now-implemented)
* [How bot works](#how-bot-works)
* [Installation & Usage](#installation--usage)

## What is now implemented
|Type of post|Is implemented?|When was added|
|:---:|:---:|:---:|
|Just text|Yes|v0.1|
|Text with photos|Yes|v0.2 - v0.3|
|Text with links|Yes|v0.2
|Text with YT vids|Text + preview's urls > **VK-API restrictions**|v0.2
|Text with audios|Text **without** audios > **VK-API [restrictions](https://vk.com/dev/audio)**|v0.2
|Polls|Not yet|~

## How bot works
* Bot sends and receives request from vk api [get.wall method]
* Then bot compares the id from *last_known_id.txt* with the id of the last post
* If id of the last post is less than id from *last_known_id.txt* the bot will write a new id to file and call the function **sendPosts()**
 * sendPosts() checks post type and
   * if the post type is just text, it sends one text message to telegram
   * if the post type is text + photo, it sends two messages to telegram: text message + message with images
   * if the post type is text + yt video, it sends two messages to telegram: text message + video preview (because vk_api does not support video links) 
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