ShouldBotLog = True  # If False bot will not create and keep bot.log file
BLACKLIST = [""]  # You can add words to the blacklist. If a post contains a blacklisted word, the post will be skipped
# BLACKLIST = ["ExAmPlE", "etc", "123456789"] <== That's an example. But be careful. Do not add just one symbol to the list.

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
tgBotForLogToken = ""   # set token here if you want vktgbot to use another bot for logging
                        # leave the variable empty if you want use first bot (tgBotToken) for logging 
                        # don't forget to add this bot to tgLogChannel as administrator 

reqVer = 5.103       # version of VK API (https://vk.com/dev/versions). used for wall.get method
reqCount = 3         # number of posts to send to telegram (2 - 100)
reqFilter = "owner"  # Filter to apply:
                     # "owner" — posts by the wall owner;
                     # "others" — posts by someone else;
                     # "all" — posts by the wall owner and others
                     # "postponed" — timed posts (only available for calls with an access_token)
                     # "suggests" — suggested posts on a community wall

singleStart = False  # if True bot will stop after  first pass through the loop 
timeSleep = 60 * 2  # waiting time between cycle passes
isPinned = False
skipAdsPosts = True  # set True if you want to skip sponsored posts
skipPostsWithCopyright = False

proxyEnable = False     # Set True if telegram is not available in your country
proxyLogin = "bot"      # Login for Socks5 proxy
proxyPass = "12345"     # Password for Socks5 proxy
proxyIp = "myproxy.com" # Socks5 proxy ip
proxyPort = "1234"      # Socks5 proxy port
