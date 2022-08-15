from typing import Union

import requests
from loguru import logger


def get_data_from_vk(
    vk_token: str, req_version: float, vk_domain: str, req_filter: str, req_count: int
) -> Union[dict, None]:
    logger.info("Trying to get posts from VK.")
    response = requests.get(
        "https://api.vk.com/method/wall.get",
        params={
            "access_token": vk_token,
            "v": req_version,
            "domain": vk_domain,
            "filter": req_filter,
            "count": req_count,
        },
    )
    data = response.json()
    if "response" in data:
        return data["response"]["items"]
    elif "error" in data:
        logger.error(
            "Error was detected when requesting data from VK: "
            f"{data['error']['error_msg']}"
        )
    return None


def get_video_url(
    vk_token: str,
    req_version: float,
    owner_id: str,
    video_id: str,
    access_key: str,
) -> str:
    if access_key == "":
        video_parameter = f"{owner_id}_{video_id}"
    else:
        video_parameter = f"{owner_id}_{video_id}_{access_key}"

    response = requests.get(
        "https://api.vk.com/method/video.get",
        params={
            "access_token": vk_token,
            "v": req_version,
            "videos": video_parameter,
        },
    )
    data = response.json()
    if "response" in data:
        return data["response"]["items"][0]["files"].get("external", "")
    elif "error" in data:
        logger.error(
            "Error was detected when requesting data from VK: "
            f"{data['error']['error_msg']}"
        )
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
        logger.error(
            "Error was detected when requesting data from VK: "
            f"{data['error']['error_msg']}"
        )
    return ""
