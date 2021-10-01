import os
from os.path import join, dirname

from dotenv import load_dotenv

tgChannel = "@aaaa"  # link to the channel in telegram
# or channel ID (for example: tgChannel = -1234567890987)
# (you can get channel ID here t.me/username_to_id_bot)
# you must add bot to this channel as an administrator
# don't forget to add bot to this channel as an administrator!

tgBotToken = "1234567890:AAA-AaA1aaa1AAaaAa1a1AAAAA-a1aa1-Aa"  # your bot's token from t.me/BotFather
vkToken = "00a0a0ab00f0a0ab00f0a6ab0c00000b0f000f000f0a0ab0a00b000000dd00000000de0"  # your token from https://github.com/alcortazzo/vktgbot/wiki/How-to-get-personal-access-token
vkDomain = "bbbb"  # domain of vk channel (vk.com/>>>>aaaaaaaa<<<<)

tgLogChannel = "@cccc"  # link to another channel in telegram if you want to get bot's log message
# you can use the same bot as for the main task
# don't forget to add bot to this channel as an administrator!
tgBotForLogToken = ""  # set token here if you want vktgbot to use another bot for logging
# leave the variable empty if you want use first bot (tgBotToken) for logging
# don't forget to add this bot to tgLogChannel as administrator

reqVer = 5.103  # version of VK API (https://vk.com/dev/versions). used for wall.get method
reqCount = 3  # number of posts to send to telegram (2 - 100)
reqFilter = "owner"  # Filter to apply:
# "owner" — posts by the wall owner;
# "others" — posts by someone else;
# "all" — posts by the wall owner and others
# "postponed" — timed posts (only available for calls with an access_token)
# "suggests" — suggested posts on a community wall

singleStart = False  # if True bot will stop after first pass through the loop
timeSleep = 60 * 2  # waiting time between cycle passes
isPinned = False
skipAdsPosts = True  # set True if you want to skip sponsored posts
skipPostsWithCopyright = False

WHITELIST = []  # Words whitelist. Bot will repost posts only containing words in whitelist. Useful for hashtags
BLACKLIST = []  # Words blacklist. If a post contains a blacklisted word, the post will be skipped
# Example
# WHITELIST = ["#music", "new"]
# BLACKLIST = ["rap", "dubstep"]
# This configuration will keep posts only with music hashtag and word "new" excluding posts with words "rap" and "dubstep"

proxyEnable = False  # Set True if telegram is not available in your country
proxyLogin = "bot"  # Login for Socks5 proxy
proxyPass = "12345"  # Password for Socks5 proxy
proxyIp = "myproxy.com"  # Socks5 proxy ip
proxyPort = "1234"  # Socks5 proxy port

logFolderName = "logs"  # name of the folder in which the log files will be stored
logFileName = "dev.log"


def get_config():
    try:
        dotenv_path = join(dirname(__file__), '.env')
        load_dotenv(dotenv_path)
    except NameError:
        print("[Config] can't parse .env file. Error: " + NameError)

    global tgChannel, tgBotToken, vkToken, vkDomain, tgLogChannel, tgBotForLogToken, tgBotForLogToken, \
        reqVer, reqCount, reqFilter, singleStart, timeSleep, isPinned, skipAdsPosts, \
        skipPostsWithCopyright, WHITELIST, BLACKLIST, proxyEnable, proxyLogin, \
        proxyPass, proxyIp, proxyPort, logFolderName, logFileName

    tgChannel = os.getenv('VAR_TG_CHANNEL', default="@aaaa")
    tgBotToken = os.getenv('VAR_TG_BOT_TOKEN', default="1234567890:AAA-AaA1aaa1AAaaAa1a1AAAAA-a1aa1-Aa")

    vkToken = os.getenv('VAR_TG_VK_TOKEN',
                        default="00a0a0ab00f0a0ab00f0a6ab0c00000b0f000f000f0a0ab0a00b000000dd00000000de0")
    vkDomain = os.getenv('VAR_TG_VK_DOMAIN', default="bbbb")

    tgLogChannel = os.getenv('VAR_TG_LOG_CHANNEL', default="@cccc")
    tgBotForLogToken = os.getenv('VAR_TG_BOT_LOG_TOKEN', default="")

    reqVer = os.getenv('VAR_REQ_VER', default=5.103)
    reqCount = os.getenv('VAR_REQ_COUNT', default=3)
    reqFilter = os.getenv('VAR_REQ_FILTER', default="owner")

    singleStart = os.getenv('VAR_SINGLE_START', default=False)
    timeSleep = os.getenv('VAR_TIMESLEEP', default=60 * 2)
    isPinned = os.getenv('VAR_IS_PINNED', default=False)
    skipAdsPosts = os.getenv('VAR_SKIP_ADS_POSTS', default=True)
    skipPostsWithCopyright = os.getenv('VAR_SKIP_POSTS_WITH_COPYRIGHT', default=False)

    WHITELIST = os.getenv('VAR_TG_WHITELIST', default=[])
    BLACKLIST = os.getenv('VAR_TG_BLACKLIST', default=[])

    proxyEnable = os.getenv('VAR_PROXY_ENABLE', default=False)
    proxyLogin = os.getenv('VAR_PROXY_LOGIN', default="bot")
    proxyPass = os.getenv('VAR_PROXY_PROXY_PASS', default="12345")
    proxyIp = os.getenv('VAR_PROXY_PROXY_IP', default="myproxy.com")
    proxyPort = os.getenv('VAR_PROXY_PROXY_PORT', default="1234")

    logFolderName = os.getenv('VAR_LOG_FOLDER_NAME', default="logs")
    logFileName = os.getenv('VAR_LOG_FILENAME', default="dev.log")
