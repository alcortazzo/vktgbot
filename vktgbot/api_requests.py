from typing import Union

import re
import requests
from loguru import logger


def get_data_from_vk(
    vk_token: str, req_version: float, vk_domain: str, req_filter: str, req_count: int
) -> Union[dict, None]:
    logger.info("Trying to get posts from VK.")

    match = re.search("^(club|public)(\d+)$", vk_domain)
    if match:
        source_param = {"owner_id": "-" + match.groups()[1]}
    else:
        source_param = {"domain": vk_domain}

    response = requests.get(
        "https://api.vk.com/method/wall.get",
        params=dict(
            {
                "access_token": vk_token,
                "v": req_version,
                "filter": req_filter,
                "count": req_count,
            },
            **source_param,
        ),
    )
    data = response.json()
    if "response" in data:
        return data["response"]["items"]
    elif "error" in data:
        logger.error("Error was detected when requesting data from VK: " f"{data['error']['error_msg']}")
    return None


def get_video_url(vk_token: str, req_version: float, owner_id: str, video_id: str, access_key: str) -> str:
    response = requests.get(
        "https://api.vk.com/method/video.get",
        params={
            "access_token": vk_token,
            "v": req_version,
            "videos": f"{owner_id}_{video_id}{'' if not access_key else f'_{access_key}'}",
        },
    )
    data = response.json()
    if "response" in data and data["response"]["items"]:
        return data["response"]["items"][0]["files"].get("external", "")
    elif "error" in data:
        logger.error(f"Error was detected when requesting data from VK: {data['error']['error_msg']}")
    return ""


def get_group_name(vk_token: str, req_version: float, owner_id) -> str:
    response = requests.get(
        "https://api.vk.com/method/groups.getById",
        params={
            "access_token": vk_token,
            "v": req_version,
            "group_id": owner_id,
        },
    )
    data = response.json()
    if "response" in data:
        return data["response"][0]["name"]
    elif "error" in data:
        logger.error(f"Error was detected when requesting data from VK: {data['error']['error_msg']}")
    return ""
