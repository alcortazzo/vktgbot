
<h1 id="-p-align-center-vktgbot-v0-8"><p align="center">vktgbot</h1>
<p align=center>
    <a target="_blank" href="https://www.python.org/downloads/" title="Python Version"><img src="https://img.shields.io/badge/python-%3E=_3.6-purple.svg"></a>
    <a target="_blank" href="https://github.com/alcortazzo/vktgbot/releases"><img alt="docker image" src="https://img.shields.io/github/v/release/alcortazzo/vktgbot?include_prereleases"></a>
    <a target="_blank" href="LICENSE" title="License: GPL-3.0"><img src="https://img.shields.io/github/license/alcortazzo/vktgbot.svg?color=red"></a>
</p>    
<p align="center"><b>Telegram Bot in Python for automated reposting from VKontakte community pages (groups or public pages) to Telegram channels.</b></p>

<p align="center">
    <a href="#what-bot-can-post-to-telegram">What bot can post to Telegram</a>
    &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;
    <a href="#how-bot-works">How bot works</a>
    &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;
    <a href="#installation--usage">Installation & Usage</a>
</p>
<p align="center">
<a href="https://youtu.be/DyLmaJg0v-w?t=3">
<img src="https://github.com/alcortazzo/vktgbot/blob/master/images/code.png"/>
</a>
</p>
<p align="center"><i>rus: Телеграм бот для автоматического парсинга (репоста) постов из пабликов ВК в Телеграм каналы</i></p>

## What bot can post to Telegram
|    Type of VK post    | Can it? |                       Notes                       |
| :-------------------: | :-----: | :-----------------------------------------------: |
|     Text of posts     | **Yes** |
|    Photos of posts    | **Yes** |
|    Links of posts     | **Yes** |
| YT/VK videos of posts | **Yes** |      *Bot will attach video links to posts.*      |
|    Polls of posts     | **No**  |
|  VK reposts of posts  | **Yes** |
|       Documents       | **Yes** |

### In addition, the bot can skip advertising posts if in `config.py`
```python
skip_ads_posts = True
```

## How bot works
* Bot requests and receives data (posts) from VK via vk api (get.wall method).
* Then the bot compares ID from *last_known_id.txt* with ID of the last received post.
* If the ID from the file is less than the ID of the received posts, bot will parse and send new posts to Telegram and write the new ID to the file.
* The bot then waits for the period set by the user in `config.py` and starts again.

## Installation & Usage
### Linux or macOS
```bash
# clone the repo
$ git clone https://github.com/alcortazzo/vktgbot.git

# change the working directory to vktgbot
$ cd vktgbot

# install python3 and python3-pip if they are not installed

# install the requirements
$ python3 -m pip install -r requirements.txt
```
Or launch it in [docker](#docker-58mb)

### Windows
 **If you want to use git**
```bash
# clone the repo
git clone https://github.com/alcortazzo/vktgbot.git

# change the working directory to vktgbot
cd vktgbot

# install python3 and python3-pip if they are not installed

# install the requirements
python -m pip install -r requirements.txt
```
**If you don't want to use git**
1. [Download](https://github.com/alcortazzo/vktgbot/archive/master.zip)  vktgbot repo as ZIP
2. Unzip vktgbot to your folder (for example C:\\Users\\%username%\\bots\\)
3. Then open **cmd** or **powershell**
```bash
# change the working directory to vktgbot
cd c:\\users\\%username%\\bots\\vktgbot

# install the requirements
python -m pip install -r requirements.txt
```
### Open **config** file and update the following variables:
```python
tg_channel = "@aaaa"
tg_bot_token = "1234567890:AAA-AaA1aaa1AAaaAa1a1AAAAA-a1aa1-Aa"
vk_token = "00a0a0ab00f0a0ab00f0a6ab0c00000b0f000f000f0a0ab0a00b000000dd00000000de0"
vk_domain = "bbbb"
```
* `tg_channel` is link or ID of the Telegram channel. **You must add bot to this channel as an administrator!**
* `tg_bot_token` is token for your Telegram bot. You can get it here: [BotFather](https://t.me/BotFather).
* `vk_token` is personal token for your VK profile. You can get it here: [HowToGet](https://github.com/alcortazzo/vktgbot/wiki/How-to-get-personal-access-token).
* `vk_domain` is part of the link (after vk.com/) to the VK channel. For example, if link is `vk.com/durov`, you should set `= "durov"`.
#### If Telegram is not available in your country, you should update these variables.
```python
proxy_enable = True
proxy_login = "bot"  
proxy_pass = "12345"  
proxy_ip = "myproxy.com"  
proxy_port = "1234"
```
#### Open file **last_known_id.txt** and write the ID of the last post (not pinned!) into it:
* For example, if the link to post is `https://vk.com/wall-22822305_1070803`, then the id of that post will be `1070803`.
* [PhotoExemple](https://i.imgur.com/eWpso0C.png)
### Launch the bot
#### Linux or macOS
```bash
$ python3 bot.py
```
#### Windows
```bash
python bot.py
```
#### Docker (58MB)
```bash
docker build -t vktgbot .
docker run -dt --name vktgbot vktgbot
```
View logs: `docker logs --follow vktgbot`
## License

GPLv3<br/>
Original Creator - [alcortazzo](https://github.com/alcortazzo)
