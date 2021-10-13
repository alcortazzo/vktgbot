import os
from dotenv import load_dotenv

# Link or ID of the Telegram channel.
# for example:
# tgChannel = "@durov"
# tgChannel = -1234567890987
# Don't forget to add bot to this channel as an administrator!
tg_channel = "@aaaa"

# Token for your Telegram bot.
# You can get it here: https://t.me/BotFather
tg_bot_token = "1234567890:AAA-AaA1aaa1AAaaAa1a1AAAAA-a1aa1-Aa"

# Personal token for your VK profile.
# You can get it here:
# https://github.com/alcortazzo/vktgbot/wiki/How-to-get-personal-access-token
vk_token = "00a0a0ab00f0a0ab00f0a6ab0c00000b0f000f000f0a0ab0a00b000000dd00000000de0"

# Part of the link (after vk.com/) to the VK channel
# for example:
# if link is vk.com/>>>example<<<
# vk_domain = "example"
vk_domain = "bbbb"

# Link to another Telegram channel if you want to receive bot log messages.
# You can use the same bot as for the main task.
# Don't forget to add bot to this channel as an administrator!
tg_log_channel = "@cccc"

# Token for another Telegram bot if you want to use another bot for logging.
# Leave the value empty if you want use main bot (tg_bot_token) for logging.
# Don't forget to add this bot to "tg_log_channel" as administrator.
tg_bot_for_log_token = ""

# Version of VK API (https://vk.com/dev/versions).
# Used for "wall.get" method
req_version = 5.103

# Number of posts to send to Telegram.
# Min value = 2
# Max value = 100
req_count = 3

# Filter to apply:
# "owner" — posts by the wall owner;
# "others" — posts by someone else;
# "all" — posts by the wall owner and others
# "postponed" — timed posts (only available for calls with an access_token)
# "suggests" — suggested posts on a community wall
req_filter = "owner"

# If True bot will stop after first pass through the loop.
single_start = False

# Waiting time between cycle passes.
# (in seconds)
time_to_sleep = 60 * 2

# Do not touch
# Bot will specify this variable itself
_is_pinned_post = False

# Set True if you want to skip sponsored posts
skip_ads_posts = True
# Set True if you want to skip posts with specified Copyright
skip_copyrighted_post = False

# Words whitelist.
# Bot will repost posts only containing words in whitelist.
# Useful for hashtags.
WHITELIST = []
# Words blacklist.
# If post contains a blacklisted word, the post will be skipped.
BLACKLIST = []
# for example:
# WHITELIST = ["#music", "new"]
# BLACKLIST = ["rap", "dubstep"]
# This configuration will keep posts only with music hashtag
# and word "new" excluding posts with words "rap" and "dubstep".


# Set True if Telegram is not available in your country
proxy_enable = False
# Login for Socks5 proxy
proxy_login = "bot"
# Password for Socks5 proxy
proxy_pass = "12345"
# Socks5 proxy ip
proxy_ip = "myproxy.com"
# Socks5 proxy port
proxy_port = "1234"

# Name of the folder where the log files will be stored.
log_folder = "logs"
# Log file name
log_file = "dev.log"


"""Initializing values from the environment, if it exists"""
load_dotenv("./build/.env")
tg_channel = os.getenv("VAR_TG_CHANNEL", tg_channel)
tg_bot_token = os.getenv("VAR_TG_BOT_TOKEN", tg_bot_token)
vk_token = os.getenv("VAR_VK_TOKEN", vk_token)
vk_domain = os.getenv("VAR_VK_DOMAIN", vk_domain)
tg_log_channel = os.getenv("VAR_TG_LOG_CHANNEL", tg_log_channel)
tg_bot_for_log_token = os.getenv("VAR_TG_BOT_LOG_TOKEN", tg_bot_for_log_token)
req_version = os.getenv("VAR_REQ_VERSION", req_version)
req_count = os.getenv("VAR_REQ_COUNT", req_count)
req_filter = os.getenv("VAR_REQ_FILTER", req_filter)
single_start = os.getenv("VAR_SINGLE_START", single_start)
time_to_sleep = os.getenv("VAR_TIME_TO_SLEEP", time_to_sleep)
skip_ads_posts = os.getenv("VAR_SKIP_ADS_POSTS", skip_ads_posts)
skip_copyrighted_post = os.getenv("VAR_SKIP_COPYRIGHTED_POST", skip_copyrighted_post)
WHITELIST = os.getenv("VAR_WHITELIST", WHITELIST)
BLACKLIST = os.getenv("VAR_BLACKLIST", BLACKLIST)
proxy_enable = os.getenv("VAR_PROXY_ENABLE", proxy_enable)
proxy_login = os.getenv("VAR_PROXY_LOGIN", proxy_login)
proxy_pass = os.getenv("VAR_PROXY_PASS", proxy_pass)
proxy_ip = os.getenv("VAR_PROXY_IP", proxy_ip)
proxy_port = os.getenv("VAR_PROXY_PORT", proxy_port)
log_folder = os.getenv("VAR_LOG_FOLDER_NAME", log_folder)
log_file = os.getenv("VAR_LOG_FILE_NAME", log_file)
