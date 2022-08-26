import json
import os

import dotenv

dotenv.load_dotenv()


TG_CHANNEL: str = os.getenv("VAR_TG_CHANNEL", "")
TG_BOT_TOKEN: str = os.getenv("VAR_TG_BOT_TOKEN", "")
VK_TOKEN: str = os.getenv("VAR_VK_TOKEN", "")
VK_DOMAIN: str = os.getenv("VAR_VK_DOMAIN", "")

REQ_VERSION: float = float(os.getenv("VAR_REQ_VERSION", 5.103))
REQ_COUNT: int = int(os.getenv("VAR_REQ_COUNT", 3))
REQ_FILTER: str = os.getenv("VAR_REQ_FILTER", "owner")

SINGLE_START: bool = os.getenv("VAR_SINGLE_START", "").lower() in ("true",)
TIME_TO_SLEEP: int = int(os.getenv("VAR_TIME_TO_SLEEP", 120))
SKIP_ADS_POSTS: bool = os.getenv("VAR_SKIP_ADS_POSTS", "").lower() in ("true",)
SKIP_COPYRIGHTED_POST: bool = os.getenv("VAR_SKIP_COPYRIGHTED_POST", "").lower() in ("true")
SKIP_REPOSTS: bool = os.getenv("VAR_SKIP_REPOSTS", "").lower() in ("true")

WHITELIST: list = json.loads(os.getenv("VAR_WHITELIST", "[]"))
BLACKLIST: list = json.loads(os.getenv("VAR_BLACKLIST", "[]"))
