import os

from loguru import logger
from pydantic import BaseModel, ValidationError
from ruamel.yaml import YAML


class ConfigParameters(BaseModel):
    """Class for validating config parameters for each section."""

    tg_channel: str
    tg_bot_token: str
    vk_token: str
    vk_domain: str

    req_version: float
    req_count: int
    req_filter: str

    single_start: bool
    time_to_sleep: int | float
    skip_ads_posts: bool
    skip_copyrighted_posts: bool
    skip_reposts: bool

    whitelist: list | None
    blacklist: list | None

    last_kwown_post_id: int


class Config:
    def __init__(self) -> None:
        self.check_if_config_exists()
        self.yaml = YAML()
        self.config: dict[str, ConfigParameters] = self.load_config()

    def check_if_config_exists(self) -> None:
        """Checks if config.yaml exists in the root directory.

        Raises:
            FileNotFoundError: If config.yaml doesn't exist.
        """
        if not os.path.exists("config.yaml"):
            raise FileNotFoundError("config.yaml not found")

    def load_config(self) -> dict[str, ConfigParameters]:
        """Loads config.yaml, validates it and returns a dict with ConfigParameters objects.

        Raises:
            ValidationError: If config.yaml is invalid.

        Returns:
            dict[str, ConfigParameters]: A dict with ConfigParameters objects.
        """
        config_to_return: dict[str, ConfigParameters] = {}

        with open("config.yaml") as file:
            config: dict[str, dict] = self.yaml.load(file)

        for key, value in config.items():
            if isinstance(value, dict):
                if "tg_channel" in value and isinstance(value["tg_channel"], int):
                    value["tg_channel"] = str(value["tg_channel"])
            try:
                config_to_return[key] = ConfigParameters(**value)
            except ValidationError as exception:
                logger.error(f"Config for {key} is invalid")
                raise exception

        return config_to_return

    def update_last_known_id(self, config_name: str, last_known_id: int) -> None:
        """Updates last_known_id in config.yaml in the specified section.

        Args:
            config_name (str): Name of the section in the config.
            last_known_id (int): Last known post id.
        """
        with open("config.yaml") as file:
            config: dict[str, dict] = self.yaml.load(file)

        config[config_name]["last_kwown_post_id"] = last_known_id

        with open("config.yaml", "w") as file:
            self.yaml.dump(config, file)
